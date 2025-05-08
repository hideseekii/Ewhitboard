# projects/urls.py
from django.urls import path
from . import views

app_name = 'projects'

urlpatterns = [
    path('', views.project_list, name='list'),
    path('new/', views.project_create, name='create'),
    path('<int:pk>/', views.project_detail, name='detail'),
    path('<int:pk>/edit/', views.project_edit, name='edit'),
    path('<int:pk>/delete/', views.project_delete, name='delete'),
    path('<int:pk>/add_collaborator/', views.add_collaborator, name='add_collaborator'),
    path('<int:pk>/remove_collaborator/<int:user_id>/', views.remove_collaborator, name='remove_collaborator'),
]