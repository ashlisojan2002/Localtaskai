import json
from channels.generic.websocket import AsyncWebsocketConsumer

class TaskConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = 'public_task_feed'

        # Join the "public_task_feed" group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Leave the group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    # This method receives messages from the group_send in views.py
    async def new_task_alert(self, event):
        # Send message to WebSocket (the browser)
        await self.send(text_data=json.dumps(event))