#!/bin/bash
# Canary Deployment Script with Progressive Rollout
# Implements safe canary deployments with automatic rollback

set -euo pipefail

# Configuration
NAMESPACE="${NAMESPACE:-prp-system}"
APP_NAME="${APP_NAME:-prp-api}"
CANARY_INITIAL_PERCENTAGE="${CANARY_INITIAL_PERCENTAGE:-5}"
CANARY_INCREMENT="${CANARY_INCREMENT:-10}"
CANARY_MAX_PERCENTAGE="${CANARY_MAX_PERCENTAGE:-100}"
WAIT_INTERVAL="${WAIT_INTERVAL:-300}" # 5 minutes between increments
ERROR_THRESHOLD="${ERROR_THRESHOLD:-0.05}" # 5% error rate threshold
LATENCY_THRESHOLD="${LATENCY_THRESHOLD:-2.0}" # 2 second latency threshold

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

# Usage
usage() {
    cat << EOF
Usage: $0 [OPTIONS] IMAGE_TAG

Deploy application using canary deployment strategy

Options:
    -n, --namespace         Kubernetes namespace (default: $NAMESPACE)
    -a, --app               Application name (default: $APP_NAME)
    -i, --initial           Initial canary percentage (default: $CANARY_INITIAL_PERCENTAGE)
    -s, --step              Percentage increment (default: $CANARY_INCREMENT)
    -m, --max               Maximum canary percentage (default: $CANARY_MAX_PERCENTAGE)
    -w, --wait              Wait interval between increments in seconds (default: $WAIT_INTERVAL)
    -e, --error-threshold   Error rate threshold (default: $ERROR_THRESHOLD)
    -l, --latency-threshold Latency threshold in seconds (default: $LATENCY_THRESHOLD)
    -h, --help              Show this help message

Example:
    $0 -n production -i 10 -s 20 v1.2.3
EOF
    exit 1
}

# Parse arguments
parse_args() {
    if [ $# -eq 0 ]; then
        usage
    fi

    while [[ $# -gt 0 ]]; do
        case $1 in
            -n|--namespace)
                NAMESPACE="$2"
                shift 2
                ;;
            -a|--app)
                APP_NAME="$2"
                shift 2
                ;;
            -i|--initial)
                CANARY_INITIAL_PERCENTAGE="$2"
                shift 2
                ;;
            -s|--step)
                CANARY_INCREMENT="$2"
                shift 2
                ;;
            -m|--max)
                CANARY_MAX_PERCENTAGE="$2"
                shift 2
                ;;
            -w|--wait)
                WAIT_INTERVAL="$2"
                shift 2
                ;;
            -e|--error-threshold)
                ERROR_THRESHOLD="$2"
                shift 2
                ;;
            -l|--latency-threshold)
                LATENCY_THRESHOLD="$2"
                shift 2
                ;;
            -h|--help)
                usage
                ;;
            *)
                IMAGE_TAG="$1"
                shift
                ;;
        esac
    done

    if [ -z "${IMAGE_TAG:-}" ]; then
        log_error "Image tag is required"
        usage
    fi
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed"
        exit 1
    fi
    
    # Check jq
    if ! command -v jq &> /dev/null; then
        log_error "jq is not installed"
        exit 1
    fi
    
    # Check prometheus access
    if ! kubectl get svc prometheus -n monitoring &> /dev/null; then
        log_warning "Prometheus service not found in monitoring namespace"
    fi
    
    # Check if namespace exists
    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log_error "Namespace $NAMESPACE does not exist"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Get current stable version
get_stable_version() {
    kubectl get deployment "${APP_NAME}-stable" -n "$NAMESPACE" \
        -o jsonpath='{.spec.template.spec.containers[0].image}' 2>/dev/null || echo "none"
}

# Deploy canary
deploy_canary() {
    log_info "Deploying canary version: $IMAGE_TAG"
    
    # Create canary deployment from stable
    kubectl get deployment "${APP_NAME}-stable" -n "$NAMESPACE" -o yaml | \
        sed -e "s/${APP_NAME}-stable/${APP_NAME}-canary/g" \
            -e "s|image:.*|image: $IMAGE_TAG|" \
            -e "s/deployment: stable/deployment: canary/g" | \
        kubectl apply -f -
    
    # Scale canary to 1 replica initially
    kubectl scale deployment "${APP_NAME}-canary" -n "$NAMESPACE" --replicas=1
    
    # Wait for canary to be ready
    log_info "Waiting for canary deployment to be ready..."
    kubectl rollout status deployment "${APP_NAME}-canary" -n "$NAMESPACE" --timeout=5m
    
    log_success "Canary deployed successfully"
}

