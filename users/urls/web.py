from django.urls import path
from django.contrib.auth import views as auth_views

from users.views.web import register, profile, edit_profile, confirm_email

urlpatterns = [
    path('register/', register, name='register'),
    path('confirm-email/<str:token>/', confirm_email, name='confirm-email'),
    path('profile/', profile, name='profile'),
    path('profile/edit/', edit_profile, name='edit-profile'),
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
]
