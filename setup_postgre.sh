#!/bin/bash

echo "=========================================="
echo "SmartFridge PostgreSQL Setup (Codespaces)"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${YELLOW}ℹ${NC} $1"
}

# Step 1: Install PostgreSQL
echo "Step 1: Installing PostgreSQL..."
if command -v psql &> /dev/null; then
    print_info "PostgreSQL already installed"
else
    sudo apt-get update -qq
    sudo apt-get install -y postgresql postgresql-contrib > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        print_success "PostgreSQL installed"
    else
        print_error "Failed to install PostgreSQL"
        exit 1
    fi
fi

# Step 2: Start PostgreSQL service
echo "Step 2: Starting PostgreSQL service..."
sudo service postgresql start > /dev/null 2>&1
if [ $? -eq 0 ]; then
    print_success "PostgreSQL service started"
else
    print_error "Failed to start PostgreSQL"
    exit 1
fi

# Step 3: Create database
echo "Step 3: Creating smartfridge database..."
sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw smartfridge
if [ $? -eq 0 ]; then
    print_info "Database 'smartfridge' already exists"
    read -p "Drop and recreate? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo -u postgres psql -c "DROP DATABASE smartfridge;" > /dev/null 2>&1
        sudo -u postgres psql -c "CREATE DATABASE smartfridge;" > /dev/null 2>&1
        print_success "Database recreated"
    fi
else
    sudo -u postgres psql -c "CREATE DATABASE smartfridge;" > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        print_success "Database 'smartfridge' created"
    else
        print_error "Failed to create database"
        exit 1
    fi
fi

# Step 4: Initialize schema
echo "Step 4: Initializing database schema..."
if [ -f "database/schema.sql" ]; then
    sudo -u postgres psql -d smartfridge -f database/schema.sql > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        print_success "Schema initialized"
    else
        print_error "Failed to initialize schema"
        exit 1
    fi
else
    print_error "schema.sql not found in database/"
    exit 1
fi

# Step 5: Create .env file
echo "Step 5: Creating .env configuration..."
if [ -f ".env" ]; then
    print_info ".env file already exists"
else
    cat > .env << 'EOF'
# SmartFridge Database Configuration (Codespaces)
DB_HOST=localhost
DB_PORT=5432
DB_NAME=smartfridge
DB_USER=postgres
DB_PASSWORD=
EOF
    print_success ".env file created"
fi

# Step 6: Install Python dependencies
echo "Step 6: Installing Python dependencies..."
pip install -q -r requirements.txt
if [ $? -eq 0 ]; then
    print_success "Python dependencies installed"
else
    print_error "Failed to install dependencies"
    exit 1
fi

# Step 7: Run migration
echo "Step 7: Migrating data from recipes.json..."
python3 -m database.migrate
if [ $? -eq 0 ]; then
    print_success "Data migration completed"
else
    print_error "Migration failed"
    exit 1
fi

# Step 8: Verify installation
echo ""
echo "Step 8: Verifying installation..."
RECIPE_COUNT=$(sudo -u postgres psql -d smartfridge -t -c "SELECT COUNT(*) FROM recipe;" | tr -d ' ')
if [ "$RECIPE_COUNT" -eq "10" ]; then
    print_success "Database verified: $RECIPE_COUNT recipes found"
else
    print_error "Verification failed: Expected 10 recipes, found $RECIPE_COUNT"
fi

echo ""
echo "=========================================="
echo "✅ Setup Complete!"
echo "=========================================="
echo ""
echo "To start the application:"
echo "  python3 api_with_db.py"
echo ""
echo "To verify database:"
echo "  sudo -u postgres psql -d smartfridge -c 'SELECT name FROM recipe;'"
echo ""
echo "To view connection info:"
echo "  curl http://localhost:5000/health"
echo ""