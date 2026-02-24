from django.contrib import admin
from django.urls import path, include
from django.conf import settings               # <--- Add this
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('guest.urls')), # This connects your home page
    path('admin-panel/', include('adminpanel.urls')),
    path('', include('doer.urls')),
    path('', include('giver.urls')),
    
    
    
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)