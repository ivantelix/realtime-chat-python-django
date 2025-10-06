import json
import redis
from django.urls import reverse
from django.conf import settings
from rest_framework import status
from rest_framework.test import APITestCase
from channels.testing import WebsocketCommunicator
from channels.routing import URLRouter
from channels.auth import AuthMiddlewareStack
from users.models import CustomUser
from .models import Conversation, Message
from .routing import websocket_urlpatterns


class ConversationAPITest(APITestCase):
    def setUp(self):
        self.user1 = CustomUser.objects.create_user(
            username='user1', 
            password='TestPassword123!', 
            first_name='User', 
            last_name='One',
            email='user1@example.com'
        )
        self.user2 = CustomUser.objects.create_user(
            username='user2', 
            password='TestPassword123!', 
            first_name='User', 
            last_name='Two',
            email='user2@example.com'
        )
        self.client.force_authenticate(user=self.user1)

    def test_create_conversation(self):
        """Ensure we can create a new conversation."""
        url = reverse('conversation-list')
        data = {'participants': [self.user2.id]}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Conversation.objects.count(), 1)
        self.assertIn(self.user1, Conversation.objects.get().participants.all())
        self.assertIn(self.user2, Conversation.objects.get().participants.all())

    def test_list_conversations(self):
        """Ensure we can list the conversations for a user."""
        conversation = Conversation.objects.create()
        conversation.participants.add(self.user1, self.user2)

        url = reverse('conversation-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_list_conversations_unauthenticated(self):
        """Ensure unauthenticated users cannot list conversations."""
        self.client.force_authenticate(user=None)
        url = reverse('conversation-list')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_conversation_detail(self):
        """Ensure we can get conversation details."""
        conversation = Conversation.objects.create()
        conversation.participants.add(self.user1, self.user2)

        url = reverse('conversation-detail', kwargs={'pk': conversation.id})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], conversation.id)

    def test_get_conversation_unauthorized(self):
        """Ensure users cannot access conversations they're not part of."""
        user3 = CustomUser.objects.create_user(
            username='user3',
            password='TestPassword123!',
            first_name='User',
            last_name='Three',
            email='user3@example.com'
        )
        conversation = Conversation.objects.create()
        conversation.participants.add(self.user2, user3)

        url = reverse('conversation-detail', kwargs={'pk': conversation.id})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class MessageAPITest(APITestCase):
    def setUp(self):
        self.user1 = CustomUser.objects.create_user(
            username='user1',
            password='TestPassword123!',
            first_name='User',
            last_name='One',
            email='user1@example.com'
        )
        self.user2 = CustomUser.objects.create_user(
            username='user2',
            password='TestPassword123!',
            first_name='User',
            last_name='Two',
            email='user2@example.com'
        )
        self.conversation = Conversation.objects.create()
        self.conversation.participants.add(self.user1, self.user2)
        self.client.force_authenticate(user=self.user1)

        # Setup Redis connection for testing
        self.redis_client = redis.StrictRedis(
            host=settings.CHANNEL_LAYERS['default']['CONFIG']['hosts'][0][0],
            port=settings.CHANNEL_LAYERS['default']['CONFIG']['hosts'][0][1],
            db=0,
            decode_responses=True
        )

    def tearDown(self):
        # Clean up Redis data after tests
        self.redis_client.flushdb()

    def test_get_messages_from_database(self):
        """Ensure we can retrieve messages from database."""
        # Create some messages
        Message.objects.create(
            conversation=self.conversation,
            sender=self.user1,
            content='Hello from user1'
        )
        Message.objects.create(
            conversation=self.conversation,
            sender=self.user2,
            content='Hello from user2'
        )

        url = reverse('conversation-messages', kwargs={'conversation_id': self.conversation.id})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['messages']), 2)
        self.assertEqual(response.data['source'], 'database')

    def test_get_messages_from_redis(self):
        """Ensure we can retrieve messages from Redis."""
        # Populate Redis with test messages
        message_key = f"conversation:{self.conversation.id}:messages"
        test_message = json.dumps({
            'id': 1,
            'sender_id': self.user1.id,
            'sender': self.user1.username,
            'content': 'Test message',
            'timestamp': '2024-01-01T12:00:00'
        })
        self.redis_client.lpush(message_key, test_message)

        url = reverse('conversation-messages', kwargs={'conversation_id': self.conversation.id})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['messages']), 1)
        self.assertEqual(response.data['source'], 'redis')

    def test_get_messages_unauthorized(self):
        """Ensure users cannot get messages from conversations they're not part of."""
        user3 = CustomUser.objects.create_user(
            username='user3',
            password='TestPassword123!',
            first_name='User',
            last_name='Three',
            email='user3@example.com'
        )
        self.client.force_authenticate(user=user3)

        url = reverse('conversation-messages', kwargs={'conversation_id': self.conversation.id})
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class HealthCheckTest(APITestCase):
    def test_health_check(self):
        """Ensure health check endpoint works."""
        url = reverse('health-check')
        response = self.client.get(url, format='json')
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_503_SERVICE_UNAVAILABLE])
        self.assertIn('status', response.data)
        self.assertIn('database', response.data)
        self.assertIn('redis', response.data)
