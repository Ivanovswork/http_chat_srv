
import asyncio
import json

from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from .models import Messages
from django.contrib.auth.models import User
from django.db.models import Q, Max
from asgiref.sync import sync_to_async
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import APIException, NotFound

from .serializers import MessageSerializer
from adrf.views import APIView


class MessageCreateView(APIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    async def post(self, request):
        serializer = MessageSerializer(data=request.data)  # Инициализируем сериализатор здесь
        if await sync_to_async(serializer.is_valid)(raise_exception=True):
            sender = request.user
            validated_data = serializer.validated_data
            recipient_id = validated_data['recipient_id'].id
            text = validated_data['text']

            try:
                recipient = await sync_to_async(User.objects.get)(pk=recipient_id)
            except User.DoesNotExist:
                raise APIException("Recipient does not exist")

            msg = Messages(sender_id=sender, recipient_id=recipient, text=text)
            await sync_to_async(msg.save)()

            saved_msg = await sync_to_async(Messages.objects.get)(pk=msg.pk)
            serialized_data = MessageSerializer(saved_msg).data
            return Response(serialized_data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MessageUpdatesView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    async def get(self, request, recipient_id):
        try:
            recipient = await sync_to_async(User.objects.get)(pk=recipient_id)
        except User.DoesNotExist:
            raise NotFound("Recipient not found")

        sender_id = await sync_to_async(lambda: request.user.id)()

        # Получаем ID последнего сообщения в чате
        last_message_id = await self.get_last_message_id(sender_id, recipient)

        messages_data = await self.check_for_updates(last_message_id, sender_id, recipient)
        return Response({'messages': messages_data}, status=status.HTTP_200_OK)

    async def get_last_message_id(self, sender_id, recipient):
        # Получаем ID последнего сообщения в чате между отправителем и получателем
        result = await sync_to_async(lambda: Messages.objects.filter(
            (Q(sender_id=sender_id, recipient_id=recipient) |
             Q(sender_id=recipient, recipient_id=sender_id))
        ).aggregate(Max('id')))()  # Вызываем aggregate без аргументов

        last_message = result['id__max']

        return last_message if last_message else 0  # Если сообщений нет, возвращаем 0

    # async def check_for_updates(self, last_message_id, sender_id, recipient):
    #     timeout = 30
    #     start_time = asyncio.get_event_loop().time()
    #
    #     while asyncio.get_event_loop().time() - start_time < timeout:
    #         new_messages = await sync_to_async(list)(Messages.objects.filter(
    #             (Q(sender_id=sender_id, recipient_id=recipient) |
    #              Q(sender_id=recipient, recipient_id=sender_id)),
    #             id__gt=last_message_id
    #         ).order_by('datetime'))
    #
    #         if new_messages:
    #             messages_data = [{
    #                 'id': await sync_to_async(lambda m: m.id)(m),
    #                 'sender_id': await sync_to_async(lambda m: m.sender_id.id)(m),
    #                 'recipient_id': await sync_to_async(lambda m: m.recipient_id.id)(m),
    #                 'text': await sync_to_async(lambda m: m.text)(m),
    #                 'datetime': await sync_to_async(lambda m: m.datetime.isoformat())(m)
    #             } for m in new_messages]
    #             return messages_data
    #
    #         await asyncio.sleep(1)
    #
    #     return []

    async def check_for_updates(self, last_message_id, sender_id, recipient):
        timeout = 20
        start_time = asyncio.get_event_loop().time()
        message_sent = False  # Флаг для проверки отправки сообщения

        while asyncio.get_event_loop().time() - start_time < timeout:
            new_messages = await sync_to_async(list)(Messages.objects.filter(
                (Q(sender_id=sender_id, recipient_id=recipient) |
                 Q(sender_id=recipient, recipient_id=sender_id)),
                id__gt=last_message_id
            ).order_by('datetime'))

            if new_messages:
                messages_data = [{
                    'id': await sync_to_async(lambda m: m.id)(m),
                    'sender_id': await sync_to_async(lambda m: m.sender_id.id)(m),
                    'recipient_id': await sync_to_async(lambda m: m.recipient_id.id)(m),
                    'text': await sync_to_async(lambda m: m.text)(m),
                    'datetime': await sync_to_async(lambda m: m.datetime.isoformat())(m)
                } for m in new_messages]

                # Проверка на наличие флага отправки сообщения
                if message_sent:
                    return Response({'status': 'message_sent'}, status=status.HTTP_204_NO_CONTENT)

                return messages_data

            # Проверка на наличие флага отправки сообщения
            if message_sent:
                return Response({'status': 'message_sent'}, status=status.HTTP_204_NO_CONTENT)

            await asyncio.sleep(1)

        return []