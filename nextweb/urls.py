from django.urls import path
from oauth import admin
from oauth import views
from oauth.views import (
    HomeView, SignupView, LoginView, LogoutView, DashboardView, 
    OAuthLoginView, OAuthCallbackView, PostNowView
)
from django.contrib import admin

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', HomeView.as_view(), name='home'),
    path('signup/', SignupView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('oauth/login/<str:platform>/', OAuthLoginView.as_view(), name='oauth_login'),
    path('post/', PostNowView.as_view(), name='post_now'),
    path('oauth/callback/<str:platform>/', views.OAuthCallbackView.as_view(), name='oauth_callback'),
]