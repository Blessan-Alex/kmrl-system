"""
Views for documents app
"""

from rest_framework import viewsets, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from .models import Document, DocumentChunk, Notification
from .serializers import DocumentSerializer, DocumentChunkSerializer, NotificationSerializer

class DocumentViewSet(viewsets.ModelViewSet):
    """ViewSet for Document model"""
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['source', 'status', 'language', 'department']
    search_fields = ['filename', 'metadata']
    ordering_fields = ['created_at', 'updated_at', 'file_size']
    ordering = ['-created_at']
    
    @action(detail=True, methods=['get'])
    def chunks(self, request, pk=None):
        """Get document chunks"""
        document = self.get_object()
        chunks = document.chunks.all()
        serializer = DocumentChunkSerializer(chunks, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_department(self, request):
        """Get documents by department"""
        department = request.query_params.get('department')
        if department:
            documents = Document.objects.filter(department=department)
            serializer = self.get_serializer(documents, many=True)
            return Response(serializer.data)
        return Response([])
    
    @action(detail=False, methods=['get'])
    def by_source(self, request):
        """Get documents by source"""
        source = request.query_params.get('source')
        if source:
            documents = Document.objects.filter(source=source)
            serializer = self.get_serializer(documents, many=True)
            return Response(serializer.data)
        return Response([])

class DocumentChunkViewSet(viewsets.ModelViewSet):
    """ViewSet for DocumentChunk model"""
    queryset = DocumentChunk.objects.all()
    serializer_class = DocumentChunkSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['document']
    search_fields = ['chunk_text']

class NotificationViewSet(viewsets.ModelViewSet):
    """ViewSet for Notification model"""
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['notification_type', 'priority', 'is_read']
    ordering = ['-created_at']
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """Mark notification as read"""
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({'status': 'marked as read'})
    
    @action(detail=False, methods=['get'])
    def unread(self, request):
        """Get unread notifications"""
        notifications = Notification.objects.filter(is_read=False)
        serializer = self.get_serializer(notifications, many=True)
        return Response(serializer.data)
