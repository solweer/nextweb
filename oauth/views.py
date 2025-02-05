from datetime import timedelta
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils.timezone import now
from django.http import JsonResponse
import requests
from requests_oauthlib import OAuth2Session
from .models import OAuthToken, Userprofile
from .config import OAUTH_CONFIG

# Basic Views
class HomeView(View):
    def get(self, request):
        return render(request, 'home.html')

class SignupView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return render(request, 'signup.html')

    def post(self, request):
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists")
            return redirect('signup')

        if password1 != password2:
            messages.error(request, "Passwords don't match")
            return redirect('signup')

        try:
            validate_password(password1)
            user = User.objects.create_user(username=email, email=email, password=password1)
            Userprofile.objects.create(user=user, email=email, name=email)
            auth_login(request, user)
            return redirect('dashboard')
        except ValidationError as e:
            messages.error(request, e.messages[0])
            return redirect('signup')

class LoginView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return render(request, 'login.html')

    def post(self, request):    
        user = authenticate(
            request,
            username=request.POST.get('email'),
            password=request.POST.get('password')
        )
        if user:
            auth_login(request, user)
            return redirect('dashboard')
        messages.error(request, "Invalid email or password")
        return redirect('login')

class LogoutView(View):
    def get(self, request):
        auth_logout(request)
        return redirect('login')

# Dashboard View
class DashboardView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')

        try:
            user_profile = request.user.userprofile
        except Userprofile.DoesNotExist:
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
            platform = conn.provider.name
            if platform in status:
                status[platform]['is_connected'] = True
                status[platform]['connected_at'] = conn.created_at

        return status

# OAuth Views
class OAuthLoginView(View):
    def get(self, request, platform):
        if not request.user.is_authenticated:
            return redirect('login')

        if platform not in OAUTH_CONFIG:
            messages.error(request, "Unsupported platform")
            return redirect('dashboard')

        oauth_config = OAUTH_CONFIG[platform]
        oauth = OAuth2Session(
            client_id=oauth_config["client_id"],
            redirect_uri=oauth_config["redirect_uri"],
            scope=oauth_config["scopes"]
        )
        authorization_url, state = oauth.authorization_url(oauth_config["authorization_url"])
        request.session[f"{platform}_oauth_state"] = state
        request.session.modified = True

        return redirect(authorization_url)

class OAuthCallbackView(View):
    def get(self, request, platform):
        if not request.user.is_authenticated:
            return redirect('login')

        oauth_config = OAUTH_CONFIG.get(platform)
        if not oauth_config:
            messages.error(request, "Unsupported platform")
            return redirect('dashboard')

        oauth = OAuth2Session(
            client_id=oauth_config["client_id"],
            redirect_uri=oauth_config["redirect_uri"]
        )

        try:
            token = oauth.fetch_token(
                oauth_config["token_url"],
                authorization_response=request.build_absolute_uri(),
                client_secret=oauth_config["client_secret"]
            )

            OAuthToken.objects.update_or_create(
                user=request.user.userprofile,
                provider__name=platform,
                defaults={
                    "access_token": token["access_token"],
                    "refresh_token": token.get("refresh_token"),
                    "expires_at": now() + timedelta(seconds=token.get("expires_in", 3600))
                }
            )
            messages.success(request, f"Successfully connected to {platform}")

        except Exception as e:
            messages.error(request, f"Failed to connect to {platform}: {str(e)}")

        return redirect('dashboard')

class PostNowView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect('login')

        tokens = OAuthToken.objects.filter(
            user=request.user.userprofile,
            expires_at__gt=now()
        )
        connected_platforms = {token.provider.name: True for token in tokens}

        return render(request, 'dasboard.html', {'platforms': connected_platforms})

    def post(self, request):
        if not request.user.is_authenticated:
            return redirect('login')

        content = request.POST.get('content')
        platforms = request.POST.getlist('platforms')

        if not content:
            return JsonResponse({'error': 'Content is required'}, status=400)

        if not platforms:
            return JsonResponse({'error': 'At least one platform is required'}, status=400)

        results = []
        for platform in platforms:
            result = self._post_to_platform(
                request.user.userprofile,
                platform,
                content
            )
            results.append(result)

        return JsonResponse({'results': results})

    def _post_to_platform(self, user_profile, platform, content):
        try:
            token = OAuthToken.objects.get(
                user=user_profile,
                provider__name=platform,
                expires_at__gt=now()
            )

            response = requests.post(
                'https://api.twitter.com/2/tweets',
                json={'text': content},
                headers={
                    'Authorization': f'Bearer {token.access_token}',
                    'Content-Type': 'application/json'
                }
            )

            return {
                'platform': platform,
                'success': response.ok,
                'error': response.text if not response.ok else None
            }
        except OAuthToken.DoesNotExist:
            return {'platform': platform, 'success': False, 'error': 'Not connected or token expired. Please reconnect.'}
        except Exception as e:
            return {'platform': platform, 'success': False, 'error': str(e)}
