import logging
import time

logger = logging.getLogger(__name__)

class APILoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()

        response = self.get_response(request)

        duration = time.time() - start_time
        user = request.user if request.user.is_authenticated else 'Anonymous'

        log_data = {
            'method': request.method,
            'path': request.path,
            'status_code': response.status_code,
            'user': str(user),
            'duration_ms': round(duration * 1000, 2)
        }

        logger.info(f"API Request: {log_data}")

        return response
