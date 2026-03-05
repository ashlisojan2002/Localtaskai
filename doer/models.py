from django.db import models
from django.conf import settings
from giver.models import Task 



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


    







class Message(models.Model):
    # Keep sender
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    
    # ADD receiver (replacing task)
    receiver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_messages')
    
    # Keep your other fields
    encrypted_content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_seen = models.BooleanField(default=False)

    # REMOVE 'task' if you want a purely direct chat
    # task = models.ForeignKey('giver.Task', on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self):
        return f"From {self.sender.username} to {self.receiver.username}"