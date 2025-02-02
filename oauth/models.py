from django.db import models
from django.contrib.auth.models import User

class Providers(models.Model):
    name = models.TextField(primary_key=True)
    base_url = models.URLField()

class Tokens(models.Model):
    token_name = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    provider = models.ForeignKey(Providers, on_delete=models.CASCADE)
    token = models.TextField()
