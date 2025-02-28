from django.shortcuts import redirect, render
from django.views import View
from django.contrib import messages
from oauth.config import OAUTH_CONFIG
from oauth.models import OAuthToken, PostStatus, UserProfile

class DashboardView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')

        user_profile = UserProfile.objects.filter(user=request.user).first()
        if not user_profile:
            messages.error(request, "Please complete your registration.")
            return redirect('home')

        connections = OAuthToken.objects.filter(user=user_profile)
        platforms_status = self._get_platforms_status(connections)

        if not any(platform.get('is_connected', False) for platform in platforms_status.values()):
            if request.path != '/connect/':
                return redirect('socialmedialogin')

        # Twitter-specific logic
        recent_posts = []
        if platforms_status.get('twitter', {}).get('is_connected'):
            recent_posts = PostStatus.objects.filter(
                user=user_profile, platform='twitter' 
            ).order_by('-created_at')[:10]
            platforms_status['twitter']['recent_posts'] = recent_posts

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
