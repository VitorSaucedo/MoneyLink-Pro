from django.urls import path
from . import views

app_name = 'ti'

urlpatterns = [
    path('controle-estoque/', views.controle_estoque, name='controle_estoque'),
    path('admin/', views.admin, name='admin'),
    path('controle-salas/', views.controle_salas, name='controle_salas'),
] 