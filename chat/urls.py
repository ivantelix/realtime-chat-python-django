from django.urls import path
from .views import ConversationListView, ConversationDetailView, ConversationMessagesView, chat_room

urlpatterns = [
    path('conversations/', ConversationListView.as_view(), name='conversation-list'),
    path('conversations/<int:pk>/', ConversationDetailView.as_view(), name='conversation-detail'),
    path('conversations/<int:conversation_id>/messages/', ConversationMessagesView.as_view(), name='conversation-messages'),
    path('room/<int:conversation_id>/', chat_room, name='chat-room'),
]
