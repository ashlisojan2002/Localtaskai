from django.urls import path
from . import views
from django.conf import settings

urlpatterns = [
path('giver/profile/', views.giver_profile_view, name='giver_profile_view'),
path('giver/profile/edit/', views.giver_profile_edit, name='giver_profile_edit'),
path('giver/profile/password/', views.giver_change_password, name='giver_change_password'),
path('giver/profile/delete/', views.giver_account_delete, name='giver_account_delete'),
path('giver/verify/', views.giver_verification, name='giver_verification'),

    path('post-task/', views.post_task, name='post_task'),
    path('my-tasks/', views.my_tasks, name='my_tasks'),
    path('delete-task/<int:pk>/', views.delete_task, name='delete_task'),
    
    # AJAX Helpers for Dependent Dropdowns
    # These are called by the JavaScript in your HTML to filter the lists
    path('ajax/load-skills/', views.load_skills, name='ajax_load_skills'),
    path('ajax/load-places/', views.load_places, name='ajax_load_places'),
    path('ajax/load-pincodes/', views.load_pincodes, name='ajax_load_pincodes'),
    path('manage-requests/', views.view_task_requests, name='manage_requests'),

path('giver-messages/', views.giver_chat_inbox, name='giver_chat_inbox'),
    path('giver-messages/<int:doer_id>/', views.giver_chat_inbox, name='giver_chat_inbox'),
    path('hire-doer-ajax/', views.hire_doer_ajax, name='hire_doer_ajax'),
    path('giver/hired-tasks/', views.giver_hired_tasks, name='giver_hired_tasks'),

    # 2. The AJAX Action to Close Task and Save Review
    path('giver/complete-and-rate/', views.giver_complete_and_rate, name='giver_complete_and_rate'),
    path('view-giver/<int:giver_id>/', views.public_giver_profile, name='public_giver_profile'),
    
]