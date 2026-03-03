from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.dateparse import parse_datetime # Added this
from adminpanel.models import District, Place, Pincode, Category, Skill

class Task(models.Model):
    STATUS_CHOICES = [
        ('Open', 'Open'),
        ('Accepted', 'Accepted'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
        ('Expired', 'Expired'),
    ]

    giver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tasks_posted')
    doer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks_accepted')
    
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    
    district = models.ForeignKey(District, on_delete=models.SET_NULL, null=True)
    place = models.ForeignKey(Place, on_delete=models.SET_NULL, null=True)
    pincode = models.ForeignKey(Pincode, on_delete=models.SET_NULL, null=True)
    
    title = models.CharField(max_length=150)
    description = models.TextField()
    budget = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='Open')
    
    created_at = models.DateTimeField(auto_now_add=True)
    expiry_at = models.DateTimeField(null=True, blank=True)
    deadline_datetime = models.DateTimeField()
    
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        # 1. FIX: Convert string to datetime object if necessary
        # This prevents the TypeError when saving from a POST request
        if isinstance(self.deadline_datetime, str):
            self.deadline_datetime = parse_datetime(self.deadline_datetime)

        # 2. Logic: Auto-set expiry to match deadline
        if self.deadline_datetime:
            self.expiry_at = self.deadline_datetime

        # 3. Logic: Handle Acceptance
        if self.doer and self.status == 'Open':
            self.status = 'Accepted'
            self.is_active = False
            
        # 4. Logic: Compare datetime objects
        # timezone.now() and self.deadline_datetime are now both datetime objects
        if self.deadline_datetime and self.status == 'Open':
            if timezone.now() > self.deadline_datetime:
                self.status = 'Expired'
                self.is_active = False
            
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} - {self.status}"