from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import UserCreate, UserLoginView, UserLogoutView, UserProfileView, login_page

urlpatterns = [
    path('register/', UserCreate.as_view(), name='user-register'),
    path('login/', UserLoginView.as_view(), name='user-login'),
    path('logout/', UserLogoutView.as_view(), name='user-logout'),
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('login-page/', login_page, name='user-login-page'),
]
