"""
Manual Backup Script
Creates a database backup immediately
"""

import sys
from pathlib import Path
from datetime import datetime

# Add backend to path
backend_path = Path(__file__).parent.parent / 'backend'
sys.path.insert(0, str(backend_path))


def main():
    from services.backup_service import get_backup_service
    
    print("\n" + "=" * 60)
    print("💾 LANCH - Manual Backup")
    print("=" * 60 + "\n")
    
    try:
        backup_service = get_backup_service()
        
        print("Creating backup...")
        result = backup_service.create_backup(compress=False)
        
        if result["success"]:
            print(f"\n✅ Backup created successfully!")
            print(f"   Filename: {result['filename']}")
            print(f"   Path: {result['path']}")
            print(f"   Size: {result['size_bytes']:,} bytes")
            
            # Rotate old backups
            print("\nRotating old backups...")
            rotation = backup_service.rotate_backups()
            
            if rotation["success"]:
                print(f"   Deleted: {rotation['deleted_count']} old backups")
                print(f"   Kept: {rotation['kept_count']} recent backups")
            
            print()
            return 0
        else:
            print(f"\n❌ Backup failed: {result.get('error', 'Unknown error')}\n")
            return 1
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
