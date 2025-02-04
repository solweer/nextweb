from django.views import View
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
import requests
import secrets
import base64
import hashlib
from nextweb import secret
from oauth.models import Userprofile, XToken

class HomeView(View):
    def get(self, request):
        return render(request, 'home.html')

class SignupView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('home')
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
        except ValidationError as e:
            messages.error(request, e.messages[0])
            return redirect('signup')

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password1
        )
        auth_login(request, user)
        return redirect('home')

class LoginView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return render(request, 'login.html')

    def post(self, request):
        user_email = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(request, username=user_email, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid email or password")
            return redirect('login')
        
class LogoutView(View):
    def get(self, request):
        if request.user.is_authenticated:
            auth_logout(request)
            return redirect('/login/')
        
class XOAuthConfig:
    AUTH_URL = 'https://twitter.com/i/oauth2/authorize'
    TOKEN_URL = 'https://api.twitter.com/2/oauth2/token'
    CLIENT_ID = secret.X_CLIENT_ID
    CLIENT_SECRET = secret.X_CLIENT_SECRET
    REDIRECT_URI = secret.X_REDIRECT_URI
    OAUTH1_CALLBACK = secret.X_OAUTH1_CALLBACK
    API_KEY = secret.X_API_KEY
    API_SECRET = secret.X_API_SECRET 

def x_login(request):
    try:
        code_verifier = secrets.token_urlsafe(32)
        request.session['code_verifier'] = code_verifier
        
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode()).digest()
        ).rstrip(b'=').decode()

        auth_url = (
            f"{XOAuthConfig.AUTH_URL}?"
            f"response_type=code&"
            f"client_id={XOAuthConfig.CLIENT_ID}&"
            f"redirect_uri={XOAuthConfig.REDIRECT_URI}&"
            f"scope=tweet.read tweet.write users.read offline.access&"
            f"state={request.session.session_key}&"
            f"code_challenge={code_challenge}&"
            f"code_challenge_method=S256"
        )
        
        return redirect(auth_url)

    except Exception as e:
        return HttpResponse(f'Error in X login: {str(e)}', status=400)
    
def x_callback(request):
    code = request.GET.get('code')
    if not code:
        return HttpResponse('Authorization code not received.', status=400)

    code_verifier = request.session.get('code_verifier')
    if not code_verifier:
        return HttpResponse('Code verifier not found.', status=400)

    response = requests.post(
        XOAuthConfig.TOKEN_URL,
        data={
            'code': code,
            'grant_type': 'authorization_code',
            'client_id': XOAuthConfig.CLIENT_ID,
            'redirect_uri': XOAuthConfig.REDIRECT_URI,
            'code_verifier': code_verifier
        },
        auth=(XOAuthConfig.CLIENT_ID, XOAuthConfig.CLIENT_SECRET)
    )

    if response.status_code != 200:
        return HttpResponse(f"Failed to obtain access token: {response.text}", status=400)

    token_data = response.json()

    user_response = requests.get(
        'https://api.twitter.com/2/users/me',
        headers={'Authorization': f'Bearer {token_data["access_token"]}'}
    )

    if user_response.status_code != 200:
        return HttpResponse(f"Failed to get user info: {user_response.text}", status=400)

    x_user_data = user_response.json()['data']

    try:
        userprofile = Userprofile.objects.get(x_id=x_user_data['id'])
        user = userprofile.user
    except Userprofile.DoesNotExist:
        username = f"x_{x_user_data['username']}"
        user = User.objects.create_user(
            username=username,
            email=f"{username}@placeholder.com"
        )
        Userprofile.objects.create(
            user=user,
            name=x_user_data.get('name', username),
            email=f"{username}@placeholder.com",
            x_id=x_user_data['id']
        )

    XToken.objects.update_or_create(
        user=user,
        defaults={
            'access_token': token_data['access_token'],
            'refresh_token': token_data.get('refresh_token', ''),
            'expires_in': token_data.get('expires_in', 7200)
        }
    )
    
    request.session.pop('code_verifier', None)
    login(request, user)
    return redirect('dashboard')


@login_required
def dashboard(request):
    return render(request, 'dashboard.html')

def logout_view(request):
    if request.user.is_authenticated:
        try:
            token = XToken.objects.get(user=request.user)
            requests.post(
                'https://api.twitter.com/2/oauth2/revoke',
                data={
                    'token': token.access_token,
                    'client_id': XOAuthConfig.CLIENT_ID,
                },
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            token.delete()
        except XToken.DoesNotExist:
            pass
        except Exception as e:
            print(f"Error during token revocation: {e}")

    logout(request)
    return redirect('login')

def post_now(request):
    if request.method != 'POST':
        return redirect('dashboard')
    
    if not request.user.is_authenticated:
        messages.error(request, 'User not authenticated')
        return redirect('login')
    
    try:
        x_token = XToken.objects.get(user=request.user)
        content = request.POST.get('content', '').strip()
        
        if not content:
            messages.error(request, 'Post content cannot be empty')
            return redirect('dashboard')
        tweet_data = {'text': content}
        
        response = requests.post(
            'https://api.twitter.com/2/tweets',
            headers={
                'Authorization': f'Bearer {x_token.access_token}',
                'Content-Type': 'application/json'
            },
            json=tweet_data
        )

        if response.status_code == 201:
            messages.success(request, 'Tweet posted successfully!')
        else:
            messages.error(request, 'Failed to post tweet. Please try again.')
        
        return redirect('dashboard')
    
    except XToken.DoesNotExist:
        messages.error(request, 'X account not connected')
        return redirect('dashboard')
    
    except Exception as e:
        messages.error(request, 'An unexpected error occurred')
        return redirect('dashboard')

@login_required
def dashboard(request):
    context = {
        'is_x_connected': hasattr(request.user, 'xtoken')
    }
    return render(request, 'dashboard.html', context)