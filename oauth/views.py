from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import OAuthToken, UserProfile
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
            UserProfile.objects.create(user=user, email=email, name=email)
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
