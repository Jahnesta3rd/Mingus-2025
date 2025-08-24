# Mingus Flask Application Health Check Endpoints

This document describes all available health check endpoints for the Mingus Flask application, designed for production monitoring and deployment validation.

## Overview

The Mingus application provides multiple health check endpoints at different levels of detail, from basic load balancer checks to comprehensive system monitoring for debugging and production operations.

## Basic Health Endpoints

### 1. Basic Health Check
**Endpoint:** `GET /health`

**Purpose:** Basic application health for load balancers and simple monitoring

**Response:**
```json
{
    "status": "healthy",
    "timestamp": "2025-01-27T10:30:00.000Z"
}
```

**Status Codes:**
- `200`: Application is healthy
- `503`: Application is unhealthy

### 2. Detailed Health Check
**Endpoint:** `GET /health/detailed`

**Purpose:** Comprehensive health check with database, Redis, external services, and system resources

**Response:**
```json
{
    "status": "healthy",
    "timestamp": "2025-01-27T10:30:00.000Z",
    "response_time_ms": 125.8,
    "services": {
        "database": {
            "status": "healthy",
            "response_time_ms": 12.5
        },
        "redis": {
            "status": "healthy",
            "response_time_ms": 2.1
        },
        "external_services": {
            "plaid_api": {
                "status": "healthy",
                "response_time_ms": 150.3
            }
        }
    },
    "system_resources": {
        "cpu": {
            "usage_percent": 15.2,
            "cores": 4
        },
        "memory": {
            "usage_percent": 45.8,
            "available_gb": 8.5
        },
        "disk": {
            "usage_percent": 35.2,
            "free_gb": 45.8
        }
    },
    "application": {
        "uptime_seconds": 86400,
        "memory_rss_mb": 256.5,
        "cpu_percent": 2.1,
        "num_threads": 8,
        "open_files": 45,
        "connections": 12
    },
    "unhealthy_services": [],
    "critical_services_failing": false
}
```

**Status Codes:**
- `200`: Application is healthy
- `503`: Application is unhealthy
- `500`: Internal server error during health check

### 3. Database Health Check
**Endpoint:** `GET /health/database`

**Purpose:** Dedicated database health check with SQLAlchemy connection, responsiveness, and connection pool monitoring

**Response:**
```json
{
    "status": "healthy",
    "timestamp": "2025-01-27T10:30:00.000Z",
    "response_time_ms": 45.2,
    "connection": {
        "status": "healthy",
        "error": null
    },
    "responsiveness": {
        "status": "healthy",
        "error": null,
        "table_count": 25
    },
    "connection_pool": {
        "status": "healthy",
        "error": null,
        "info": {
            "pool_size": 10,
            "checked_in": 8,
            "checked_out": 2,
            "overflow": 0,
            "invalid": 0
        }
    }
}
```

**Status Codes:**
- `200`: Database is healthy (including warnings)
- `503`: Database is unhealthy
- `500`: Internal server error during health check

**Features:**
- ✅ **SQLAlchemy Connection Test** - Basic connection verification
- ✅ **Database Responsiveness** - Complex query testing with table count
- ✅ **Connection Pool Monitoring** - Pool size, usage, and invalid connection detection
- ✅ **Performance Metrics** - Response time measurement
- ✅ **Detailed Error Reporting** - Specific error messages for each component

### 4. Redis Health Check
**Endpoint:** `GET /health/redis`

**Purpose:** Dedicated Redis health check with connectivity, cache operations, and memory usage monitoring

**Response:**
```json
{
    "status": "healthy",
    "timestamp": "2025-01-27T10:30:00.000Z",
    "response_time_ms": 25.8,
    "connectivity": {
        "status": "healthy",
        "error": null,
        "response_time_ms": 2.1,
        "host": "localhost",
        "port": 6379,
        "db": 0
    },
    "cache_operations": {
        "status": "healthy",
        "error": null,
        "response_time_ms": 15.3
    },
    "memory_usage": {
        "status": "healthy",
        "error": null,
        "info": {
            "used_memory_human": "45.2M",
            "used_memory_peak_human": "50.1M",
            "used_memory_rss_human": "48.5M",
            "used_memory_lua_human": "38.0K",
            "mem_fragmentation_ratio": 1.12,
            "memory_usage_percent": 35.2,
            "total_connections_received": 1250,
            "total_commands_processed": 45600,
            "keyspace_hits": 42000,
            "keyspace_misses": 3600,
            "uptime_in_seconds": 86400,
            "connected_clients": 5
        }
    }
}
```

