from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

class Userprofile(models.Model):
    name = models.TextField()
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    email = models.EmailField(unique=True)
    x_id = models.CharField(max_length=100, unique=True, null=True)
    linkedin_id = models.CharField(max_length=100, unique=True, null=True)

class OAuthProvider(models.Model):
    name = models.CharField(max_length=50, unique=True)
    base_url = models.URLField()

class OAuthToken(models.Model):
    user = models.ForeignKey(Userprofile, on_delete=models.CASCADE, related_name="oauth_tokens")
    provider = models.ForeignKey(OAuthProvider, on_delete=models.CASCADE, related_name="tokens")
    access_token = models.TextField()
    refresh_token = models.TextField(null=True, blank=True) 
    expires_at = models.DateTimeField(null=True, blank=True) 
    scope = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "provider")

    def __str__(self):
        return f"{self.user.user.username} - {self.provider.name}"
    
class PostStatus(models.Model):
    PLATFORM_CHOICES = [
        ("linkedin", "LinkedIn"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("posted", "Posted"),
        ("failed", "Failed"),
    ]

    user = models.ForeignKey(Userprofile, on_delete=models.CASCADE, related_name="post_statuses")
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES, default="linkedin")
    content = models.TextField() 
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="pending")
    post_id = models.CharField(max_length=100, null=True, blank=True)
    error_message = models.TextField(null=True, blank=True) 
    access_token = models.ForeignKey(OAuthToken, on_delete=models.SET_NULL, null=True, blank=True, related_name="posts")
    created_at = models.DateTimeField(auto_now_add=True)  
    updated_at = models.DateTimeField(auto_now=True) 

    def __str__(self):
        return f"{self.platform.capitalize()} Post by {self.user.user.username} - Status: {self.status}"
