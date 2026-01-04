"""
Actividades URL patterns.
"""
from django.urls import path
from . import views

app_name = 'actividades'

urlpatterns = [
    path('', views.ActividadListView.as_view(), name='lista'),
    path('calendario/', views.CalendarioView.as_view(), name='calendario'),
    path('<uuid:pk>/', views.ActividadDetailView.as_view(), name='detalle'),
    path('<uuid:pk>/partial/', views.ActividadDetailPartialView.as_view(), name='detalle_partial'),
    path('programacion/', views.ProgramacionListView.as_view(), name='programacion'),
    path('programacion/importar/', views.ImportarProgramacionView.as_view(), name='importar'),
]
