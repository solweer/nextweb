from django.urls import path
from oauth import views

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('signup/', views.SignupView.as_view(), name='signup'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
    path('linkedin/login/', views.LinkedInLoginView.as_view(), name='linkedin-login'),
    path('linkedin/callback/', views.LinkedInCallbackView.as_view(), name='linkedin-callback'),
    path('linkedin/post/', views.LinkedInPostView.as_view(), name='linkedin-post'),
    path('linkedin/disconnect/', views.LinkedInLogoutView.as_view(), name='linkedin-disconnect'),
]
