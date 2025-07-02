#!/usr/bin/env python3
"""
Secret Encryption Utility for LeanVibe
Encrypts sensitive configuration for secure deployment
"""

import json
import base64
import getpass
import argparse
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


def generate_key_from_password(password: str, salt: bytes = None) -> tuple[bytes, bytes]:
    """Generate encryption key from password"""
    if salt is None:
        salt = b"leanvibe_salt_2025"  # Use consistent salt for reproducibility
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key, salt


def encrypt_secrets(secrets_dict: dict, password: str) -> str:
    """Encrypt secrets dictionary"""
    key, salt = generate_key_from_password(password)
    fernet = Fernet(key)
    
    json_data = json.dumps(secrets_dict, indent=2)
    encrypted_data = fernet.encrypt(json_data.encode())
    
    return base64.b64encode(encrypted_data).decode()


def decrypt_secrets(encrypted_data: str, password: str) -> dict:
    """Decrypt secrets dictionary"""
    key, salt = generate_key_from_password(password)
    fernet = Fernet(key)
    
    encrypted_bytes = base64.b64decode(encrypted_data.encode())
    decrypted_data = fernet.decrypt(encrypted_bytes)
    
    return json.loads(decrypted_data.decode())


def create_production_secrets():
    """Interactive creation of production secrets"""
    print("🔐 LeanVibe Production Secrets Setup")
    print("=" * 50)
    
    secrets = {}
    
    # Required secrets
    required_secrets = [
        ("LEANVIBE_SECRET_KEY", "Application secret key (generate with openssl rand -hex 32)"),
        ("LEANVIBE_DATABASE_URL", "Production database URL"),
        ("LEANVIBE_REDIS_URL", "Production Redis URL"),
    ]
    
    # Optional secrets
    optional_secrets = [
        ("ANALYTICS_API_KEY", "Analytics service API key"),
        ("LEANVIBE_ENCRYPTION_KEY", "Additional encryption key for sensitive data"),
    ]
    
    print("\n📝 Required Secrets:")
    for key, description in required_secrets:
        while True:
            value = getpass.getpass(f"{key} ({description}): ")
            if value.strip():
                secrets[key] = value.strip()
                break
            print("❌ This secret is required. Please provide a value.")
    
    print("\n📝 Optional Secrets (press Enter to skip):")
    for key, description in optional_secrets:
        value = getpass.getpass(f"{key} ({description}): ")
        if value.strip():
            secrets[key] = value.strip()
    
    return secrets


def create_staging_secrets():
    """Create staging environment secrets"""
    return {
        "LEANVIBE_SECRET_KEY": "staging-secret-key-change-in-production",
        "LEANVIBE_DATABASE_URL": "postgresql://leanvibe:password@localhost:5432/leanvibe_staging",
        "LEANVIBE_REDIS_URL": "redis://localhost:6379/1",
        "LEANVIBE_MLX_STRATEGY": "PRODUCTION",
        "LEANVIBE_ENV": "staging",
    }


def main():
    parser = argparse.ArgumentParser(description="Encrypt LeanVibe secrets")
    parser.add_argument("--environment", choices=["staging", "production"], required=True,
                        help="Environment to create secrets for")
    parser.add_argument("--output", default="secrets.enc",
                        help="Output file for encrypted secrets")
    parser.add_argument("--interactive", action="store_true",
                        help="Interactive mode for secret input")
    parser.add_argument("--decrypt", action="store_true",
                        help="Decrypt and display secrets (for verification)")
    
    args = parser.parse_args()
    
    if args.decrypt:
        # Decrypt mode
        if not Path(args.output).exists():
            print(f"❌ Encrypted file {args.output} not found")
            return
        
        password = getpass.getpass("🔑 Enter encryption password: ")
        try:
            encrypted_data = Path(args.output).read_text()
            secrets = decrypt_secrets(encrypted_data, password)
            
            print(f"\n✅ Successfully decrypted {len(secrets)} secrets:")
            for key in sorted(secrets.keys()):
                # Don't show full values for security
                value = secrets[key]
                if len(value) > 20:
                    display_value = value[:10] + "..." + value[-5:]
                else:
                    display_value = "*" * len(value)
                print(f"  {key}: {display_value}")
                
        except Exception as e:
            print(f"❌ Failed to decrypt secrets: {e}")
        return
    
    # Encrypt mode
    if args.interactive or args.environment == "production":
        secrets = create_production_secrets()
    else:
        secrets = create_staging_secrets()
    
    print(f"\n🔐 Encrypting {len(secrets)} secrets...")
    
    # Get encryption password
    while True:
        password = getpass.getpass("🔑 Enter encryption password: ")
        confirm_password = getpass.getpass("🔑 Confirm encryption password: ")
        
        if password == confirm_password:
            break
        print("❌ Passwords don't match. Please try again.")
    
    try:
        encrypted_data = encrypt_secrets(secrets, password)
        
        # Write encrypted secrets
        output_path = Path(args.output)
        output_path.write_text(encrypted_data)
        
        print(f"✅ Secrets encrypted and saved to {output_path}")
        print(f"📁 File size: {output_path.stat().st_size} bytes")
        
        # Create environment file with encryption key instruction
        env_file = output_path.parent / f".env.{args.environment}"
        env_content = f"""# {args.environment.title()} Environment Configuration
# Generated by encrypt_secrets.py

# Set this environment variable to decrypt secrets
# LEANVIBE_ENCRYPTION_KEY=your_encryption_password_here

# Environment
LEANVIBE_ENV={args.environment}

# Secrets file location
LEANVIBE_SECRETS_FILE={output_path.name}

# Additional configuration
LEANVIBE_ENABLE_LOGGING=true
LEANVIBE_ENABLE_MONITORING=true
"""
        
        env_file.write_text(env_content)
        print(f"📝 Environment template created: {env_file}")
        
        print("\n🚀 Next steps:")
        print(f"1. Set LEANVIBE_ENCRYPTION_KEY environment variable")
        print(f"2. Deploy {output_path} to your {args.environment} environment")
        print(f"3. Update your deployment to use the encrypted secrets")
        
        # Security reminder
        print("\n⚠️  Security reminders:")
        print("- Never commit secrets.enc to version control")
        print("- Store encryption password securely (password manager, CI/CD secrets)")
        print("- Rotate secrets regularly")
        print("- Use different passwords for staging and production")
        
    except Exception as e:
        print(f"❌ Failed to encrypt secrets: {e}")


if __name__ == "__main__":
    main()