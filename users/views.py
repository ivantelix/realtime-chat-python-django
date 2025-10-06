import logging
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as django_login
from django.contrib import messages
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from .models import CustomUser
from .serializers import UserSerializer, UserLoginSerializer

logger = logging.getLogger(__name__)


class UserCreate(generics.CreateAPIView):
    """User registration endpoint"""
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = []  # Allow any user to register
    authentication_classes = []  # No authentication required

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        logger.info(f"User registered - Username: {response.data.get('username')}")
        return response


class UserLoginView(APIView):
    """User login endpoint - returns JWT tokens"""
    permission_classes = []  # Allow any user to login
    authentication_classes = []  # No authentication required
    
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            
            user = authenticate(username=username, password=password)
            
            if user is not None:
                refresh = RefreshToken.for_user(user)
                logger.info(f"User logged in - Username: {username}")
                return Response({
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'first_name': user.first_name,
                        'last_name': user.last_name
                    }
                }, status=status.HTTP_200_OK)
            else:
                logger.warning(f"Failed login attempt - Username: {username}")
                return Response({
                    'error': 'Invalid credentials'
                }, status=status.HTTP_401_UNAUTHORIZED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLogoutView(APIView):
    """User logout endpoint - blacklists refresh token"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                try:
                    token = RefreshToken(refresh_token)
                    token.blacklist()
                    logger.info(f"User logged out - Username: {request.user.username}")
                    return Response({'message': 'Successfully logged out'}, status=status.HTTP_200_OK)
                except AttributeError:
                    # Token blacklist is not installed, just accept the logout
                    logger.info(f"User logged out (blacklist not available) - Username: {request.user.username}")
                    return Response({'message': 'Successfully logged out'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Refresh token required'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Logout error - User: {request.user.username}, Error: {str(e)}")
            return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(APIView):
    """Get current user profile"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


def login_page(request):
    """
    Página de login con interfaz Bootstrap para usuarios del chat
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        next_url = request.POST.get('next', '/api/chat/room/5/')  # Default al chat grupal
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            django_login(request, user)
            logger.info(f"User logged in via web - Username: {username}")
            messages.success(request, f'¡Bienvenido {user.first_name}!')
            return redirect(next_url)
        else:
            logger.warning(f"Failed web login attempt - Username: {username}")
            messages.error(request, 'Usuario o contraseña incorrectos')
    
    next_url = request.GET.get('next', '/api/chat/room/5/')
    return render(request, 'users/login.html', {'next': next_url})
