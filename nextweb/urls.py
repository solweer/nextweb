from django.urls import path
from oauth.views import (
    HomeView, SignupView, LoginView, LogoutView, DashboardView, 
    OAuthLoginView, OAuthCallbackView, PostNowView
)

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('signup/', SignupView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('oauth/login/<str:platform>/', OAuthLoginView.as_view(), name='oauth_login'),
    path('oauth/callback/<str:platform>/', OAuthCallbackView.as_view(), name='oauth_callback'),
    path('post/', PostNowView.as_view(), name='post_now'),
]