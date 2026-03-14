from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
import re
from django.core.files.base import ContentFile
import base64
from django.http import JsonResponse
from .models import Task,Review
from adminpanel.models import District, Place, Pincode, Category, Skill
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils import timezone
from datetime import datetime
from django.db.models import Q
from doer.models import TaskRequest, Message 
from doer.utils import decrypt_message
from django.db.models import Q
from accounts.models import User
from django.db import transaction
from django.db.models import Avg, Count
from accounts.models import User, UserReport
from .utils import get_ai_recommended_doers
from django.urls import reverse






@login_required
def giver_profile_view(request):
    # Calculate average rating received by the Giver
    stats = Review.objects.filter(reviewee=request.user).aggregate(
        avg_rating=Avg('rating'),
        total_reviews=Count('id')
    )

    context = {
        'avg_rating': stats['avg_rating'] or 0,
        'total_reviews': stats['total_reviews'] or 0,
    }
    return render(request, 'giver/profile.html', context)

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




def post_task(request):
    if request.method == "POST":
        # 1. Get the string from POST
        deadline_str = request.POST.get('deadline_datetime')
        
        # 2. Safety check: Convert string to a real Python datetime object
        try:
            # Matches 'YYYY-MM-DD HH:MM' format from HTML datetime-local
            # Note: some browsers use 'YYYY-MM-DDTHH:MM', if so, use '%Y-%m-%dT%H:%M'
            naive_datetime = datetime.strptime(deadline_str.replace('T', ' '), '%Y-%m-%d %H:%M')
            aware_deadline = timezone.make_aware(naive_datetime)
        except (ValueError, TypeError):
            # Fallback if date is missing or malformed
            aware_deadline = timezone.now() + timezone.timedelta(days=1)

        # 3. Create the Task
        new_task = Task.objects.create(
            giver=request.user,
            category_id=request.POST.get('category'),
            skill_id=request.POST.get('skill'),
            district_id=request.POST.get('district'),
            place_id=request.POST.get('place'),
            pincode_id=request.POST.get('pincode'),
            title=request.POST.get('title'),
            description=request.POST.get('description'),
            budget=request.POST.get('budget'),
            deadline_datetime=aware_deadline,
        )

        # 4. WEBSOCKET BROADCAST (Channels)
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            'public_task_feed', 
            {
                'type': 'new_task_alert',
                'task_data': {
                    'id': new_task.id,
                    'title': new_task.title,
                    'budget': str(new_task.budget),
                    'district': new_task.district.district_name if new_task.district else "N/A",
                    'place': new_task.place.place_name if new_task.place else "N/A",
                }
            }
        )
        return redirect('my_tasks')

    # GET request: Load initial data for the form
    context = {
        'districts': District.objects.all(),
        'categories': Category.objects.all(),
    }
    return render(request, 'giver/post_task.html', context)

# --- AJAX Loaders for Dependent Dropdowns ---

def load_places(request):
    district_id = request.GET.get('district_id')
    places = Place.objects.filter(district_id=district_id).values('id', 'place_name')
    return JsonResponse(list(places), safe=False)

def load_pincodes(request):
    place_id = request.GET.get('place_id')
    pincodes = Pincode.objects.filter(place_id=place_id).values('id', 'pincode_number')
    return JsonResponse(list(pincodes), safe=False)

def load_skills(request):
    category_id = request.GET.get('category_id')
    skills = Skill.objects.filter(category_id=category_id).values('id', 'skill_name')
    return JsonResponse(list(skills), safe=False)

# --- Task Management ---

def my_tasks(request):
    # Fetch tasks belonging to the logged-in giver
    tasks = Task.objects.filter(giver=request.user).order_by('-created_at')
    status_filter = request.GET.get('status')
    
    # 3. Apply filter if it's not empty
    if status_filter:
        tasks = tasks.filter(status=status_filter)
    # Make sure 'my_task.html' matches your actual filename
    return render(request, 'giver/my_task.html', {'tasks': tasks})

def delete_task(request, pk):
    # Get the task or return 404 if not found
    # We filter by giver=request.user to ensure only the owner can delete it
    task = get_object_or_404(Task, id=pk, giver=request.user)
    
    # You can either completely delete the record:
    task.delete()
    
    # OR, if you prefer a "soft delete" (keeping the data but hiding it):
    # task.status = 'Cancelled'
    # task.is_active = False
    # task.save()
    
    return redirect('my_tasks')

@login_required
def view_task_requests(request):
    # Fetch all tasks posted by this Giver
    # Use prefetch_related to get the Doer requests efficiently
    my_tasks = Task.objects.filter(giver=request.user).prefetch_related(
        'task_requests', 'task_requests__doer'
    ).order_by('-created_at')

    return render(request, 'giver/view_requests.html', {
        'my_tasks': my_tasks
    })




