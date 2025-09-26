from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('assets/', views.assets, name='assets'),
    path('requests/', views.requests, name='requests'),
    path('signup/', views.signup, name='signup'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('asset/delete/<int:pk>/', views.asset_delete, name='asset_delete'),
    path('probate/upload/', views.probate_upload, name='probate_upload'),
    path('probate/review/', views.review_queue, name='review_queue'),
    path('probate/review/<int:pk>/<str:action>/', views.review_probate, name='review_probate'),
    path('', views.home, name='home'),
]