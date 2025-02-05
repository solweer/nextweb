from django.contrib import admin
from .models import Userprofile

@admin.register(Userprofile)
class UserprofileAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'user')
    search_fields = ('name', 'email', 'user__username')
    raw_id_fields = ('user',)