**Status Codes:**
- `200`: Redis is healthy (including warnings)
- `503`: Redis is unhealthy
- `500`: Internal server error during health check

**Features:**
- ✅ **Redis Connectivity Test** - Basic connection verification with ping
- ✅ **Cache Operations Verification** - Write, read, and delete operations testing
- ✅ **Memory Usage Monitoring** - Comprehensive memory metrics and thresholds
- ✅ **Performance Metrics** - Response time measurement for each operation
- ✅ **Cache Hit Rate Analysis** - Keyspace hits and misses tracking
- ✅ **Connection Monitoring** - Active client connections and total connections
- ✅ **Memory Threshold Alerts** - Warnings for high memory usage (>90%) and critical usage (>95%)
- ✅ **Fragmentation Monitoring** - Memory fragmentation ratio tracking



### 5. External Services Health Check
**Endpoint:** `GET /health/external`

**Purpose:** Dedicated external services health check with Supabase, Stripe, Resend, and Twilio monitoring

**Response:**
```json
{
    "status": "healthy",
    "timestamp": "2025-01-27T10:30:00.000Z",
    "response_time_ms": 1250.5,
    "services": {
        "supabase_api": {
            "status": "healthy",
            "response_time_ms": 150.2,
            "error": null
        },
        "stripe_api": {
            "status": "healthy",
            "response_time_ms": 200.8,
            "error": null
        },
        "email_service_resend": {
            "status": "healthy",
            "response_time_ms": 180.5,
            "error": null
        },
        "sms_service_twilio": {
            "status": "healthy",
            "response_time_ms": 220.1,
            "error": null
        }
    },
    "unhealthy_services": [],
    "not_configured_services": [],
    "summary": {
        "total_services": 4,
        "healthy_services": 4,
        "unhealthy_services": 0,
        "not_configured_services": 0
    }
}
```

**Status Codes:**
- `200`: External services are healthy (including not configured)
- `503`: External services are unhealthy
- `500`: Internal server error during health check

**Features:**
- ✅ **Supabase API Connectivity** - Database and authentication service monitoring
- ✅ **Stripe API Status** - Payment processing service monitoring
- ✅ **Email Service (Resend) Status** - Email delivery service monitoring
- ✅ **SMS Service (Twilio) Status** - SMS delivery service monitoring
- ✅ **Performance Metrics** - Response time measurement for each service
- ✅ **Configuration Detection** - Identifies services that are not configured
- ✅ **Comprehensive Summary** - Overall health status and service counts
- ✅ **Error Reporting** - Detailed error messages for each service
- ✅ **Graceful Degradation** - Continues checking other services if one fails

---

## Comprehensive System Health Endpoints

### 6. System Health Overview
**Endpoint:** `GET /api/system/health/`

**Purpose:** Comprehensive health check of all system components

**Response:**
```json
{
    "success": true,
    "timestamp": "2025-01-27T10:30:00.000Z",
    "data": {
        "overall_status": "healthy",
        "response_time_ms": 45.2,
        "timestamp": "2025-01-27T10:30:00.000Z",
        "services": {
            "database": {
                "status": "healthy",
                "connection": "active",
                "response_time_ms": 12.5,
                "table_count": 25,
                "last_check": "2025-01-27T10:30:00.000Z"
            },
            "redis": {
                "status": "healthy",
                "connection": "active",
                "response_time_ms": 2.1,
                "memory_usage_mb": 45.2,
                "last_check": "2025-01-27T10:30:00.000Z"
            },
            "external_services": {
                "plaid_api": {
                    "status": "healthy",
                    "response_time_ms": 150.3,
                    "last_check": "2025-01-27T10:30:00.000Z"
                }
            },
            "system_resources": {
                "cpu": {
                    "status": "healthy",
                    "usage_percent": 15.2,
                    "cores": 4
                },
                "memory": {
                    "status": "healthy",
                    "usage_percent": 45.8,
                    "available_gb": 8.5
                },
                "disk": {
                    "status": "healthy",
                    "usage_percent": 35.2,
                    "free_gb": 45.8
                }
            },
            "application": {
                "status": "healthy",
                "uptime_seconds": 86400,
                "version": "1.0.0",
                "environment": "production"
            }
        },
        "unhealthy_services": [],
        "critical_services_failing": false
    }
}
```

### 7. Simple Health Check
**Endpoint:** `GET /api/system/health/simple`

**Purpose:** Quick health check for load balancers with minimal overhead

