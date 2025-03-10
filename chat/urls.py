from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('room/<uuid:room_id>/', views.room, name='room'),
    path('contacts/', views.contacts, name='contacts'),
    path('add_contact/<int:user_id>/', views.add_contact, name='add_contact'),
    path('remove_contact/<int:contact_id>/', views.remove_contact, name='remove_contact'),
    path('start_chat/<int:user_id>/', views.start_chat, name='start_chat'),
    path('create_group/', views.create_group, name='create_group'),
    path('upload_file/<uuid:room_id>/', views.upload_file, name='upload_file'),
]