#!/bin/bash
# autofix-processor.sh - Process trigger files and fix failures

TRIGGER_DIR="$HOME/.tofu-autofix"
REPO_DIR="$HOME/.openclaw/workspace/test-public-repo"
REPO="kittipond2365/Tofu-Test"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================"
echo "Tofu AutoFix Processor"
echo "Time: $(date)"
echo "========================================"

# Check for trigger files
TRIGGER_FILES=$(find "$TRIGGER_DIR" -name "failure-*.json" -type f 2>/dev/null)

if [ -z "$TRIGGER_FILES" ]; then
    printf "${GREEN}No trigger files found. Nothing to fix.${NC}\n"
    exit 0
fi

printf "${YELLOW}Found trigger files to process:${NC}\n"
echo "$TRIGGER_FILES"
echo ""

# Process each trigger file
for trigger_file in $TRIGGER_FILES; do
    printf "${YELLOW}Processing: $(basename $trigger_file)${NC}\n"
    
    # Parse trigger file
    RUN_ID=$(jq -r '.run_id' "$trigger_file")
    CONCLUSION=$(jq -r '.conclusion' "$trigger_file")
    COMMIT_SHA=$(jq -r '.commit_sha' "$trigger_file")
    
    echo "  Run ID: $RUN_ID"
    echo "  Conclusion: $CONCLUSION"
    echo "  Commit: $COMMIT_SHA"
    echo ""
    
    # Fetch run logs
    echo "  Fetching run logs..."
    LOG_FILE="$TRIGGER_DIR/logs-$RUN_ID.txt"
    gh run view "$RUN_ID" --repo "$REPO" --log > "$LOG_FILE" 2>&1 || echo "Could not fetch logs"
    
    # Fetch failed jobs details
    echo "  Analyzing failed jobs..."
    JOBS_JSON=$(gh run view "$RUN_ID" --repo "$REPO" --json jobs 2>/dev/null || echo '{"jobs":[]}')
    
    # Save analysis
    ANALYSIS_FILE="$TRIGGER_DIR/analysis-$RUN_ID.json"
    echo "$JOBS_JSON" > "$ANALYSIS_FILE"
    
    echo "  Logs saved to: $LOG_FILE"
    echo "  Analysis saved to: $ANALYSIS_FILE"
    echo ""
    
    # Create a marker file for the agent to process
    # The agent will look for .pending files
    PENDING_FILE="$TRIGGER_DIR/pending-$RUN_ID.json"
    cp "$trigger_file" "$PENDING_FILE"
    echo "  Created pending marker: $PENDING_FILE"
    echo ""
    
    # Keep the original trigger file for reference (processed files can be archived)
    ARCHIVE_DIR="$TRIGGER_DIR/processed"
    mkdir -p "$ARCHIVE_DIR"
    mv "$trigger_file" "$ARCHIVE_DIR/$(basename $trigger_file)"
    printf "${GREEN}  Moved trigger file to archive${NC}\n"
    echo ""
done

echo "========================================"
echo "Trigger processing complete."
echo "Pending fixes: $(ls -1 $TRIGGER_DIR/pending-*.json 2>/dev/null | wc -l)"
echo "========================================"
