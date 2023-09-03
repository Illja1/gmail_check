from django.urls import path
from . import views

urlpatterns = [
    path('', views.mark_messages_as_read, name=''),
    
]