from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('workspace/', views.workspace, name='workspace'),
    path('convert/', views.convert, name='convert'),
    path('chat/', views.chat, name='chat'),
    path('download/', views.download_excel, name='download_excel'),
]
