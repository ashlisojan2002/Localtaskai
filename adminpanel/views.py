from django.contrib.auth.decorators import user_passes_test
from accounts.models import User,UserReport
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.urls import reverse
from django.shortcuts import render, redirect
from django.shortcuts import render, redirect, get_object_or_404
from .models import District, Place, Pincode
from .models import Category, Skill
from giver.models import Task
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Count
from django.db.models import Avg, Count
from giver.models import Review  # Ensure this path matches where your Review model is
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required


# Security: Only allow Superusers to see this page

def is_admin(user):
    return user.is_superuser


@login_required
@never_cache
@user_passes_test(is_admin)
def admin_dashboard(request):
    # 1. Total Users (Excluding superusers)
    total_users = User.objects.filter(is_superuser=False).count()
    
    # 2. No of Doers
    no_of_doers = User.objects.filter(role='doer').count()
    
    # 3. No of Givers
    no_of_givers = User.objects.filter(role='giver').count()
    
    # 4. Verified Doers
    verified_doers = User.objects.filter(role='doer', approval_status='Accepted').count()
    
    # 5. Verified Givers
    verified_givers = User.objects.filter(role='giver', approval_status='Accepted').count()
    
    # 6. Verification Status: Under Review
    under_review_users = User.objects.filter(approval_status='Under Review').count()
    
    # 7. No of Open Tasks
    no_of_open_tasks = Task.objects.filter(status='Open').count()
    
    # 8. No of Completed Tasks
    no_of_completed_tasks = Task.objects.filter(status='Completed').count()
    
    # 9. No of Reported Accounts
    # (Counts unique users who have at least one report against them)
    no_of_reported_accounts = User.objects.annotate(
        r_count=Count('reports_received')
    ).filter(r_count__gt=0).count()

    context = {
        'total_users': total_users,
        'no_of_doers': no_of_doers,
        'no_of_givers': no_of_givers,
        'verified_doers': verified_doers,
        'verified_givers': verified_givers,
        'under_review_users': under_review_users,
        'no_of_open_tasks': no_of_open_tasks,
        'no_of_completed_tasks': no_of_completed_tasks,
        'no_of_reported_accounts': no_of_reported_accounts,
    }
    return render(request, 'adminpanel/dashboard.html', context)


@login_required
@never_cache
@user_passes_test(is_admin)
@user_passes_test(lambda u: u.is_superuser)
def admin_user_management(request):
    # 1. Get the filter status and search query from the URL
    status_filter = request.GET.get('status', 'Under Review')
    search_query = request.GET.get('search', '').strip()
    
    # 2. Define human-readable titles for the UI
    filter_titles = {
        'Under Review': 'Under Review',
        'Accepted': 'Verified Users',
        'Rejected': 'Rejected Applications',
        'pending': 'pending'
    }

    # 3. Base Query: Exclude superusers and order by newest
    users = User.objects.exclude(is_superuser=True).order_by('-id')

    # 4. Apply Status Filter logic
    if status_filter != 'All':
        users = users.filter(approval_status=status_filter)

    # 5. Apply Search logic (if search box is used)
    if search_query:
        from django.db.models import Q
        users = users.filter(
            Q(name__icontains=search_query) | 
            Q(email__icontains=search_query) |
            Q(adhar_card__icontains=search_query)
        )

    # 6. Return the CLEAN context (No unclosed braces here!)
    return render(request, 'adminpanel/user_management.html', {
        'users': users,
        'current_filter': status_filter,
        'display_title': filter_titles.get(status_filter, status_filter),
        'search_query': search_query,
    })

@login_required
@never_cache
@user_passes_test(is_admin)
def update_user_status(request, user_id, action):
    user_to_update = get_object_or_404(User, id=user_id)
    
    # 1. Capture the filter the admin was currently viewing
    current_filter = request.GET.get('current_filter', 'Under Review')
    
    if action == 'accept':
        user_to_update.approval_status = 'Accepted'
        messages.success(request, f"User {user_to_update.name} has been approved.")
    elif action == 'reject':
        user_to_update.approval_status = 'Rejected'
        messages.warning(request, f"User {user_to_update.name} has been rejected.")
    elif action == 'delete':
        user_to_update.delete()
        messages.error(request, "User account has been permanently deleted.")
        return redirect(f"{reverse('admin_user_management')}?status={current_filter}")

    user_to_update.save()
    
    # 2. Redirect back with the 'status' parameter to maintain the view
    return redirect(f"{reverse('admin_user_management')}?status={current_filter}")



@login_required
@never_cache
@user_passes_test(is_admin)
def location_management(request):
    if request.method == "POST":
        action = request.POST.get('action')

        # 1. Logic for Adding District
        if action == "add_district":
            district_name = request.POST.get('district_name')
            if district_name:
                District.objects.create(district_name=district_name)
        
        # 2. Logic for Adding Place
        elif action == "add_place":
            district_id = request.POST.get('district_id')
            place_name = request.POST.get('place_name')
            if district_id and place_name:
                dist = get_object_or_404(District, id=district_id)
                Place.objects.create(district=dist, place_name=place_name)

        # 3. Logic for Adding Pincode
        elif action == "add_pincode":
            place_id = request.POST.get('place_id')
            pincode_number = request.POST.get('pincode_number')
            if place_id and pincode_number:
                place_obj = get_object_or_404(Place, id=place_id)
                Pincode.objects.create(place=place_obj, pincode_number=pincode_number)

        return redirect('location_management')

    # Data for the view (Tabs and Dropdowns)
    context = {
        'districts': District.objects.all(),
        'places': Place.objects.all(),
        'pincodes': Pincode.objects.select_related('place__district').all(),
    }
    return render(request, 'adminpanel/location_management.html', context)