# Update traffic split
update_traffic_split() {
    local canary_weight=$1
    local stable_weight=$((100 - canary_weight))
    
    log_info "Updating traffic split: Canary=${canary_weight}%, Stable=${stable_weight}%"
    
    # Update service mesh traffic split (example for Istio)
    cat <<EOF | kubectl apply -f -
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: ${APP_NAME}
  namespace: ${NAMESPACE}
spec:
  hosts:
  - ${APP_NAME}
  http:
  - match:
    - headers:
        canary:
          exact: "true"
    route:
    - destination:
        host: ${APP_NAME}
        subset: canary
      weight: 100
  - route:
    - destination:
        host: ${APP_NAME}
        subset: stable
      weight: ${stable_weight}
    - destination:
        host: ${APP_NAME}
        subset: canary
      weight: ${canary_weight}
---
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: ${APP_NAME}
  namespace: ${NAMESPACE}
spec:
  host: ${APP_NAME}
  subsets:
  - name: stable
    labels:
      deployment: stable
  - name: canary
    labels:
      deployment: canary
EOF
    
    log_success "Traffic split updated"
}

# Query Prometheus metrics
query_prometheus() {
    local query=$1
    local prometheus_url="http://prometheus.monitoring.svc.cluster.local:9090"
    
    kubectl run prometheus-query --rm -i --restart=Never --image=curlimages/curl:latest -- \
        -s "${prometheus_url}/api/v1/query?query=${query}" | \
        jq -r '.data.result[0].value[1]' 2>/dev/null || echo "0"
}

# Check canary health
check_canary_health() {
    log_info "Checking canary health metrics..."
    
    # Calculate error rate
    local error_rate_query='sum(rate(http_requests_total{deployment="canary",status=~"5.."}[5m]))/sum(rate(http_requests_total{deployment="canary"}[5m]))'
    local error_rate=$(query_prometheus "$error_rate_query")
    
    # Calculate P95 latency
    local latency_query='histogram_quantile(0.95,sum(rate(http_request_duration_seconds_bucket{deployment="canary"}[5m]))by(le))'
    local latency=$(query_prometheus "$latency_query")
    
    # Compare with stable
    local stable_error_query='sum(rate(http_requests_total{deployment="stable",status=~"5.."}[5m]))/sum(rate(http_requests_total{deployment="stable"}[5m]))'
    local stable_error_rate=$(query_prometheus "$stable_error_query")
    
    log_info "Canary metrics: Error rate=${error_rate}, Latency=${latency}s"
    log_info "Stable metrics: Error rate=${stable_error_rate}"
    
    # Check thresholds
    if (( $(echo "$error_rate > $ERROR_THRESHOLD" | bc -l) )); then
        log_error "Canary error rate ${error_rate} exceeds threshold ${ERROR_THRESHOLD}"
        return 1
    fi
    
    if (( $(echo "$latency > $LATENCY_THRESHOLD" | bc -l) )); then
        log_error "Canary latency ${latency}s exceeds threshold ${LATENCY_THRESHOLD}s"
        return 1
    fi
    
    if (( $(echo "$error_rate > $stable_error_rate * 1.5" | bc -l) )); then
        log_error "Canary error rate is 50% higher than stable"
        return 1
    fi
    
    log_success "Canary health check passed"
    return 0
}

# Rollback canary
rollback_canary() {
    log_warning "Rolling back canary deployment..."
    
    # Route all traffic back to stable
    update_traffic_split 0
    
    # Delete canary deployment
    kubectl delete deployment "${APP_NAME}-canary" -n "$NAMESPACE" --ignore-not-found=true
    
    # Clean up virtual service
    kubectl delete virtualservice "${APP_NAME}" -n "$NAMESPACE" --ignore-not-found=true
    kubectl delete destinationrule "${APP_NAME}" -n "$NAMESPACE" --ignore-not-found=true
    
    log_success "Canary rollback completed"
    
    # Send notification
    send_notification "Canary deployment rolled back" "error"
    
    exit 1
}

