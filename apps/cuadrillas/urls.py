"""
Cuadrillas URL patterns.
"""
from django.urls import path
from . import views

app_name = 'cuadrillas'

urlpatterns = [
    path('', views.CuadrillaListView.as_view(), name='lista'),
    path('<uuid:pk>/', views.CuadrillaDetailView.as_view(), name='detalle'),
    path('mapa/', views.MapaCuadrillasView.as_view(), name='mapa'),
    path('mapa/partial/', views.MapaCuadrillasPartialView.as_view(), name='mapa_partial'),
]
