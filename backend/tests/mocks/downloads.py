"""Mocks for download service in tests"""
import os
from datetime import datetime


async def mock_create_download_record(*args, **kwargs):
    """Mock that returns a ready download without real processing"""
    if os.getenv('SKIP_EMAIL_VERIFICATION') != 'true':
        # В продакшене — реальный импорт
        from downloads.service import create_download_record as real_func
        return await real_func(*args, **kwargs)

    # В тестах — заглушка
    return type('obj', (object,), {
        'task_id': 'test-task-id',
        'status': 'ready',
        'progress': 100,
        'filename': kwargs.get('title', 'video') + '_test.mp4',
        'platform': 'youtube' if 'youtube' in kwargs.get('video_url', '') else 'unknown',
        'created_at': datetime.now()
    })()
