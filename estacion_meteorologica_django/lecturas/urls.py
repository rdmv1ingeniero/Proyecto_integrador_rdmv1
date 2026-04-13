from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_lecturas, name='lista'),
    path('api/lecturas/', views.lecturas_json, name='lecturas_json'),
    path('estaciones/', views.estaciones, name='estaciones'),
    path('historial/', views.historial, name='historial'),
    path('reportes/', views.reportes, name='reportes'),
    path('reporte-pdf/', views.generar_reporte_pdf, name='generar_reporte_pdf'),
    path('mantenimiento/limpiar/', views.eliminar_data_view, name='limpiar_data'),

]
