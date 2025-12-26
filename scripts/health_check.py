"""
Health Check Script
Validates system health and readiness
"""

import sys
import os
from pathlib import Path
import urllib.request
import json

# Add backend to path
backend_path = Path(__file__).parent.parent / 'backend'
sys.path.insert(0, str(backend_path))


def check_api_health(url: str = "http://localhost:8000/health") -> tuple:
    """Check if API is responding"""
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode())
            return True, data.get("status", "unknown")
    except Exception as e:
        return False, str(e)


def check_database() -> tuple:
    """Check if database file exists and is accessible"""
    try:
        db_path = Path(__file__).parent.parent / 'database' / 'lanch.db'
        if not db_path.exists():
            return False, "Database file not found"
        
        # Check file size
        size = db_path.stat().st_size
        if size == 0:
            return False, "Database file is empty"
        
        return True, f"OK ({size:,} bytes)"
    except Exception as e:
        return False, str(e)


def check_directories() -> tuple:
    """Check required directories exist"""
    base_path = Path(__file__).parent.parent
    required_dirs = ['logs', 'exports', 'backups']
    missing = []
    
    for dir_name in required_dirs:
        if not (base_path / dir_name).exists():
            missing.append(dir_name)
    
    if missing:
        return False, f"Missing directories: {', '.join(missing)}"
    
    return True, "All directories exist"


def check_disk_space(path: Path, min_mb: int = 100) -> tuple:
    """Check available disk space"""
    try:
        if os.name == 'nt':  # Windows
            import ctypes
            free_bytes = ctypes.c_ulonglong(0)
            ctypes.windll.kernel32.GetDiskFreeSpaceExW(
                str(path), None, None, ctypes.pointer(free_bytes)
            )
            free_mb = free_bytes.value / (1024 * 1024)
        else:  # Unix/Linux
            stat = os.statvfs(path)
            free_mb = (stat.f_bavail * stat.f_frsize) / (1024 * 1024)
        
        if free_mb < min_mb:
            return False, f"Low disk space: {free_mb:.0f} MB (minimum: {min_mb} MB)"
        
        return True, f"OK ({free_mb:.0f} MB available)"
    except Exception as e:
        return False, str(e)


def check_backups() -> tuple:
    """Check if backups exist and are recent"""
    try:
        from services.backup_service import get_backup_service
        from datetime import datetime, timedelta
        
        backup_service = get_backup_service()
        backups = backup_service.list_backups()
        
        if not backups:
            return False, "No backups found"
        
        # Check if most recent backup is less than 7 days old
        latest = backups[0]
        latest_time = datetime.fromisoformat(latest["modified"])
        age_days = (datetime.now() - latest_time).days
        
        if age_days > 7:
            return False, f"Latest backup is {age_days} days old"
        
        return True, f"{len(backups)} backups, latest {age_days} days old"
    except Exception as e:
        return False, str(e)


def main():
    print("\n" + "=" * 60)
    print("🏥 LANCH - System Health Check")
    print("=" * 60 + "\n")
    
    checks = [
        ("API Health", lambda: check_api_health()),
        ("Database", check_database),
        ("Directories", check_directories),
        ("Disk Space", lambda: check_disk_space(Path(__file__).parent.parent)),
        ("Backups", check_backups),
    ]
    
    all_passed = True
    
    for name, check_func in checks:
        try:
            passed, message = check_func()
            status = "✅" if passed else "❌"
            print(f"{status} {name:20s} {message}")
            
            if not passed:
                all_passed = False
        except Exception as e:
            print(f"❌ {name:20s} Error: {str(e)}")
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All checks passed! System is healthy.")
    else:
        print("❌ Some checks failed. Please review above.")
    print("=" * 60 + "\n")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