@login_required
def giver_chat_inbox(request, doer_id=None):
    # 1. Base Query for the Sidebar
    my_tasks_applications = TaskRequest.objects.filter(
        task__giver=request.user
    ).select_related('doer', 'task')

    # 2. MARK AS READ: If a user is selected, clear their unread messages FIRST
    # This ensures the badge disappears immediately upon page load for that specific user
    if doer_id:
        Message.objects.filter(
            sender_id=doer_id, 
            receiver=request.user, 
            is_seen=False
        ).update(is_seen=True)

    # 3. UNIQUE DOERS LOGIC: Process the sidebar list
    unique_doers = []
    seen_doer_ids = set()
    
    for app in my_tasks_applications:
        if app.doer.id not in seen_doer_ids:
            # Check if accepted status exists for this doer
            app.is_accepted = my_tasks_applications.filter(doer=app.doer, status="accepted").exists()
            
            # CALCULATE UNREAD COUNT: This provides the number for the professional badge
            # We count only messages sent TO you that are still marked as unseen
            app.unread_count = Message.objects.filter(
                sender=app.doer,
                receiver=request.user,
                is_seen=False
            ).count()
            
            unique_doers.append(app)
            seen_doer_ids.add(app.doer.id)

    # 4. ACTIVE CHAT LOGIC
    other_user = None
    chat_history = []
    room_id = ""
    active_app_accepted = False

    if doer_id:
        other_user = get_object_or_404(User, id=doer_id)
        # Sort IDs to ensure the room name is consistent (e.g., 1_5 is the same as 5_1)
        user_ids = sorted([request.user.id, other_user.id])
        room_id = f"{user_ids[0]}_{user_ids[1]}"
        
        active_app_accepted = my_tasks_applications.filter(doer=other_user, status="accepted").exists()

        # Fetch message history
        raw_messages = Message.objects.filter(
            (Q(sender=request.user) & Q(receiver=other_user)) | 
            (Q(sender=other_user) & Q(receiver=request.user))
        ).order_by('timestamp')

        for msg in raw_messages:
            try:
                encrypted_data = msg.encrypted_content
                if isinstance(encrypted_data, str):
                    encrypted_data = encrypted_data.encode()
                content = decrypt_message(encrypted_data)
            except Exception:
                content = "[Encrypted Message]"
            
            chat_history.append({
                'sender_name': msg.sender.name,
                'content': content,
                'is_seen': msg.is_seen,
                'timestamp': msg.timestamp
            })

    # 5. RENDER
    return render(request, 'giver/giver_messages.html', {
        'applications': unique_doers,
        'other_user': other_user,
        'chat_history': chat_history,
        'room_id': room_id,
        'active_app_accepted': active_app_accepted
    })




