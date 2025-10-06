import logging
import redis
from django.conf import settings
from django.db import connection
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


class HealthCheckView(APIView):
    """
    Health check endpoint to verify service status
    """
    permission_classes = []  # Public endpoint
    authentication_classes = []
    
    def get(self, request):
        health_status = {
            'status': 'healthy',
            'database': self._check_database(),
            'redis': self._check_redis(),
        }
        
        # Overall health is unhealthy if any component fails
        if not all([health_status['database'], health_status['redis']]):
            health_status['status'] = 'unhealthy'
            return Response(health_status, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        return Response(health_status, status=status.HTTP_200_OK)
    
    def _check_database(self):
        """Check database connectivity"""
        try:
            connection.ensure_connection()
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            return False
    
    def _check_redis(self):
        """Check Redis connectivity"""
        try:
            redis_client = redis.StrictRedis(
                host=settings.CHANNEL_LAYERS['default']['CONFIG']['hosts'][0][0],
                port=settings.CHANNEL_LAYERS['default']['CONFIG']['hosts'][0][1],
                db=0,
                socket_connect_timeout=5
            )
            redis_client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {str(e)}")
            return False

