from django.db import models

class District(models.Model):
    district_name = models.CharField(max_length=100)
    status = models.CharField(max_length=20, default='Active')

    def __str__(self):
        return self.district_name

class Place(models.Model):
    district = models.ForeignKey(District, on_delete=models.CASCADE, related_name='places')
    place_name = models.CharField(max_length=100)
    status = models.CharField(max_length=20, default='Active')

    def __str__(self):
        return self.place_name

class Pincode(models.Model):
    place = models.ForeignKey(Place, on_delete=models.CASCADE, related_name='pincodes')
    pincode_number = models.CharField(max_length=10)
    status = models.CharField(max_length=20, default='Active')

    def __str__(self):
        return self.pincode_number
    
class Category(models.Model):
    # Added unique constraint to prevent duplicates
    category_name = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20, default='Active')

    def __str__(self):
        return self.category_name

class Skill(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='skills')
    skill_name = models.CharField(max_length=100)
    status = models.CharField(max_length=20, default='Active')

    def __str__(self):
        return f"{self.skill_name} ({self.category.category_name})"