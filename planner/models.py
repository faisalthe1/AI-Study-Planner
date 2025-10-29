from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
import datetime

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    preferred_study_hours_start = models.TimeField(default=datetime.time(9, 0))
    preferred_study_hours_end = models.TimeField(default=datetime.time(21, 0))
    break_duration = models.IntegerField(
        default=15,
        validators=[MinValueValidator(5), MaxValueValidator(60)],
        help_text="Break duration in minutes"
    )
    study_session_duration = models.IntegerField(
        default=50,
        validators=[MinValueValidator(20), MaxValueValidator(120)],
        help_text="Study session duration in minutes"
    )
    daily_study_hours = models.FloatField(
        default=4.0,
        validators=[MinValueValidator(1.0), MaxValueValidator(12.0)],
        help_text="Daily study hours target"
    )
    
    def __str__(self):
        return f"{self.user.username}'s Profile"

class Course(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, blank=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default="#3b82f6") 
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Task(models.Model):
    PRIORITY_CHOICES = [
        (1, 'Low'),
        (2, 'Medium'),
        (3, 'High'),
        (4, 'Urgent'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True, blank=True)
    due_date = models.DateTimeField()
    priority = models.IntegerField(choices=PRIORITY_CHOICES, default=2)
    estimated_duration = models.IntegerField(
        help_text="Estimated duration in minutes",
        validators=[MinValueValidator(15)]
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['due_date']
    
    def __str__(self):
        return self.title

class StudySession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, null=True, blank=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=200)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    completed = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['start_time']
    
    def __str__(self):
        return f"{self.title} - {self.start_time.strftime('%Y-%m-%d %H:%M')}"