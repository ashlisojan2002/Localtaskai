from django.urls import re_path
from django.urls import path
from . import consumers

websocket_urlpatterns = [
    # Existing Public Task Feed
    re_path(r'^ws/tasks/$', consumers.TaskConsumer.as_asgi()), 
    
    # Existing Direct Chat Room
    path('ws/chat/<str:room_id>/', consumers.ChatConsumer.as_asgi()),
    
    # NEW: Global Update Channel (Required for real-time sidebar badges)
    # This matches the WebSocket URL we added to the base template
    path('ws/chat/global_updates/', consumers.ChatConsumer.as_asgi()),
]