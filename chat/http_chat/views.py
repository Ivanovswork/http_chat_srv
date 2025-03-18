from django.shortcuts import render

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication

from . import models
from .serializers import MessageSerializer
from .models import Messages, User
from django.shortcuts import get_object_or_404
from django.db.models import Q


class MessageCreateView(generics.CreateAPIView):
    """
    Представление для отправки сообщения.
    """
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def perform_create(self, serializer):
        """
        Переопределяем для сохранения отправителя, получателя и времени создания.
        """
        sender = self.request.user
        recipient_id = self.request.data.get('recipient_id')
        recipient = get_object_or_404(User, pk=recipient_id)

        serializer.save(sender_id=sender, recipient_id=recipient)


class MessageListView(generics.ListAPIView):
    """
    Представление для получения списка сообщений между двумя пользователями.
    """
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get_queryset(self):
        """
        Возвращает queryset с сообщениями между текущим пользователем (sender) и указанным получателем.
        """
        recipient_id = self.request.query_params.get('recipient_id')
        if not recipient_id:
            return Messages.objects.none()

        try:
            recipient = User.objects.get(pk=recipient_id)
        except User.DoesNotExist:
            return Messages.objects.none()

        sender = self.request.user

        queryset = Messages.objects.filter(
            (Q(sender_id=sender, recipient_id=recipient) |
             Q(sender_id=recipient, recipient_id=sender))
        ).order_by('datetime')

        return queryset
