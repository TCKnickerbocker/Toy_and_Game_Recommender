import time
import threading
import functools
from prometheus_client import Counter, Histogram, Gauge, Summary, start_http_server

# Service Metrics for the API
class ServiceMetrics:
    def __init__(self, service_name):
        # Existing metrics
        self.requests_total = Counter(
            f'{service_name}_requests_total', 
            'Total number of requests',
            ['method', 'endpoint', 'status']
        )
        
        self.request_latency = Histogram(
            f'{service_name}_request_latency_seconds', 
            'Request latency in seconds',
            ['method', 'endpoint']
        )
        
        self.active_connections = Gauge(
            f'{service_name}_active_connections', 
            'Number of active connections'
        )

        self.recommendations_generated = Counter(
            f'{service_name}_recommendations_generated_total',
            'Total number of product recommendations generated',
            ['endpoint']
        )

        self.recommendation_latency = Summary(
            f'{service_name}_recommendation_latency_seconds',
            'Latency for generating recommendations',
            ['endpoint']
        )

        self.database_query_latency = Histogram(
            f'{service_name}_database_query_latency_seconds',
            'Latency for database queries',
            ['endpoint', 'query_type']
        )

        self.external_model_call_latency = Histogram(
            f'{service_name}_external_model_call_latency_seconds',
            'Latency for external model API calls',
            ['model_endpoint']
        )

        self.recommendation_error_rate = Counter(
            f'{service_name}_recommendation_errors_total',
            'Total number of recommendation generation errors',
            ['endpoint', 'error_type']
        )

    def track_request(self, method, endpoint, status):
        self.requests_total.labels(method, endpoint, status).inc()
    
    def observe_latency(self, method, endpoint, latency):
        self.request_latency.labels(method, endpoint).observe(latency)

    def track_recommendation_generation(self, endpoint):
        self.recommendations_generated.labels(endpoint).inc()

    def observe_recommendation_latency(self, endpoint, latency):
        self.recommendation_latency.labels(endpoint).observe(latency)

    def observe_database_query_latency(self, endpoint, query_type, latency):
        self.database_query_latency.labels(endpoint, query_type).observe(latency)

    def track_recommendation_error(self, endpoint, error_type):
        self.recommendation_error_rate.labels(endpoint, error_type).inc()

    def observe_external_model_call_latency(self, model_endpoint, latency):
        self.external_model_call_latency.labels(model_endpoint).observe(latency)

# Decorator for tracking metrics
def track_metrics(service_metrics, method, endpoint):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                latency = time.time() - start_time
                service_metrics.track_request(method, endpoint, 'success')
                service_metrics.observe_latency(method, endpoint, latency)
                return result
            except Exception as e:
                latency = time.time() - start_time
                service_metrics.track_request(method, endpoint, 'error')
                service_metrics.observe_latency(method, endpoint, latency)
                raise
        return wrapper
    return decorator


# Metrics server
def start_metrics_server(port=9102):
    """Start a metrics server on the specified port"""
    start_http_server(port)
