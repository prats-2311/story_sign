"""
Backup Service for StorySign Platform
Handles automated backups, data corruption detection, and recovery procedures.
"""

import asyncio
import json
import logging
import os
import shutil
import subprocess
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

import aiofiles
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from core.database_service import DatabaseService
from core.monitoring_service import DatabaseMonitoringService


class BackupType(Enum):
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"


class BackupStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CORRUPTED = "corrupted"


@dataclass
class BackupMetadata:
    backup_id: str
    backup_type: BackupType
    timestamp: datetime
    size_bytes: int
    checksum: str
    tables_included: List[str]
    status: BackupStatus
    error_message: Optional[str] = None
    recovery_point: Optional[datetime] = None


class BackupService:
    """Service for managing database backups and disaster recovery."""
    
    def __init__(
        self,
        db_service: DatabaseService,
        monitoring_service: DatabaseMonitoringService,
        backup_config: Dict[str, Any]
    ):
        self.db_service = db_service
        self.monitoring = monitoring_service
        self.config = backup_config
        self.logger = logging.getLogger(__name__)
        
        # Backup configuration
        self.backup_dir = Path(backup_config.get("backup_directory", "/var/backups/storysign"))
        self.retention_days = backup_config.get("retention_days", 30)
        self.max_backup_size = backup_config.get("max_backup_size_gb", 100) * 1024 * 1024 * 1024
        self.compression_enabled = backup_config.get("compression", True)
        
        # Ensure backup directory exists
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize backup metadata storage
        self.metadata_file = self.backup_dir / "backup_metadata.json"
        self.backup_metadata: Dict[str, BackupMetadata] = {}
        self._load_metadata()

    async def create_full_backup(self) -> str:
        """Create a full database backup."""
        backup_id = f"full_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            self.logger.info(f"Starting full backup: {backup_id}")
            
            # Create backup metadata
            metadata = BackupMetadata(
                backup_id=backup_id,
                backup_type=BackupType.FULL,
                timestamp=datetime.now(),
                size_bytes=0,
                checksum="",
                tables_included=[],
                status=BackupStatus.RUNNING
            )
            
            self.backup_metadata[backup_id] = metadata
            await self._save_metadata()
            
            # Create backup directory
            backup_path = self.backup_dir / backup_id
            backup_path.mkdir(exist_ok=True)
            
            # Get list of all tables
            tables = await self._get_all_tables()
            metadata.tables_included = tables
            
            # Backup each table
            total_size = 0
            for table in tables:
                table_file = backup_path / f"{table}.sql"
                size = await self._backup_table(table, table_file)
                total_size += size
                
                # Check size limits
                if total_size > self.max_backup_size:
                    raise Exception(f"Backup size exceeded limit: {total_size} bytes")
            
            # Create backup manifest
            manifest = {
                "backup_id": backup_id,
                "backup_type": "full",
                "timestamp": metadata.timestamp.isoformat(),
                "tables": tables,
                "total_size": total_size,
                "compression": self.compression_enabled
            }
            
            manifest_file = backup_path / "manifest.json"
            async with aiofiles.open(manifest_file, 'w') as f:
                await f.write(json.dumps(manifest, indent=2))
            
            # Compress backup if enabled
            if self.compression_enabled:
                compressed_file = await self._compress_backup(backup_path)
                total_size = compressed_file.stat().st_size
                
                # Remove uncompressed files
                shutil.rmtree(backup_path)
            
            # Calculate checksum
            checksum = await self._calculate_checksum(backup_path if not self.compression_enabled else compressed_file)
            
            # Update metadata
            metadata.size_bytes = total_size
            metadata.checksum = checksum
            metadata.status = BackupStatus.COMPLETED
            
            await self._save_metadata()
            
            # Monitor backup completion
            await self.monitoring.record_metric("backup_completed", {
                "backup_id": backup_id,
                "backup_type": "full",
                "size_bytes": total_size,
                "duration_seconds": (datetime.now() - metadata.timestamp).total_seconds()
            })
            
            self.logger.info(f"Full backup completed: {backup_id}, Size: {total_size} bytes")
            return backup_id
            
        except Exception as e:
            self.logger.error(f"Full backup failed: {backup_id}, Error: {str(e)}")
            metadata.status = BackupStatus.FAILED
            metadata.error_message = str(e)
            await self._save_metadata()
            
            await self.monitoring.record_metric("backup_failed", {
                "backup_id": backup_id,
                "backup_type": "full",
                "error": str(e)
            })
            
            raise

    async def create_incremental_backup(self, since_backup_id: Optional[str] = None) -> str:
        """Create an incremental backup since the last backup or specified backup."""
        backup_id = f"incr_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            self.logger.info(f"Starting incremental backup: {backup_id}")
            
            # Find reference point
            if since_backup_id is None:
                since_backup_id = self._get_latest_backup_id()
            
            if since_backup_id is None:
                raise Exception("No reference backup found for incremental backup")
            
            reference_backup = self.backup_metadata.get(since_backup_id)
            if not reference_backup:
                raise Exception(f"Reference backup not found: {since_backup_id}")
            
            # Create backup metadata
            metadata = BackupMetadata(
                backup_id=backup_id,
                backup_type=BackupType.INCREMENTAL,
                timestamp=datetime.now(),
                size_bytes=0,
                checksum="",
                tables_included=[],
                status=BackupStatus.RUNNING,
                recovery_point=reference_backup.timestamp
            )
            
            self.backup_metadata[backup_id] = metadata
            await self._save_metadata()
            
            # Create backup directory
            backup_path = self.backup_dir / backup_id
            backup_path.mkdir(exist_ok=True)
            
            # Backup changed data since reference point
            tables = await self._get_all_tables()
            total_size = 0
            
            for table in tables:
                changes_file = backup_path / f"{table}_changes.sql"
                size = await self._backup_table_changes(table, reference_backup.timestamp, changes_file)
                if size > 0:
                    metadata.tables_included.append(table)
                    total_size += size
            
            # Create backup manifest
            manifest = {
                "backup_id": backup_id,
                "backup_type": "incremental",
                "timestamp": metadata.timestamp.isoformat(),
                "reference_backup": since_backup_id,
                "reference_timestamp": reference_backup.timestamp.isoformat(),
                "tables": metadata.tables_included,
                "total_size": total_size
            }
            
            manifest_file = backup_path / "manifest.json"
            async with aiofiles.open(manifest_file, 'w') as f:
                await f.write(json.dumps(manifest, indent=2))
            
            # Compress if enabled
            if self.compression_enabled:
                compressed_file = await self._compress_backup(backup_path)
                total_size = compressed_file.stat().st_size
                shutil.rmtree(backup_path)
            
            # Calculate checksum
            checksum = await self._calculate_checksum(backup_path if not self.compression_enabled else compressed_file)
            
            # Update metadata
            metadata.size_bytes = total_size
            metadata.checksum = checksum
            metadata.status = BackupStatus.COMPLETED
            
            await self._save_metadata()
            
            self.logger.info(f"Incremental backup completed: {backup_id}, Size: {total_size} bytes")
            return backup_id
            
        except Exception as e:
            self.logger.error(f"Incremental backup failed: {backup_id}, Error: {str(e)}")
            metadata.status = BackupStatus.FAILED
            metadata.error_message = str(e)
            await self._save_metadata()
            raise

    async def verify_backup_integrity(self, backup_id: str) -> bool:
        """Verify the integrity of a backup."""
        try:
            metadata = self.backup_metadata.get(backup_id)
            if not metadata:
                self.logger.error(f"Backup metadata not found: {backup_id}")
                return False
            
            # Check if backup file exists
            backup_file = self._get_backup_file_path(backup_id)
            if not backup_file.exists():
                self.logger.error(f"Backup file not found: {backup_file}")
                return False
            
            # Verify checksum
            current_checksum = await self._calculate_checksum(backup_file)
            if current_checksum != metadata.checksum:
                self.logger.error(f"Backup checksum mismatch: {backup_id}")
                metadata.status = BackupStatus.CORRUPTED
                await self._save_metadata()
                return False
            
            # Verify backup can be read
            if backup_file.suffix == '.tar.gz':
                # Test compressed backup
                result = subprocess.run(['tar', '-tzf', str(backup_file)], 
                                      capture_output=True, text=True)
                if result.returncode != 0:
                    self.logger.error(f"Backup archive corrupted: {backup_id}")
                    return False
            
            self.logger.info(f"Backup integrity verified: {backup_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Backup verification failed: {backup_id}, Error: {str(e)}")
            return False

    async def restore_from_backup(self, backup_id: str, target_database: Optional[str] = None) -> bool:
        """Restore database from a backup."""
        try:
            self.logger.info(f"Starting restore from backup: {backup_id}")
            
            # Verify backup integrity first
            if not await self.verify_backup_integrity(backup_id):
                raise Exception(f"Backup integrity check failed: {backup_id}")
            
            metadata = self.backup_metadata[backup_id]
            backup_file = self._get_backup_file_path(backup_id)
            
            # Create temporary directory for extraction
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Extract backup if compressed
                if backup_file.suffix == '.tar.gz':
                    subprocess.run(['tar', '-xzf', str(backup_file), '-C', str(temp_path)], 
                                 check=True)
                    backup_path = temp_path / backup_id
                else:
                    backup_path = backup_file
                
                # Read manifest
                manifest_file = backup_path / "manifest.json"
                async with aiofiles.open(manifest_file, 'r') as f:
                    manifest = json.loads(await f.read())
                
                # Restore tables
                async with self.db_service.get_session() as session:
                    for table in manifest['tables']:
                        table_file = backup_path / f"{table}.sql"
                        if table_file.exists():
                            await self._restore_table(session, table, table_file)
                    
                    await session.commit()
            
            await self.monitoring.record_metric("backup_restored", {
                "backup_id": backup_id,
                "backup_type": metadata.backup_type.value,
                "tables_restored": len(metadata.tables_included)
            })
            
            self.logger.info(f"Restore completed successfully: {backup_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Restore failed: {backup_id}, Error: {str(e)}")
            await self.monitoring.record_metric("backup_restore_failed", {
                "backup_id": backup_id,
                "error": str(e)
            })
            return False

    async def cleanup_old_backups(self) -> int:
        """Clean up old backups based on retention policy."""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            cleaned_count = 0
            
            for backup_id, metadata in list(self.backup_metadata.items()):
                if metadata.timestamp < cutoff_date:
                    backup_file = self._get_backup_file_path(backup_id)
                    if backup_file.exists():
                        backup_file.unlink()
                        self.logger.info(f"Deleted old backup: {backup_id}")
                    
                    del self.backup_metadata[backup_id]
                    cleaned_count += 1
            
            if cleaned_count > 0:
                await self._save_metadata()
            
            self.logger.info(f"Cleaned up {cleaned_count} old backups")
            return cleaned_count
            
        except Exception as e:
            self.logger.error(f"Backup cleanup failed: {str(e)}")
            return 0

    async def detect_data_corruption(self) -> List[Dict[str, Any]]:
        """Detect potential data corruption in the database."""
        corruption_issues = []
        
        try:
            async with self.db_service.get_session() as session:
                # Check for orphaned records
                orphaned_checks = [
                    ("sentence_attempts", "session_id", "practice_sessions", "id"),
                    ("user_profiles", "user_id", "users", "id"),
                    ("group_memberships", "user_id", "users", "id"),
                    ("group_memberships", "group_id", "learning_groups", "id"),
                    ("practice_sessions", "user_id", "users", "id"),
                    ("practice_sessions", "story_id", "stories", "id"),
                ]
                
                for child_table, child_fk, parent_table, parent_pk in orphaned_checks:
                    query = text(f"""
                        SELECT COUNT(*) as orphaned_count
                        FROM {child_table} c
                        LEFT JOIN {parent_table} p ON c.{child_fk} = p.{parent_pk}
                        WHERE p.{parent_pk} IS NULL
                    """)
                    
                    result = await session.execute(query)
                    orphaned_count = result.scalar()
                    
                    if orphaned_count > 0:
                        corruption_issues.append({
                            "type": "orphaned_records",
                            "table": child_table,
                            "count": orphaned_count,
                            "description": f"Found {orphaned_count} orphaned records in {child_table}"
                        })
                
                # Check for invalid data ranges
                data_checks = [
                    ("practice_sessions", "overall_score", "overall_score < 0 OR overall_score > 1"),
                    ("sentence_attempts", "confidence_score", "confidence_score < 0 OR confidence_score > 1"),
                    ("stories", "avg_rating", "avg_rating < 0 OR avg_rating > 5"),
                    ("practice_sessions", "sentences_completed", "sentences_completed > total_sentences"),
                ]
                
                for table, column, condition in data_checks:
                    query = text(f"SELECT COUNT(*) FROM {table} WHERE {condition}")
                    result = await session.execute(query)
                    invalid_count = result.scalar()
                    
                    if invalid_count > 0:
                        corruption_issues.append({
                            "type": "invalid_data",
                            "table": table,
                            "column": column,
                            "count": invalid_count,
                            "description": f"Found {invalid_count} invalid values in {table}.{column}"
                        })
                
                # Check for duplicate unique constraints
                unique_checks = [
                    ("users", "email"),
                    ("users", "username"),
                    ("stories", "title", "created_by"),
                ]
                
                for table, *columns in unique_checks:
                    column_list = ", ".join(columns)
                    query = text(f"""
                        SELECT {column_list}, COUNT(*) as duplicate_count
                        FROM {table}
                        GROUP BY {column_list}
                        HAVING COUNT(*) > 1
                    """)
                    
                    result = await session.execute(query)
                    duplicates = result.fetchall()
                    
                    if duplicates:
                        corruption_issues.append({
                            "type": "duplicate_records",
                            "table": table,
                            "columns": columns,
                            "count": len(duplicates),
                            "description": f"Found {len(duplicates)} duplicate records in {table}"
                        })
            
            if corruption_issues:
                await self.monitoring.record_metric("data_corruption_detected", {
                    "issues_count": len(corruption_issues),
                    "issues": corruption_issues
                })
            
            return corruption_issues
            
        except Exception as e:
            self.logger.error(f"Data corruption detection failed: {str(e)}")
            return []

    # Private helper methods
    
    async def _get_all_tables(self) -> List[str]:
        """Get list of all tables in the database."""
        async with self.db_service.get_session() as session:
            result = await session.execute(text("SHOW TABLES"))
            return [row[0] for row in result.fetchall()]

    async def _backup_table(self, table_name: str, output_file: Path) -> int:
        """Backup a single table to SQL file."""
        # Use mysqldump for TiDB compatibility
        cmd = [
            'mysqldump',
            '--host', self.config.get('host', 'localhost'),
            '--port', str(self.config.get('port', 4000)),
            '--user', self.config.get('username', 'root'),
            '--password=' + self.config.get('password', ''),
            '--single-transaction',
            '--routines',
            '--triggers',
            self.config.get('database', 'storysign'),
            table_name
        ]
        
        with open(output_file, 'w') as f:
            result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)
            
        if result.returncode != 0:
            raise Exception(f"mysqldump failed for table {table_name}: {result.stderr}")
        
        return output_file.stat().st_size

    async def _backup_table_changes(self, table_name: str, since_timestamp: datetime, output_file: Path) -> int:
        """Backup only changes to a table since a specific timestamp."""
        # This is a simplified implementation - in production, you'd use binlog or CDC
        async with self.db_service.get_session() as session:
            # Check if table has timestamp columns
            timestamp_columns = ['created_at', 'updated_at', 'timestamp']
            
            for col in timestamp_columns:
                try:
                    query = text(f"SELECT COUNT(*) FROM {table_name} WHERE {col} > :since_time")
                    result = await session.execute(query, {"since_time": since_timestamp})
                    count = result.scalar()
                    
                    if count > 0:
                        # Export changed records
                        export_query = text(f"SELECT * FROM {table_name} WHERE {col} > :since_time")
                        result = await session.execute(export_query, {"since_time": since_timestamp})
                        
                        # Write to file (simplified - would need proper SQL generation)
                        async with aiofiles.open(output_file, 'w') as f:
                            await f.write(f"-- Changes for {table_name} since {since_timestamp}\n")
                            for row in result.fetchall():
                                # This is simplified - would need proper INSERT statement generation
                                await f.write(f"-- Row: {dict(row)}\n")
                        
                        return output_file.stat().st_size
                    break
                except:
                    continue
        
        return 0

    async def _restore_table(self, session: AsyncSession, table_name: str, sql_file: Path):
        """Restore a table from SQL file."""
        async with aiofiles.open(sql_file, 'r') as f:
            sql_content = await f.read()
        
        # Execute SQL statements (simplified - would need proper parsing)
        statements = sql_content.split(';')
        for statement in statements:
            statement = statement.strip()
            if statement and not statement.startswith('--'):
                await session.execute(text(statement))

    async def _compress_backup(self, backup_path: Path) -> Path:
        """Compress backup directory."""
        compressed_file = backup_path.with_suffix('.tar.gz')
        
        cmd = ['tar', '-czf', str(compressed_file), '-C', str(backup_path.parent), backup_path.name]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"Compression failed: {result.stderr}")
        
        return compressed_file

    async def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of a file."""
        import hashlib
        
        hash_sha256 = hashlib.sha256()
        async with aiofiles.open(file_path, 'rb') as f:
            while chunk := await f.read(8192):
                hash_sha256.update(chunk)
        
        return hash_sha256.hexdigest()

    def _get_backup_file_path(self, backup_id: str) -> Path:
        """Get the file path for a backup."""
        # Check for compressed version first
        compressed_path = self.backup_dir / f"{backup_id}.tar.gz"
        if compressed_path.exists():
            return compressed_path
        
        # Check for uncompressed directory
        uncompressed_path = self.backup_dir / backup_id
        if uncompressed_path.exists():
            return uncompressed_path
        
        # Default to compressed path
        return compressed_path

    def _get_latest_backup_id(self) -> Optional[str]:
        """Get the ID of the most recent successful backup."""
        latest_backup = None
        latest_timestamp = None
        
        for backup_id, metadata in self.backup_metadata.items():
            if metadata.status == BackupStatus.COMPLETED:
                if latest_timestamp is None or metadata.timestamp > latest_timestamp:
                    latest_timestamp = metadata.timestamp
                    latest_backup = backup_id
        
        return latest_backup

    def _load_metadata(self):
        """Load backup metadata from file."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    data = json.load(f)
                
                for backup_id, metadata_dict in data.items():
                    self.backup_metadata[backup_id] = BackupMetadata(
                        backup_id=metadata_dict['backup_id'],
                        backup_type=BackupType(metadata_dict['backup_type']),
                        timestamp=datetime.fromisoformat(metadata_dict['timestamp']),
                        size_bytes=metadata_dict['size_bytes'],
                        checksum=metadata_dict['checksum'],
                        tables_included=metadata_dict['tables_included'],
                        status=BackupStatus(metadata_dict['status']),
                        error_message=metadata_dict.get('error_message'),
                        recovery_point=datetime.fromisoformat(metadata_dict['recovery_point']) if metadata_dict.get('recovery_point') else None
                    )
            except Exception as e:
                self.logger.error(f"Failed to load backup metadata: {str(e)}")

    async def _save_metadata(self):
        """Save backup metadata to file."""
        try:
            data = {}
            for backup_id, metadata in self.backup_metadata.items():
                data[backup_id] = {
                    'backup_id': metadata.backup_id,
                    'backup_type': metadata.backup_type.value,
                    'timestamp': metadata.timestamp.isoformat(),
                    'size_bytes': metadata.size_bytes,
                    'checksum': metadata.checksum,
                    'tables_included': metadata.tables_included,
                    'status': metadata.status.value,
                    'error_message': metadata.error_message,
                    'recovery_point': metadata.recovery_point.isoformat() if metadata.recovery_point else None
                }
            
            async with aiofiles.open(self.metadata_file, 'w') as f:
                await f.write(json.dumps(data, indent=2))
        except Exception as e:
            self.logger.error(f"Failed to save backup metadata: {str(e)}")