from django.urls import path
from .views import MessageUpdatesView, MessageCreateView

urlpatterns = [
    path('messages/<int:recipient_id>/', MessageUpdatesView.as_view(), name='message_updates'),
    path('messages/create/', MessageCreateView.as_view(), name='message_create'),
]

