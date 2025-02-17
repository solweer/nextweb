from django.urls import path
from .views import HomeView, SignupView,LoginView,LogoutView
from .linkedin_views import LinkedInLoginView, LinkedInCallbackView, LinkedInPostView, LinkedInLogoutView

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('signup/', SignupView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('linkedin/login/', LinkedInLoginView.as_view(), name='linkedin-login'),
    path('linkedin/callback/', LinkedInCallbackView.as_view(), name='linkedin-callback'),
    path('linkedin/post/',LinkedInPostView.as_view(), name='linkedin-post'),
    path('linkedin/disconnect/', LinkedInLogoutView.as_view(), name='linkedin-disconnect'),
]