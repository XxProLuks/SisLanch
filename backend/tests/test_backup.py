"""
LANCH - Backup Service Tests
Tests for backup service functionality
"""

import pytest
import os
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from services.backup_service import BackupService


@pytest.fixture
def temp_db_path():
    """Create a temporary database file for testing"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.db', delete=False) as f:
        f.write("test database content")
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.remove(temp_path)


@pytest.fixture
def temp_backup_dir():
    """Create a temporary backup directory"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    
    # Cleanup
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


@pytest.fixture
def backup_service(temp_db_path, temp_backup_dir):
    """Create a BackupService instance with temporary paths"""
    return BackupService(temp_db_path, temp_backup_dir, retention_days=7)


class TestBackupCreation:
    """Tests for backup creation"""
    
    def test_create_backup_success(self, backup_service):
        """Test successful backup creation"""
        result = backup_service.create_backup(compress=False)
        
        assert result["success"] is True
        assert "filename" in result
        assert "path" in result
        assert "size_bytes" in result
        assert result["compressed"] is False
        
        # Verify file exists
        assert os.path.exists(result["path"])
    
    def test_create_backup_compressed(self, backup_service):
        """Test compressed backup creation"""
        result = backup_service.create_backup(compress=True)
        
        assert result["success"] is True
        assert result["compressed"] is True
        assert result["filename"].endswith('.db.gz')
        
        # Verify compressed file exists
        assert os.path.exists(result["path"])
    
    def test_create_backup_nonexistent_db(self, temp_backup_dir):
        """Test backup fails gracefully with non-existent database"""
        service = BackupService("/nonexistent/database.db", temp_backup_dir)
        result = service.create_backup()
        
        assert result["success"] is False
        assert "error" in result
    
    def test_backup_filename_format(self, backup_service):
        """Test backup filename has correct format"""
        result = backup_service.create_backup()
        
        assert result["success"] is True
        filename = result["filename"]
        
        # Should match: lanch_backup_YYYYMMDD_HHMMSS.db
        assert filename.startswith("lanch_backup_")
        assert filename.endswith(".db")
        
        # Extract timestamp
        parts = filename.replace("lanch_backup_", "").replace(".db", "").split("_")
        assert len(parts) == 2
        
        # Validate date format
        date_str = parts[0]
        time_str = parts[1]
        assert len(date_str) == 8  # YYYYMMDD
        assert len(time_str) == 6  # HHMMSS


class TestBackupRotation:
    """Tests for backup rotation"""
    
    def test_rotate_backups_keeps_recent(self, backup_service):
        """Test rotation keeps recent backups"""
        # Create several backups
        for _ in range(3):
            backup_service.create_backup()
        
        # Rotate (all should be kept as they're recent)
        result = backup_service.rotate_backups()
        
        assert result["success"] is True
        assert result["kept_count"] == 3
        assert result["deleted_count"] == 0
    
    def test_rotate_backups_deletes_old(self, backup_service, temp_backup_dir):
        """Test rotation deletes old backups"""
        # Create old backup by creating file with old timestamp
        old_date = (datetime.now() - timedelta(days=10)).strftime("%Y%m%d_%H%M%S")
        old_backup = Path(temp_backup_dir) / f"lanch_backup_{old_date}.db"
        old_backup.write_text("old backup")
        
        # Create recent backup
        backup_service.create_backup()
        
        # Rotate
        result = backup_service.rotate_backups()
        
        assert result["success"] is True
        assert result["deleted_count"] == 1
        assert result["kept_count"] == 1
        
        # Verify old backup was deleted
        assert not old_backup.exists()
    
    def test_rotate_backups_respects_retention_days(self, temp_db_path, temp_backup_dir):
        """Test rotation respects custom retention period"""
        # Create service with 3-day retention
        service = BackupService(temp_db_path, temp_backup_dir, retention_days=3)
        
        # Create backup 5 days old
        old_date = (datetime.now() - timedelta(days=5)).strftime("%Y%m%d_%H%M%S")
        old_backup = Path(temp_backup_dir) / f"lanch_backup_{old_date}.db"
        old_backup.write_text("old backup")
        
        # Rotate
        result = service.rotate_backups()
        
        assert result["deleted_count"] == 1


