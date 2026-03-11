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


    # Main Messages Inbox
    path('messages/', views.doer_chat_inbox, name='doer_chat_inbox'),
    
    # Specific Chat Selection in Inbox (Changed from task_id to giver_id)
    path('messages/<int:giver_id>/', views.doer_chat_inbox, name='doer_chat_inbox'),
    path('my-hired-jobs/', views.doer_hired_jobs, name='doer_hired_jobs'),
    path('submit-task-approval/', views.submit_task_for_approval, name='submit_task_for_approval'),
    path('doer/rate-giver/', views.doer_rate_giver, name='doer_rate_giver'),
    path('doer/history/', views.doer_completed_history, name='doer_completed_history'),
    # URL for the single-page skill and location management
path('manage-preferences/<int:user_id>/', views.manage_doer_preferences, name='manage_preferences'),
path('view-doer/<int:doer_id>/', views.public_doer_profile, name='public_doer_profile'),
]