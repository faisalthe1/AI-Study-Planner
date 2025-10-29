import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Task, Course, StudySession, UserProfile
from .forms import CustomUserCreationForm, UserProfileForm, TaskForm, CourseForm, StudySessionForm
from .scheduling_algorithm import StudyPlannerAlgorithm


def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'home.html')


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(user=user)
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)
            
            messages.success(request, 'Registration successful!')
            return redirect('profile')
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def dashboard(request):
    upcoming_tasks = Task.objects.filter(
        user=request.user, 
        due_date__gte=timezone.now()
    ).order_by('due_date')[:5]
    
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    today_sessions = StudySession.objects.filter(
        user=request.user,
        start_time__range=[today_start, today_end]
    ).order_by('start_time')
    
    context = {
        'upcoming_tasks': upcoming_tasks,
        'today_sessions': today_sessions,
    }
    return render(request, 'dashboard.html', context)


@login_required
def profile(request):
    profile = UserProfile.objects.get(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=profile)
    
    return render(request, 'registration/profile.html', {'form': form})


@login_required
def task_list(request):
    tasks = Task.objects.filter(user=request.user).order_by('due_date')
    return render(request, 'tasks/task_list.html', {'tasks': tasks})


@login_required
def task_create(request):
    if request.method == 'POST':
        form = TaskForm(request.user, request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
            task.save()
            messages.success(request, 'Task created successfully!')
            return redirect('task_list')
    else:
        form = TaskForm(request.user)
    
    return render(request, 'tasks/task_form.html', {'form': form, 'title': 'Create Task'})


@login_required
def task_edit(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = TaskForm(request.user, request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, 'Task updated successfully!')
            return redirect('task_list')
    else:
        form = TaskForm(request.user, instance=task)
    
    return render(request, 'tasks/task_form.html', {'form': form, 'title': 'Edit Task'})


@login_required
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk, user=request.user)
    if request.method == 'POST':
        task.delete()
        messages.success(request, 'Task deleted successfully!')
        return redirect('task_list')
    
    return render(request, 'tasks/task_confirm_delete.html', {'task': task})


@login_required
def course_list(request):
    courses = Course.objects.filter(user=request.user).order_by('name')
    return render(request, 'courses/course_list.html', {'courses': courses})


@login_required
def course_create(request):
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save(commit=False)
            course.user = request.user
            course.save()
            messages.success(request, 'Course created successfully!')
            return redirect('course_list')
    else:
        form = CourseForm()
    return render(request, 'courses/course_form.html', {'form': form, 'title': 'Create Course'})


@login_required
def course_edit(request, pk):
    course = get_object_or_404(Course, pk=pk, user=request.user)
    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, 'Course updated successfully!')
            return redirect('course_list')
    else:
        form = CourseForm(instance=course)
    return render(request, 'courses/course_form.html', {'form': form, 'title': 'Edit Course'})


@login_required
def course_delete(request, pk):
    course = get_object_or_404(Course, pk=pk, user=request.user)
    if request.method == 'POST':
        course.delete()
        messages.success(request, 'Course deleted successfully!')
        return redirect('course_list')
    return render(request, 'courses/course_confirm_delete.html', {'course': course})


@login_required
def calendar_view(request):
    return render(request, 'calendar.html')


@login_required
def calendar_events(request):
    start = request.GET.get('start')
    end = request.GET.get('end')
    start_date = datetime.fromisoformat(start)
    end_date = datetime.fromisoformat(end)
    sessions = StudySession.objects.filter(
        user=request.user,
        start_time__gte=start_date,
        end_time__lte=end_date
    )
    
    events = []
    for session in sessions:
        color = session.course.color if session.course else '#3b82f6'
        events.append({
            'id': session.id,
            'title': session.title,
            'start': session.start_time.isoformat(),
            'end': session.end_time.isoformat(),
            'color': color,
            'extendedProps': {
                'type': 'study_session',
                'task': session.task.title if session.task else 'General Study',
                'course': session.course.name if session.course else 'No Course',
            }
        })
    
    tasks = Task.objects.filter(
        user=request.user,
        due_date__gte=start_date,
        due_date__lte=end_date
    )
    
    for task in tasks:
        events.append({
            'id': f'task-{task.id}',
            'title': f'Due: {task.title}',
            'start': task.due_date.isoformat(),
            'allDay': True,
            'color': '#ef4444',
            'extendedProps': {
                'type': 'task_due',
            }
        })
    
    return JsonResponse(events, safe=False)


@login_required
def generate_schedule(request):
    if request.method == 'POST':
        planner = StudyPlannerAlgorithm(request.user)
        study_sessions = planner.generate_schedule(days=7)
        messages.success(request, f'Schedule generated with {len(study_sessions)} study sessions!')
        return redirect('calendar')
    
    return redirect('dashboard')


@login_required
def api_study_sessions(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        
        session = StudySession(
            user=request.user,
            title=data.get('title', 'Study Session'),
            start_time=datetime.fromisoformat(data['start']),
            end_time=datetime.fromisoformat(data['end']),
        )
        
        if 'taskId' in data:
            try:
                session.task = Task.objects.get(id=data['taskId'], user=request.user)
            except Task.DoesNotExist:
                pass
                
        if 'courseId' in data:
            try:
                session.course = Course.objects.get(id=data['courseId'], user=request.user)
            except Course.DoesNotExist:
                pass
                
        session.save()
        
        return JsonResponse({'status': 'success', 'sessionId': session.id})
    
    elif request.method == 'PUT':
        data = json.loads(request.body)
        session_id = data.get('id')
        
        try:
            session = StudySession.objects.get(id=session_id, user=request.user)
            session.start_time = datetime.fromisoformat(data['start'])
            session.end_time = datetime.fromisoformat(data['end'])
            session.save()
            
            return JsonResponse({'status': 'success'})
        except StudySession.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Session not found'}, status=404)
    
    elif request.method == 'DELETE':
        data = json.loads(request.body)
        session_id = data.get('id')
        
        try:
            session = StudySession.objects.get(id=session_id, user=request.user)
            session.delete()
            
            return JsonResponse({'status': 'success'})
        except StudySession.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Session not found'}, status=404)
    
    return JsonResponse({'status': 'error'}, status=400)


def api_upcoming_tasks(request):
    """API endpoint for Java notification service to get upcoming tasks"""
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    auth_token = request.headers.get('Authorization')
    if not auth_token or not auth_token.startswith('Token '):
        return JsonResponse({'error': 'Unauthorized'}, status=401)
    token = auth_token.split(' ')[1]
    start_date = timezone.now()
    end_date = start_date + timedelta(days=7)
    
    tasks = Task.objects.filter(
        due_date__range=[start_date, end_date],
        status__in=['pending', 'in_progress']
    ).select_related('course', 'user')
    
    task_list = []
    for task in tasks:
        task_list.append({
            'id': task.id,
            'title': task.title,
            'due_date': task.due_date.isoformat(),
            'priority': task.priority,
            'user_email': task.user.email,
            'course': task.course.name if task.course else None
        })
    
    return JsonResponse(task_list, safe=False)


def custom_logout(request):
    """Custom logout view that shows a confirmation message"""
    from django.contrib.auth import logout as auth_logout
    if request.method == 'POST':
        auth_logout(request)
        messages.success(request, 'You have been successfully logged out.')
        return redirect('home')
    
    return render(request, 'registration/logout_confirm.html')