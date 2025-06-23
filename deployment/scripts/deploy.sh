#!/bin/bash

# Mingus Application Deployment Script
# This script handles automated deployment with rollback capabilities

set -e

# Configuration
APP_NAME="mingus-app"
DOCKER_REGISTRY="your-registry.com"
ENVIRONMENT=${1:-staging}
VERSION=${2:-latest}
ROLLBACK_VERSION=${3:-}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Error handling
trap 'log_error "Deployment failed. Rolling back..."; rollback_deployment; exit 1' ERR

# Function to check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if required tools are installed
    command -v docker >/dev/null 2>&1 || { log_error "Docker is required but not installed."; exit 1; }
    command -v kubectl >/dev/null 2>&1 || { log_error "kubectl is required but not installed."; exit 1; }
    command -v aws >/dev/null 2>&1 || { log_error "AWS CLI is required but not installed."; exit 1; }
    
    # Check if kubectl is configured
    kubectl cluster-info >/dev/null 2>&1 || { log_error "kubectl is not configured or cluster is not accessible."; exit 1; }
    
    # Check if AWS credentials are configured
    aws sts get-caller-identity >/dev/null 2>&1 || { log_error "AWS credentials are not configured."; exit 1; }
    
    log_success "Prerequisites check passed"
}

# Function to validate environment
validate_environment() {
    log_info "Validating environment: $ENVIRONMENT"
    
    case $ENVIRONMENT in
        staging|production)
            log_success "Environment $ENVIRONMENT is valid"
            ;;
        *)
            log_error "Invalid environment: $ENVIRONMENT. Use 'staging' or 'production'"
            exit 1
            ;;
    esac
}

# Function to run pre-deployment tests
run_pre_deployment_tests() {
    log_info "Running pre-deployment tests..."
    
    # Run unit tests
    log_info "Running unit tests..."
    if ! docker run --rm $DOCKER_REGISTRY/$APP_NAME:$VERSION pytest tests/unit/; then
        log_error "Unit tests failed"
        exit 1
    fi
    
    # Run integration tests
    log_info "Running integration tests..."
    if ! docker run --rm $DOCKER_REGISTRY/$APP_NAME:$VERSION pytest tests/integration/; then
        log_error "Integration tests failed"
        exit 1
    fi
    
    # Run security scans
    log_info "Running security scans..."
    if ! docker run --rm $DOCKER_REGISTRY/$APP_NAME:$VERSION bandit -r backend/; then
        log_warning "Security scan found issues"
    fi
    
    log_success "Pre-deployment tests completed"
}

# Function to backup current deployment
backup_current_deployment() {
    log_info "Backing up current deployment..."
    
    # Get current deployment version
    CURRENT_VERSION=$(kubectl get deployment $APP_NAME -o jsonpath='{.spec.template.spec.containers[0].image}' | cut -d: -f2)
    
    if [ "$CURRENT_VERSION" != "" ]; then
        echo $CURRENT_VERSION > .current_version
        log_success "Current version $CURRENT_VERSION backed up"
    else
        log_warning "No current deployment found"
    fi
}

# Function to deploy application
deploy_application() {
    log_info "Deploying application version $VERSION to $ENVIRONMENT..."
    
    # Update deployment
    kubectl set image deployment/$APP_NAME $APP_NAME=$DOCKER_REGISTRY/$APP_NAME:$VERSION
    
    # Wait for rollout to complete
    log_info "Waiting for deployment to complete..."
    if kubectl rollout status deployment/$APP_NAME --timeout=300s; then
        log_success "Deployment completed successfully"
    else
        log_error "Deployment failed"
        exit 1
    fi
}

