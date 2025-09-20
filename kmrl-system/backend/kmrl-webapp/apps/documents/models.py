"""
Document Models for KMRL Webapp
Handles document metadata, processing status, and RAG chunks
"""

from django.db import models
from django.contrib.auth.models import User
import uuid

class Document(models.Model):
    """KMRL Document model"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    filename = models.CharField(max_length=255)
    source = models.CharField(max_length=50, choices=[
        ('email', 'Email'),
        ('maximo', 'Maximo'),
        ('sharepoint', 'SharePoint'),
        ('whatsapp', 'WhatsApp'),
        ('manual', 'Manual Upload')
    ])
    content_type = models.CharField(max_length=100)
    file_size = models.BigIntegerField()
    storage_path = models.TextField()
    metadata = models.JSONField(default=dict)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('rejected', 'Rejected')
    ], default='pending')
    confidence_score = models.FloatField(null=True, blank=True)
    language = models.CharField(max_length=10, choices=[
        ('english', 'English'),
        ('malayalam', 'Malayalam'),
        ('mixed', 'Mixed'),
        ('unknown', 'Unknown')
    ], default='unknown')
    department = models.CharField(max_length=50, choices=[
        ('engineering', 'Engineering'),
        ('finance', 'Finance'),
        ('hr', 'Human Resources'),
        ('safety', 'Safety'),
        ('operations', 'Operations'),
        ('executive', 'Executive'),
        ('general', 'General')
    ], default='general')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.filename} ({self.source})"

class DocumentChunk(models.Model):
    """Document chunks for RAG processing"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='chunks')
    chunk_text = models.TextField()
    chunk_index = models.IntegerField()
    embedding = models.JSONField(null=True, blank=True)  # Store embedding vector
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['chunk_index']
    
    def __str__(self):
        return f"Chunk {self.chunk_index} of {self.document.filename}"

class Notification(models.Model):
    """Smart notifications for KMRL stakeholders"""
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
    document = models.ForeignKey(Document, on_delete=models.CASCADE, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.priority})"
