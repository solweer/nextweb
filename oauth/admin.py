from django.contrib import admin
from .models import Userprofile, OAuthProvider, OAuthToken

@admin.register(Userprofile)
class UserprofileAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'user', 'x_id')
    search_fields = ('name', 'email', 'user__username', 'x_id')
    raw_id_fields = ('user',)
    ordering = ('name',)

@admin.register(OAuthProvider)
class OAuthProviderAdmin(admin.ModelAdmin):
    list_display = ('name', 'base_url')
    search_fields = ('name', 'base_url')
    ordering = ('name',)

@admin.register(OAuthToken)
class OAuthTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'provider', 'access_token', 'expires_at', 'created_at')
    search_fields = ('user__user__username', 'provider__name', 'access_token')
    raw_id_fields = ('user', 'provider')
    list_filter = ('provider',)
    ordering = ('-created_at',)
