import datetime
from datetime import timedelta
from .models import Task, StudySession, UserProfile
from django.utils import timezone

class StudyPlannerAlgorithm:
    def __init__(self, user):
        self.user = user
        self.profile = UserProfile.objects.get(user=user)
        self.now = timezone.now()
    
    def calculate_task_score(self, task):
        """Calculate a priority score for a task based on deadline and priority"""
        time_until_due = (task.due_date - self.now).total_seconds() / 3600  # hours until due
        
        # Higher priority tasks and closer deadlines get higher scores
        priority_weight = task.priority * 0.4
        time_weight = (1 / max(1, time_until_due)) * 0.6
        
        return priority_weight + time_weight
    
    def generate_schedule(self, days=7):
        """Generate a study schedule for the next specified days"""
        # Clear existing non-completed study sessions
        StudySession.objects.filter(
            user=self.user, 
            start_time__gte=self.now,
            completed=False
        ).delete()
        
        # Get all pending tasks
        tasks = Task.objects.filter(
            user=self.user, 
            status__in=['pending', 'in_progress'],
            due_date__gte=self.now
        ).order_by('due_date')
        
        if not tasks:
            return []
        
        # Calculate priority scores for all tasks
        task_scores = [(task, self.calculate_task_score(task)) for task in tasks]
        task_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Generate time slots for each day
        study_sessions = []
        current_date = self.now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        for day in range(days):
            day_date = current_date + timedelta(days=day)
            
            # Skip weekends if user prefers (could be extended based on preferences)
            if day_date.weekday() >= 5:  # 5=Saturday, 6=Sunday
                continue
                
            # Get available time slots for this day
            time_slots = self.get_available_time_slots(day_date)
            
            for task, score in task_scores:
                if task.estimated_duration <= 0:
                    continue
                    
                # Try to schedule this task
                remaining_duration = task.estimated_duration
                
                for slot in time_slots:
                    if remaining_duration <= 0:
                        break
                        
                    slot_duration = (slot['end'] - slot['start']).total_seconds() / 60
                    
                    if slot_duration <= 0:
                        continue
                    
                    # Determine how much time we can use in this slot
                    time_to_use = min(remaining_duration, slot_duration)
                    
                    # Create study session
                    session_start = slot['start']
                    session_end = session_start + timedelta(minutes=time_to_use)
                    
                    study_session = StudySession(
                        user=self.user,
                        task=task,
                        course=task.course,
                        title=f"Study: {task.title}",
                        start_time=session_start,
                        end_time=session_end,
                        notes=f"Scheduled by AI planner for {task.title}"
                    )
                    study_session.save()
                    study_sessions.append(study_session)
                    
                    # Update slot availability
                    slot['start'] = session_end
                    remaining_duration -= time_to_use
                    
                    # Update task estimated duration
                    task.estimated_duration -= time_to_use
                    if task.estimated_duration <= 0:
                        task.estimated_duration = 0
                    task.save()
        
        return study_sessions
    
    def get_available_time_slots(self, date):
        """Get available time slots for studying on a given date"""
        slots = []
        
        # Get user's preferred study hours
        start_time = datetime.datetime.combine(
            date, 
            self.profile.preferred_study_hours_start
        ).replace(tzinfo=timezone.utc)
        
        end_time = datetime.datetime.combine(
            date, 
            self.profile.preferred_study_hours_end
        ).replace(tzinfo=timezone.utc)
        
        # Check if the date is today - if so, start from current time if later
        if date.date() == self.now.date() and self.now > start_time:
            start_time = self.now
        
        # Create time blocks based on session duration and breaks
        current_time = start_time
        session_duration = timedelta(minutes=self.profile.study_session_duration)
        break_duration = timedelta(minutes=self.profile.break_duration)
        
        while current_time + session_duration <= end_time:
            slot_end = current_time + session_duration
            slots.append({
                'start': current_time,
                'end': slot_end
            })
            
            # Add break time
            current_time = slot_end + break_duration
        
        return slots