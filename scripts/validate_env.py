"""
Stand-alone Environment Validator
Run this script to validate .env configuration without starting the application
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / 'backend'
sys.path.insert(0, str(backend_path))

from utils.env_validator import validate_environment


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🔍 LANCH - Environment Validation")
    print("=" * 60 + "\n")
    
    if validate_environment():
        print("\n✅ Validation successful! The environment is properly configured.\n")
        sys.exit(0)
    else:
        print("\n❌ Validation failed! Please fix the issues above.\n")
        sys.exit(1)
