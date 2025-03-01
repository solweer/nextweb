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

        # twitter platform
        if platforms_status.get('twitter', {}).get('is_connected'):
            twitter_posts = PostStatus.objects.filter(
                user=user_profile, platform='twitter' 
            ).order_by('-created_at')[:3]
            platforms_status['twitter']['recent_posts'] = twitter_posts

        # linkedin platform
        if platforms_status.get('linkedin', {}).get('is_connected'):
            linkedin_posts = PostStatus.objects.filter(
                user=user_profile, platform='linkedin'
            ).order_by('-created_at')[:3]
            platforms_status['linkedin']['recent_posts'] = linkedin_posts

        return render(request, 'dashboard.html', {
            'user': request.user,
            'platforms': platforms_status,
            'total_connections': connections.count(),
            'account_created': request.user.date_joined
        })
    
   #checkbox code 
    def post(self, request):
        """Redirect to the correct post view based on selected platforms."""
        selected_platforms = request.POST.getlist("platforms")
        if not selected_platforms:
            messages.error(request, "Please select at least one platform to post.")
            return redirect("dashboard")

        # Redirect to LinkedInPostView if only LinkedIn is selected
        if selected_platforms == ["linkedin"]:
            return redirect("linkedin-post")

        # Redirect to TwitterPostView if only Twitter is selected
        elif selected_platforms == ["twitter"]:
            return redirect("twitter_post")

        # Handle multiple selections (LinkedIn + Twitter)
        elif "linkedin" in selected_platforms and "twitter" in selected_platforms:
            request.session["post_content"] = request.POST.get("content", "").strip()
            return redirect("multi-post")  # A new view to handle multi-platform posts

        return redirect("dashboard")

    def _get_platforms_status(self, connections):
        status = {platform: {'name': platform.capitalize(), 'is_connected': False} for platform in OAUTH_CONFIG.keys()}

        for conn in connections:
            platform = conn.provider
            if platform in status:
                status[platform]['is_connected'] = True
                status[platform]['connected_at'] = conn.created_at

        return status  
