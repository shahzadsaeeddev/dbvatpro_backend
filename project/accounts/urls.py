from django.urls import path

from . import views
from .views import UserListView, TechnicianListView, UserRolesListCreateView

app_name="accounts"
urlpatterns = [
    path("auth/", views.GetKeycloakToken.as_view(), name="get_user_token"),
    path("refresh-token/", views.GetKeycloakRefresh.as_view(), name="get_refresh_token"),
    path('user-group/', views.UserRolesView.as_view(), name='user_groups'),
    path('role-group/', UserRolesListCreateView.as_view(), name='user_groups'),
    path('users/', views.UserView.as_view(), name='users'),
    path('users-detail/', UserListView.as_view(), name='user'),
    path('technician-select/', TechnicianListView.as_view(), name='technician_select'),
    path('users/<str:pk>', views.UserDetailView.as_view(), name='users_detail'),
    path('profile/', views.UserProfileView.as_view(), name='users_profile'),
]