class TestBackupListing:
    """Tests for backup listing"""
    
    def test_list_backups_empty(self, backup_service):
        """Test listing with no backups"""
        backups = backup_service.list_backups()
        assert len(backups) == 0
    
    def test_list_backups(self, backup_service):
        """Test listing backups"""
        # Create backups
        backup_service.create_backup()
        backup_service.create_backup(compress=True)
        
        backups = backup_service.list_backups()
        
        assert len(backups) == 2
        
        # Verify structure
        for backup in backups:
            assert "filename" in backup
            assert "path" in backup
            assert "size_bytes" in backup
            assert "modified" in backup
            assert "compressed" in backup
    
    def test_list_backups_sorted_by_date(self, backup_service):
        """Test backups are sorted by date (newest first)"""
        # Create multiple backups
        for _ in range(3):
            backup_service.create_backup()
        
        backups = backup_service.list_backups()
        
        # Verify sorted (newest first)
        for i in range(len(backups) - 1):
            assert backups[i]["modified"] >= backups[i + 1]["modified"]


class TestBackupRestore:
    """Tests for backup restoration"""
    
    def test_restore_backup_success(self, backup_service, temp_db_path):
        """Test successful backup restoration"""
        # Create backup
        backup_result = backup_service.create_backup()
        backup_filename = backup_result["filename"]
        
        # Modify original database
        with open(temp_db_path, 'w') as f:
            f.write("modified content")
        
        # Restore
        restore_result = backup_service.restore_backup(backup_filename)
        
        assert restore_result["success"] is True
        assert "safety_backup" in restore_result
        
        # Verify content restored
        with open(temp_db_path, 'r') as f:
            content = f.read()
        assert content == "test database content"
    
    def test_restore_creates_safety_backup(self, backup_service, temp_db_path):
        """Test restore creates safety backup of current database"""
        # Create backup
        backup_result = backup_service.create_backup()
        
        # Restore
        restore_result = backup_service.restore_backup(backup_result["filename"])
        
        assert restore_result["success"] is True
        
        # Verify safety backup exists
        safety_backup = restore_result["safety_backup"]
        assert os.path.exists(safety_backup)
    
    def test_restore_nonexistent_backup(self, backup_service):
        """Test restore fails gracefully with non-existent backup"""
        result = backup_service.restore_backup("nonexistent_backup.db")
        
        assert result["success"] is False
        assert "error" in result
    
    def test_restore_compressed_backup(self, backup_service, temp_db_path):
        """Test restoring compressed backup"""
        # Create compressed backup
        backup_result = backup_service.create_backup(compress=True)
        
        # Modify database
        with open(temp_db_path, 'w') as f:
            f.write("modified")
        
        # Restore
        restore_result = backup_service.restore_backup(backup_result["filename"])
        
        assert restore_result["success"] is True
        
        # Verify content restored
        with open(temp_db_path, 'r') as f:
            content = f.read()
        assert content == "test database content"


class TestBackupIntegrity:
    """Tests for backup integrity validation"""
    
    def test_backup_size_matches_original(self, backup_service, temp_db_path):
        """Test backup has same size as original (uncompressed)"""
        original_size = os.path.getsize(temp_db_path)
        
        result = backup_service.create_backup(compress=False)
        backup_size = result["size_bytes"]
        
        assert backup_size == original_size
    
    def test_compressed_backup_smaller(self, backup_service, temp_db_path):
        """Test compressed backup is smaller than original"""
        # Create larger test database
        with open(temp_db_path, 'w') as f:
            f.write("test " * 1000)
        
        original_size = os.path.getsize(temp_db_path)
        
        result = backup_service.create_backup(compress=True)
        compressed_size = result["size_bytes"]
        
        # Compressed should be smaller
        assert compressed_size < original_size
