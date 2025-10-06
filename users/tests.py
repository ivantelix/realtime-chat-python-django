from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
from .models import CustomUser


class UserRegistrationTest(APITestCase):
    def test_register_user_success(self):
        """Ensure we can create a new user."""
        url = reverse('user-register')
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'TestPassword123!',
            'first_name': 'Test',
            'last_name': 'User'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CustomUser.objects.count(), 1)
        self.assertEqual(CustomUser.objects.get().username, 'testuser')
        self.assertEqual(CustomUser.objects.get().email, 'test@example.com')

    def test_register_user_fail_no_username(self):
        """Ensure user registration fails without a username."""
        url = reverse('user-register')
        data = {
            'email': 'test@example.com',
            'password': 'TestPassword123!',
            'first_name': 'Test',
            'last_name': 'User'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_user_fail_invalid_email(self):
        """Ensure user registration fails with invalid email."""
        url = reverse('user-register')
        data = {
            'username': 'testuser',
            'email': 'invalid-email',
            'password': 'TestPassword123!',
            'first_name': 'Test',
            'last_name': 'User'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_user_fail_weak_password(self):
        """Ensure user registration fails with weak password."""
        url = reverse('user-register')
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': '123',
            'first_name': 'Test',
            'last_name': 'User'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_user_fail_duplicate_username(self):
        """Ensure user registration fails with duplicate username."""
        CustomUser.objects.create_user(
            username='testuser',
            email='existing@example.com',
            password='TestPassword123!',
            first_name='Existing',
            last_name='User'
        )
        url = reverse('user-register')
        data = {
            'username': 'testuser',
            'email': 'new@example.com',
            'password': 'TestPassword123!',
            'first_name': 'Test',
            'last_name': 'User'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_user_fail_missing_first_name(self):
        """Ensure user registration fails without first name."""
        url = reverse('user-register')
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'TestPassword123!',
            'last_name': 'User'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserAuthenticationTest(APITestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPassword123!',
            first_name='Test',
            last_name='User'
        )

    def test_login_success(self):
        """Ensure we can login with valid credentials."""
        url = reverse('user-login')
        data = {
            'username': 'testuser',
            'password': 'TestPassword123!'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)

    def test_login_fail_invalid_credentials(self):
        """Ensure login fails with invalid credentials."""
        url = reverse('user-login')
        data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_fail_missing_fields(self):
        """Ensure login fails with missing fields."""
        url = reverse('user-login')
        data = {'username': 'testuser'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_profile_authenticated(self):
        """Ensure authenticated user can access profile."""
        self.client.force_authenticate(user=self.user)
        url = reverse('user-profile')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')
        self.assertEqual(response.data['email'], 'test@example.com')

    def test_user_profile_unauthenticated(self):
        """Ensure unauthenticated user cannot access profile."""
        url = reverse('user-profile')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_refresh(self):
        """Ensure we can refresh access token."""
        refresh = RefreshToken.for_user(self.user)
        url = reverse('token-refresh')
        data = {'refresh': str(refresh)}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
