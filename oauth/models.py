from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    name = models.TextField()
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    email = models.EmailField(unique=True)

class OAuthToken(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name="oauth_tokens")
    provider = models.CharField(max_length=50)
    provider_user_id = models.CharField(max_length=100, null=True, blank=True) 
    access_token = models.TextField()
    refresh_token = models.TextField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    scope = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "provider", "provider_user_id") 

class PostStatus(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("posted", "Posted"),
        ("failed", "Failed"),
    ]
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name="post_statuses")
    platform = models.CharField(max_length=20, default="linkedin")
    content = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    post_id = models.CharField(max_length=100, null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    access_token = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
