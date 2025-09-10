"""
시스템 백업 및 복원 관리자
UTF-8 인코딩 문제 없이 안전한 백업/복원 기능 제공
"""

import os
import sqlite3
import shutil
import json
import zipfile
import tempfile
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

# UTF-8 로깅 설정
logging.basicConfig(level=logging.INFO, encoding='utf-8')
logger = logging.getLogger(__name__)

class BackupManager:
    def __init__(self, base_path: str = "."):
        self.base_path = base_path
        self.backup_dir = os.path.join(base_path, "backups")
        self.ensure_backup_directory()
        
    def ensure_backup_directory(self):
        """백업 디렉토리 생성"""
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir, exist_ok=True)
            logger.info(f"백업 디렉토리 생성: {self.backup_dir}")
    
    def get_backup_items(self) -> Dict[str, Any]:
        """백업 대상 항목들 정의"""
        return {
            "database": {
                "files": ["erp_system.db"],
                "description": "SQLite 데이터베이스"
            },
            "languages": {
                "directories": ["languages", "locales"],
                "description": "다국어 언어 파일"
            },
            "templates": {
                "directories": ["templates"],
                "description": "HTML 템플릿 파일"
            },
            "core_files": {
                "files": ["app.py"],
                "directories": ["managers", "pages", "components"],
                "description": "핵심 애플리케이션 파일"
            },
            "config": {
                "directories": [".streamlit", "config_files"],
                "description": "설정 파일"
            },
            "assets": {
                "directories": ["attached_assets"],
                "description": "첨부 자산 (이미지, 문서 등)"
            }
        }
    
    def create_backup(self, include_categories: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        시스템 백업 생성
        
        Args:
            include_categories: 백업할 카테고리 목록 (None이면 모든 카테고리)
            
        Returns:
            백업 결과 정보
        """
        try:
            # 백업 파일명 생성 (UTF-8 안전)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"erp_backup_{timestamp}.zip"
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            # 백업 대상 항목
            backup_items = self.get_backup_items()
            if include_categories:
                backup_items = {k: v for k, v in backup_items.items() if k in include_categories}
            
            # 백업 정보 수집
            backup_info = {
                "timestamp": timestamp,
                "filename": backup_filename,
                "path": backup_path,
                "items": {},
                "total_files": 0,
                "total_size": 0,
                "status": "success",
                "errors": []
            }
            
            # ZIP 파일 생성 (UTF-8 지원)
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
                
                for category, config in backup_items.items():
                    category_info = {
                        "files": [],
                        "size": 0,
                        "count": 0
                    }
                    
                    try:
                        # 파일 백업
                        if "files" in config:
                            for file_path in config["files"]:
                                full_path = os.path.join(self.base_path, file_path)
                                if os.path.exists(full_path):
                                    # UTF-8 안전한 파일 처리
                                    arcname = file_path.replace("\\", "/")
                                    zipf.write(full_path, arcname)
                                    
                                    file_size = os.path.getsize(full_path)
                                    category_info["files"].append({
                                        "path": file_path,
                                        "size": file_size
                                    })
                                    category_info["size"] += file_size
                                    category_info["count"] += 1
                        
                        # 디렉토리 백업
                        if "directories" in config:
                            for dir_path in config["directories"]:
                                full_dir_path = os.path.join(self.base_path, dir_path)
                                if os.path.exists(full_dir_path):
                                    for root, dirs, files in os.walk(full_dir_path):
                                        for file in files:
                                            file_full_path = os.path.join(root, file)
                                            # 상대 경로 계산 (UTF-8 안전)
                                            arcname = os.path.relpath(file_full_path, self.base_path).replace("\\", "/")
                                            
                                            try:
                                                zipf.write(file_full_path, arcname)
                                                file_size = os.path.getsize(file_full_path)
                                                category_info["files"].append({
                                                    "path": arcname,
                                                    "size": file_size
                                                })
                                                category_info["size"] += file_size
                                                category_info["count"] += 1
                                            except Exception as e:
                                                error_msg = f"파일 백업 실패: {file_full_path} - {str(e)}"
                                                backup_info["errors"].append(error_msg)
                                                logger.warning(error_msg)
                    
                    except Exception as e:
                        error_msg = f"카테고리 '{category}' 백업 실패: {str(e)}"
                        backup_info["errors"].append(error_msg)
                        logger.error(error_msg)
                    
                    backup_info["items"][category] = category_info
                    backup_info["total_files"] += category_info["count"]
                    backup_info["total_size"] += category_info["size"]
                
                # 백업 메타데이터 추가
                metadata = {
                    "backup_info": backup_info,
                    "system_info": {
                        "backup_version": "1.0",
                        "python_version": "3.x",
                        "encoding": "utf-8"
                    }
                }
                
                # UTF-8로 메타데이터 저장
                metadata_json = json.dumps(metadata, ensure_ascii=False, indent=2).encode('utf-8')
                zipf.writestr("backup_metadata.json", metadata_json)
            
            # 백업 파일 크기 확인
            if os.path.exists(backup_path):
                backup_info["backup_file_size"] = os.path.getsize(backup_path)
                logger.info(f"백업 완료: {backup_filename} ({backup_info['backup_file_size']} bytes)")
            else:
                backup_info["status"] = "failed"
                backup_info["errors"].append("백업 파일이 생성되지 않았습니다.")
            
            return backup_info
            
        except Exception as e:
            error_msg = f"백업 생성 실패: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "failed",
                "error": error_msg,
                "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S")
            }
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """사용 가능한 백업 목록 조회"""
        backups = []
        
        try:
            if not os.path.exists(self.backup_dir):
                return backups
            
            for filename in os.listdir(self.backup_dir):
                if filename.endswith('.zip') and filename.startswith('erp_backup_'):
                    backup_path = os.path.join(self.backup_dir, filename)
                    
                    # 파일 정보
                    stat_info = os.stat(backup_path)
                    backup_info = {
                        "filename": filename,
                        "path": backup_path,
                        "size": stat_info.st_size,
                        "created": datetime.fromtimestamp(stat_info.st_ctime),
                        "modified": datetime.fromtimestamp(stat_info.st_mtime)
                    }
                    
                    # 메타데이터 읽기 시도
                    try:
                        with zipfile.ZipFile(backup_path, 'r') as zipf:
                            if "backup_metadata.json" in zipf.namelist():
                                metadata_content = zipf.read("backup_metadata.json").decode('utf-8')
                                metadata = json.loads(metadata_content)
                                backup_info["metadata"] = metadata.get("backup_info", {})
                    except Exception as e:
                        logger.warning(f"백업 메타데이터 읽기 실패: {filename} - {str(e)}")
                    
                    backups.append(backup_info)
            
            # 생성 시간 순으로 정렬 (최신 순)
            backups.sort(key=lambda x: x["created"], reverse=True)
            
        except Exception as e:
            logger.error(f"백업 목록 조회 실패: {str(e)}")
        
        return backups
    
    def restore_backup(self, backup_filename: str, restore_categories: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        백업에서 시스템 복원
        
        Args:
            backup_filename: 복원할 백업 파일명
            restore_categories: 복원할 카테고리 목록 (None이면 모든 카테고리)
            
        Returns:
            복원 결과 정보
        """
        try:
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            if not os.path.exists(backup_path):
                return {
                    "status": "failed",
                    "error": f"백업 파일을 찾을 수 없습니다: {backup_filename}"
                }
            
            restore_info = {
                "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
                "backup_file": backup_filename,
                "restored_files": [],
                "total_files": 0,
                "status": "success",
                "errors": []
            }
            
            # 임시 디렉토리에서 작업
            with tempfile.TemporaryDirectory() as temp_dir:
                # ZIP 파일 압축 해제
                with zipfile.ZipFile(backup_path, 'r') as zipf:
                    zipf.extractall(temp_dir)
                
                # 메타데이터 확인
                metadata_path = os.path.join(temp_dir, "backup_metadata.json")
                if os.path.exists(metadata_path):
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                        logger.info(f"백업 메타데이터 확인: {metadata.get('system_info', {})}")
                
                # 파일 복원
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        if file == "backup_metadata.json":
                            continue
                        
                        source_path = os.path.join(root, file)
                        relative_path = os.path.relpath(source_path, temp_dir)
                        target_path = os.path.join(self.base_path, relative_path)
                        
                        # 카테고리 필터링
                        if restore_categories:
                            category_match = False
                            for category in restore_categories:
                                if relative_path.startswith(category) or any(
                                    relative_path.startswith(d) for d in self.get_backup_items().get(category, {}).get("directories", [])
                                ):
                                    category_match = True
                                    break
                            if not category_match:
                                continue
                        
                        try:
                            # 대상 디렉토리 생성
                            target_dir = os.path.dirname(target_path)
                            if target_dir and not os.path.exists(target_dir):
                                os.makedirs(target_dir, exist_ok=True)
                            
                            # 파일 복사 (UTF-8 안전)
                            shutil.copy2(source_path, target_path)
                            restore_info["restored_files"].append(relative_path)
                            restore_info["total_files"] += 1
                            
                        except Exception as e:
                            error_msg = f"파일 복원 실패: {relative_path} - {str(e)}"
                            restore_info["errors"].append(error_msg)
                            logger.warning(error_msg)
            
            logger.info(f"복원 완료: {restore_info['total_files']}개 파일")
            return restore_info
            
        except Exception as e:
            error_msg = f"백업 복원 실패: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "failed",
                "error": error_msg,
                "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S")
            }
    
    def delete_backup(self, backup_filename: str) -> Dict[str, Any]:
        """백업 파일 삭제"""
        try:
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            if not os.path.exists(backup_path):
                return {
                    "status": "failed",
                    "error": f"백업 파일을 찾을 수 없습니다: {backup_filename}"
                }
            
            os.remove(backup_path)
            logger.info(f"백업 파일 삭제: {backup_filename}")
            
            return {
                "status": "success",
                "message": f"백업 파일이 삭제되었습니다: {backup_filename}"
            }
            
        except Exception as e:
            error_msg = f"백업 파일 삭제 실패: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "failed",
                "error": error_msg
            }
    
    def get_system_info(self) -> Dict[str, Any]:
        """현재 시스템 정보 조회"""
        try:
            db_path = os.path.join(self.base_path, "erp_system.db")
            system_info = {
                "database_exists": os.path.exists(db_path),
                "database_size": os.path.getsize(db_path) if os.path.exists(db_path) else 0,
                "languages_count": len([f for f in os.listdir(os.path.join(self.base_path, "languages")) if f.endswith('.json')]) if os.path.exists(os.path.join(self.base_path, "languages")) else 0,
                "templates_count": len(os.listdir(os.path.join(self.base_path, "templates"))) if os.path.exists(os.path.join(self.base_path, "templates")) else 0,
                "backup_count": len(self.list_backups()),
                "timestamp": datetime.now().isoformat()
            }
            
            # 데이터베이스 테이블 정보
            if system_info["database_exists"]:
                try:
                    with sqlite3.connect(db_path) as conn:
                        cursor = conn.cursor()
                        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                        tables = [row[0] for row in cursor.fetchall()]
                        system_info["database_tables"] = tables
                        system_info["database_table_count"] = len(tables)
                except Exception as e:
                    logger.warning(f"데이터베이스 정보 조회 실패: {str(e)}")
            
            return system_info
            
        except Exception as e:
            logger.error(f"시스템 정보 조회 실패: {str(e)}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }