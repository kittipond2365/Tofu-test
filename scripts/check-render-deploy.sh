#!/bin/bash
# Render Deploy Monitor
# Check deploy status after push - separate from GitHub Actions

RENDER_TOKEN="rnd_M5id7MAhHpqNtHsczEiv33DCkWn8"
BACKEND_SERVICE="srv-d66u6375r7bs739fm1og"
FRONTEND_SERVICE="srv-d674higgjchc73ahsgtg"

check_deploy() {
    local service_id=$1
    local service_name=$2
    
    echo "🔍 Checking $service_name..."
    
    # Get latest deploy
    latest_deploy=$(curl -s -H "Authorization: Bearer $RENDER_TOKEN" \
        "https://api.render.com/v1/services/$service_id/deploys?limit=1" | \
        jq -r '.[0].deploy // empty')
    
    if [ -z "$latest_deploy" ]; then
        echo "❌ $service_name: No deploy found"
        return 1
    fi
    
    deploy_id=$(echo "$latest_deploy" | jq -r '.id')
    status=$(echo "$latest_deploy" | jq -r '.status')
    created_at=$(echo "$latest_deploy" | jq -r '.createdAt')
    
    echo "  Deploy: $deploy_id"
    echo "  Status: $status"
    echo "  Created: $created_at"
    
    case "$status" in
        "live")
            echo "✅ $service_name: Deploy successful"
            return 0
            ;;
        "build_failed"|"update_failed"|"canceled")
            echo "❌ $service_name: Deploy FAILED ($status)"
            return 1
            ;;
        "building"|"created")
            echo "⏳ $service_name: Still building..."
            return 2
            ;;
        *)
            echo "⚠️ $service_name: Unknown status ($status)"
            return 3
            ;;
    esac
}

# Check both services
echo "📊 Render Deploy Status Check"
echo "============================="
echo ""

backend_ok=false
frontend_ok=false

if check_deploy "$BACKEND_SERVICE" "Backend"; then
    backend_ok=true
fi

echo ""

if check_deploy "$FRONTEND_SERVICE" "Frontend"; then
    frontend_ok=true
fi

echo ""
echo "============================="

# Summary
if [ "$backend_ok" = true ] && [ "$frontend_ok" = true ]; then
    echo "✅ All deploys successful"
    exit 0
else
    echo "❌ Some deploys failed"
    exit 1
fi
