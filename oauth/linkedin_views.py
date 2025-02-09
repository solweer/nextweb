from django.shortcuts import redirect
from django.utils import timezone
from datetime import timedelta
from django.contrib import messages
from django.views import View
import requests
from requests_oauthlib import OAuth2Session
from .models import OAuthToken, UserProfile, PostStatus
from .config import OAUTH_CONFIG

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
            provider_user_id = profile_data.get('sub')  
            
            if not provider_user_id:
                raise Exception("Could not retrieve LinkedIn member ID")
            
            user_profile, _ = UserProfile.objects.get_or_create(user=request.user)
            
            OAuthToken.objects.update_or_create(
                user=user_profile,
                provider='linkedin', 
                defaults={
                    'provider_user_id': provider_user_id,
                    'access_token': token['access_token'],
                    'refresh_token': token.get('refresh_token', ''),
                    'expires_at': expires_at,
                    'scope': ' '.join(token.get('scope', []))
                }
            )

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
            user_profile = UserProfile.objects.get(user=request.user)
            token = OAuthToken.objects.get(user=user_profile, provider='linkedin')
            
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
                "author": f"urn:li:person:{token.provider_user_id}",
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
                access_token=token.access_token  
            )

            response = requests.post(
                'https://api.linkedin.com/v2/ugcPosts',
                json=post_data,
                headers=headers
            )

            if response.status_code in [200, 201]:
                post_id = response.json().get('id')
                post_status.status = 'posted'
                post_status.post_id = post_id
                post_status.save()
                messages.success(request, "Post successfully shared on LinkedIn!")
            else:
                raise Exception(f"LinkedIn API Error: {response.text}")

        except OAuthToken.DoesNotExist:
            messages.error(request, "You need to connect your LinkedIn account first.")
            return redirect('linkedin-login')

        except Exception as e:
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
            user_profile = UserProfile.objects.get(user=request.user)
            token = OAuthToken.objects.filter(user=user_profile, provider='linkedin').first()

            if token:
                token.delete()
                messages.success(request, "Successfully disconnected from LinkedIn.")
            else:
                messages.info(request, "No active LinkedIn connection found.")

        except Exception as e:
            messages.error(request, f"Error disconnecting from LinkedIn: {str(e)}")

        return redirect('dashboard')
