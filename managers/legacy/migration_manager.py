import pandas as pd
import os
import shutil
from datetime import datetime
from pathlib import Path
import json

class MigrationManager:
    """Data migration and backup management system"""
    
    def __init__(self):
        self.backup_dir = "backups"
        self.migration_log_file = "data/migration_log.csv"
        self.version_file = "data/system_version.json"
        self.init_migration_system()
    
    def init_migration_system(self):
        """Initialize migration system"""
        Path("data").mkdir(exist_ok=True)
        Path(self.backup_dir).mkdir(exist_ok=True)
        
        # Initialize migration log
        if not os.path.exists(self.migration_log_file):
            df = pd.DataFrame(columns=[
                'migration_id', 'from_version', 'to_version', 'migration_type',
                'status', 'backup_path', 'started_at', 'completed_at',
                'error_message', 'files_migrated', 'records_migrated'
            ])
            df.to_csv(self.migration_log_file, index=False, encoding='utf-8-sig')
        
        # Initialize version file
        if not os.path.exists(self.version_file):
            version_info = {
                "current_version": "06.00.00",
                "previous_version": None,
                "last_migration": None,
                "database_version": "06.00.00",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            with open(self.version_file, 'w', encoding='utf-8') as f:
                json.dump(version_info, f, indent=2, ensure_ascii=False)
    
    def get_current_version(self):
        """Get current system version"""
        try:
            with open(self.version_file, 'r', encoding='utf-8') as f:
                version_info = json.load(f)
                return version_info.get('current_version', '06.00.00')
        except Exception as e:
            print(f"Error getting current version: {e}")
            return '06.00.00'
    
    def create_backup(self, backup_name=None):
        """Create full system backup"""
        try:
            if not backup_name:
                backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            backup_path = os.path.join(self.backup_dir, backup_name)
            Path(backup_path).mkdir(exist_ok=True)
            
            # Backup data directory
            data_backup_path = os.path.join(backup_path, "data")
            if os.path.exists("data"):
                shutil.copytree("data", data_backup_path, dirs_exist_ok=True)
            
            # Backup templates directory
            templates_backup_path = os.path.join(backup_path, "templates")
            if os.path.exists("templates"):
                shutil.copytree("templates", templates_backup_path, dirs_exist_ok=True)
            
            # Backup localization directory
            localization_backup_path = os.path.join(backup_path, "localization")
            if os.path.exists("localization"):
                shutil.copytree("localization", localization_backup_path, dirs_exist_ok=True)
            
            # Create backup manifest
            manifest = {
                "backup_name": backup_name,
                "created_at": datetime.now().isoformat(),
                "system_version": self.get_current_version(),
                "directories_backed_up": ["data", "templates", "localization"],
                "backup_size": self._get_directory_size(backup_path)
            }
            
            manifest_path = os.path.join(backup_path, "backup_manifest.json")
            with open(manifest_path, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)
            
            return backup_path
        except Exception as e:
            print(f"Error creating backup: {e}")
            return None
    
    def restore_backup(self, backup_path):
        """Restore system from backup"""
        try:
            if not os.path.exists(backup_path):
                return False, "Backup path does not exist"
            
            # Verify backup manifest
            manifest_path = os.path.join(backup_path, "backup_manifest.json")
            if not os.path.exists(manifest_path):
                return False, "Invalid backup: manifest file missing"
            
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            
            # Create current backup before restoration
            current_backup = self.create_backup(f"pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            
            # Restore data directory
            data_backup_path = os.path.join(backup_path, "data")
            if os.path.exists(data_backup_path):
                if os.path.exists("data"):
                    shutil.rmtree("data")
                shutil.copytree(data_backup_path, "data")
            
            # Restore templates directory
            templates_backup_path = os.path.join(backup_path, "templates")
            if os.path.exists(templates_backup_path):
                if os.path.exists("templates"):
                    shutil.rmtree("templates")
                shutil.copytree(templates_backup_path, "templates")
            
            # Restore localization directory
            localization_backup_path = os.path.join(backup_path, "localization")
            if os.path.exists(localization_backup_path):
                if os.path.exists("localization"):
                    shutil.rmtree("localization")
                shutil.copytree(localization_backup_path, "localization")
            
            return True, f"System restored from backup: {manifest['backup_name']}"
        except Exception as e:
            print(f"Error restoring backup: {e}")
            return False, f"Restoration failed: {e}"
    
    def migrate_from_v05(self, v05_data_path):
        """Migrate data from version 05 to version 06"""
        try:
            migration_id = f"MIG_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Log migration start
            self._log_migration(migration_id, "05.xx.xx", "06.00.00", "version_upgrade", "started")
            
            # Create backup before migration
            backup_path = self.create_backup(f"pre_migration_v06_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            
            migrated_files = 0
            migrated_records = 0
            
            # Migrate existing data files
            if os.path.exists(v05_data_path):
                for file_name in os.listdir(v05_data_path):
                    if file_name.endswith('.csv'):
                        source_path = os.path.join(v05_data_path, file_name)
                        dest_path = os.path.join("data", file_name)
                        
                        # Copy file
                        shutil.copy2(source_path, dest_path)
                        migrated_files += 1
                        
                        # Count records
                        try:
                            df = pd.read_csv(dest_path, encoding='utf-8-sig')
                            migrated_records += len(df)
                        except:
                            pass
            
            # Initialize new V06 data files
            self._initialize_v06_data_files()
            
            # Update version info
            self._update_version_info("06.00.00", "05.xx.xx")
            
            # Log migration completion
            self._log_migration(migration_id, "05.xx.xx", "06.00.00", "version_upgrade", "completed",
                              backup_path, migrated_files, migrated_records)
            
            return True, f"Migration completed. Files: {migrated_files}, Records: {migrated_records}"
        except Exception as e:
            print(f"Error during migration: {e}")
            self._log_migration(migration_id, "05.xx.xx", "06.00.00", "version_upgrade", "failed", error_message=str(e))
            return False, f"Migration failed: {e}"
    
    def _initialize_v06_data_files(self):
        """Initialize new data files for V06"""
        try:
            # Initialize all manager classes to create new data files
            from auth_manager import AuthManager
            from employee_manager import EmployeeManager
            from customer_manager import CustomerManager
            from product_manager import ProductManager
            from supplier_manager import SupplierManager
            from quotation_manager import QuotationManager
            from approval_manager import ApprovalManager
            from exchange_rate_manager import ExchangeRateManager
            from business_process_manager import BusinessProcessManager
            from pdf_design_manager import PDFDesignManager
            from product_code_manager import ProductCodeManager
            from inventory_manager import InventoryManager
            from shipping_manager import ShippingManager
            from invoice_manager import InvoiceManager
            from purchase_order_manager import PurchaseOrderManager
            from notification_manager import NotificationManager
            
            # Initialize all managers
            managers = [
                AuthManager(),
                EmployeeManager(),
                CustomerManager(),
                ProductManager(),
                SupplierManager(),
                QuotationManager(),
                ApprovalManager(),
                ExchangeRateManager(),
                BusinessProcessManager(),
                PDFDesignManager(),
                ProductCodeManager(),
                InventoryManager(),
                ShippingManager(),
                InvoiceManager(),
                PurchaseOrderManager(),
                NotificationManager()
            ]
            
            return True
        except Exception as e:
            print(f"Error initializing V06 data files: {e}")
            return False
    
    def _log_migration(self, migration_id, from_version, to_version, migration_type, 
                      status, backup_path=None, files_migrated=0, records_migrated=0, error_message=None):
        """Log migration activity"""
        try:
            df = pd.read_csv(self.migration_log_file, encoding='utf-8-sig')
            
            # Check if migration already exists
            existing = df[df['migration_id'] == migration_id]
            
            if existing.empty:
                # Create new entry
                migration_data = {
                    'migration_id': migration_id,
                    'from_version': from_version,
                    'to_version': to_version,
                    'migration_type': migration_type,
                    'status': status,
                    'backup_path': backup_path,
                    'started_at': datetime.now(),
                    'completed_at': datetime.now() if status in ['completed', 'failed'] else None,
                    'error_message': error_message,
                    'files_migrated': files_migrated,
                    'records_migrated': records_migrated
                }
                
                new_entry = pd.DataFrame([migration_data])
                df = pd.concat([df, new_entry], ignore_index=True)
            else:
                # Update existing entry
                df.loc[df['migration_id'] == migration_id, 'status'] = status
                if status in ['completed', 'failed']:
                    df.loc[df['migration_id'] == migration_id, 'completed_at'] = datetime.now()
                if error_message:
                    df.loc[df['migration_id'] == migration_id, 'error_message'] = error_message
                if files_migrated > 0:
                    df.loc[df['migration_id'] == migration_id, 'files_migrated'] = files_migrated
                if records_migrated > 0:
                    df.loc[df['migration_id'] == migration_id, 'records_migrated'] = records_migrated
            
            df.to_csv(self.migration_log_file, index=False, encoding='utf-8-sig')
            return True
        except Exception as e:
            print(f"Error logging migration: {e}")
            return False
    
    def _update_version_info(self, new_version, previous_version):
        """Update system version information"""
        try:
            version_info = {
                "current_version": new_version,
                "previous_version": previous_version,
                "last_migration": datetime.now().isoformat(),
                "database_version": new_version,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            with open(self.version_file, 'w', encoding='utf-8') as f:
                json.dump(version_info, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"Error updating version info: {e}")
            return False
    
    def _get_directory_size(self, directory_path):
        """Get total size of directory in bytes"""
        try:
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(directory_path):
                for filename in filenames:
                    file_path = os.path.join(dirpath, filename)
                    if os.path.exists(file_path):
                        total_size += os.path.getsize(file_path)
            return total_size
        except Exception as e:
            print(f"Error calculating directory size: {e}")
            return 0
    
    def get_migration_history(self):
        """Get migration history"""
        try:
            df = pd.read_csv(self.migration_log_file, encoding='utf-8-sig')
            return df.sort_values('started_at', ascending=False)
        except Exception as e:
            print(f"Error getting migration history: {e}")
            return pd.DataFrame()
    
    def get_backup_list(self):
        """Get list of available backups"""
        try:
            backups = []
            
            if os.path.exists(self.backup_dir):
                for backup_name in os.listdir(self.backup_dir):
                    backup_path = os.path.join(self.backup_dir, backup_name)
                    if os.path.isdir(backup_path):
                        manifest_path = os.path.join(backup_path, "backup_manifest.json")
                        
                        if os.path.exists(manifest_path):
                            try:
                                with open(manifest_path, 'r', encoding='utf-8') as f:
                                    manifest = json.load(f)
                                    manifest['backup_path'] = backup_path
                                    backups.append(manifest)
                            except:
                                # If manifest is corrupted, create basic info
                                backups.append({
                                    "backup_name": backup_name,
                                    "backup_path": backup_path,
                                    "created_at": "Unknown",
                                    "system_version": "Unknown",
                                    "backup_size": self._get_directory_size(backup_path)
                                })
            
            return sorted(backups, key=lambda x: x.get('created_at', ''), reverse=True)
        except Exception as e:
            print(f"Error getting backup list: {e}")
            return []
    
    def delete_backup(self, backup_name):
        """Delete specific backup"""
        try:
            backup_path = os.path.join(self.backup_dir, backup_name)
            if os.path.exists(backup_path):
                shutil.rmtree(backup_path)
                return True
            return False
        except Exception as e:
            print(f"Error deleting backup: {e}")
            return False
    
    def cleanup_old_backups(self, keep_count=10):
        """Clean up old backups, keeping only the most recent ones"""
        try:
            backups = self.get_backup_list()
            
            if len(backups) > keep_count:
                # Sort by creation date and delete oldest
                backups_to_delete = backups[keep_count:]
                deleted_count = 0
                
                for backup in backups_to_delete:
                    if self.delete_backup(backup['backup_name']):
                        deleted_count += 1
                
                return deleted_count
            
            return 0
        except Exception as e:
            print(f"Error cleaning up old backups: {e}")
            return 0
    
    def export_data(self, export_path, data_types=None):
        """Export system data to external location"""
        try:
            if not data_types:
                data_types = ['all']
            
            Path(export_path).mkdir(parents=True, exist_ok=True)
            
            exported_files = 0
            
            if 'all' in data_types or 'data' in data_types:
                if os.path.exists("data"):
                    data_export_path = os.path.join(export_path, "data")
                    shutil.copytree("data", data_export_path, dirs_exist_ok=True)
                    exported_files += len(os.listdir("data"))
            
            if 'all' in data_types or 'templates' in data_types:
                if os.path.exists("templates"):
                    templates_export_path = os.path.join(export_path, "templates")
                    shutil.copytree("templates", templates_export_path, dirs_exist_ok=True)
            
            if 'all' in data_types or 'localization' in data_types:
                if os.path.exists("localization"):
                    localization_export_path = os.path.join(export_path, "localization")
                    shutil.copytree("localization", localization_export_path, dirs_exist_ok=True)
            
            # Create export manifest
            manifest = {
                "export_date": datetime.now().isoformat(),
                "system_version": self.get_current_version(),
                "data_types": data_types,
                "exported_files": exported_files
            }
            
            manifest_path = os.path.join(export_path, "export_manifest.json")
            with open(manifest_path, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)
            
            return True, f"Data exported successfully. Files: {exported_files}"
        except Exception as e:
            print(f"Error exporting data: {e}")
            return False, f"Export failed: {e}"
