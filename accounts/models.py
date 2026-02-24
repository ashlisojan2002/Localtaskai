from django.contrib.auth.models import AbstractUser
from django.db import models

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