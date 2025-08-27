"""
Multi-Factor Authentication (MFA) service for enhanced security
"""

import secrets
import qrcode
import pyotp
import io
import base64
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging

from core.base_service import BaseService


class MFAService(BaseService):
    """
    Service for managing multi-factor authentication
    """
    
    def __init__(self, service_name: str = "MFAService", config: Optional[Dict[str, Any]] = None):
        super().__init__(service_name, config)
        self.issuer_name = config.get("issuer_name", "StorySign ASL Platform") if config else "StorySign ASL Platform"
        self.backup_codes_count = 10
        
    async def initialize(self) -> None:
        """Initialize MFA service"""
        self.logger.info("MFA service initialized")
    
    async def cleanup(self) -> None:
        """Clean up MFA service"""
        pass
    
    def generate_secret_key(self) -> str:
        """
        Generate a new TOTP secret key
        
        Returns:
            Base32-encoded secret key
        """
        return pyotp.random_base32()
    
    def generate_qr_code(self, user_email: str, secret_key: str) -> str:
        """
        Generate QR code for TOTP setup
        
        Args:
            user_email: User's email address
            secret_key: TOTP secret key
            
        Returns:
            Base64-encoded QR code image
        """
        try:
            # Create TOTP URI
            totp_uri = pyotp.totp.TOTP(secret_key).provisioning_uri(
                name=user_email,
                issuer_name=self.issuer_name
            )
            
            # Generate QR code
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(totp_uri)
            qr.make(fit=True)
            
            # Create QR code image
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            
            qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            return qr_code_base64
            
        except Exception as e:
            self.logger.error(f"QR code generation error: {e}")
            raise ValueError("Failed to generate QR code")
    
    def verify_totp_code(self, secret_key: str, code: str, window: int = 1) -> bool:
        """
        Verify TOTP code
        
        Args:
            secret_key: TOTP secret key
            code: 6-digit TOTP code
            window: Time window for verification (default: 1 = 30 seconds before/after)
            
        Returns:
            True if code is valid, False otherwise
        """
        try:
            totp = pyotp.TOTP(secret_key)
            return totp.verify(code, valid_window=window)
        except Exception as e:
            self.logger.error(f"TOTP verification error: {e}")
            return False
    
    def generate_backup_codes(self) -> list:
        """
        Generate backup codes for MFA recovery
        
        Returns:
            List of backup codes
        """
        backup_codes = []
        for _ in range(self.backup_codes_count):
            # Generate 8-character alphanumeric code
            code = secrets.token_hex(4).upper()
            backup_codes.append(code)
        
        return backup_codes
    
    def hash_backup_codes(self, backup_codes: list) -> list:
        """
        Hash backup codes for secure storage
        
        Args:
            backup_codes: List of plain backup codes
            
        Returns:
            List of hashed backup codes
        """
        import hashlib
        
        hashed_codes = []
        for code in backup_codes:
            # Use SHA-256 with salt
            salt = secrets.token_hex(16)
            hashed = hashlib.sha256((code + salt).encode()).hexdigest()
            hashed_codes.append(f"{salt}:{hashed}")
        
        return hashed_codes
    
    def verify_backup_code(self, hashed_codes: list, code: str) -> Tuple[bool, Optional[str]]:
        """
        Verify backup code and return the used code hash for removal
        
        Args:
            hashed_codes: List of hashed backup codes
            code: Backup code to verify
            
        Returns:
            Tuple of (is_valid, used_code_hash)
        """
        import hashlib
        
        for hashed_code in hashed_codes:
            try:
                salt, stored_hash = hashed_code.split(":", 1)
                computed_hash = hashlib.sha256((code + salt).encode()).hexdigest()
                
                if computed_hash == stored_hash:
                    return True, hashed_code
                    
            except ValueError:
                continue
        
        return False, None
    
    def generate_sms_code(self) -> str:
        """
        Generate SMS verification code
        
        Returns:
            6-digit SMS code
        """
        return f"{secrets.randbelow(1000000):06d}"
    
    def generate_email_code(self) -> str:
        """
        Generate email verification code
        
        Returns:
            6-digit email code
        """
        return f"{secrets.randbelow(1000000):06d}"
    
    async def send_sms_code(self, phone_number: str, code: str) -> bool:
        """
        Send SMS verification code (placeholder implementation)
        
        Args:
            phone_number: Phone number to send code to
            code: Verification code
            
        Returns:
            True if sent successfully, False otherwise
        """
        # TODO: Implement actual SMS sending (Twilio, AWS SNS, etc.)
        self.logger.info(f"SMS code sent to {phone_number}: {code}")
        return True
    
    async def send_email_code(self, email: str, code: str) -> bool:
        """
        Send email verification code (placeholder implementation)
        
        Args:
            email: Email address to send code to
            code: Verification code
            
        Returns:
            True if sent successfully, False otherwise
        """
        # TODO: Implement actual email sending
        self.logger.info(f"Email code sent to {email}: {code}")
        return True
    
    def is_code_expired(self, created_at: datetime, expiry_minutes: int = 5) -> bool:
        """
        Check if verification code is expired
        
        Args:
            created_at: When the code was created
            expiry_minutes: Expiry time in minutes
            
        Returns:
            True if expired, False otherwise
        """
        expiry_time = created_at + timedelta(minutes=expiry_minutes)
        return datetime.utcnow() > expiry_time
    
    def validate_phone_number(self, phone_number: str) -> bool:
        """
        Validate phone number format
        
        Args:
            phone_number: Phone number to validate
            
        Returns:
            True if valid, False otherwise
        """
        import re
        
        # Basic international phone number validation
        pattern = r'^\+?[1-9]\d{1,14}$'
        return bool(re.match(pattern, phone_number.replace(" ", "").replace("-", "")))
    
    def get_mfa_methods(self) -> Dict[str, Dict[str, Any]]:
        """
        Get available MFA methods
        
        Returns:
            Dictionary of MFA methods and their properties
        """
        return {
            "totp": {
                "name": "Authenticator App",
                "description": "Use an authenticator app like Google Authenticator or Authy",
                "setup_required": True,
                "backup_codes": True
            },
            "sms": {
                "name": "SMS",
                "description": "Receive codes via text message",
                "setup_required": True,
                "backup_codes": False
            },
            "email": {
                "name": "Email",
                "description": "Receive codes via email",
                "setup_required": False,
                "backup_codes": False
            }
        }