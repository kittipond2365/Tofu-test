#!/bin/bash
# Render Monitor Script
# Check Render service status and logs

RENDER_TOKEN="rnd_M5id7MAhHpqNtHsczEiv33DCkWn8"

echo "🔍 Checking Render Services..."

# List services
curl -s -H "Authorization: Bearer $RENDER_TOKEN" \
  "https://api.render.com/v1/services?limit=20" | \
  jq -r '.[] | "\(.service.name) | Status: \(.service.status) | Type: \(.service.type)"' 2>/dev/null || echo "Unable to fetch services"

echo ""
echo "📋 To see detailed logs, use:"
echo "render logs --service badminton-backend --tail"
echo "render logs --service tofubadminton --tail"
