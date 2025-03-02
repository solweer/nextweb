from django.urls import path
from dashboard.generative_views import generate_social_post
from .views import DashboardView

urlpatterns = [
   path('dashboard/', DashboardView.as_view(), name='dashboard'),
   path('generate_social_post', generate_social_post, name="generate_social_post")
]