# Vault Setup Guide

This guide walks you through setting up Hashicorp Vault for storing database credentials.

## Prerequisites

- Vault CLI installed: https://www.vaultproject.io/downloads
- Vault server running (dev mode for local testing)

## Quick Start

### 1. Start Vault in Dev Mode

Open a terminal and run:

```bash
vault server -dev
```

This will output something like:

```
WARNING! dev mode is enabled! In this mode, Vault runs entirely in-memory
and every restart will lose all your data. Never use dev mode for
production.

You may need to set the following environment variable:

    $ export VAULT_ADDR='http://127.0.0.1:8200'

The unseal key and root token are displayed below in case you want to
seal/unseal the Vault or re-authenticate.

Unseal Key: xxxxxxxxx
Root Token: s.xxxxxxxxxx

...
```

**Save the Root Token** - you'll need it in step 3.

### 2. Open Another Terminal

In a new terminal window, set the Vault token:

```bash
export VAULT_ADDR='http://127.0.0.1:8200'
export VAULT_TOKEN='s.xxxxxxxxxx'  # Replace with your root token from step 1
```

### 3. Store Your Database Credentials in Vault

```bash
vault kv put fastapi/database \
  username=postgres \
  password=postgres \
  host=localhost \
  port=5432 \
  database=fastapi_db
```

You should see:

```
Success! Data written to: secret/data/fastapi/database
```

### 4. Verify the Secret Was Stored

```bash
vault kv get fastapi/database
```

Expected output:

```
====== Secret Path ======
secret/data/fastapi/database

====== Data ======
Key         Value
---         -----
database    fastapi_db
host        localhost
password    postgres
port        5432
username    postgres
```

### 5. Update Your `.env` File

Edit `.env` in your project:

```env
# Database
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=fastapi_db

# Vault Configuration - ENABLE IT
VAULT_ENABLED=true
VAULT_ADDR=http://127.0.0.1:8200
VAULT_TOKEN=s.xxxxxxxxxx  # Your root token from step 1
VAULT_SECRET_PATH=fastapi/database
```

**Important**:
- `VAULT_ENABLED=true` - This enables Vault credential fetching
- `VAULT_SECRET_PATH=fastapi/database` - This is just `fastapi/database`, NOT `secret/data/fastapi/database`
- The code automatically handles the KV v2 path conversion

### 6. Test the Connection

Start your FastAPI app:

```bash
python -m uvicorn app.main:app --reload
```

If Vault is configured correctly, you should see in the logs:

```
INFO:app.database:Database credentials fetched from Vault
INFO:app.database:Database engine initialized
```

If there's an error, check:
- Vault server is running
- VAULT_TOKEN is correct
- VAULT_ADDR is correct
- Secret path exists in Vault

---

## How It Works

The application:

1. Checks if `VAULT_ENABLED=true`
2. If yes, connects to Vault using `VAULT_ADDR` and `VAULT_TOKEN`
3. Fetches secrets from the path `fastapi/database` (stored as `secret/data/fastapi/database` in KV v2)
4. Extracts `username`, `password`, `host`, `port`, `database` from the secret
5. Builds a PostgreSQL connection URL
6. Uses that to connect to the database

If Vault is disabled or fails, it falls back to environment variables:

```env
VAULT_ENABLED=false
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=fastapi_db
```

---

## Path Explanation

**In Vault CLI**, you create secrets at:
```
fastapi/database
```

**But it's stored as**:
```
secret/data/fastapi/database
```

(The `secret/` mount and `/data/` are KV v2 conventions)

**In your `.env`**, use:
```
VAULT_SECRET_PATH=fastapi/database
```

The Python hvac client handles the mount and version automatically!

---

## Production Setup

For production with a real Vault server:

1. Set up Vault with proper authentication (JWT, OIDC, etc.)
2. Store credentials in your organization's secret mount
3. Use:

```env
VAULT_ENABLED=true
VAULT_ADDR=https://vault.company.com
VAULT_TOKEN=<token_from_auth_system>
VAULT_SECRET_PATH=production/database
```

4. Implement token refresh (Vault tokens expire)
5. Use Vault's dynamic secrets for database passwords (if supported)

---

## Troubleshooting

### Error: `could not find version data`

**Cause**: Path includes `secret/data/` prefix

**Solution**: Remove prefix from `VAULT_SECRET_PATH`
- ❌ Wrong: `secret/data/fastapi/database`
- ✅ Correct: `fastapi/database`

### Error: `permission denied`

**Cause**: Token doesn't have read permission

**Solution**: Use a token with proper ACL policies, or use root token for testing

### Error: `connection refused`

**Cause**: Vault server not running or wrong address

**Solution**:
- Check Vault is running: `vault status`
- Check `VAULT_ADDR` matches Vault server address
- Default dev mode: `http://127.0.0.1:8200`

### Error: `invalid token`

**Cause**: Invalid or expired token

**Solution**:
- In dev mode: Get root token from `vault server -dev` output
- Token format should be: `s.xxxxxxxxxx` or `hvs.xxxxxxxxxx`

---

## Security Best Practices

1. **Never commit tokens** - Use `.env` in `.gitignore`
2. **Rotate tokens regularly** - Vault tokens have TTLs
3. **Use dynamic secrets** - Let Vault generate temporary DB passwords
4. **Audit access** - Enable Vault audit logging
5. **Principle of least privilege** - Limit token permissions with ACL policies

---

## Next Steps

- Read: [Hashicorp Vault Documentation](https://www.vaultproject.io/docs)
- Set up dynamic database secrets for auto-rotating passwords
- Implement proper authentication (don't use root token in production)
- Add Vault agent for automatic token renewal
