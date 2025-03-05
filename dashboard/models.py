from django.db import models

# Create your models here.
class prompt(models.Model):
    content = models.TextField()
    role = models.CharField(max_length=6)
    type = models.CharField(max_length=20)
    purpose = models.CharField(max_length=50)