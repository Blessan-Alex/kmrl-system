"""
Serializers for documents app
"""

from rest_framework import serializers
from .models import Document, DocumentChunk, Notification

class DocumentSerializer(serializers.ModelSerializer):
    """Serializer for Document model"""
    
    class Meta:
        model = Document
        fields = [
            'id', 'filename', 'source', 'content_type', 'file_size',
            'storage_path', 'metadata', 'status', 'confidence_score',
            'language', 'department', 'uploaded_by', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class DocumentChunkSerializer(serializers.ModelSerializer):
    """Serializer for DocumentChunk model"""
    
    class Meta:
        model = DocumentChunk
        fields = [
            'id', 'document', 'chunk_text', 'chunk_index',
            'embedding', 'metadata', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for Notification model"""
    
    class Meta:
        model = Notification
        fields = [
            'id', 'title', 'message', 'notification_type', 'priority',
            'recipients', 'document', 'is_read', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
