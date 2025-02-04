from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Userprofile(models.Model):
    name = models.TextField()
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    email = models.EmailField(unique=True)
    x_id = models.CharField(max_length=100, unique=True, null=True)

class Providers(models.Model):
    name = models.TextField(primary_key=True)
    base_url = models.URLField()

class Tokens(models.Model):
    token_name = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    provider = models.ForeignKey(Providers, on_delete=models.CASCADE)
    token = models.TextField()

class OAuthCredentials(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='oauthcredentials')
    provider = models.CharField(max_length=20, choices=[
        ('twitter_v1', 'Twitter API v1.1'),
        ('twitter_v2', 'Twitter API v2')
    ])
    consumer_key = models.CharField(max_length=100, blank=True)
    consumer_secret = models.CharField(max_length=100, blank=True)
    access_token = models.CharField(max_length=100, blank=True)
    access_token_secret = models.CharField(max_length=100, blank=True)
    client_id = models.CharField(max_length=100, blank=True)
    client_secret = models.CharField(max_length=100, blank=True)
    
    class Meta:
        unique_together = ['user', 'provider']
        
    def __str__(self):
        return f"{self.user.username} - {self.provider}"   

class XToken(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    access_token = models.TextField()
    refresh_token = models.TextField()
    expires_in = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Token for {self.user.username}"

    @property
    def is_expired(self):
        return timezone.now() >= self.created_at + timezone.timedelta(seconds=self.expires_in)