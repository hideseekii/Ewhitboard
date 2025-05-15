# users/urls.py
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

app_name = 'users'

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout/', views.custom_logout, name='logout'),  # 使用自定義登出視圖
    path('profile/', views.profile, name='profile'),
    path('complete-registration/', views.complete_registration, name='complete_registration'),
]