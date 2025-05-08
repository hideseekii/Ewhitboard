from django.urls import path
from . import views

app_name = 'boards'

urlpatterns = [
    path('create/<int:project_id>/', views.board_create, name='create'),
    path('<int:pk>/', views.board_detail, name='detail'),
    path('<int:pk>/edit/', views.board_edit, name='edit'),
    path('<int:pk>/delete/', views.board_delete, name='delete'),
    path('<int:pk>/elements/', views.board_elements, name='elements'),
    path('<int:pk>/export/', views.board_export, name='export'),
    path('<int:pk>/record/', views.board_record, name='record'),
]