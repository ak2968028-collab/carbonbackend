from django.urls import path, include
from carbon_api.auth_views import LoginView, LogoutView, MeView

urlpatterns = [
    path("api/auth/login/",  LoginView.as_view(),  name="auth-login"),
    path("api/auth/logout/", LogoutView.as_view(), name="auth-logout"),
    path("api/auth/me/",     MeView.as_view(),     name="auth-me"),
    path("api/",             include("carbon_api.urls")),
]
