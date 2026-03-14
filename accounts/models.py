from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Count

class User(AbstractUser):
    # Registration Fields
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    
    ROLE_CHOICES = (
        ('giver', 'Giver'),
        ('doer', 'Doer'),
        ('admin', 'Admin'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)

    # Post-Login Fields (Updated after approval/login)
    adhar_photo = models.ImageField(upload_to='adhar_photos/', null=True, blank=True)
    photo = models.ImageField(upload_to='profile_photos/', null=True, blank=True)
    certificate_file = models.FileField(upload_to='certificates/', null=True, blank=True)
    verification_attempts = models.IntegerField(default=0)

    # Admin Control
    approval_status = models.CharField(max_length=20, default='pending')
    status = models.CharField(max_length=20, default='Active')
    verification_live_photo = models.ImageField(
    upload_to='verification/live_photos/',
    null=True,
    blank=True
)

    # Login configuration: Use Email instead of Username
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'name']

    def __str__(self):
        return self.email
    



class UserReport(models.Model):
    REPORT_REASONS = [
        ('fake', 'Fake Profile / Scammer'),
        ('harassment', 'Harassment or Rude Behavior'),
        ('payment', 'Payment Issues'),
        ('quality', 'Poor Work Quality / No Show'),
        ('no_show', 'Did Not Do/Finish Task'),
        ('other', 'Other'),
    ]

    # The person filing the report
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reports_filed')
    
    # The person being reported
    reported_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reports_received')
    
    reason = models.CharField(max_length=20, choices=REPORT_REASONS)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Admin can mark as 'Resolved' if the report was fake or handled
    is_resolved = models.BooleanField(default=False)

    def __str__(self):
        return f"Report against {self.reported_user.email} by {self.reporter.email}"
    
