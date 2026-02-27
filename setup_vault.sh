#!/bin/bash

# Vault Setup Script

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Vault Setup ===${NC}\n"

# Get token from user
echo -e "${BLUE}Enter your Vault token (from 'vault server -dev' output):${NC}"
read -p "Vault Token: " VAULT_TOKEN

if [ -z "$VAULT_TOKEN" ]; then
    echo -e "${RED}Error: Vault token is required${NC}"
    exit 1
fi

# Get database credentials from user
echo -e "${BLUE}Enter your database credentials:${NC}"
read -p "Database Username (default: postgres): " DB_USER
DB_USER=${DB_USER:-postgres}
read -sp "Database Password: " DB_PASSWORD
echo
read -p "Database Host (default: localhost): " DB_HOST
DB_HOST=${DB_HOST:-localhost}
read -p "Database Port (default: 5432): " DB_PORT
DB_PORT=${DB_PORT:-5432}
read -p "Database Name (default: postgres): " DB_NAME
DB_NAME=${DB_NAME:-postgres}

if [ -z "$DB_PASSWORD" ]; then
    echo -e "${RED}Error: Database password is required${NC}"
    exit 1
fi

# Export for curl commands
export VAULT_TOKEN
export VAULT_ADDR="http://localhost:8200"

echo -e "\n${BLUE}Testing Vault connection...${NC}"
if ! curl -s -H "X-Vault-Token: $VAULT_TOKEN" "$VAULT_ADDR/v1/sys/health" > /dev/null; then
    echo -e "${RED}Error: Cannot connect to Vault${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Vault is accessible${NC}\n"

# Create the secret
echo -e "${BLUE}Creating secret 'fastapi/database' in Vault...${NC}"

curl -s -X POST \
  -H "X-Vault-Token: $VAULT_TOKEN" \
  -d '{
    "data": {
      "username": "'$DB_USER'",
      "password": "'$DB_PASSWORD'",
      "host": "'$DB_HOST'",
      "port": "'$DB_PORT'",
      "database": "'$DB_NAME'"
    }
  }' \
  "$VAULT_ADDR/v1/secret/data/fastapi/database" > /dev/null

echo -e "${GREEN}✓ Secret created successfully${NC}\n"

# Verify the secret
echo -e "${BLUE}Verifying secret...${NC}"
curl -s -H "X-Vault-Token: $VAULT_TOKEN" \
  "$VAULT_ADDR/v1/secret/data/fastapi/database"

echo -e "\n${GREEN}✓ Setup complete!${NC}"
echo -e "${GREEN}Your .env is already configured.${NC}"
echo -e "${GREEN}You can now run the app!${NC}\n"
