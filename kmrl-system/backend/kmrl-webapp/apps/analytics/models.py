"""
Analytics Models for KMRL Webapp
"""

from django.db import models
import uuid

class Analytics(models.Model):
    """Analytics model for KMRL"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    metric_name = models.CharField(max_length=100)
    metric_value = models.FloatField()
    metric_type = models.CharField(max_length=50, choices=[
        ('document_count', 'Document Count'),
        ('processing_time', 'Processing Time'),
        ('error_rate', 'Error Rate'),
        ('user_activity', 'User Activity')
    ])
    department = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.metric_name}: {self.metric_value}"
