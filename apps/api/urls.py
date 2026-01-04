"""
API URL configuration with Django Ninja.
"""
from django.urls import path
from .router import api

urlpatterns = [
    path('', api.urls),
]
