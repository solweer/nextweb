from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    
    def save(self, *args, **kwargs):
        self.username = self.email 
        super().save(*args, **kwargs)

class Providers(models.Model):
    name = models.TextField(primary_key=True)
    base_url = models.URLField()

class Tokens(models.Model):
    token_name = models.TextField()
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    provider = models.ForeignKey(Providers, on_delete=models.CASCADE)
    token = models.TextField()
