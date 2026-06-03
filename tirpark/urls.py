# tirpark/urls.py
from django.urls import path
from . import views

app_name = 'tirpark'

urlpatterns = [
    # API endpoints (برای Next.js)
    path('v1/list/', views.get_parking_list, name='api_list'),
    path('v1/sync/', views.sync_parking_data, name='api_sync'),
    path('v1/history/', views.get_sync_history, name='api_history'),
    path('v1/stats/', views.get_parking_stats, name='api_stats'),
]