from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Remove .as_view() - Consumers are not standard Views
    re_path(r'^ws/tasks/$', consumers.TaskConsumer.as_asgi()), 
]