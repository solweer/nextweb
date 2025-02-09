from django.contrib import admin
from .models import OAuthToken, PostStatus, UserProfile

admin.site.register(UserProfile)
admin.site.register(OAuthToken)
admin.site.register(PostStatus)
