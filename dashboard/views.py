from django.shortcuts import redirect, render
from django.views import View
from django.contrib import messages
from oauth.config import OAUTH_CONFIG
from oauth.models import OAuthToken, UserProfile

# Create your views here.
class DashboardView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')

        try:
            user_profile = request.user.userprofile
        except UserProfile.DoesNotExist:
            messages.error(request, "Please complete your registration.")
            return redirect('home')

        connections = OAuthToken.objects.filter(user=user_profile)
        platforms_status = self._get_platforms_status(connections)

        return render(request, 'dashboard.html', {
            'user': request.user,
            'platforms': platforms_status,
            'total_connections': connections.count(),
            'account_created': request.user.date_joined
        })

    def _get_platforms_status(self, connections):
        status = {platform: {'name': platform.capitalize(), 'is_connected': False} for platform in OAUTH_CONFIG.keys()}

        for conn in connections:
            platform = conn.provider
            if platform in status:
                status[platform]['is_connected'] = True
                status[platform]['connected_at'] = conn.created_at

        return status
