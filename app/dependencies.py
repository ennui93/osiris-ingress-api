"""
Contains dependencies used in several places of the application.
"""
import time

from functools import wraps

from fastapi import HTTPException
from prometheus_client import Histogram, Counter


class Metric:
    """
    Class to wrap all metrics for prometheus.
    """
    HISTOGRAM = Histogram('osiris_ingress_api', 'Osiris Ingress API (method, guid, time)', ['method', 'guid',
                                                                                            'status_code'])
    COUNTER = Counter('osiris_ingress_api_method_counter',
                      'Osiris Ingress API counter (method, guid)',
                      ['method', 'guid'])

    @staticmethod
    def histogram(func):
        """
        Decorator method for metrics of type histogram
        """
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                result = await func(*args, **kwargs)
            except HTTPException as e:
                time_taken = time.time() - start_time
                Metric.HISTOGRAM.labels(func.__name__, kwargs['guid'], e.status_code).observe(time_taken)
                raise e

            time_taken = time.time() - start_time
            Metric.HISTOGRAM.labels(func.__name__, kwargs['guid'], result.status_code).observe(time_taken)
            return result

        return wrapper

    @staticmethod
    def counter(func):
        """
        Decorator method for metrics of type counter
        """
        @wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            Metric.COUNTER.labels(func.__name__, kwargs['guid']).inc()
            return result

        return wrapper
