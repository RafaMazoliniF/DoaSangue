from django.urls import path
from . import views

urlpatterns = [
    path('', views.cadastro_list, name='cadastro_list'),
    path('new/', views.cadastro_create, name='cadastro_create'),
    path('<int:pk>/edit/', views.cadastro_update, name='cadastro_update'),
    path('<int:pk>/delete/', views.cadastro_delete, name='cadastro_delete'),
]
