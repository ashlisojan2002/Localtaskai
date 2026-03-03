from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
import re
from django.core.files.base import ContentFile
import base64
from django.shortcuts import render
from giver.models import Task  # Import Task from the giver app
from adminpanel.models import District, Category, Skill # Import these from adminpanel
from .models import TaskRequest

@login_required
def doer_profile_view(request):
    # 'doer' will now specifically refer to the person owning this profile
    return render(request, 'doer/profile.html', {'doer': request.user})

@login_required
def doer_profile_edit(request):
    user = request.user
    
    if request.method == 'POST':
        # 1. Update Text Fields
        # We use .get() to avoid MultiValueDictKeyError if a field is missing
        user.name = request.POST.get('name')
        user.phone = request.POST.get('phone')

        # 2. Handle Profile Picture Upload
        # 'photo' matches the name="photo" in your HTML input
        if 'photo' in request.FILES:
            user.photo = request.FILES['photo']

        # 3. Save the changes
        user.save()
        
        # 4. Success Feedback
        messages.success(request, "Profile details updated successfully!")
        
        # Redirect to the profile view page
        return redirect('doer_profile_view')

    # If GET request, just render the edit page
    return render(request, 'doer/edit_profile.html')

@login_required
def doer_account_delete(request):
    if request.method == 'POST':
        request.user.delete()
        messages.info(request, "Account successfully deleted.")
        # Change 'login' to 'login_page'
        return redirect('login_page')# Replace with your login URL name




@login_required
def change_password(request):
    if request.method == 'POST':
        old_pass = request.POST.get('old_password')
        new_pass = request.POST.get('new_password')
        confirm_pass = request.POST.get('confirm_password')
        user = request.user

        # 1️⃣ Check if old password is correct
        if not user.check_password(old_pass):
            messages.error(request, "The current password you entered is incorrect.")

        # 2️⃣ Check if passwords match
        elif new_pass != confirm_pass:
            messages.error(request, "New passwords do not match.")

        # 3️⃣ Length check
        elif len(new_pass) < 6:
            messages.error(request, "New password must be at least 6 characters long.")

        # 4️⃣ Similar to email/username
        elif user.email and user.email.split('@')[0].lower() in new_pass.lower():
            messages.error(request, "Password is too similar to your email.")

        # 5️⃣ Strength validation
        elif not re.search(r"[A-Za-z]", new_pass) \
             or not re.search(r"[0-9]", new_pass) \
             or not re.search(r"[!@#$%^&*]", new_pass):
            messages.error(
                request,
                "Password must contain letters, numbers, and a special character."
            )

        else:
            # ✅ All validations passed
            user.set_password(new_pass)
            user.save()

            # Keep user logged in
            update_session_auth_hash(request, user)

            messages.success(request, "Your password was successfully updated!")
            return redirect('doer_profile_view')

    return render(request, 'doer/change_password.html')


@login_required
def verification_badge(request):
    user = request.user

    # 🚫 Block if already failed 3 times
    if user.verification_attempts >= 3 and user.approval_status == "Rejected":
        messages.error(request, "3 attempts failed. You will not be verified.")
        return render(request, "doer/verification_badge.html")

    if request.method == "POST":
        aadhaar_file = request.FILES.get('aadhaar_photo_file') 
        certificate = request.FILES.get('non_criminal_certificate')
        live_photo_data = request.POST.get('live_photo_data')

        if not all([aadhaar_file, certificate, live_photo_data]):
            messages.error(request, "All files and a live photo are required.")
            return redirect('verification_badge')

        try:
            # 1. Handle Aadhaar Photo Upload
            user.adhar_photo = aadhaar_file 

            # 2. Decode and Handle Live Photo (Base64)
            format, imgstr = live_photo_data.split(';base64,')
            ext = format.split('/')[-1]
            user.verification_live_photo = ContentFile(
                base64.b64decode(imgstr), 
                name=f'v_live_{user.id}.{ext}'
            )
            
            # 3. Handle Certificate
            user.certificate_file = certificate

            # 🔥 IMPORTANT LOGIC
            # If previously rejected, count attempt
            if user.approval_status == "Rejected":
                user.verification_attempts += 1
            elif user.verification_attempts == 0:
                user.verification_attempts = 1

            # After resubmitting → always Under Review
            user.approval_status = "Under Review"

            user.save()

            messages.success(request, "Application submitted! Admin will verify soon.")
            return redirect('verification_badge')

        except Exception as e:
            messages.error(request, f"Error saving: {e}")
    
    return render(request, "doer/verification_badge.html")







