"""
LANCH - Backup Service
Automated database backup with rotation and compression
"""

import os
import shutil
import gzip
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)


class BackupService:
    """Service for managing database backups"""
    
    def __init__(self, db_path: str, backup_dir: str, retention_days: int = 30):
        """
        Initialize backup service
        
        Args:
            db_path: Path to database file
            backup_dir: Directory to store backups
            retention_days: Number of days to keep backups (default: 30)
        """
        self.db_path = Path(db_path)
        self.backup_dir = Path(backup_dir)
        self.retention_days = retention_days
        
        # Ensure backup directory exists
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def create_backup(self, compress: bool = False) -> dict:
        """
        Create a database backup
        
        Args:
            compress: Whether to compress the backup with gzip
            
        Returns:
            dict with backup information
        """
        try:
            # Validate source database exists
            if not self.db_path.exists():
                raise FileNotFoundError(f"Database file not found: {self.db_path}")
            
            # Generate backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"lanch_backup_{timestamp}.db"
            backup_path = self.backup_dir / backup_filename
            
            # Copy database file
            logger.info(f"Creating backup: {backup_filename}")
            shutil.copy2(self.db_path, backup_path)
            
            # Compress if requested
            if compress:
                logger.info("Compressing backup...")
                compressed_path = self._compress_backup(backup_path)
                os.remove(backup_path)
                backup_path = compressed_path
                backup_filename = compressed_path.name
            
            # Verify backup
            if not backup_path.exists():
                raise RuntimeError("Backup file was not created successfully")
            
            backup_size = backup_path.stat().st_size
            
            logger.info(f"Backup created successfully: {backup_filename} ({backup_size} bytes)")
            
            return {
                "success": True,
                "filename": backup_filename,
                "path": str(backup_path),
                "size_bytes": backup_size,
                "compressed": compress,
                "timestamp": timestamp
            }
            
        except Exception as e:
            logger.error(f"Backup failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _compress_backup(self, backup_path: Path) -> Path:
        """Compress a backup file with gzip"""
        compressed_path = backup_path.with_suffix('.db.gz')
        
        with open(backup_path, 'rb') as f_in:
            with gzip.open(compressed_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        return compressed_path
    
    def rotate_backups(self) -> dict:
        """
        Remove old backups based on retention policy
        
        Returns:
            dict with rotation information
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            deleted_files = []
            kept_files = []
            
            # List all backup files
            backup_files = list(self.backup_dir.glob("lanch_backup_*.db*"))
            
            for backup_file in backup_files:
                # Extract timestamp from filename
                try:
                    # Format: lanch_backup_YYYYMMDD_HHMMSS.db[.gz]
                    parts = backup_file.stem.split('_')
                    if len(parts) >= 3:
                        date_str = parts[2]  # YYYYMMDD
                        time_str = parts[3] if len(parts) > 3 else "000000"  # HHMMSS
                        
                        backup_datetime = datetime.strptime(
                            f"{date_str}_{time_str}", 
                            "%Y%m%d_%H%M%S"
                        )
                        
                        if backup_datetime < cutoff_date:
                            logger.info(f"Deleting old backup: {backup_file.name}")
                            backup_file.unlink()
                            deleted_files.append(backup_file.name)
                        else:
                            kept_files.append(backup_file.name)
                except (ValueError, IndexError) as e:
                    logger.warning(f"Could not parse backup filename: {backup_file.name}")
                    continue
            
            logger.info(f"Backup rotation complete: {len(deleted_files)} deleted, {len(kept_files)} kept")
            
            return {
                "success": True,
                "deleted_count": len(deleted_files),
                "kept_count": len(kept_files),
                "deleted_files": deleted_files
            }
            
        except Exception as e:
            logger.error(f"Backup rotation failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def list_backups(self) -> List[dict]:
        """List all available backups"""
        backups = []
        backup_files = sorted(
            self.backup_dir.glob("lanch_backup_*.db*"),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )
        
        for backup_file in backup_files:
            stat = backup_file.stat()
            backups.append({
                "filename": backup_file.name,
                "path": str(backup_file),
                "size_bytes": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "compressed": backup_file.suffix == '.gz'
            })
        
        return backups
    
    def restore_backup(self, backup_filename: str) -> dict:
        """
        Restore database from backup
        
        Args:
            backup_filename: Name of the backup file to restore
            
        Returns:
            dict with restoration information
        """
        try:
            backup_path = self.backup_dir / backup_filename
            
            if not backup_path.exists():
                raise FileNotFoundError(f"Backup file not found: {backup_filename}")
            
            # Create a backup of current database before restoring
            logger.info("Creating safety backup of current database...")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safety_backup = self.db_path.with_suffix(f'.db.before_restore_{timestamp}')
            shutil.copy2(self.db_path, safety_backup)
            
            # Decompress if needed
            if backup_path.suffix == '.gz':
                logger.info("Decompressing backup...")
                temp_path = backup_path.with_suffix('')
                with gzip.open(backup_path, 'rb') as f_in:
                    with open(temp_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                restore_source = temp_path
            else:
                restore_source = backup_path
            
            # Restore database
            logger.info(f"Restoring database from {backup_filename}...")
            shutil.copy2(restore_source, self.db_path)
            
            # Clean up decompressed temp file
            if restore_source != backup_path:
                restore_source.unlink()
            
            logger.info("Database restored successfully")
            
            return {
                "success": True,
                "backup_filename": backup_filename,
                "safety_backup": str(safety_backup)
            }
            
        except Exception as e:
            logger.error(f"Restore failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }


def get_backup_service() -> BackupService:
    """Get BackupService instance with default configuration"""
    from config import settings
    
    # Parse database path from DATABASE_URL
    # Assumes format: sqlite:///../database/lanch.db
    db_url = settings.DATABASE_URL
    if db_url.startswith('sqlite:///'):
        db_path = db_url.replace('sqlite:///', '')
        # Handle relative paths
        if not os.path.isabs(db_path):
            base_path = Path(__file__).parent.parent
            db_path = str(base_path / db_path)
    else:
        raise ValueError("Only SQLite databases are supported for backup")
    
    backup_dir = str(Path(__file__).parent.parent.parent / 'backups')
    
    return BackupService(db_path, backup_dir, retention_days=30)
