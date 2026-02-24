from django import forms
from .models import District, Place, Pincode

class DistrictForm(forms.ModelForm):
    class Meta:
        model = District
        fields = ['district_name', 'status']

class PlaceForm(forms.ModelForm):
    class Meta:
        model = Place
        fields = ['district', 'place_name', 'status']

class PincodeForm(forms.ModelForm):
    class Meta:
        model = Pincode
        fields = ['place', 'pincode_number', 'status']