**Response:**
```json
{
    "success": true,
    "timestamp": "2025-01-27T10:30:00.000Z",
    "data": {
        "status": "healthy",
        "database": "healthy",
        "redis": "healthy",
        "timestamp": "2025-01-27T10:30:00.000Z"
    }
}
```

### 8. Detailed Health Check
**Endpoint:** `GET /api/system/health/detailed`

**Purpose:** Comprehensive health check with detailed system information for debugging

**Response:**
```json
{
    "success": true,
    "timestamp": "2025-01-27T10:30:00.000Z",
    "data": {
        "overall_status": "healthy",
        "timestamp": "2025-01-27T10:30:00.000Z",
        "response_time_ms": 125.8,
        "services": {
            // Same as comprehensive health check
        },
        "process_info": {
            "pid": 12345,
            "memory_rss_mb": 256.5,
            "cpu_percent": 2.1,
            "num_threads": 8,
            "open_files": 45,
            "connections": 12
        },
        "environment": {
            "python_version": "/usr/bin/python3",
            "flask_env": "production",
            "debug_mode": false
        },
        "unhealthy_services": []
    }
}
```

---

## Kubernetes/Container Orchestration Endpoints

### 9. Readiness Probe
**Endpoint:** `GET /api/system/health/readiness`

**Purpose:** Kubernetes readiness probe - indicates if the application is ready to serve traffic

**Response:**
```json
{
    "success": true,
    "timestamp": "2025-01-27T10:30:00.000Z",
    "data": {
        "ready": true,
        "timestamp": "2025-01-27T10:30:00.000Z",
        "services": {
            "database": "healthy",
            "redis": "healthy"
        }
    }
}
```

**Status Codes:**
- `200`: Application is ready to serve traffic
- `503`: Application is not ready (database/redis unavailable)

### 10. Liveness Probe
**Endpoint:** `GET /api/system/health/liveness`

**Purpose:** Kubernetes liveness probe - indicates if the application is alive and running

**Response:**
```json
{
    "success": true,
    "timestamp": "2025-01-27T10:30:00.000Z",
    "data": {
        "alive": true,
        "timestamp": "2025-01-27T10:30:00.000Z",
        "uptime_seconds": 86400
    }
}
```

**Status Codes:**
- `200`: Application is alive
- `503`: Application is not responding

### 11. Startup Probe
**Endpoint:** `GET /api/system/health/startup`

**Purpose:** Kubernetes startup probe - indicates if the application has finished startup

**Response:**
```json
{
    "success": true,
    "timestamp": "2025-01-27T10:30:00.000Z",
    "data": {
        "started": true,
        "timestamp": "2025-01-27T10:30:00.000Z",
        "services": {
            "database": "healthy",
            "redis": "healthy",
            "system_resources": "healthy"
        }
    }
}
```

**Status Codes:**
- `200`: Application has finished startup
- `503`: Application is still starting up

---

## Individual Service Health Checks

### 12. Database Health
**Endpoint:** `GET /api/system/health/database`

**Purpose:** Check database connectivity and performance

**Response:**
```json
{
    "success": true,
    "timestamp": "2025-01-27T10:30:00.000Z",
    "data": {
        "status": "healthy",
        "connection": "active",
        "response_time_ms": 12.5,
        "table_count": 25,
        "last_check": "2025-01-27T10:30:00.000Z"
    }
}
```

### 13. Redis Health
**Endpoint:** `GET /api/system/health/redis`

**Purpose:** Check Redis connectivity and performance

**Response:**
```json
{
    "success": true,
    "timestamp": "2025-01-27T10:30:00.000Z",
    "data": {
        "status": "healthy",
        "connection": "active",
        "response_time_ms": 2.1,
        "memory_usage_mb": 45.2,
        "last_check": "2025-01-27T10:30:00.000Z"
    }
}
```

### 14. External Services Health
**Endpoint:** `GET /api/system/health/external`

**Purpose:** Check external service dependencies (Plaid API, etc.)

**Response:**
```json
{
    "success": true,
    "timestamp": "2025-01-27T10:30:00.000Z",
    "data": {
        "plaid_api": {
            "status": "healthy",
            "response_time_ms": 150.3,
            "last_check": "2025-01-27T10:30:00.000Z"
        }
    }
}
```

### 15. System Resources Health
**Endpoint:** `GET /api/system/health/resources`

**Purpose:** Check system resource utilization

**Response:**
```json
{
    "success": true,
    "timestamp": "2025-01-27T10:30:00.000Z",
    "data": {
        "cpu": {
            "status": "healthy",
            "usage_percent": 15.2,
            "cores": 4
        },
        "memory": {
            "status": "healthy",
            "usage_percent": 45.8,
            "available_gb": 8.5
        },
        "disk": {
            "status": "healthy",
            "usage_percent": 35.2,
            "free_gb": 45.8
        }
    }
}
```

