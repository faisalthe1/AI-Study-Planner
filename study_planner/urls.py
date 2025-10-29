from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from planner import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
     path('logout/', views.custom_logout, name='logout'),
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('password-change/', auth_views.PasswordChangeView.as_view(
        template_name='registration/password_change.html'), name='password_change'),
    path('password-change/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='registration/password_change_done.html'), name='password_change_done'),
        path('tasks/', include([
        path('', views.task_list, name='task_list'),
        path('create/', views.task_create, name='task_create'),
        path('<int:pk>/edit/', views.task_edit, name='task_edit'),
        path('<int:pk>/delete/', views.task_delete, name='task_delete'),
    ])),
    
    path('courses/', include([
        path('', views.course_list, name='course_list'),
        path('create/', views.course_create, name='course_create'),
        path('<int:pk>/edit/', views.course_edit, name='course_edit'),
        path('<int:pk>/delete/', views.course_delete, name='course_delete'),
    ])),
    
    path('calendar/', views.calendar_view, name='calendar'),
    path('calendar/events/', views.calendar_events, name='calendar_events'),
    path('generate-schedule/', views.generate_schedule, name='generate_schedule'),
    path('api/study-sessions/', views.api_study_sessions, name='api_study_sessions'),
    
    # API endpoints for Java notification service
    path('api/upcoming-tasks/', views.api_upcoming_tasks, name='api_upcoming_tasks'),
]