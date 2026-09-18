"""Prometheus metrics integration."""

from prometheus_client import Counter, Gauge, Histogram, Info
from prometheus_client import start_http_server
from typing import Dict

# Application info
app_info = Info(
    'opscode_build_info',
    'Build information about Opscode'
)

# Workload metrics
workloads_total = Gauge(
    'opscode_workloads_total',
    'Total number of discovered workloads',
    ['namespace', 'kind']
)

workloads_healthy = Gauge(
    'opscode_workloads_healthy',
    'Number of healthy workloads',
    ['namespace']
)

workloads_degraded = Gauge(
    'opscode_workloads_degraded',
    'Number of degraded workloads',
    ['namespace']
)

workloads_unhealthy = Gauge(
    'opscode_workloads_unhealthy',
    'Number of unhealthy workloads',
    ['namespace']
)

# Incident metrics
incidents_total = Counter(
    'opscode_incidents_total',
    'Total number of incidents detected',
    ['severity', 'type']
)

incidents_open = Gauge(
    'opscode_incidents_open',
    'Number of currently open incidents',
    ['severity']
)

incidents_resolved_total = Counter(
    'opscode_incidents_resolved_total',
    'Total number of resolved incidents',
    ['severity']
)

# Remediation metrics
remediation_total = Counter(
    'opscode_remediation_total',
    'Total number of remediation actions',
    ['action', 'status']
)

remediation_failures_total = Counter(
    'opscode_remediation_failures_total',
    'Total number of failed remediation actions',
    ['action']
)

remediation_duration_seconds = Histogram(
    'opscode_remediation_duration_seconds',
    'Duration of remediation actions',
    ['action'],
    buckets=[0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0]
)

# Health check metrics
health_check_duration_seconds = Histogram(
    'opscode_health_check_duration_seconds',
    'Duration of health checks',
    ['check_type'],
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0]
)

health_checks_total = Counter(
    'opscode_health_checks_total',
    'Total number of health checks performed',
    ['check_type', 'status']
)

# API metrics
api_requests_total = Counter(
    'opscode_api_requests_total',
    'Total number of API requests',
    ['method', 'endpoint', 'status']
)

api_request_duration_seconds = Histogram(
    'opscode_api_request_duration_seconds',
    'Duration of API requests',
    ['method', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0]
)

# Database metrics
db_query_duration_seconds = Histogram(
    'opscode_db_query_duration_seconds',
    'Duration of database queries',
    ['operation'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0]
)

db_connections_active = Gauge(
    'opscode_db_connections_active',
    'Number of active database connections'
)

# Redis metrics
redis_operations_total = Counter(
    'opscode_redis_operations_total',
    'Total number of Redis operations',
    ['operation', 'status']
)

redis_operation_duration_seconds = Histogram(
    'opscode_redis_operation_duration_seconds',
    'Duration of Redis operations',
    ['operation'],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5]
)

# Kubernetes metrics
kubernetes_operations_total = Counter(
    'opscode_kubernetes_operations_total',
    'Total number of Kubernetes operations',
    ['operation', 'status']
)

kubernetes_operation_duration_seconds = Histogram(
    'opscode_kubernetes_operation_duration_seconds',
    'Duration of Kubernetes operations',
    ['operation'],
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0]
)


def init_metrics() -> None:
    """Initialize Prometheus metrics."""
    from app.core.config import get_settings

    settings = get_settings()

    # Set application info
    app_info.info({
        'version': settings.app_version,
        'environment': settings.environment,
    })

    if settings.prometheus_enabled:
        # Note: The actual HTTP server is started by FastAPI middleware
        # This is just for the metrics setup
        pass


def record_workload_metrics(workloads: list) -> None:
    """Record workload metrics."""
    from collections import defaultdict

    namespace_counts = defaultdict(lambda: {'healthy': 0, 'degraded': 0, 'unhealthy': 0, 'total': 0})
    kind_counts = defaultdict(int)

    for workload in workloads:
        namespace = workload.namespace
        kind = workload.kind
        health = workload.health.value

        namespace_counts[namespace]['total'] += 1
        kind_counts[kind] += 1

        if health == 'HEALTHY':
            namespace_counts[namespace]['healthy'] += 1
        elif health == 'DEGRADED':
            namespace_counts[namespace]['degraded'] += 1
        elif health == 'UNHEALTHY':
            namespace_counts[namespace]['unhealthy'] += 1

    # Update gauges
    for namespace, counts in namespace_counts.items():
        workloads_healthy.labels(namespace=namespace).set(counts['healthy'])
        workloads_degraded.labels(namespace=namespace).set(counts['degraded'])
        workloads_unhealthy.labels(namespace=namespace).set(counts['unhealthy'])

    for kind, count in kind_counts.items():
        workloads_total.labels(namespace='all', kind=kind).set(count)


def record_incident_created(severity: str, incident_type: str) -> None:
    """Record incident creation."""
    incidents_total.labels(severity=severity, type=incident_type).inc()


def record_incident_resolved(severity: str) -> None:
    """Record incident resolution."""
    incidents_resolved_total.labels(severity=severity).inc()


def update_open_incidents(incidents: list) -> None:
    """Update open incidents gauge."""
    from collections import defaultdict

    severity_counts = defaultdict(int)

    for incident in incidents:
        if incident.status.value == 'OPEN':
            severity_counts[incident.severity.value] += 1

    for severity, count in severity_counts.items():
        incidents_open.labels(severity=severity).set(count)


def record_remediation_started(action: str) -> None:
    """Record remediation start."""
    remediation_total.labels(action=action, status='started').inc()


def record_remediation_completed(action: str, status: str, duration: float) -> None:
    """Record remediation completion."""
    remediation_total.labels(action=action, status=status).inc()
    remediation_duration_seconds.labels(action=action).observe(duration)

    if status == 'FAILED':
        remediation_failures_total.labels(action=action).inc()


def record_health_check(check_type: str, status: str, duration: float) -> None:
    """Record health check."""
    health_checks_total.labels(check_type=check_type, status=status).inc()
    health_check_duration_seconds.labels(check_type=check_type).observe(duration)


def record_api_request(method: str, endpoint: str, status: int, duration: float) -> None:
    """Record API request."""
    api_requests_total.labels(method=method, endpoint=endpoint, status=status).inc()
    api_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)


def record_db_query(operation: str, duration: float) -> None:
    """Record database query."""
    db_query_duration_seconds.labels(operation=operation).observe(duration)


def record_redis_operation(operation: str, status: str, duration: float) -> None:
    """Record Redis operation."""
    redis_operations_total.labels(operation=operation, status=status).inc()
    redis_operation_duration_seconds.labels(operation=operation).observe(duration)


def record_kubernetes_operation(operation: str, status: str, duration: float) -> None:
    """Record Kubernetes operation."""
    kubernetes_operations_total.labels(operation=operation, status=status).inc()
    kubernetes_operation_duration_seconds.labels(operation=operation).observe(duration)
