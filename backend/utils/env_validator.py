
"""
LANCH - Environment Validator
Validates .env configuration before application startup
"""

import os
import sys
from pathlib import Path


class EnvValidator:
    """Validates environment configuration"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
    
    def validate_secret_key(self, secret_key: str) -> bool:
        """Validate SECRET_KEY is properly configured"""
        if not secret_key:
            self.errors.append("SECRET_KEY is not set")
            return False
        
        if len(secret_key) < 32:
            self.errors.append(f"SECRET_KEY is too short ({len(secret_key)} chars, minimum 32)")
            return False
        
        # Check for example values
        dangerous_patterns = [
            'your-secret-key-here',
            'change-this',
            'example',
            'test',
            'secret'
        ]
        
        for pattern in dangerous_patterns:
            if pattern.lower() in secret_key.lower():
                self.errors.append(
                    f"SECRET_KEY appears to contain example value '{pattern}'. "
                    "Generate a new one with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
                )
                return False
        
        return True
    
    def validate_debug_mode(self, debug: str, is_production: bool = False) -> bool:
        """Validate DEBUG setting"""
        if is_production and debug and debug.lower() in ('true', '1', 'yes'):
            self.errors.append("DEBUG=True in production environment is a CRITICAL security risk!")
            return False
        
        if debug and debug.lower() in ('true', '1', 'yes'):
            self.warnings.append("Running in DEBUG mode - this should only be used in development")
        
        return True
    
    def validate_allowed_origins(self, allowed_origins: str, is_production: bool = False) -> bool:
        """Validate CORS origins"""
        if not allowed_origins:
            self.warnings.append("ALLOWED_ORIGINS not set, using defaults")
            return True
        
        origins = [o.strip() for o in allowed_origins.split(',')]
        
        if is_production:
            if 'localhost' in allowed_origins.lower():
                self.warnings.append("CORS allows localhost origins in production")
            
            if '*' in allowed_origins:
                self.errors.append("CORS allows all origins (*) in production - this is a security risk!")
                return False
        
        return True
    
    def validate_database_url(self, database_url: str) -> bool:
        """Validate database connection"""
        if not database_url:
            self.errors.append("DATABASE_URL is not set")
            return False
        
        # Check if database file exists for SQLite
        if database_url.startswith('sqlite:///'):
            db_path = database_url.replace('sqlite:///', '')
            
            # Handle relative paths
            if not os.path.isabs(db_path):
                db_path = os.path.join(os.path.dirname(__file__), '..', db_path)
            
            db_dir = os.path.dirname(db_path)
            if not os.path.exists(db_dir):
                self.warnings.append(f"Database directory does not exist: {db_dir}")
        
        return True
    
    def validate_directories(self) -> bool:
        """Validate required directories exist"""
        base_path = Path(__file__).parent.parent.parent
        required_dirs = ['logs', 'exports', 'backups']
        
        for dir_name in required_dirs:
            dir_path = base_path / dir_name
            if not dir_path.exists():
                self.warnings.append(f"Directory '{dir_name}' does not exist and will be created")
        
        return True
    
    def validate_all(self) -> bool:
        """Run all validations"""
        from dotenv import load_dotenv
        
        # Load .env file
        env_file = Path(__file__).parent.parent.parent / '.env'
        if not env_file.exists():
            self.errors.append(
                f".env file not found at {env_file}. "
                "Copy .env.example to .env and configure it."
            )
            return False
        
        load_dotenv(env_file)
        
        # Get environment variables
        secret_key = os.getenv('SECRET_KEY', '')
        debug = os.getenv('DEBUG', 'False')
        allowed_origins = os.getenv('ALLOWED_ORIGINS', '')
        database_url = os.getenv('DATABASE_URL', '')
        
        # Determine if production
        is_production = debug.lower() not in ('true', '1', 'yes')
        
        # Run validations
        all_valid = True
        all_valid &= self.validate_secret_key(secret_key)
        all_valid &= self.validate_debug_mode(debug, is_production)
        all_valid &= self.validate_allowed_origins(allowed_origins, is_production)
        all_valid &= self.validate_database_url(database_url)
        all_valid &= self.validate_directories()
        
        return all_valid
    
    def print_results(self):
        """Print validation results"""
        if self.errors:
            print("\n" + "=" * 60)
            print("❌ ERRORS DE CONFIGURAÇÃO:")
            print("=" * 60)
            for error in self.errors:
                print(f"  • {error}")
            print()
        
        if self.warnings:
            print("\n" + "=" * 60)
            print("⚠️  AVISOS:")
            print("=" * 60)
            for warning in self.warnings:
                print(f"  • {warning}")
            print()
        
        if not self.errors and not self.warnings:
            print("\n✅ Configuração validada com sucesso!")


def validate_environment() -> bool:
    """Main validation function"""
    validator = EnvValidator()
    is_valid = validator.validate_all()
    validator.print_results()
    
    if not is_valid:
        print("\n💡 Dica: Revise o arquivo .env e corrija os erros acima.")
        print("   Consulte .env.example para referência.\n")
    
    return is_valid


if __name__ == "__main__":
    if not validate_environment():
        sys.exit(1)
