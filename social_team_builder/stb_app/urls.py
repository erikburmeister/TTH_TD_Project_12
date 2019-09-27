from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from . import views

app_name = 'stb_app'
urlpatterns = [
    # ----- Home Page -----
    path('home/', views.index, name='home'),
    path('home/project_needs/<str:skill_needed>', views.index, name='home_skill_needed'),
    # ----- Features -----
    path('notifications/', views.notifications, name='notifications'),
    path('search/', views.search, name='search'),
    # ----- Profile stuff -----
    path('my_profile', views.my_profile, name='my_profile'),
    path('profile/<int:pk>', views.profile, name='profile'),
    path('profile_new/', views.profile_new, name='profile_new'),
    path('profile_edit/<int:pk>', views.profile_edit, name='profile_edit'),
    # ----- Application stuff -----
    path('applications/', views.applications, name='applications'),
    path('applications/<str:applications>/<str:project>', views.applications, name='applications_project'),
    path('applications/<str:applications>/<str:project>/<str:choice>/<int:app_pk>',views.applications, name='applications_choice'),
    # ----- Project stuff -----
    path('project/<int:project_pk>/', views.project, name='project'),
    path('project_new/', views.project_new, name='project_new'),
    path('project_edit/<int:project_pk>', views.project_edit, name='project_edit'),
    path('project/<int:project_pk>/<int:position_pk>/<str:choice>', views.project, name='project_position'),
    path('project/delete/<int:project_pk>', views.project_delete, name='project_delete'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
