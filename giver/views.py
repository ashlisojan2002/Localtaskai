from django.shortcuts import render, redirect
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
import re
from django.core.files.base import ContentFile
import base64

@login_required
def giver_profile_view(request):
    return render(request, 'giver/profile.html')

@login_required
def giver_profile_edit(request):
    user = request.user
    
    if request.method == 'POST':
        # Update fields
        user.name = request.POST.get('name')
        user.phone = request.POST.get('phone')

        # Handle Profile Picture
        if 'photo' in request.FILES:
            user.photo = request.FILES['photo']

        user.save()
        messages.success(request, "Giver profile updated successfully!")
        return redirect('giver_profile_view')

    return render(request, 'giver/edit_profile.html')

@login_required
def giver_change_password(request):
    if request.method == 'POST':
        old_pass = request.POST.get('old_password')
        new_pass = request.POST.get('new_password')
        confirm_pass = request.POST.get('confirm_password')
        user = request.user

        if not user.check_password(old_pass):
            messages.error(request, "The current password you entered is incorrect.")

        elif new_pass != confirm_pass:
            messages.error(request, "New passwords do not match.")

        elif len(new_pass) < 6:
            messages.error(request, "New password must be at least 6 characters long.")

        elif not re.search(r"[A-Za-z]", new_pass) or not re.search(r"[0-9]", new_pass) or not re.search(r"[!@#$%^&*]", new_pass):
            messages.error(request, "Password must contain letters, numbers, and a special character.")

        else:
            user.set_password(new_pass)
            user.save()
            update_session_auth_hash(request, user) # Prevents logout after password change
            messages.success(request, "Giver password updated successfully!")
            return redirect('giver_profile_view')

    return render(request, 'giver/change_password.html')

@login_required
def giver_account_delete(request):
    if request.method == 'POST':
        request.user.delete()
        messages.info(request, "Giver account successfully deleted.")
        return redirect('login_page')

@login_required
def giver_verification(request):
    user = request.user

    # 🚫 Block if 3 attempts already failed
    if user.verification_attempts >= 3 and user.approval_status == "Rejected":
        messages.error(request, "You have reached the maximum verification attempts (3).")
        return render(request, "giver/identity_verification.html")

    if request.method == "POST":

        aadhaar = request.FILES.get('aadhaar_photo_file')
        certificate = request.FILES.get('non_criminal_certificate')
        live_photo_data = request.POST.get('live_photo_data')

        if not all([aadhaar, certificate, live_photo_data]):
            messages.error(request, "Please provide the ID, certificate, and a live photo.")
            return redirect('giver_verification')

        try:
            # Decode Live Photo
            format, imgstr = live_photo_data.split(';base64,')
            ext = format.split('/')[-1]

            user.verification_live_photo = ContentFile(
                base64.b64decode(imgstr),
                name=f'giver_v_live_{user.id}.{ext}'
            )

            # Assign files
            user.adhar_photo = aadhaar
            user.certificate_file = certificate

            # 🔁 Increase attempt count ONLY if previous was rejected
            if user.approval_status == "Rejected":
                user.verification_attempts += 1
            else:
                user.verification_attempts = 1

            # Reset status to Under Review
            user.approval_status = "Under Review"

            user.save()

            messages.success(request, "Verification documents submitted successfully!")
            return redirect('giver_verification')

        except Exception as e:
            messages.error(request, f"An error occurred during submission: {e}")

    return render(request, "giver/identity_verification.html")