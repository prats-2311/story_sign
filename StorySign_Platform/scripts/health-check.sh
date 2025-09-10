#!/bin/bash

# Health Check Script for StorySign Platform
# Tests both local and production deployments

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if jq is available
check_jq() {
    if ! command -v jq &> /dev/null; then
        print_warning "jq is not installed. JSON parsing will be limited."
        return 1
    fi
    return 0
}

# Test a health endpoint
test_health_endpoint() {
    local url=$1
    local name=$2
    
    print_status "Testing $name health endpoint: $url"
    
    # Make request with timeout
    local response=$(curl -s -w "%{http_code}" --max-time 10 "$url" 2>/dev/null || echo "000")
    local http_code="${response: -3}"
    local body="${response%???}"
    
    if [ "$http_code" = "200" ]; then
        print_success "$name health check passed (HTTP $http_code)"
        
        # Try to parse JSON response if jq is available
        if check_jq && echo "$body" | jq . >/dev/null 2>&1; then
            local status=$(echo "$body" | jq -r '.status // "unknown"')
            local uptime=$(echo "$body" | jq -r '.uptime_seconds // "unknown"')
            echo "  Status: $status"
            echo "  Uptime: $uptime seconds"
        else
            echo "  Response: ${body:0:100}..."
        fi
        return 0
    else
        print_error "$name health check failed (HTTP $http_code)"
        if [ "$http_code" = "000" ]; then
            echo "  Error: Connection timeout or network error"
        else
            echo "  Response: ${body:0:200}..."
        fi
        return 1
    fi
}

# Test frontend availability
test_frontend() {
    local url=$1
    local name=$2
    
    print_status "Testing $name frontend: $url"
    
    local http_code=$(curl -s -w "%{http_code}" -o /dev/null --max-time 10 "$url" 2>/dev/null || echo "000")
    
    if [ "$http_code" = "200" ]; then
        print_success "$name frontend is accessible (HTTP $http_code)"
        return 0
    else
        print_error "$name frontend is not accessible (HTTP $http_code)"
        return 1
    fi
}

# Main health check function
run_health_checks() {
    local environment=$1
    local backend_url=$2
    local frontend_url=$3
    
    echo "🏥 Health Check for $environment Environment"
    echo "============================================"
    
    local backend_success=0
    local frontend_success=0
    
    # Test backend health
    if test_health_endpoint "$backend_url/health" "$environment Backend"; then
        backend_success=1
    fi
    
    # Test frontend
    if test_frontend "$frontend_url" "$environment Frontend"; then
        frontend_success=1
    fi
    
    # Test API root endpoint
    print_status "Testing $environment API root endpoint"
    if test_health_endpoint "$backend_url/" "$environment API Root"; then
        echo "  API documentation available at: $backend_url/docs"
    fi
    
    # Summary
    echo
    echo "📊 Summary for $environment:"
    echo "  Backend Health: $([ $backend_success -eq 1 ] && echo "✅ Healthy" || echo "❌ Unhealthy")"
    echo "  Frontend: $([ $frontend_success -eq 1 ] && echo "✅ Accessible" || echo "❌ Inaccessible")"
    
    return $((2 - backend_success - frontend_success))
}

# Show usage
show_usage() {
    echo "Usage: $0 [local|production|all]"
    echo
    echo "Options:"
    echo "  local       Test local development environment"
    echo "  production  Test production environment"
    echo "  all         Test both environments"
    echo "  help        Show this help message"
    echo
    echo "Examples:"
    echo "  $0 local"
    echo "  $0 production"
    echo "  $0 all"
}

# Main script
main() {
    local environment=${1:-"all"}
    
    case $environment in
        "local")
            run_health_checks "Local" "http://localhost:8000" "http://localhost:3000"
            ;;
        "production")
            run_health_checks "Production" "https://storysign-backend.onrender.com" "https://storysign-platform.netlify.app"
            ;;
        "all")
            echo "🔍 Running health checks for all environments..."
            echo
            
            local local_result=0
            local prod_result=0
            
            run_health_checks "Local" "http://localhost:8000" "http://localhost:3000" || local_result=$?
            echo
            run_health_checks "Production" "https://storysign-backend.onrender.com" "https://storysign-platform.netlify.app" || prod_result=$?
            
            echo
            echo "🎯 Overall Summary:"
            echo "  Local Environment: $([ $local_result -eq 0 ] && echo "✅ All services healthy" || echo "⚠️ Some issues detected")"
            echo "  Production Environment: $([ $prod_result -eq 0 ] && echo "✅ All services healthy" || echo "⚠️ Some issues detected")"
            
            return $((local_result + prod_result))
            ;;
        "help"|"-h"|"--help")
            show_usage
            return 0
            ;;
        *)
            print_error "Invalid option: $environment"
            show_usage
            return 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"