from django.urls import path
from . import views

urlpatterns = [
    path('profile/', views.doer_profile_view, name='doer_profile_view'),
    path('profile/edit/', views.doer_profile_edit, name='doer_profile_edit'),
    path('profile/delete/', views.doer_account_delete, name='doer_account_delete'),
    path('profile/change-password/', views.change_password, name='change_password'),
    path('verification/', views.verification_badge, name='verification_badge'),
    path('task-feed/', views.doer_task_feed, name='doer_task_feed'),


    path('task/<int:task_id>/', views.task_detail_view, name='task_detail'),
    path('task/<int:task_id>/request/', views.request_task, name='request_task'),# Add this line
    path('task/<int:task_id>/cancel/', views.cancel_task_request, name='cancel_task_request'),
    path('my-requests/', views.my_task_requests_view, name='my_requests'),

    path('task/<int:task_id>/chat/', views.chat_with_giver, name='chat_with_giver'), # Add this if missing too
]