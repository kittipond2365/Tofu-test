#!/bin/bash
#
# Security Fixes Application Script
# This script applies all security fixes to the Badminton Club App
#

set -e  # Exit on error

echo "========================================"
echo "Badminton App - Security Fixes"
echo "========================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend/app"

# Check if running from correct directory
if [ ! -d "$BACKEND_DIR" ]; then
    echo -e "${RED}Error: Could not find backend/app directory${NC}"
    echo "Please run this script from the project root directory"
    exit 1
fi

echo "Step 1: Creating backups..."
mkdir -p "$BACKEND_DIR/backups"

# Backup function
backup_file() {
    local file="$1"
    if [ -f "$file" ]; then
        cp "$file" "$BACKEND_DIR/backups/$(basename $file).$(date +%Y%m%d_%H%M%S).bak"
        echo -e "${GREEN}✓${NC} Backed up: $(basename $file)"
    fi
}

# Backup original files
backup_file "$BACKEND_DIR/core/config.py"
backup_file "$BACKEND_DIR/core/security.py"
backup_file "$BACKEND_DIR/core/database.py"
backup_file "$BACKEND_DIR/main.py"
backup_file "$BACKEND_DIR/websocket/socket_manager.py"
backup_file "$BACKEND_DIR/api/auth.py"
backup_file "$BACKEND_DIR/services/line_oauth.py"
backup_file "$BACKEND_DIR/models/models.py"

echo ""
echo "Step 2: Applying security fixes..."

# Apply secure versions
copy_secure() {
    local src="$1"
    local dest="$2"
    if [ -f "$src" ]; then
        cp "$src" "$dest"
        echo -e "${GREEN}✓${NC} Applied: $(basename $dest)"
    else
        echo -e "${YELLOW}⚠${NC} Missing: $(basename $src)"
    fi
}

copy_secure "$BACKEND_DIR/core/config_secure.py" "$BACKEND_DIR/core/config.py"
copy_secure "$BACKEND_DIR/core/security_secure.py" "$BACKEND_DIR/core/security.py"
copy_secure "$BACKEND_DIR/core/database_secure.py" "$BACKEND_DIR/core/database.py"
copy_secure "$BACKEND_DIR/main_secure.py" "$BACKEND_DIR/main.py"
copy_secure "$BACKEND_DIR/websocket/socket_manager_secure.py" "$BACKEND_DIR/websocket/socket_manager.py"
copy_secure "$BACKEND_DIR/api/auth_secure.py" "$BACKEND_DIR/api/auth.py"
copy_secure "$BACKEND_DIR/services/line_oauth_secure.py" "$BACKEND_DIR/services/line_oauth.py"
copy_secure "$BACKEND_DIR/models/models_secure.py" "$BACKEND_DIR/models/models.py"

echo ""
echo "Step 3: Verifying fixes..."

# Check if main files exist
if [ -f "$BACKEND_DIR/main.py" ]; then
    if grep -q "security_headers_middleware" "$BACKEND_DIR/main.py"; then
        echo -e "${GREEN}✓${NC} Security middleware applied"
    else
        echo -e "${YELLOW}⚠${NC} Security middleware may not be applied correctly"
    fi
fi

if [ -f "$BACKEND_DIR/core/security.py" ]; then
    if grep -q "JWT_ISSUER" "$BACKEND_DIR/core/security.py"; then
        echo -e "${GREEN}✓${NC} JWT security claims added"
    else
        echo -e "${YELLOW}⚠${NC} JWT security claims may not be applied correctly"
    fi
fi

if [ -f "$BACKEND_DIR/core/config.py" ]; then
    if grep -q "validate_production_settings" "$BACKEND_DIR/core/config.py"; then
        echo -e "${GREEN}✓${NC} Production settings validation added"
    else
        echo -e "${YELLOW}⚠${NC} Production validation may not be applied correctly"
    fi
fi

echo ""
echo "========================================"
echo "Security fixes applied successfully!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Generate a strong SECRET_KEY:"
echo "   python3 -c \"import secrets; print(secrets.token_urlsafe(64))\""
echo ""
echo "2. Update your .env file with:"
echo "   ENVIRONMENT=production"
echo "   DEBUG=false"
echo "   SECRET_KEY=<your-generated-key>"
echo "   CORS_ORIGINS_STR=https://yourdomain.com"
echo ""
echo "3. Run database migrations:"
echo "   cd backend && alembic upgrade head"
echo "   python migrate_indexes.py --all"
echo ""
echo "4. Deploy using your chosen method:"
echo "   - See DEPLOYMENT.md for instructions"
echo ""
echo "========================================"
echo ""

# Optional: Generate secret key
read -p "Generate a secure SECRET_KEY now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "Your SECRET_KEY:"
    echo "----------------------------------------"
    python3 -c "import secrets; print(secrets.token_urlsafe(64))"
    echo "----------------------------------------"
    echo ""
    echo "Copy this value to your .env file as SECRET_KEY"
fi

echo ""
echo -e "${GREEN}Done!${NC}"
