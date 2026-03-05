import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .utils import encrypt_message, decrypt_message

class TaskConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = 'public_task_feed'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def new_task_alert(self, event):
        await self.send(text_data=json.dumps(event))

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'
        
        # --- NEW: Also join a personal notification group ---
        self.user_id = self.scope['user'].id
        self.notification_group = f"user_notifications_{self.user_id}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.channel_layer.group_add(self.notification_group, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        await self.channel_layer.group_discard(self.notification_group, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        msg_type = data.get('type')
        sender = self.scope['user']

        if msg_type == 'mark_as_read':
            await self.mark_messages_as_seen(sender)
            await self.channel_layer.group_send(
                self.room_group_name,
                {'type': 'messages_read_receipt'}
            )
            return

        message = data.get('message', '')
        if message.strip():
            await self.save_message(sender, message)

            # 1. Send to the specific Chat Room
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'sender': sender.name,
                    'sender_id': sender.id
                }
            )

            # 2. NEW: Send to the Receiver's Global Notification Channel
            # This ensures the sidebar updates even if they are in a different room
            user_ids = self.room_id.split('_')
            receiver_id = user_ids[1] if str(sender.id) == user_ids[0] else user_ids[0]
            
            await self.channel_layer.group_send(
                f"user_notifications_{receiver_id}",
                {
                    'type': 'global_unread_update',
                    'sender_id': sender.id
                }
            )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event))

    # --- NEW: Handler for global unread updates ---
    async def global_unread_update(self, event):
        await self.send(text_data=json.dumps(event))

    async def messages_read_receipt(self, event):
        await self.send(text_data=json.dumps({'type': 'messages_read'}))

    @database_sync_to_async
    def save_message(self, sender, message):
        from .models import Message
        from accounts.models import User 
        try:
            user_ids = self.room_id.split('_')
            receiver_id = user_ids[1] if str(sender.id) == user_ids[0] else user_ids[0]
            receiver = User.objects.get(id=receiver_id)
            encrypted = encrypt_message(message)
            Message.objects.create(
                sender=sender,
                receiver=receiver,
                encrypted_content=encrypted
            )
        except Exception as e:
            print(f"Error saving message: {e}")

    @database_sync_to_async
    def mark_messages_as_seen(self, user):
        from .models import Message
        user_ids = self.room_id.split('_')
        other_user_id = user_ids[1] if str(user.id) == user_ids[0] else user_ids[0]
        Message.objects.filter(
            sender__id=other_user_id,
            receiver=user,
            is_seen=False
        ).update(is_seen=True)