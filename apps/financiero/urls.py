"""
Financiero URL patterns.
"""
from django.urls import path
from . import views

app_name = 'financiero'

urlpatterns = [
    path('', views.DashboardFinancieroView.as_view(), name='dashboard'),
    path('presupuestos/', views.PresupuestoListView.as_view(), name='presupuestos'),
    path('presupuesto/<uuid:pk>/', views.PresupuestoDetailView.as_view(), name='presupuesto_detalle'),
    path('cuadro-costos/', views.CuadroCostosView.as_view(), name='cuadro_costos'),
    path('facturacion/', views.FacturacionView.as_view(), name='facturacion'),
]
