#!/usr/bin/env python3
"""
백업 관리 시스템
- 자동/수동 백업 기능
- 백업 복원 기능
- 백업 파일 관리
"""

import os
import shutil
import zipfile
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import json
import logging
from pathlib import Path

class BackupManager:
    def __init__(self):
        self.backup_dir = Path("backups")
        self.data_dir = Path("data")
        self.db_file = "erp_system.db"
        
        # 백업 디렉토리 생성
        self.backup_dir.mkdir(exist_ok=True)
        
        # 로깅 설정
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def create_backup(self, backup_type="manual", description=""):
        """
        백업 생성
        Args:
            backup_type: 'manual' 또는 'auto'
            description: 백업 설명
        Returns:
            tuple: (성공 여부, 백업 파일 경로)
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_{backup_type}_{timestamp}"
            backup_path = self.backup_dir / backup_name
            backup_path.mkdir(exist_ok=True)
            
            # 백업 메타데이터
            metadata = {
                "backup_type": backup_type,
                "timestamp": timestamp,
                "description": description,
                "created_at": datetime.now().isoformat(),
                "files_backed_up": [],
                "database_backed_up": False
            }
            
            # 1. 데이터 파일 백업 (CSV 파일들)
            if self.data_dir.exists():
                data_backup_path = backup_path / "data"
                shutil.copytree(self.data_dir, data_backup_path, dirs_exist_ok=True)
                
                # 백업된 파일 목록 추가
                for file in data_backup_path.rglob("*"):
                    if file.is_file():
                        metadata["files_backed_up"].append(str(file.relative_to(backup_path)))
                
                self.logger.info(f"데이터 파일 백업 완료: {data_backup_path}")
            
            # 2. 데이터베이스 백업
            if os.path.exists(self.db_file):
                db_backup_path = backup_path / "database"
                db_backup_path.mkdir(exist_ok=True)
                
                # SQLite 데이터베이스 백업
                shutil.copy2(self.db_file, db_backup_path / self.db_file)
                
                # 추가로 SQL 덤프도 생성
                self._create_sql_dump(db_backup_path / "database_dump.sql")
                
                metadata["database_backed_up"] = True
                metadata["files_backed_up"].extend([
                    f"database/{self.db_file}",
                    "database/database_dump.sql"
                ])
                
                self.logger.info(f"데이터베이스 백업 완료: {db_backup_path}")
            
            # 3. 설정 파일 백업
            config_files = [
                "replit.md",
                ".replit", 
                "pyproject.toml",
                "locales",
                "templates"
            ]
            
            for config_item in config_files:
                if os.path.exists(config_item):
                    if os.path.isfile(config_item):
                        shutil.copy2(config_item, backup_path / config_item)
                        metadata["files_backed_up"].append(config_item)
                    elif os.path.isdir(config_item):
                        shutil.copytree(config_item, backup_path / config_item, dirs_exist_ok=True)
                        for file in (backup_path / config_item).rglob("*"):
                            if file.is_file():
                                metadata["files_backed_up"].append(str(file.relative_to(backup_path)))
            
            # 4. 메타데이터 저장
            with open(backup_path / "backup_metadata.json", "w", encoding="utf-8") as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            # 5. 백업을 ZIP 파일로 압축
            zip_file_path = self.backup_dir / f"{backup_name}.zip"
            with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in backup_path.rglob("*"):
                    if file_path.is_file():
                        arcname = file_path.relative_to(backup_path)
                        zipf.write(file_path, arcname)
            
            # 임시 백업 폴더 삭제
            shutil.rmtree(backup_path)
            
            self.logger.info(f"백업 생성 완료: {zip_file_path}")
            return True, str(zip_file_path)
            
        except Exception as e:
            self.logger.error(f"백업 생성 실패: {str(e)}")
            return False, str(e)
    
    def _create_sql_dump(self, dump_path):
        """SQLite 데이터베이스의 SQL 덤프를 생성합니다"""
        try:
            conn = sqlite3.connect(self.db_file)
            with open(dump_path, 'w', encoding='utf-8') as f:
                for line in conn.iterdump():
                    f.write('%s\n' % line)
            conn.close()
            self.logger.info(f"SQL 덤프 생성 완료: {dump_path}")
        except Exception as e:
            self.logger.error(f"SQL 덤프 생성 실패: {str(e)}")
    
    def list_backups(self):
        """백업 목록을 반환합니다"""
        backups = []
        
        for backup_file in self.backup_dir.glob("backup_*.zip"):
            try:
                # ZIP 파일에서 메타데이터 읽기
                with zipfile.ZipFile(backup_file, 'r') as zipf:
                    if "backup_metadata.json" in zipf.namelist():
                        metadata_content = zipf.read("backup_metadata.json").decode('utf-8')
                        metadata = json.loads(metadata_content)
                        
                        metadata['file_path'] = str(backup_file)
                        metadata['file_size'] = backup_file.stat().st_size
                        metadata['file_size_mb'] = round(backup_file.stat().st_size / (1024*1024), 2)
                        
                        backups.append(metadata)
            except Exception as e:
                self.logger.error(f"백업 파일 읽기 실패 {backup_file}: {str(e)}")
        
        # 날짜순 정렬 (최신순)
        backups.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        return backups
    
    def restore_backup(self, backup_file_path, restore_data=True, restore_database=True):
        """
        백업을 복원합니다
        Args:
            backup_file_path: 복원할 백업 파일 경로
            restore_data: 데이터 파일 복원 여부
            restore_database: 데이터베이스 복원 여부
        Returns:
            tuple: (성공 여부, 메시지)
        """
        try:
            # 복원 전 현재 데이터 백업
            pre_restore_backup = self.create_backup("pre_restore", "복원 전 자동 백업")
            if not pre_restore_backup[0]:
                return False, f"복원 전 백업 실패: {pre_restore_backup[1]}"
            
            backup_path = Path(backup_file_path)
            if not backup_path.exists():
                return False, "백업 파일이 존재하지 않습니다"
            
            # 임시 복원 디렉토리
            temp_restore_path = self.backup_dir / "temp_restore"
            if temp_restore_path.exists():
                shutil.rmtree(temp_restore_path)
            temp_restore_path.mkdir(exist_ok=True)
            
            # ZIP 파일 압축 해제
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                zipf.extractall(temp_restore_path)
            
            restored_items = []
            
            # 데이터 파일 복원
            if restore_data and (temp_restore_path / "data").exists():
                if self.data_dir.exists():
                    shutil.rmtree(self.data_dir)
                shutil.copytree(temp_restore_path / "data", self.data_dir)
                restored_items.append("데이터 파일")
                self.logger.info("데이터 파일 복원 완료")
            
            # 데이터베이스 복원
            if restore_database and (temp_restore_path / "database").exists():
                db_backup_file = temp_restore_path / "database" / self.db_file
                if db_backup_file.exists():
                    if os.path.exists(self.db_file):
                        os.remove(self.db_file)
                    shutil.copy2(db_backup_file, self.db_file)
                    restored_items.append("데이터베이스")
                    self.logger.info("데이터베이스 복원 완료")
            
            # 설정 파일 복원
            config_files = ["replit.md", ".replit", "pyproject.toml"]
            for config_file in config_files:
                config_backup_path = temp_restore_path / config_file
                if config_backup_path.exists():
                    if config_backup_path.is_file():
                        shutil.copy2(config_backup_path, config_file)
                    elif config_backup_path.is_dir():
                        if os.path.exists(config_file):
                            shutil.rmtree(config_file)
                        shutil.copytree(config_backup_path, config_file)
                    restored_items.append(f"설정: {config_file}")
            
            # 임시 디렉토리 정리
            shutil.rmtree(temp_restore_path)
            
            success_message = f"백업 복원 완료. 복원된 항목: {', '.join(restored_items)}"
            self.logger.info(success_message)
            return True, success_message
            
        except Exception as e:
            error_message = f"백업 복원 실패: {str(e)}"
            self.logger.error(error_message)
            return False, error_message
    
    def delete_backup(self, backup_file_path):
        """백업 파일을 삭제합니다"""
        try:
            backup_path = Path(backup_file_path)
            if backup_path.exists():
                os.remove(backup_path)
                self.logger.info(f"백업 파일 삭제 완료: {backup_path}")
                return True, "백업 파일이 삭제되었습니다"
            else:
                return False, "백업 파일이 존재하지 않습니다"
        except Exception as e:
            error_message = f"백업 파일 삭제 실패: {str(e)}"
            self.logger.error(error_message)
            return False, error_message
    
    def cleanup_old_backups(self, keep_days=30, keep_count=10):
        """
        오래된 백업을 정리합니다
        Args:
            keep_days: 보관할 일 수
            keep_count: 최소 보관할 백업 개수
        """
        try:
            backups = self.list_backups()
            cutoff_date = datetime.now() - timedelta(days=keep_days)
            
            deleted_count = 0
            for backup in backups[keep_count:]:  # 최소 개수는 유지
                backup_date = datetime.fromisoformat(backup['created_at'])
                if backup_date < cutoff_date:
                    success, message = self.delete_backup(backup['file_path'])
                    if success:
                        deleted_count += 1
            
            self.logger.info(f"오래된 백업 {deleted_count}개 정리 완료")
            return True, f"오래된 백업 {deleted_count}개가 정리되었습니다"
            
        except Exception as e:
            error_message = f"백업 정리 실패: {str(e)}"
            self.logger.error(error_message)
            return False, error_message
    
    def auto_backup(self):
        """자동 백업 실행 (스케줄러에서 호출)"""
        return self.create_backup("auto", "자동 백업")
    
    def get_backup_statistics(self):
        """백업 통계 정보를 반환합니다"""
        backups = self.list_backups()
        
        if not backups:
            return {
                "total_backups": 0,
                "total_size_mb": 0,
                "latest_backup": None,
                "auto_backups": 0,
                "manual_backups": 0
            }
        
        total_size = sum(backup.get('file_size', 0) for backup in backups)
        auto_count = sum(1 for backup in backups if backup.get('backup_type') == 'auto')
        manual_count = len(backups) - auto_count
        
        return {
            "total_backups": len(backups),
            "total_size_mb": round(total_size / (1024*1024), 2),
            "latest_backup": backups[0]['created_at'] if backups else None,
            "auto_backups": auto_count,
            "manual_backups": manual_count
        }