# Promote canary to stable
promote_canary() {
    log_info "Promoting canary to stable..."
    
    # Get canary image
    local canary_image=$(kubectl get deployment "${APP_NAME}-canary" -n "$NAMESPACE" \
        -o jsonpath='{.spec.template.spec.containers[0].image}')
    
    # Update stable deployment
    kubectl set image deployment/"${APP_NAME}-stable" \
        "${APP_NAME}=${canary_image}" -n "$NAMESPACE"
    
    # Wait for stable rollout
    kubectl rollout status deployment "${APP_NAME}-stable" -n "$NAMESPACE" --timeout=10m
    
    # Clean up canary
    kubectl delete deployment "${APP_NAME}-canary" -n "$NAMESPACE" --ignore-not-found=true
    kubectl delete virtualservice "${APP_NAME}" -n "$NAMESPACE" --ignore-not-found=true
    kubectl delete destinationrule "${APP_NAME}" -n "$NAMESPACE" --ignore-not-found=true
    
    log_success "Canary promoted to stable successfully"
}

# Send notification
send_notification() {
    local message=$1
    local status=${2:-info}
    
    # Slack notification (if webhook is set)
    if [ -n "${SLACK_WEBHOOK:-}" ]; then
        local color="good"
        [ "$status" = "error" ] && color="danger"
        [ "$status" = "warning" ] && color="warning"
        
        curl -X POST "$SLACK_WEBHOOK" \
            -H 'Content-Type: application/json' \
            -d "{
                \"attachments\": [{
                    \"color\": \"$color\",
                    \"title\": \"Canary Deployment Update\",
                    \"text\": \"$message\",
                    \"fields\": [
                        {\"title\": \"Application\", \"value\": \"$APP_NAME\", \"short\": true},
                        {\"title\": \"Namespace\", \"value\": \"$NAMESPACE\", \"short\": true},
                        {\"title\": \"Version\", \"value\": \"$IMAGE_TAG\", \"short\": true}
                    ]
                }]
            }" 2>/dev/null || true
    fi
}

# Main deployment flow
main() {
    parse_args "$@"
    
    log_info "Starting canary deployment"
    log_info "Configuration:"
    log_info "  Namespace: $NAMESPACE"
    log_info "  Application: $APP_NAME"
    log_info "  Image: $IMAGE_TAG"
    log_info "  Initial %: $CANARY_INITIAL_PERCENTAGE"
    log_info "  Increment: $CANARY_INCREMENT"
    log_info "  Max %: $CANARY_MAX_PERCENTAGE"
    
    check_prerequisites
    
    # Save current stable version for rollback
    STABLE_VERSION=$(get_stable_version)
    log_info "Current stable version: $STABLE_VERSION"
    
    # Deploy canary
    deploy_canary
    
    # Progressive rollout
    local current_percentage=$CANARY_INITIAL_PERCENTAGE
    
    while [ "$current_percentage" -le "$CANARY_MAX_PERCENTAGE" ]; do
        log_info "Setting canary traffic to ${current_percentage}%"
        update_traffic_split "$current_percentage"
        
        # Wait for traffic to stabilize
        log_info "Waiting ${WAIT_INTERVAL}s for metrics to stabilize..."
        sleep "$WAIT_INTERVAL"
        
        # Check canary health
        if ! check_canary_health; then
            log_error "Canary health check failed"
            rollback_canary
        fi
        
        # Send progress notification
        send_notification "Canary at ${current_percentage}% - Health check passed" "good"
        
        # Check if we've reached max
        if [ "$current_percentage" -eq "$CANARY_MAX_PERCENTAGE" ]; then
            break
        fi
        
        # Increment traffic
        current_percentage=$((current_percentage + CANARY_INCREMENT))
        if [ "$current_percentage" -gt "$CANARY_MAX_PERCENTAGE" ]; then
            current_percentage=$CANARY_MAX_PERCENTAGE
        fi
    done
    
    # Final health check
    log_info "Running final health check before promotion..."
    sleep 60
    if ! check_canary_health; then
        log_error "Final health check failed"
        rollback_canary
    fi
    
    # Promote canary
    promote_canary
    
    send_notification "Canary deployment completed successfully! Version $IMAGE_TAG is now stable." "good"
    log_success "Canary deployment completed successfully!"
}

# Run main function
main "$@"