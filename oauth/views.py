from django.db import IntegrityError
from django.utils import timezone
from datetime import timedelta
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
import requests
from requests_oauthlib import OAuth2Session
from .models import OAuthProvider, OAuthToken, PostStatus, Userprofile
from .config import OAUTH_CONFIG

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
    
class LinkedInLoginView(View):
    def get(self, request):
        linkedin = OAuth2Session(
            OAUTH_CONFIG['linkedin']['client_id'],
            redirect_uri=OAUTH_CONFIG['linkedin']['redirect_uri'],
            scope=OAUTH_CONFIG['linkedin']['scopes']
        )
        authorization_url, state = linkedin.authorization_url(OAUTH_CONFIG['linkedin']['authorization_url'])
        request.session['oauth_state'] = state
        return redirect(authorization_url)

class LinkedInCallbackView(View):
    def get(self, request):
        linkedin = OAuth2Session(
            OAUTH_CONFIG['linkedin']['client_id'],
            state=request.session['oauth_state'],
            redirect_uri=OAUTH_CONFIG['linkedin']['redirect_uri']
        )
        
        try:
            token = linkedin.fetch_token(
                token_url=OAUTH_CONFIG['linkedin']['token_url'],
                client_secret=OAUTH_CONFIG['linkedin']['client_secret'],
                authorization_response=request.build_absolute_uri(),
                include_client_id=True
            )
            
            expires_in = token.get('expires_in', 0)
            expires_at = timezone.now() + timedelta(seconds=int(expires_in)) if expires_in else None
            
            headers = {'Authorization': f"Bearer {token['access_token']}"}
            profile_response = requests.get(
                'https://api.linkedin.com/v2/userinfo',
                headers=headers
            )
            
            if not profile_response.ok:
                raise Exception(f"Failed to fetch LinkedIn profile: {profile_response.text}")
                
            profile_data = profile_response.json()
            linkedin_id = profile_data.get('sub') 
            
            if not linkedin_id:
                raise Exception("Could not retrieve LinkedIn member ID")
            
            linkedin_provider = OAuthProvider.objects.get_or_create(
                name="linkedin",
                defaults={"base_url": "https://api.linkedin.com/v2/"}
            )[0]
            existing_profile = Userprofile.objects.filter(linkedin_id=linkedin_id).first()

            if existing_profile:
                if existing_profile.user != request.user:
                    existing_profile.linkedin_id = None
                    existing_profile.save()

                    messages.success(
                        request,
                        "Your LinkedIn account was previously connected to another user. It has now been disconnected."
                    )
                else:
                    messages.info(
                        request,
                        "Your LinkedIn account is already connected."
                    )
            user_profile = request.user.userprofile
            user_profile.linkedin_id = linkedin_id
            if profile_data.get('name'):
                user_profile.name = profile_data.get('name')
            user_profile.save()
            oauth_token = OAuthToken.objects.update_or_create(
                user=user_profile,
                provider=linkedin_provider,
                defaults={
                    'access_token': token['access_token'],
                    'refresh_token': token.get('refresh_token', ''),
                    'expires_at': expires_at,
                    'scope': ' '.join(token.get('scope', []))
                }
            )[0]
            
            messages.success(request, "LinkedIn connected successfully!")

        except Exception as e:
            messages.error(request, f"Error connecting LinkedIn: {str(e)}")
            
        return redirect('dashboard')

class LinkedInPostView(View):
    def post(self, request):
        content = request.POST.get('content')
        if not content:
            messages.error(request, "Content cannot be empty.")
            return redirect('linkedin-post')
        try:
            user_profile = request.user.userprofile
            token = OAuthToken.objects.get(user=user_profile, provider__name='linkedin')

            verify_url = 'https://api.linkedin.com/v2/userinfo'
            headers = {
                'Authorization': f'Bearer {token.access_token}',
            }
            verify_response = requests.get(verify_url, headers=headers)
            
            if verify_response.status_code != 200:
                token.delete()
                messages.error(request, "LinkedIn connection expired. Please reconnect your account.")
                return redirect('linkedin-login')

            headers.update({
                'X-Restli-Protocol-Version': '2.0.0',
                'Content-Type': 'application/json',
            })
            post_data = {
                "author": f"urn:li:person:{user_profile.linkedin_id}",
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {
                            "text": content
                        },
                        "shareMediaCategory": "NONE"
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                }
            }
            post_status = PostStatus.objects.create(
                user=user_profile,
                platform='linkedin',
                content=content,
                status='pending',
                access_token=token
            )

            response = requests.post(
                'https://api.linkedin.com/v2/ugcPosts',
                json=post_data,
                headers=headers
            )

            if response.status_code not in [200, 201]:
                post_data['author'] = f"urn:li:member:{user_profile.linkedin_id}"
                response = requests.post(
                    'https://api.linkedin.com/v2/ugcPosts',
                    json=post_data,
                    headers=headers
                )
            if response.status_code in [200, 201]:
                post_id = response.json().get('id')

                recent_posts_url = f'https://api.linkedin.com/v2/ugcPosts?q=authors&authors=List({post_data["author"]})'
                recent_posts = requests.get(recent_posts_url, headers=headers)
                
                if recent_posts.status_code == 200:
                    post_status.status = 'posted'
                    post_status.post_id = post_id
                    post_status.save()
                    messages.success(request, "Post successfully shared on LinkedIn!")
                else:
                    post_status.status = 'posted'
                    post_status.post_id = post_id
                    post_status.save()
                    messages.success(request, "Post likely shared on LinkedIn. Please verify on your LinkedIn profile.")
            else:
                raise Exception(f"LinkedIn API Error: {response.text}")

        except OAuthToken.DoesNotExist:
            messages.error(request, "You need to connect your LinkedIn account first.")
            return redirect('linkedin-login')
        except Exception as e:
            if 'post_status' in locals():
                post_status.status = 'failed'
                post_status.error_message = str(e)
                post_status.save()
            messages.error(request, f"Error posting on LinkedIn: {str(e)}")

        return redirect('dashboard')
    
class LinkedInLogoutView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            messages.error(request, "You need to be logged in to disconnect LinkedIn.")
            return redirect('login')

        try:
            user_profile = request.user.userprofile
            token = OAuthToken.objects.filter(
                user=user_profile,
                provider__name='linkedin'
            ).first()

            if token:
                token.delete()
                user_profile.linkedin_id = None
                user_profile.save()
                messages.success(request, "Successfully disconnected from LinkedIn.")
            else:
                messages.info(request, "No active LinkedIn connection found.")

        except Exception as e:
            messages.error(request, f"Error disconnecting from LinkedIn: {str(e)}")

        return redirect('dashboard')