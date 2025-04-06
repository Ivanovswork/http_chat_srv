from rest_framework import serializers
from .models import Messages, User


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('id', 'username')


class MessageSerializer(serializers.ModelSerializer):
    recipient_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Messages
        fields = ['id', 'sender_id', 'recipient_id', 'text', 'datetime']
        read_only_fields = ['id', 'sender_id', 'datetime']

    def create(self, validated_data):
        validated_data['sender_id'] = self.context['request'].user
        return super().create(validated_data)
