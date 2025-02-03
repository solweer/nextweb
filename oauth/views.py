from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth import authenticate,login, logout
from django.contrib import messages
from django import forms
from .models import Userprofile
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout

class HomeView(View):
    def get(self, request):
        return render(request, 'home.html')

class SignupForm(forms.Form):
    email = forms.EmailField()
    password1 = forms.CharField(widget=forms.PasswordInput())
    password2 = forms.CharField(widget=forms.PasswordInput())

class SignupView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('home')
        return render(request, 'signup.html', {'form': SignupForm()})

    def post(self, request):
        form = SignupForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password1 = form.cleaned_data['password1']
            password2 = form.cleaned_data['password2']

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
            login(request, user)
            return redirect('home')

        return render(request, 'signup.html', {'form': form})

class LoginView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('/')
        return render(request, 'login.html')

    def post(self, request):
        user_email = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(request, username=user_email, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect('/')
        else:
            messages.error(request, "Invalid email or password")
            return redirect('/login/')

class LogoutView(View):
    def get(self, request):
        if request.user.is_authenticated:
            auth_logout(request)
            return redirect('/login/')