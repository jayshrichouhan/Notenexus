from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('auth/', views.auth_view, name='auth'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('instructor/', views.instructor_dashboard_view, name='instructor'),
    path('user/', views.user_dashboard_view, name='user'),
    path('ask-doubt/', views.ask_doubt_view, name='ask_doubt'),
    path('notes/<int:note_id>/view/', views.note_view_redirect, name='note_view'),
    path('notes/<int:note_id>/download/', views.note_download_redirect, name='note_download'),
    path('pyqs/<int:pyq_id>/download/', views.pyq_download_redirect, name='pyq_download'),
    path('user/profile/', views.user_profile_view, name='user_profile'),
    path('instructor/profile/', views.instructor_profile_view, name='instructor_profile'),
    path('about/', views.about_view, name='about'),
]