### 16. Application Health
**Endpoint:** `GET /api/system/health/application`

**Purpose:** Check application-specific health metrics

**Response:**
```json
{
    "success": true,
    "timestamp": "2025-01-27T10:30:00.000Z",
    "data": {
        "status": "healthy",
        "uptime_seconds": 86400,
        "version": "1.0.0",
        "environment": "production",
        "active_connections": 45,
        "requests_per_minute": 120
    }
}
```

---

## Monitoring Metrics Endpoint

### 16. Health Metrics
**Endpoint:** `GET /api/system/health/metrics`

**Purpose:** Provide metrics in a format suitable for monitoring systems (Prometheus, etc.)

**Response:**
```json
{
    "success": true,
    "timestamp": "2025-01-27T10:30:00.000Z",
    "data": {
        "mingus_database_status": 1,
        "mingus_redis_status": 1,
        "mingus_database_response_time_ms": 12.5,
        "mingus_redis_response_time_ms": 2.1,
        "mingus_cpu_usage_percent": 15.2,
        "mingus_memory_usage_percent": 45.8,
        "mingus_disk_usage_percent": 35.2,
        "mingus_uptime_seconds": 86400,
        "mingus_health_check_timestamp": 1706352600
    }
}
```

---

## Usage Examples

### Basic Health Check
```bash
curl http://localhost:5003/health
```

### Detailed Health Check
```bash
curl http://localhost:5003/health/detailed
```

### Database Health Check
```bash
curl http://localhost:5003/health/database
```

### Redis Health Check
```bash
curl http://localhost:5003/health/redis
```

### Comprehensive System Health
```bash
curl http://localhost:5003/api/system/health/
```

### Load Balancer Configuration
```nginx
# Nginx configuration for load balancer health checks
upstream mingus_backend {
    server 127.0.0.1:5003 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    
    location /health {
        proxy_pass http://mingus_backend;
        proxy_connect_timeout 5s;
        proxy_send_timeout 5s;
        proxy_read_timeout 5s;
    }
}
```

### Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mingus-app
spec:
  template:
    spec:
      containers:
      - name: mingus
        image: mingus:latest
        ports:
        - containerPort: 5003
        livenessProbe:
          httpGet:
            path: /api/system/health/liveness
            port: 5003
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/system/health/readiness
            port: 5003
          initialDelaySeconds: 5
          periodSeconds: 5
        startupProbe:
          httpGet:
            path: /api/system/health/startup
            port: 5003
          failureThreshold: 30
          periodSeconds: 10
```

### Monitoring with Prometheus
```yaml
# Prometheus scrape configuration
scrape_configs:
  - job_name: 'mingus-health'
    static_configs:
      - targets: ['localhost:5003']
    metrics_path: '/api/system/health/metrics'
    scrape_interval: 30s
```

---

## Error Handling

All health check endpoints return consistent error responses:

```json
{
    "success": false,
    "timestamp": "2025-01-27T10:30:00.000Z",
    "data": {
        "error": "Error description",
        "type": "error_type"
    }
}
```

**Common HTTP Status Codes:**
- `200`: Healthy/Ready
- `503`: Unhealthy/Not Ready
- `500`: Internal Server Error
- `404`: Endpoint Not Found

---

## Security Considerations

1. **Authentication:** Health check endpoints are designed to be accessible without authentication for monitoring systems
2. **Rate Limiting:** Consider implementing rate limiting for detailed health checks to prevent abuse
3. **Information Disclosure:** Detailed health checks may expose sensitive system information - use in controlled environments only
4. **Network Security:** Ensure health check endpoints are only accessible from trusted monitoring networks

---

## Best Practices

1. **Use appropriate endpoints:**
   - `/health` for basic load balancer checks
   - `/api/system/health/simple` for quick health verification
   - `/api/system/health/readiness` for Kubernetes readiness probes
   - `/api/system/health/liveness` for Kubernetes liveness probes
   - `/api/system/health/detailed` for debugging and troubleshooting

2. **Monitor response times:** Health checks should complete quickly (< 1 second for basic checks)

3. **Set appropriate timeouts:** Configure monitoring systems with appropriate timeouts based on endpoint complexity

4. **Log health check failures:** Monitor and alert on health check failures in production

5. **Regular testing:** Test health check endpoints regularly to ensure they accurately reflect system health 