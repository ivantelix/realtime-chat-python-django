import json
import time
import logging
from datetime import datetime
import redis
from django.conf import settings
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from .models import Conversation, Message
from users.models import CustomUser

logger = logging.getLogger(__name__)

# Connect to Redis
redis_instance = redis.StrictRedis(
    host=settings.CHANNEL_LAYERS['default']['CONFIG']['hosts'][0][0], 
    port=settings.CHANNEL_LAYERS['default']['CONFIG']['hosts'][0][1], 
    db=0,
    decode_responses=True
)

THROTTLE_RATE_SECONDS = 1  # 1 message per second


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.conversation_group_name = f'chat_{self.conversation_id}'
        self.user = self.scope['user']

        logger.info(f"WebSocket connection attempt - User: {self.user}, Conversation: {self.conversation_id}")

        # Check if user is authenticated and authorized
        if self.user.is_authenticated:
            is_authorized = await self.check_user_authorization()
            if is_authorized:
                await self.channel_layer.group_add(
                    self.conversation_group_name,
                    self.channel_name
                )
                await self.accept()
                logger.info(f"WebSocket connected - User: {self.user.username}, Conversation: {self.conversation_id}")
            else:
                logger.warning(f"Unauthorized WebSocket attempt - User: {self.user.username}, Conversation: {self.conversation_id}")
                await self.close(code=4003)
        else:
            logger.warning(f"Unauthenticated WebSocket attempt - Conversation: {self.conversation_id}")
            await self.close(code=4001)

    async def disconnect(self, close_code):
        logger.info(f"WebSocket disconnected - User: {self.user}, Conversation: {self.conversation_id}, Code: {close_code}")
        await self.channel_layer.group_discard(
            self.conversation_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        try:
            # Throttling check
            throttle_key = f"throttle_{self.user.id}_{self.conversation_id}"
            last_message_time = redis_instance.get(throttle_key)

            if last_message_time and (time.time() - float(last_message_time)) < THROTTLE_RATE_SECONDS:
                logger.warning(f"Throttled message - User: {self.user.username}, Conversation: {self.conversation_id}")
                await self.send(text_data=json.dumps({
                    'error': 'You are sending messages too fast. Please wait a moment.'
                }))
                return

            redis_instance.set(throttle_key, time.time(), ex=THROTTLE_RATE_SECONDS)

            text_data_json = json.loads(text_data)
            message_content = text_data_json.get('message', '').strip()

            if not message_content:
                await self.send(text_data=json.dumps({
                    'error': 'Message content cannot be empty.'
                }))
                return

            # Save message to database
            message = await self.save_message(self.user, self.conversation_id, message_content)

            # Save message to Redis for fast retrieval
            await self.save_message_to_redis(message)

            logger.info(f"Message saved - User: {self.user.username}, Conversation: {self.conversation_id}")

            # Broadcast message to room group
            await self.channel_layer.group_send(
                self.conversation_group_name,
                {
                    'type': 'chat_message',
                    'message_id': message.id,
                    'message': message.content,
                    'sender_id': self.user.id,
                    'sender': self.user.username,
                    'timestamp': message.timestamp.isoformat(),
                }
            )
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON received - User: {self.user.username}")
            await self.send(text_data=json.dumps({
                'error': 'Invalid message format.'
            }))
        except Exception as e:
            logger.error(f"Error processing message - User: {self.user.username}, Error: {str(e)}")
            await self.send(text_data=json.dumps({
                'error': 'Failed to process message.'
            }))

    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message_id': event['message_id'],
            'message': event['message'],
            'sender_id': event['sender_id'],
            'sender': event['sender'],
            'timestamp': event['timestamp'],
        }))

    @sync_to_async
    def check_user_authorization(self):
        """Check if user is participant in the conversation"""
        try:
            conversation = Conversation.objects.get(id=self.conversation_id)
            return conversation.participants.filter(id=self.user.id).exists()
        except Conversation.DoesNotExist:
            return False

    @sync_to_async
    def save_message(self, sender, conversation_id, message_content):
        """Save message to database"""
        conversation = Conversation.objects.get(id=conversation_id)
        message = Message.objects.create(
            sender=sender,
            conversation=conversation,
            content=message_content
        )
        return message

    async def save_message_to_redis(self, message):
        """Save message to Redis for fast retrieval"""
        try:
            message_key = f"conversation:{self.conversation_id}:messages"
            message_data = json.dumps({
                'id': message.id,
                'sender_id': message.sender.id,
                'sender': message.sender.username,
                'content': message.content,
                'timestamp': message.timestamp.isoformat()
            })
            # Use Redis list to store messages (LPUSH adds to beginning, newest first)
            redis_instance.lpush(message_key, message_data)
            # Keep only last 100 messages in Redis for performance
            redis_instance.ltrim(message_key, 0, 99)
            # Set expiry to 24 hours (messages remain in DB permanently)
            redis_instance.expire(message_key, 86400)
        except Exception as e:
            logger.error(f"Failed to save message to Redis: {str(e)}")
