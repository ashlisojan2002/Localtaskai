from django.urls import path
from . import views
from django.conf import settings

urlpatterns = [
path('giver/profile/', views.giver_profile_view, name='giver_profile_view'),
path('giver/profile/edit/', views.giver_profile_edit, name='giver_profile_edit'),
path('giver/profile/password/', views.giver_change_password, name='giver_change_password'),
path('giver/profile/delete/', views.giver_account_delete, name='giver_account_delete'),
path('giver/verify/', views.giver_verification, name='giver_verification'),
]