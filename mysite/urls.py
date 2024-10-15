from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('cadastro/', include('cadastro.urls')),  # Inclui as URLs da app cadastro
        # URL de login
    path('', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    
    # URL de logout
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]
