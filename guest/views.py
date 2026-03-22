from django.shortcuts import render, redirect
from django.contrib import messages
from accounts.models import User
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout
import random
from django.core.mail import send_mail
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib import messages
from accounts.models import User
from django.views.decorators.cache import never_cache
from django.views.decorators.cache import cache_page

@cache_page(60 * 15)
def index(request):
    return render(request, 'guest/index.html')








@never_cache
def register(request):
    if request.method == "POST":
        # --- 1. RESEND OTP LOGIC ---
        if 'resend_otp' in request.POST:
            reg_data = request.session.get('reg_data')
            if reg_data:
                otp = random.randint(100000, 999999)
                request.session['register_otp'] = otp
                try:
                    send_mail(
                        'Your New OTP - LocalTaskAI',
                        f'Your new verification code is: {otp}',
                        settings.EMAIL_HOST_USER,
                        [reg_data['email']],
                        fail_silently=False,
                    )
                    messages.success(request, "A new OTP has been sent to your email.")
                except Exception as e:
                    messages.error(request, "Failed to resend email. Please check your connection.")
            return render(request, 'guest/register.html', {'otp_sent': True})

        # --- 2. OTP VERIFICATION ---
        if 'otp_verification' in request.POST:
            user_otp = request.POST.get('otp')
            session_otp = request.session.get('register_otp')
            reg_data = request.session.get('reg_data')

            if str(user_otp) == str(session_otp):
                try:
                    User.objects.create_user(
                        username=reg_data['email'],
                        email=reg_data['email'],
                        name=reg_data['name'],
                        phone=reg_data['phone'],
                        password=reg_data['password'],
                        role=reg_data['role']
                    )
                    del request.session['register_otp']
                    del request.session['reg_data']
                    messages.success(request, "Account created successfully! Please login.")
                    return redirect('login_page')
                except Exception as e:
                    messages.error(request, f"Registration failed: {e}")
            else:
                # This specifically handles the "Wrong OTP" issue you mentioned
                messages.error(request, "Invalid OTP code. Please try again.")
                return render(request, 'guest/register.html', {'otp_sent': True})

        # --- 3. INITIAL FORM SUBMISSION ---
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        confirm_p = request.POST.get('confirmpassword')
        role = request.POST.get('role')

        if password != confirm_p:
            messages.error(request, "Passwords do not match!")
            return render(request, 'guest/register.html')

        if User.objects.filter(email=email).exists():
            messages.error(request, "This email is already registered!")
            return render(request, 'guest/register.html')

        # Generate OTP and store in session
        otp = random.randint(100000, 999999)
        request.session['register_otp'] = otp
        request.session['reg_data'] = {
            'name': name, 'email': email, 'phone': phone, 
            'password': password, 'role': role
        }

        try:
            send_mail(
                'Verify your LocalTaskAI Account',
                f'Hello {name}, your OTP is {otp}.',
                settings.EMAIL_HOST_USER,
                [email],
                fail_silently=False,
            )
            messages.info(request, f"Verification code sent to {email}")
            return render(request, 'guest/register.html', {'otp_sent': True})
        except Exception:
            # This handles your "No such mail id" or invalid mail concern
            messages.error(request, "Invalid email address or service error. Please check your mail ID.")
            return render(request, 'guest/register.html')

    return render(request, 'guest/register.html')















@never_cache
def login_page(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        # We use email as the username because of your model configuration
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            login(request, user)
            
            # Redirect logic based on role
            if user.is_superuser:
                return redirect('admin_dashboard')
            elif user.role == 'giver':
                return redirect('giver_home')
            else:
                return redirect('doer_home')
        else:
            messages.error(request, "Invalid email or password.")
            
    return render(request, 'guest/login.html')


# ... (your existing imports and register/login views) ...

# ADD THESE AT THE BOTTOM OF guest/views.py
def giver_home(request):
    return render(request, 'giver/home.html')

def doer_home(request):
    return render(request, 'doer/home.html')

def logout_user(request):
    from django.contrib.auth import logout
    logout(request)
    return redirect('login_page')


@never_cache
def forgot_password(request):
    step = 1  # 1: Email, 2: OTP, 3: New Password
    
    if request.method == "POST":
        # STEP 1: Check Email and Send OTP
        if 'send_otp' in request.POST:
            email = request.POST.get('email')
            try:
                user = User.objects.get(email=email)
                otp = random.randint(100000, 999999)
                request.session['reset_otp'] = otp
                request.session['reset_email'] = email
                
                send_mail(
                    'Password Reset OTP',
                    f'Your OTP for resetting the password is: {otp}',
                    settings.EMAIL_HOST_USER,
                    [email],
                )
                messages.success(request, "OTP has been sent to your registered email.")
                step = 2
            except User.DoesNotExist:
                messages.error(request, "No such mail ID exists in our records.")
                step = 1

        # STEP 2: Verify OTP
        elif 'verify_otp' in request.POST:
            user_otp = request.POST.get('otp')
            if str(user_otp) == str(request.session.get('reset_otp')):
                step = 3
            else:
                messages.error(request, "Incorrect OTP. Please try again.")
                step = 2

        # STEP 3: Reset Password
        elif 'reset_password' in request.POST:
            new_p = request.POST.get('new_password')
            conf_p = request.POST.get('confirm_password')
            if new_p == conf_p:
                email = request.session.get('reset_email')
                user = User.objects.get(email=email)
                user.set_password(new_p)
                user.save()
                messages.success(request, "Password reset successfully! You can now login.")
                return redirect('login_page')
            else:
                messages.error(request, "Passwords do not match.")
                step = 3

    return render(request, 'guest/forgot_password.html', {'step': step})


@cache_page(60 * 60)
def how_it_works(request):
    return render(request, 'guest/how_it_works.html')