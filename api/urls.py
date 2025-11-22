from django.urls import path
from . import views

urlpatterns = [
    path('analyze/text/', views.analyze_text, name='analyze_text'),
    path('analyze/image/', views.analyze_image, name='analyze_image'),
    path('resources/support/', views.support_resources, name='support_resources'),
    path('resources/tips/', views.safety_tips, name='safety_tips'),
    path('health/', views.health_check, name='health_check'),
]