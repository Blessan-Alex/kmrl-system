"""
Celery Configuration for KMRL Gateway
"""

import os

# Celery Configuration
broker_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
result_backend = os.getenv('REDIS_URL', 'redis://localhost:6379')

# Task Configuration
task_serializer = 'json'
accept_content = ['json']
result_serializer = 'json'
timezone = 'Asia/Kolkata'
enable_utc = True

# Worker Configuration
worker_prefetch_multiplier = 1
task_acks_late = True
worker_disable_rate_limits = True
