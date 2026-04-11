from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_lecturas, name='lista'),
    path('api/lecturas/', views.lecturas_json, name='lecturas_json'),
]
