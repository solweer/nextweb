from django.urls import path
from .socialogin_views import SocialMediaLoginView
from .twitter_views import TwitterCallbackView, TwitterLoginView, TwitterLogoutView, TwitterPostView
from .views import HomeView, RecentPostsView, SignupView,LoginView,LogoutView 
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

    path('twitter/login/', TwitterLoginView.as_view(), name='twitter_login'),
    path('twitter/callback/', TwitterCallbackView.as_view(), name='twitter_callback'),
    path('twitter/post/', TwitterPostView.as_view(), name='twitter_post'),
    path('twitter/logout/', TwitterLogoutView.as_view(), name='twitter_logout'),

    path('recent-posts/', RecentPostsView.as_view(), name="recent-posts"), #recentposts.html
    
    path('connect/', SocialMediaLoginView.as_view(), name='socialmedialogin'), #socialogin.html

]