@login_required
def hire_doer_ajax(request):
    if request.method == "POST":
        req_id = request.POST.get('req_id')
        # Ensure the requester is the owner of the task
        task_request = get_object_or_404(TaskRequest, id=req_id, task__giver=request.user)
        task = task_request.task

        if task.status == 'Open':
            with transaction.atomic():
                # 1. Update TaskRequest
                task_request.status = 'Accepted'
                task_request.save()

                # 2. Assign doer to Task (This triggers your model save logic)
                task.doer = task_request.doer
                task.status = 'Accepted'
                task.save()

                # 3. Mark other pending applicants as Rejected
                task.task_requests.filter(status='Pending').exclude(id=req_id).update(status='Rejected')

            return JsonResponse({'status': 'success', 'message': f'Hired {task_request.doer.name} successfully!'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Task is no longer open.'})

    return JsonResponse({'status': 'error', 'message': 'Invalid request.'}, status=400)




@login_required
def giver_complete_and_rate(request):
    if request.method == "POST":
        task_id = request.POST.get('task_id')
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')
        
        task = get_object_or_404(Task, id=task_id, giver=request.user)

        with transaction.atomic():
            # 1. Update Task Status
            task.status = 'Completed'
            task.save()

            # 2. Create the Review
            Review.objects.create(
                task=task,
                reviewer=request.user,
                reviewee=task.doer,
                rating=rating,
                comment=comment
            )
            
            # 3. Logic for AI: You can trigger a function here to 
            # recalculate the Doer's Priority Score based on this rating.

        return JsonResponse({'status': 'success', 'message': 'Task closed and Doer rated!'})
    
@login_required
def giver_hired_tasks(request):
    # Fetch tasks where a doer is assigned
    hired_tasks = Task.objects.filter(
        giver=request.user, 
        doer__isnull=False
    ).select_related('doer', 'category').order_by('-created_at')
    
    return render(request, 'giver/hired_tasks.html', {
        'hired_tasks': hired_tasks
    })

@login_required
def public_giver_profile(request, giver_id):
    giver_user = get_object_or_404(User, id=giver_id)
    
    # --- ADD THIS POST LOGIC ---
    if request.method == "POST":
        reason = request.POST.get('reason')
        desc = request.POST.get('description')
        
        # Anti-Spam Logic: Update existing or create new
        report, created = UserReport.objects.update_or_create(
            reporter=request.user, 
            reported_user=giver_user,
            is_resolved=False, 
            defaults={'reason': reason, 'description': desc}
        )
        
        if created:
            messages.success(request, f"Report filed against {giver_user.name}.")
        else:
            messages.info(request, "Your previous report for this Giver has been updated.")
            
        # CRITICAL: Redirect back to THIS SAME VIEW (Giver Profile)
        return redirect('public_giver_profile', giver_id=giver_id)
    # ---------------------------

    # Your existing GET logic
    stats = Review.objects.filter(reviewee=giver_user).aggregate(
        avg=Avg('rating'), count=Count('id')
    )
    reviews = Review.objects.filter(reviewee=giver_user).select_related('reviewer').order_by('-created_at')
    
    context = {
        'giver': giver_user,
        'avg_rating': stats['avg'] or 0,
        'total_reviews': stats['count'],
        'reviews': reviews,
    }
    return render(request, 'doer/view_giver_public.html', context)












@login_required
def ai_match_expert_page(request):
    # 1. Fetch Giver's tasks that are either Open or currently Requested
    my_tasks = Task.objects.filter(giver=request.user, status__in=['Open', 'Requested'])
    
    selected_task_id = request.GET.get('task_id')
    recommendations = []
    task = None
    # Instead of invited_ids from a table, we check who is currently in the task.doer field
    current_requested_doer_id = None

    if selected_task_id:
        task = get_object_or_404(Task, id=selected_task_id, giver=request.user)
        recommendations = get_ai_recommended_doers(task) 
        
        # If the task is already 'Requested', identify the doer so the UI can show "Pending"
        if task.status == 'Requested' and task.doer:
            current_requested_doer_id = task.doer.id

    # Handle the "Schedule Job" Request
    if request.method == "POST":
        doer_id = request.POST.get('doer_id')
        t_id = request.POST.get('target_task_id')
        
        target_task = get_object_or_404(Task, id=t_id, giver=request.user)
        doer_user = get_object_or_404(User, id=doer_id)
        
        # LOGIC CHANGE: Assign doer directly to Task and change status
        target_task.doer = doer_user
        target_task.status = 'Requested'
        target_task.save()

        messages.success(request, f"Schedule request sent to {doer_user.name}!")
        # Use reverse to ensure the redirect path is always correct
        return redirect(reverse('ai_match_expert_page') + f'?task_id={t_id}')

    return render(request, 'giver/ai_match_page.html', {
        'my_tasks': my_tasks,
        'recommendations': recommendations,
        'selected_task': task,
        'current_requested_doer_id': current_requested_doer_id # Pass this to HTML
    })




@login_required
def giver_home(request):
    # 1. Direct Filter
    tasks_query = Task.objects.filter(giver=request.user)
    total_posted = tasks_query.count()

    # 2. DEBUG PRINT (Check your VS Code/PyCharm terminal)
    print(f"--- GIVER HOME DEBUG ---")
    print(f"User: {request.user.email} (ID: {request.user.id})")
    print(f"Count via request.user: {total_posted}")
    
    # 3. Fallback Check: Does the DB have ANY tasks for this user ID?
    # This helps if request.user is somehow proxied or lazy
    total_posted_alt = Task.objects.filter(giver_id=request.user.id).count()
    print(f"Count via raw ID: {total_posted_alt}")

    active_hired = Task.objects.filter(giver=request.user, status='Accepted').count()
    completed_count = Task.objects.filter(giver=request.user, status='Completed').count()
    
    from django.db.models import Sum
    total_spent = Task.objects.filter(giver=request.user, status='Completed').aggregate(total=Sum('budget'))['total'] or 0

    recent_tasks = Task.objects.filter(giver=request.user).order_by('-created_at')[:3]
    new_applications = TaskRequest.objects.filter(task__giver=request.user, status='Pending').select_related('doer', 'task').order_by('-created_at')[:3]

    context = {
        'total_posted': total_posted_alt, # Using the raw ID count just in case
        'active_hired': active_hired,
        'completed_count': completed_count,
        'total_spent': total_spent,
        'recent_tasks': recent_tasks,
        'new_applications': new_applications,
        'is_verified': request.user.approval_status == 'Approved',
        'today': timezone.now(),
    }
    return render(request, 'giver/home.html', context)