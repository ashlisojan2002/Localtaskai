from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/users/', views.admin_user_management, name='admin_user_management'),

    # Action URL (Accept/Reject/Delete)
    # This matches the <int:user_id> and <str:action> expected by your update_user_status view
    path('admin/user/update/<int:user_id>/<str:action>/', views.update_user_status, name='update_status'),
    
    
    path('location-management/', views.location_management, name='location_management'),

    # Delete Action (Requires the ID of the Pincode)
    path('delete-location/<int:pk>/', views.delete_location, name='delete_location'),

path('delete-place/<int:pk>/', views.delete_place, name='delete_place'),
path('delete-district/<int:pk>/', views.delete_district, name='delete_district'),

# --- Skill & Category Management ---
    
    # Main Management Page (Handles viewing and adding via POST)
    path('skills/', views.skill_management, name='skill_management'),
    
    # Delete Actions
    # Using <int:pk> is the standard professional approach for primary keys
    path('skills/category/delete/<int:pk>/', views.delete_category, name='delete_category'),
    path('skills/delete/<int:pk>/', views.delete_skill, name='delete_skill'),
    path('tasks/', views.admin_task_management, name='admin_task_management'),
path('delete-task/<int:pk>/', views.admin_delete_task, name='admin_delete_task'),
path('enforcement/', views.admin_report_center, name='admin_report_center'),
path('investigate/<int:user_id>/', views.admin_investigate_user, name='admin_investigate_user'),

]