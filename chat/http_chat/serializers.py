from rest_framework import serializers
from .models import Messages, User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username')


class MessageSerializer(serializers.ModelSerializer):
    sender_id = UserSerializer(read_only=True)
    recipient_id = UserSerializer(read_only=True)

    class Meta:
        model = Messages
        fields = ('id', 'sender_id', 'recipient_id', 'text', 'datetime')
        read_only_fields = ('datetime',)