"""
Lineas URL patterns.
"""
from django.urls import path
from . import views

app_name = 'lineas'

urlpatterns = [
    path('', views.LineaListView.as_view(), name='lista'),
    path('<uuid:pk>/', views.LineaDetailView.as_view(), name='detalle'),
    path('<uuid:pk>/torres/', views.TorresLineaView.as_view(), name='torres'),
    path('torre/<uuid:pk>/', views.TorreDetailView.as_view(), name='torre_detalle'),
    path('mapa/', views.MapaLineasView.as_view(), name='mapa'),
]
