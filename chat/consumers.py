import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import Room, Message

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type', 'text')
        content = data.get('message', '')
        file_url = data.get('file_url', '')
        
        # Save message to database
        user = self.scope["user"]
        message = await self.save_message(user, content, message_type, file_url)
        
        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': content,
                'message_type': message_type,
                'file_url': file_url,
                'username': user.username,
                'user_id': user.id,
                'timestamp': str(message.timestamp)
            }
        )

    # Receive message from room group
    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'message_type': event['message_type'],
            'file_url': event.get('file_url', ''),
            'username': event['username'],
            'user_id': event['user_id'],
            'timestamp': event['timestamp']
        }))

    @database_sync_to_async
    def save_message(self, user, content, message_type, file_url):
        room = Room.objects.get(id=self.room_id)
        if file_url:
            # The file is already uploaded via a separate view
            message = Message.objects.create(
                room=room,
                sender=user,
                content=content,
                file=file_url,
                message_type=message_type
            )
        else:
            message = Message.objects.create(
                room=room,
                sender=user,
                content=content,
                message_type=message_type
            )
        return message