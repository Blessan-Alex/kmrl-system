"""
Notification Models for KMRL Webapp
"""

from django.db import models
from django.contrib.auth.models import User
import uuid

class Notification(models.Model):
    """Notification model for KMRL"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(max_length=50, choices=[
        ('urgent_maintenance', 'Urgent Maintenance'),
        ('safety_incident', 'Safety Incident'),
        ('compliance_violation', 'Compliance Violation'),
        ('deadline_approaching', 'Deadline Approaching'),
        ('budget_exceeded', 'Budget Exceeded')
    ])
    priority = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ])
    recipients = models.ManyToManyField(User, related_name='notifications')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.priority})"
