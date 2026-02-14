#!/bin/bash
# Render Deploy Monitor with State Tracking
# Runs every 2 minutes to check deploy status

RENDER_TOKEN="rnd_M5id7MAhHpqNtHsczEiv33DCkWn8"
BACKEND_SERVICE="srv-d66u6375r7bs739fm1og"
FRONTEND_SERVICE="srv-d674higgjchc73ahsgtg"
STATE_FILE="$HOME/.tofu-autofix/render-deploy-state.json"

# Create state file if not exists
[ -f "$STATE_FILE" ] || echo '{"backend":{"last_deploy":"","status":""},"frontend":{"last_deploy":"","status":""}}' > "$STATE_FILE"

check_service() {
    local service_id=$1
    local service_name=$2
    local service_key=$3
    
    # Get latest deploy
    deploy_info=$(curl -s -H "Authorization: Bearer $RENDER_TOKEN" \
        "https://api.render.com/v1/services/$service_id/deploys?limit=1" | \
        jq -r '.[0].deploy // empty')
    
    [ -z "$deploy_info" ] && return
    
    deploy_id=$(echo "$deploy_info" | jq -r '.id')
    status=$(echo "$deploy_info" | jq -r '.status')
    
    # Read previous state
    last_deploy=$(jq -r ".$service_key.last_deploy" "$STATE_FILE")
    last_status=$(jq -r ".$service_key.status" "$STATE_FILE")
    
    # Only notify on status change or new deploy
    if [ "$deploy_id" != "$last_deploy" ] || [ "$status" != "$last_status" ]; then
        
        # Update state
        jq ".$service_key.last_deploy = \"$deploy_id\" | .$service_key.status = \"$status\"" "$STATE_FILE" > "${STATE_FILE}.tmp" && mv "${STATE_FILE}.tmp" "$STATE_FILE"
        
        case "$status" in
            "live")
                if [ "$deploy_id" != "$last_deploy" ]; then
                    echo "✅ $service_name: Deploy $deploy_id is LIVE"
                    # Here you could send notification that deploy succeeded
                fi
                ;;
            "build_failed"|"update_failed")
                echo "❌ $service_name: Deploy $deploy_id FAILED ($status)"
                # Create trigger for agent to investigate
                mkdir -p "$HOME/.tofu-autofix"
                cat > "$HOME/.tofu-autofix/render-fail-$service_key-$(date +%s).json" << EOF
{
    "type": "render_deploy_failed",
    "service": "$service_name",
    "service_id": "$service_id",
    "deploy_id": "$deploy_id",
    "status": "$status",
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
                ;;
            "building")
                echo "⏳ $service_name: Deploy $deploy_id is building..."
                ;;
        esac
    fi
}

# Check both services
check_service "$BACKEND_SERVICE" "Backend" "backend"
check_service "$FRONTEND_SERVICE" "Frontend" "frontend"
