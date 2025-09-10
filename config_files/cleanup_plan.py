#!/usr/bin/env python3
"""
안전한 파일 정리 도구 - 백업 후 삭제
"""

import os
import shutil
import datetime
from pathlib import Path

class SafeFileCleanup:
    def __init__(self):
        self.backup_dir = Path("cleanup_backup")
        self.backup_dir.mkdir(exist_ok=True)
        
        # 절대 삭제하면 안 되는 핵심 파일들
        self.critical_files = {
            'app.py',
            'replit.md',
            'erp_system.db',
            '.replit'
        }
        
        # 절대 삭제하면 안 되는 폴더들
        self.critical_dirs = {
            'pages',
            'languages', 
            'templates',
            'locales'
        }
        
        # 안전하게 삭제 가능한 파일 패턴들
        self.safe_patterns = [
            'add_*.py',
            'debug_*.py', 
            'test_*.py',
            'clean_*.py',
            'fix_*.py',
            '*_old.py',
            '*_backup.py',
            '*_v1.py',
            '*_temp.py'
        ]

    def create_backup(self, file_path):
        """파일을 백업 폴더로 복사"""
        try:
            backup_path = self.backup_dir / file_path.name
            shutil.copy2(file_path, backup_path)
            print(f"✅ 백업 완료: {file_path}")
            return True
        except Exception as e:
            print(f"❌ 백업 실패: {file_path} - {e}")
            return False

    def is_safe_to_delete(self, file_path):
        """삭제해도 안전한 파일인지 확인"""
        file_name = file_path.name
        
        # 핵심 파일 체크
        if file_name in self.critical_files:
            return False
            
        # 핵심 폴더 체크  
        if file_path.is_dir() and file_name in self.critical_dirs:
            return False
            
        # SQLite 매니저 체크 (현재 사용 중)
        if file_name.startswith('sqlite_') and file_name.endswith('.py'):
            return False
            
        # 안전한 패턴 체크
        import fnmatch
        for pattern in self.safe_patterns:
            if fnmatch.fnmatch(file_name, pattern):
                return True
                
        return False

    def preview_cleanup(self):
        """삭제할 파일들 미리보기"""
        to_delete = []
        for file_path in Path('.').rglob('*'):
            if file_path.is_file() and self.is_safe_to_delete(file_path):
                to_delete.append(file_path)
        
        print(f"\n📋 삭제 예정 파일들 ({len(to_delete)}개):")
        for file_path in sorted(to_delete):
            print(f"  🗑️  {file_path}")
            
        return to_delete

    def safe_cleanup(self, confirm=False):
        """백업 후 안전하게 삭제"""
        to_delete = self.preview_cleanup()
        
        if not confirm:
            print(f"\n⚠️  {len(to_delete)}개 파일이 삭제됩니다.")
            print("실행하려면 safe_cleanup(confirm=True)를 호출하세요.")
            return
        
        success_count = 0
        for file_path in to_delete:
            if self.create_backup(file_path):
                try:
                    file_path.unlink()
                    success_count += 1
                    print(f"🗑️  삭제 완료: {file_path}")
                except Exception as e:
                    print(f"❌ 삭제 실패: {file_path} - {e}")
        
        print(f"\n✅ 정리 완료: {success_count}개 파일 삭제")
        print(f"📁 백업 위치: {self.backup_dir}")

if __name__ == "__main__":
    cleaner = SafeFileCleanup()
    cleaner.preview_cleanup()