@login_required
def doer_task_feed(request):
    # Only show active tasks that are still 'Open'
    tasks = Task.objects.filter(is_active=True, status='Open').order_by('-created_at')
    
    # Get parameters from the URL
    district_id = request.GET.get('district')
    skill_id = request.GET.get('skill')
    min_budget = request.GET.get('min_budget') # Added this
    
    # Apply Filters
    if district_id:
        tasks = tasks.filter(district_id=district_id)
    if skill_id:
        tasks = tasks.filter(skill_id=skill_id)
    if min_budget:
        tasks = tasks.filter(budget__gte=min_budget) # Filter tasks with budget >= min_budget

    context = {
        'tasks': tasks,
        'districts': District.objects.all(),
        'skills': Skill.objects.all(),
    }
    return render(request, 'doer/task_feed.html', context)






@login_required
def task_detail_view(request, task_id):
    # 1. Fetch the task with all related data
    task = get_object_or_404(
        Task.objects.select_related('district', 'place', 'pincode', 'giver', 'category', 'skill'), 
        id=task_id
    )
    
    # 2. Check if the current user (Doer) has already requested this task
    # We look for 'Pending' or 'Accepted' statuses. 
    # If the status is 'Cancelled', they should be able to request it again.
    user_has_requested = TaskRequest.objects.filter(
        task=task, 
        doer=request.user
    ).exclude(status='Cancelled').exists()
    
    return render(request, 'doer/task_detail.html', {
        'task': task,
        'user_has_requested': user_has_requested # This is the key for the button toggle
    })


@login_required
def request_task(request, task_id):
    if request.method == "POST":
        task = get_object_or_404(Task, id=task_id)
        
        # 1. Prevent Givers from requesting their own tasks
        if task.giver == request.user:
            messages.error(request, "You cannot request your own task!")
            return redirect('task_detail', task_id=task.id)

        # 2. Get or Create the request (handles "Multiple Doer" logic)
        obj, created = TaskRequest.objects.get_or_create(
            task=task, 
            doer=request.user
        )

        if created:
            messages.success(request, f"Request sent for {task.title}!")
        else:
            # If it already existed but was 'Cancelled', re-open it
            if obj.status == 'Cancelled':
                obj.status = 'Pending'
                obj.save()
                messages.success(request, "Request re-sent!")
            else:
                messages.info(request, "You have already requested this task.")

        return redirect('task_detail', task_id=task.id)

@login_required
def cancel_task_request(request, task_id):
    if request.method == "POST":
        # Find the specific request by this Doer for this Task
        task_request = get_object_or_404(TaskRequest, task_id=task_id, doer=request.user)
        
        # Change status instead of deleting (better for record keeping)
        task_request.status = 'Cancelled'
        task_request.save()
        
        messages.warning(request, "Your request has been cancelled.")
        return redirect('task_detail', task_id=task_id)



@login_required
def chat_with_giver(request, task_id):
    """
    Placeholder for the chat system.
    We will build the actual messaging logic later.
    """
    task = get_object_or_404(Task, id=task_id)
    # For now, just show a simple message or redirect back
    # We'll replace this with a real chat template soon!
    return render(request, 'doer/chat_placeholder.html', {'task': task})

@login_required
def my_task_requests_view(request):
    # Fetch all requests made by this Doer, ordered by the most recent first
    my_requests = TaskRequest.objects.filter(doer=request.user).select_related(
        'task', 'task__giver', 'task__district', 'task__place'
    ).order_by('-created_at')

    return render(request, 'doer/my_requests.html', {
        'my_requests': my_requests
    })