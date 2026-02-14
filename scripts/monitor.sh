#!/bin/bash
# GitHub Actions Monitor - Auto-check for test failures
# Usage: ./monitor.sh

REPO="kittipond2365/Tofu-Test"
TOKEN_FILE="$HOME/.github/tofu-token"

# อ่าน token จากไฟล์ (สร้างไฟล์นี้เอง อย่า commit)
if [ -f "$TOKEN_FILE" ]; then
    GITHUB_TOKEN=$(cat "$TOKEN_FILE")
else
    echo "❌ ไม่พบ token file: $TOKEN_FILE"
    echo "สร้างไฟล์นี้แล้วใส่ GitHub token ลงไป"
    exit 1
fi

# ดึง run ล่าสุด
echo "🔍 เช็คสถานะ GitHub Actions..."

LATEST_RUN=$(curl -s -H "Authorization: token $GITHUB_TOKEN" \
    "https://api.github.com/repos/$REPO/actions/runs?per_page=1")

RUN_ID=$(echo "$LATEST_RUN" | jq -r '.workflow_runs[0].id')
RUN_NAME=$(echo "$LATEST_RUN" | jq -r '.workflow_runs[0].name')
STATUS=$(echo "$LATEST_RUN" | jq -r '.workflow_runs[0].status')
CONCLUSION=$(echo "$LATEST_RUN" | jq -r '.workflow_runs[0].conclusion')
HTML_URL=$(echo "$LATEST_RUN" | jq -r '.workflow_runs[0].html_url')

echo "📋 $RUN_NAME"
echo "   Status: $STATUS"
echo "   Result: $CONCLUSION"
echo "   URL: $HTML_URL"

# ถ้า fail ดึง logs
if [ "$CONCLUSION" = "failure" ]; then
    echo ""
    echo "❌ Test Failed! กำลังดึง logs..."
    
    curl -s -H "Authorization: token $GITHUB_TOKEN" \
        "https://api.github.com/repos/$REPO/actions/runs/$RUN_ID/logs" \
        -L -o /tmp/tofu-test-logs.zip
    
    echo "📁 Logs บันทึกที่: /tmp/tofu-test-logs.zip"
    echo "   แกะไฟล์: unzip /tmp/tofu-test-logs.zip -d /tmp/tofu-logs/"
    
    # แสดง error คร่าวๆ
    unzip -q /tmp/tofu-test-logs.zip -d /tmp/tofu-logs/
    echo ""
    echo "🔴 Errors พบ:"
    grep -r "Error\|FAIL\|failed" /tmp/tofu-logs/ 2>/dev/null | head -20
fi

echo ""
echo "✅ เช็คเสร็จแล้ว $(date)"
