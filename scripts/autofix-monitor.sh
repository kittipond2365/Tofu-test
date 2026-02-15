#!/bin/bash
# autofix-monitor.sh - Monitor GitHub Actions and create trigger files for auto-fixing

REPO="kittipond2365/Tofu-Test"
TRIGGER_DIR="$HOME/.tofu-autofix"
WORKFLOW_NAME="Test After Deploy"

# Ensure trigger directory exists
mkdir -p "$TRIGGER_DIR"

# Get the most recent workflow run
LATEST_RUN=$(gh run list --repo "$REPO" --workflow "$WORKFLOW_NAME" --limit 1 --json databaseId,status,conclusion,headSha,createdAt --jq '.[0]')

if [ -z "$LATEST_RUN" ] || [ "$LATEST_RUN" = "null" ]; then
    echo "[$(date)] No runs found for workflow: $WORKFLOW_NAME"
    exit 0
fi

RUN_ID=$(echo "$LATEST_RUN" | jq -r '.databaseId')
STATUS=$(echo "$LATEST_RUN" | jq -r '.status')
CONCLUSION=$(echo "$LATEST_RUN" | jq -r '.conclusion')
SHA=$(echo "$LATEST_RUN" | jq -r '.headSha')
CREATED_AT=$(echo "$LATEST_RUN" | jq -r '.createdAt')

# Check if we already processed this run
PROCESSED_FILE="$TRIGGER_DIR/.processed-runs"
touch "$PROCESSED_FILE"

if grep -q "^$RUN_ID$" "$PROCESSED_FILE"; then
    echo "[$(date)] Run $RUN_ID already processed"
    exit 0
fi

# Only process completed runs
if [ "$STATUS" != "completed" ]; then
    echo "[$(date)] Run $RUN_ID not yet completed (status: $STATUS)"
    exit 0
fi

# Mark as processed
echo "$RUN_ID" >> "$PROCESSED_FILE"

# Check if it failed
if [ "$CONCLUSION" != "success" ] && [ "$CONCLUSION" != "skipped" ]; then
    echo "[$(date)] Detected failed run: $RUN_ID (conclusion: $CONCLUSION)"
    
    # Create trigger file with details
    TRIGGER_FILE="$TRIGGER_DIR/failure-${RUN_ID}-$(date +%s).json"
    
    cat > "$TRIGGER_FILE" << EOF
{
  "run_id": "$RUN_ID",
  "repository": "$REPO",
  "workflow": "$WORKFLOW_NAME",
  "conclusion": "$CONCLUSION",
  "commit_sha": "$SHA",
  "created_at": "$CREATED_AT",
  "detected_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
    
    echo "[$(date)] Created trigger file: $TRIGGER_FILE"
    
    # Send notification (if configured)
    if command -v notify-send &> /dev/null; then
        notify-send "Tofu AutoFix" "GitHub Actions failure detected. Run: $RUN_ID"
    fi
else
    echo "[$(date)] Run $RUN_ID succeeded (conclusion: $CONCLUSION)"
fi
