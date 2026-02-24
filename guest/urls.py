from django.urls import path
from . import views
from django.conf import settings

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('login/', views.login_page, name='login_page'),
    path('giver-home/', views.giver_home, name='giver_home'),
    path('doer-home/', views.doer_home, name='doer_home'),
    path('logout/', views.logout_user, name='logout_user'),
]
