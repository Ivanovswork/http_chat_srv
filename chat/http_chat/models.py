from django.contrib.auth.models import User
from django.db import models


class Messages(models.Model):
    sender_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sender_messages')
    recipient_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recipient_messages')
    text = models.TextField()
    datetime = models.DateTimeField(auto_now_add=True)