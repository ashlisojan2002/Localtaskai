from django.shortcuts import render, redirect
from django.contrib import messages
from accounts.models import User
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout

def index(request):
    return render(request, 'guest/index.html')

def register(request):
    # Get the role from the URL (giver or doer)
    role = request.GET.get('role', 'giver') 
    
    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        confirm_p = request.POST.get('confirmpassword')
        user_role = request.POST.get('role')

        # 1. Validation: Check if passwords match
        if password != confirm_p:
            messages.error(request, "Passwords do not match!")
            return render(request, 'guest/register.html', {'role': role})

        # 2. Validation: Check if email already exists
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered!")
            return render(request, 'guest/register.html', {'role': role})

        # 3. Success: Create the user directly in the Database
        try:
            User.objects.create_user(
                username=email, # Using email as username
                email=email,
                name=name,
                phone=phone,
                password=password,
                role=user_role
            )
            messages.success(request, "Registration successful! Please login.")
            return redirect('login_page')
        except Exception as e:
            messages.error(request, f"Error saving user: {e}")
            return render(request, 'guest/register.html', {'role': role})

    return render(request, 'guest/register.html', {'role': role})

def login_page(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        # Django uses the username field for authentication by default
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            login(request, user)
            # Redirect based on role
            if user.is_superuser:
                return redirect('admin_dashboard')
            if user.role == 'giver':
                return redirect('giver_home')
            else:
                return redirect('doer_home')
        else:
            messages.error(request, "Invalid email or password.")
            
    return render(request, 'guest/login.html')
def giver_home(request):
    return render(request, 'giver/home.html')

def doer_home(request):
    return render(request, 'doer/home.html')


def logout_user(request):
    logout(request)
    return redirect('login_page')