from django.db import models
from django.conf import settings
from giver.models import Task  # Importing Task from the giver app

class TaskRequest(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Accepted', 'Accepted'),
        ('Rejected', 'Rejected'),
        ('Cancelled', 'Cancelled'),
    ]

    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='task_requests')
    doer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='my_requests')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    
    # Optional: A small note like "I am available tomorrow morning"
    message = models.TextField(blank=True, null=True) 
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # This is key! It prevents a Doer from requesting the same task twice.
        unique_together = ('task', 'doer')

    def __str__(self):
        return f"{self.doer.username} -> {self.task.title} ({self.status})"