#!/bin/bash

echo "=========================================="
echo "Fixing PostgreSQL Authentication"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_info() {
    echo -e "${YELLOW}ℹ${NC} $1"
}

# Option 1: Configure PostgreSQL to trust local connections
echo "Configuring PostgreSQL for local trust authentication..."

# Find pg_hba.conf location
PG_HBA=$(sudo -u postgres psql -t -P format=unaligned -c 'SHOW hba_file;')
print_info "Found pg_hba.conf at: $PG_HBA"

# Backup original
sudo cp $PG_HBA ${PG_HBA}.backup
print_success "Created backup: ${PG_HBA}.backup"

# Modify to trust local connections
sudo sed -i 's/local   all             postgres                                peer/local   all             postgres                                trust/' $PG_HBA
sudo sed -i 's/local   all             all                                     peer/local   all             all                                     trust/' $PG_HBA
sudo sed -i 's/host    all             all             127.0.0.1\/32            scram-sha-256/host    all             all             127.0.0.1\/32            trust/' $PG_HBA
sudo sed -i 's/host    all             all             ::1\/128                 scram-sha-256/host    all             all             ::1\/128                 trust/' $PG_HBA

print_success "Updated pg_hba.conf to trust local connections"

# Restart PostgreSQL to apply changes
echo ""
echo "Restarting PostgreSQL service..."
sudo service postgresql restart

if [ $? -eq 0 ]; then
    print_success "PostgreSQL restarted"
else
    echo "Failed to restart PostgreSQL"
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ Authentication Fixed!"
echo "=========================================="
echo ""
echo "You can now run:"
echo "  ./setup_postgres_codespaces.sh"
echo ""