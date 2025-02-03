from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Providers, Tokens

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser',
                                  'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )

@admin.register(Providers)
class ProvidersAdmin(admin.ModelAdmin):
    list_display = ('name', 'base_url')
    search_fields = ('name',)

@admin.register(Tokens)
class TokensAdmin(admin.ModelAdmin):
    list_display = ('token_name', 'user', 'provider')
    list_filter = ('provider',)
    search_fields = ('token_name', 'user__email', 'provider__name')