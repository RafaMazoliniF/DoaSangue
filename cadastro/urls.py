from django.urls import path
from . import views
from .views import user_profile_view, logout_view

urlpatterns = [
    path('', views.cadastro_list, name='cadastro_list'),
    path('new/', views.cadastro_create, name='cadastro_create'),
    path('<int:pk>/edit/', views.cadastro_update, name='cadastro_update'),
    path('<int:pk>/delete/', views.cadastro_delete, name='cadastro_delete'),
    path('login', views.login_view, name='login_submit'),
    path('perfil/', user_profile_view, name='user_profile'),
    path('logout/', logout_view, name='logout2'),
]