# Function to run post-deployment tests
run_post_deployment_tests() {
    log_info "Running post-deployment tests..."
    
    # Get service URL
    SERVICE_URL=$(kubectl get service $APP_NAME -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
    
    if [ -z "$SERVICE_URL" ]; then
        SERVICE_URL="localhost:5002"
    fi
    
    # Wait for service to be ready
    log_info "Waiting for service to be ready..."
    for i in {1..30}; do
        if curl -f http://$SERVICE_URL/health >/dev/null 2>&1; then
            break
        fi
        sleep 10
    done
    
    # Run smoke tests
    log_info "Running smoke tests..."
    
    # Health check
    if ! curl -f http://$SERVICE_URL/health; then
        log_error "Health check failed"
        return 1
    fi
    
    # API endpoint check
    if ! curl -f http://$SERVICE_URL/api/auth/check-auth; then
        log_error "API endpoint check failed"
        return 1
    fi
    
    # Database connectivity check
    if ! curl -f http://$SERVICE_URL/api/health/database; then
        log_error "Database connectivity check failed"
        return 1
    fi
    
    log_success "Post-deployment tests passed"
}

# Function to rollback deployment
rollback_deployment() {
    log_warning "Rolling back deployment..."
    
    if [ -f .current_version ]; then
        PREVIOUS_VERSION=$(cat .current_version)
        log_info "Rolling back to version $PREVIOUS_VERSION"
        
        kubectl set image deployment/$APP_NAME $APP_NAME=$DOCKER_REGISTRY/$APP_NAME:$PREVIOUS_VERSION
        
        if kubectl rollout status deployment/$APP_NAME --timeout=300s; then
            log_success "Rollback completed successfully"
        else
            log_error "Rollback failed"
            exit 1
        fi
    else
        log_error "No previous version found for rollback"
        exit 1
    fi
}

# Function to update monitoring
update_monitoring() {
    log_info "Updating monitoring configuration..."
    
    # Update Prometheus targets if needed
    if [ -f "monitoring/prometheus.yml" ]; then
        kubectl create configmap prometheus-config --from-file=monitoring/prometheus.yml --dry-run=client -o yaml | kubectl apply -f -
        kubectl rollout restart deployment/prometheus
    fi
    
    # Update Grafana dashboards if needed
    if [ -d "monitoring/grafana/dashboards" ]; then
        kubectl create configmap grafana-dashboards --from-file=monitoring/grafana/dashboards --dry-run=client -o yaml | kubectl apply -f -
        kubectl rollout restart deployment/grafana
    fi
    
    log_success "Monitoring configuration updated"
}

# Function to send notifications
send_notification() {
    local status=$1
    local message=$2
    
    log_info "Sending deployment notification..."
    
    # Send Slack notification
    if [ ! -z "$SLACK_WEBHOOK_URL" ]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"Deployment $status: $message\"}" \
            $SLACK_WEBHOOK_URL
    fi
    
    # Send email notification
    if [ ! -z "$NOTIFICATION_EMAIL" ]; then
        echo "Deployment $status: $message" | mail -s "Mingus Deployment $status" $NOTIFICATION_EMAIL
    fi
    
    log_success "Notification sent"
}

# Function to cleanup
cleanup() {
    log_info "Cleaning up deployment artifacts..."
    
    # Remove temporary files
    rm -f .current_version
    
    log_success "Cleanup completed"
}

# Function to display deployment status
show_deployment_status() {
    log_info "Deployment Status:"
    
    echo "Environment: $ENVIRONMENT"
    echo "Version: $VERSION"
    echo "Timestamp: $(date)"
    
    # Show pod status
    kubectl get pods -l app=$APP_NAME
    
    # Show service status
    kubectl get service $APP_NAME
    
    # Show deployment status
    kubectl get deployment $APP_NAME
}

# Main deployment function
main() {
    log_info "Starting deployment process..."
    log_info "Environment: $ENVIRONMENT"
    log_info "Version: $VERSION"
    
    # Check if this is a rollback
    if [ ! -z "$ROLLBACK_VERSION" ]; then
        log_info "Performing rollback to version $ROLLBACK_VERSION"
        VERSION=$ROLLBACK_VERSION
    fi
    
    # Execute deployment steps
    check_prerequisites
    validate_environment
    run_pre_deployment_tests
    backup_current_deployment
    deploy_application
    run_post_deployment_tests
    update_monitoring
    show_deployment_status
    send_notification "SUCCESS" "Deployment to $ENVIRONMENT completed successfully"
    cleanup
    
    log_success "Deployment completed successfully!"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [environment] [version] [rollback_version]"
    echo ""
    echo "Arguments:"
    echo "  environment       Deployment environment (staging|production)"
    echo "  version          Docker image version to deploy"
    echo "  rollback_version Version to rollback to (optional)"
    echo ""
    echo "Examples:"
    echo "  $0 staging latest"
    echo "  $0 production v1.2.3"
    echo "  $0 production v1.2.2 v1.2.1"
}

# Check if help is requested
if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    show_usage
    exit 0
fi

# Check if environment is provided
if [ -z "$1" ]; then
    log_error "Environment is required"
    show_usage
    exit 1
fi

# Execute main function
main "$@" 