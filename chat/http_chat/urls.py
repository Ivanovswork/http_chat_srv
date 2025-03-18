from django.urls import path
from . import views

urlpatterns = [
    path('messages/send/', views.MessageCreateView.as_view(), name='message-send'),
    path('messages/', views.MessageListView.as_view(), name='message-list'),
]