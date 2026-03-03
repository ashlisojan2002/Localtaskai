from django.urls import path
from . import views

urlpatterns = [
    path('profile/', views.doer_profile_view, name='doer_profile_view'),
    path('profile/edit/', views.doer_profile_edit, name='doer_profile_edit'),
    path('profile/delete/', views.doer_account_delete, name='doer_account_delete'),
    path('profile/change-password/', views.change_password, name='change_password'),
    path('verification/', views.verification_badge, name='verification_badge'),
    path('task-feed/', views.doer_task_feed, name='doer_task_feed'),
]