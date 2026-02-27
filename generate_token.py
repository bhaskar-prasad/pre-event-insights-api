import jwt
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Generate token for sample admin user
payload = {
    "username": "user_cognito_001",  # Sample user from DB
    "tenant_id": "tenant_001",        # Sample tenant from DB
    "exp": datetime.utcnow() + timedelta(hours=1)
}

# Get secret from environment (fallback to placeholder if not set)
secret = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")

token = jwt.encode(payload, secret, algorithm="HS256")
print("Generated Token:")
print(token)