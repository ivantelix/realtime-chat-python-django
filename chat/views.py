import json
import logging
import redis
from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer
from users.models import CustomUser

logger = logging.getLogger(__name__)

# Connect to Redis
redis_instance = redis.StrictRedis(
    host=settings.CHANNEL_LAYERS['default']['CONFIG']['hosts'][0][0],
    port=settings.CHANNEL_LAYERS['default']['CONFIG']['hosts'][0][1],
    db=0,
    decode_responses=True
)


class ConversationListView(generics.ListCreateAPIView):
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.request.user.conversations.all()

    def perform_create(self, serializer):
        participants_data = self.request.data.get('participants', [])
        participants = CustomUser.objects.filter(id__in=participants_data)
        conversation = serializer.save()
        conversation.participants.add(self.request.user, *participants)
        logger.info(f"Conversation created - ID: {conversation.id}, Creator: {self.request.user.username}")


class ConversationDetailView(generics.RetrieveAPIView):
    queryset = Conversation.objects.all()
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.request.user.conversations.all()


class ConversationMessagesView(APIView):
    """
    Retrieve messages for a conversation from Redis (fast) or database (fallback)
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, conversation_id):
        try:
            # Check if user is participant in the conversation
            conversation = Conversation.objects.filter(
                id=conversation_id,
                participants=request.user
            ).first()

            if not conversation:
                return Response(
                    {'error': 'Conversation not found or unauthorized'},
                    status=status.HTTP_404_NOT_FOUND
                )

            # Try to get messages from Redis first
            message_key = f"conversation:{conversation_id}:messages"
            redis_messages = redis_instance.lrange(message_key, 0, -1)

            if redis_messages:
                # Messages found in Redis
                messages = [json.loads(msg) for msg in redis_messages]
                # Reverse to show oldest first
                messages.reverse()
                logger.info(f"Messages retrieved from Redis - Conversation: {conversation_id}, Count: {len(messages)}")
                return Response({
                    'conversation_id': conversation_id,
                    'messages': messages,
                    'source': 'redis'
                })
            else:
                # Fallback to database
                db_messages = Message.objects.filter(
                    conversation_id=conversation_id
                ).order_by('timestamp')[:100]
                
                serializer = MessageSerializer(db_messages, many=True)
                messages = serializer.data

                # Populate Redis cache for future requests
                if messages:
                    self._populate_redis_cache(conversation_id, db_messages)

                logger.info(f"Messages retrieved from DB - Conversation: {conversation_id}, Count: {len(messages)}")
                return Response({
                    'conversation_id': conversation_id,
                    'messages': messages,
                    'source': 'database'
                })

        except Exception as e:
            logger.error(f"Error retrieving messages - Conversation: {conversation_id}, Error: {str(e)}")
            return Response(
                {'error': 'Failed to retrieve messages'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _populate_redis_cache(self, conversation_id, messages):
        """Populate Redis cache with messages from database"""
        try:
            message_key = f"conversation:{conversation_id}:messages"
            for message in messages:
                message_data = json.dumps({
                    'id': message.id,
                    'sender_id': message.sender.id,
                    'sender': message.sender.username,
                    'content': message.content,
                    'timestamp': message.timestamp.isoformat()
                })
                redis_instance.rpush(message_key, message_data)
            redis_instance.expire(message_key, 86400)  # 24 hours
        except Exception as e:
            logger.error(f"Failed to populate Redis cache: {str(e)}")


@login_required
def chat_room(request, conversation_id):
    """
    Vista de la sala de chat con interfaz Bootstrap
    """
    conversation = get_object_or_404(
        Conversation,
        id=conversation_id,
        participants=request.user
    )
    
    context = {
        'conversation_id': conversation_id,
        'conversation': conversation,
        'participants': conversation.participants.all(),
        'user': request.user
    }
    
    return render(request, 'chat/room.html', context)
