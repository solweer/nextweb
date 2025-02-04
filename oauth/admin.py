from django.contrib import admin
from .models import Userprofile, Providers, Tokens

@admin.register(Userprofile)
class UserprofileAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'user')
    search_fields = ('name', 'email', 'user__username')
    raw_id_fields = ('user',)

@admin.register(Providers)
class ProvidersAdmin(admin.ModelAdmin):
    list_display = ('name', 'base_url')
    search_fields = ('name',)

@admin.register(Tokens)
class TokensAdmin(admin.ModelAdmin):
    list_display = ('token_name', 'user', 'provider')
    list_filter = ('provider',)
    search_fields = ('token_name', 'user__username', 'provider__name')
    raw_id_fields = ('user',)