# --- DELETE ACTIONS ---


@login_required
@never_cache
@user_passes_test(is_admin)
def delete_location(request, pk):
    """Deletes a specific Pincode"""
    pincode = get_object_or_404(Pincode, id=pk)
    pincode.delete()
    return redirect('location_management')


@login_required
@never_cache
@user_passes_test(is_admin)
def delete_place(request, pk):
    """Deletes a Place and all its associated Pincodes"""
    place = get_object_or_404(Place, id=pk)
    place.delete()
    return redirect('location_management')

@login_required
@never_cache
@user_passes_test(is_admin)
def delete_district(request, pk):
    """Deletes a District and EVERYTHING inside it (Places & Pincodes)"""
    district = get_object_or_404(District, id=pk)
    district.delete()
    return redirect('location_management')




@login_required
@never_cache
@user_passes_test(is_admin)
def skill_management(request):
    if request.method == "POST":
        action = request.POST.get('action')

        # Add Category Logic
        if action == "add_category":
            cat_name = request.POST.get('category_name')
            if cat_name:
                Category.objects.create(category_name=cat_name)

        # Add Skill Logic
        elif action == "add_skill":
            cat_id = request.POST.get('category_id')
            skill_name = request.POST.get('skill_name')
            if cat_id and skill_name:
                category_obj = get_object_or_404(Category, id=cat_id)
                Skill.objects.create(category=category_obj, skill_name=skill_name)

        return redirect('skill_management')

    context = {
        'categories': Category.objects.all().order_by('category_name'),
        'skills': Skill.objects.select_related('category').all().order_by('-id'),
    }
    return render(request, 'adminpanel/skill_management.html', context)


@login_required
@never_cache
@user_passes_test(is_admin)
def delete_category(request, pk):
    get_object_or_404(Category, id=pk).delete()
    return redirect('skill_management')

@login_required
@never_cache
@user_passes_test(is_admin)
def delete_skill(request, pk):
    get_object_or_404(Skill, id=pk).delete()
    return redirect('skill_management')



@login_required
@never_cache
@user_passes_test(is_admin)
def admin_task_management(request):
    user_id = request.GET.get('user_id')
    
    if user_id:
        tasks = Task.objects.filter(giver_id=user_id).order_by('-created_at')
        viewing_user = get_object_or_404(User, id=user_id)
    else:
        tasks = Task.objects.all().order_by('-created_at')
        viewing_user = None

    return render(request, 'adminpanel/admin_tasks.html', {
        'tasks': tasks,
        'viewing_user': viewing_user
    })


@login_required
@never_cache
@user_passes_test(is_admin)
def admin_delete_task(request, pk):
    task = get_object_or_404(Task, id=pk)
    task.delete()
    return redirect('admin_task_management')













@login_required
@never_cache
@user_passes_test(is_admin)
def admin_report_center(request):
    """
    Main Enforcement List.
    - Purges users with 5+ reports automatically.
    - Links to the INTERNAL investigation page.
    """
    # 1. AUTO-PURGE LOGIC (Threshold of 5)
    bad_users = User.objects.annotate(r_count=Count('reports_received')).filter(r_count__gte=5)
    for user in bad_users:
        user.delete()

    # 2. HANDLE QUICK ACTIONS FROM LIST
    if request.method == "POST":
        target_id = request.POST.get('user_id')
        action = request.POST.get('action')
        target_user = get_object_or_404(User, id=target_id)

        if action == "delete":
            target_user.delete()
            messages.success(request, "Account purged.")
        elif action == "clear":
            UserReport.objects.filter(reported_user=target_user).delete()
            messages.success(request, "Reports cleared.")
        return redirect('admin_report_center')

    # 3. GET DATA
    reported_users = User.objects.annotate(
        report_count=Count('reports_received')
    ).filter(report_count__gt=0).order_by('-report_count')

    return render(request, 'adminpanel/report_center.html', {'reported_users': reported_users})


@login_required
@never_cache
@user_passes_test(is_admin)
def admin_investigate_user(request, user_id):
    """
    The NEW Dedicated Investigation Page.
    Now correctly fetches reputation stats and reviews.
    """
    target_user = get_object_or_404(User, id=user_id)
    
    # 1. Fetch Reports
    reports = UserReport.objects.filter(reported_user=target_user).select_related('reporter').order_by('-created_at')
    
    # 2. Fetch Reviews (Reputation)
    # We fetch reviews where the target_user is the 'reviewee'
    reviews = Review.objects.filter(reviewee=target_user).select_related('reviewer').order_by('-created_at')
    
    # 3. Calculate Stats
    stats = reviews.aggregate(
        avg=Avg('rating'), 
        count=Count('id')
    )

    # 4. Handle POST actions (Clear/Delete)
    if request.method == "POST":
        action = request.POST.get('action')
        if action == "delete":
            target_user.delete()
            messages.success(request, "Account purged.")
            return redirect('admin_report_center')
        elif action == "clear":
            reports.delete()
            messages.success(request, "Reports cleared.")
            return redirect('admin_investigate_user', user_id=user_id)

    return render(request, 'adminpanel/investigate_user.html', {
        'target_user': target_user,
        'reports': reports,
        'report_count': reports.count(),
        'reviews': reviews,                         # Added this
        'avg_rating': stats['avg'] or 0,           # Added this
        'total_reviews': stats['count'] or 0       # Added this
    })