from django.shortcuts import redirect, render
from django.views import View
from django.contrib import messages
from .config import OAUTH_CONFIG
from .models import OAuthToken, UserProfile

class SocialMediaLoginView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')

        try:
            user_profile = UserProfile.objects.get(user=request.user)
        except UserProfile.DoesNotExist:
            messages.error(request, "Please complete your registration.")
            return redirect('home')

        # Get connections for this user
        connections = OAuthToken.objects.filter(user=user_profile)
        platforms_status = self._get_platforms_status(connections)

        return render(request, 'socialogin.html', {
            'user': request.user,
            'platforms': platforms_status,
            'total_connections': connections.count()
        })

    def _get_platforms_status(self, connections):
        status = {platform.lower(): {'name': platform.capitalize(), 'is_connected': False, 'connected_at': None} 
                for platform in OAUTH_CONFIG.keys()}
        
        for conn in connections:
            platform = conn.provider.lower().strip()
            
            if platform in status:
                status[platform]['is_connected'] = True
                status[platform]['connected_at'] = conn.created_at.strftime('%Y-%m-%d %H:%M:%S')
        
        return status
