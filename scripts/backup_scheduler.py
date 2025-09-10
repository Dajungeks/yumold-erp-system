#!/usr/bin/env python3
"""
백업 스케줄러 - 자동 백업 실행을 위한 스케줄링 시스템
"""

import threading
import time
import schedule
from datetime import datetime, timedelta
from managers.legacy.backup_manager import BackupManager
import logging

class BackupScheduler:
    def __init__(self):
        self.backup_manager = BackupManager()
        self.scheduler_thread = None
        self.running = False
        
        # 로깅 설정
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def start_scheduler(self):
        """백업 스케줄러를 시작합니다"""
        if self.running:
            self.logger.info("스케줄러가 이미 실행 중입니다.")
            return False
        
        try:
            # 매일 자정에 자동 백업 실행
            schedule.every().day.at("00:00").do(self._run_daily_backup)
            
            # 개발/테스트용 - 매 시간마다 백업 (선택사항)
            # schedule.every().hour.do(self._run_hourly_backup)
            
            self.running = True
            self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
            self.scheduler_thread.start()
            
            self.logger.info("백업 스케줄러가 시작되었습니다.")
            return True
            
        except Exception as e:
            self.logger.error(f"스케줄러 시작 실패: {str(e)}")
            return False
    
    def stop_scheduler(self):
        """백업 스케줄러를 중지합니다"""
        try:
            self.running = False
            schedule.clear()
            
            if self.scheduler_thread and self.scheduler_thread.is_alive():
                self.scheduler_thread.join(timeout=5)
            
            self.logger.info("백업 스케줄러가 중지되었습니다.")
            return True
            
        except Exception as e:
            self.logger.error(f"스케줄러 중지 실패: {str(e)}")
            return False
    
    def _scheduler_loop(self):
        """스케줄러 메인 루프"""
        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # 1분마다 스케줄 확인
            except Exception as e:
                self.logger.error(f"스케줄러 루프 오류: {str(e)}")
                time.sleep(60)
    
    def _run_daily_backup(self):
        """매일 자동 백업을 실행합니다"""
        try:
            self.logger.info("일일 자동 백업을 시작합니다.")
            
            # 자동 백업 실행
            success, result = self.backup_manager.auto_backup()
            
            if success:
                self.logger.info(f"일일 자동 백업 완료: {result}")
                
                # 오래된 백업 정리 (30일 이상, 10개 미만은 유지)
                cleanup_success, cleanup_msg = self.backup_manager.cleanup_old_backups(30, 10)
                if cleanup_success:
                    self.logger.info(f"백업 정리 완료: {cleanup_msg}")
                else:
                    self.logger.warning(f"백업 정리 실패: {cleanup_msg}")
                    
            else:
                self.logger.error(f"일일 자동 백업 실패: {result}")
                
        except Exception as e:
            self.logger.error(f"일일 백업 실행 중 오류: {str(e)}")
    
    def _run_hourly_backup(self):
        """시간별 백업 (개발/테스트용)"""
        try:
            self.logger.info("시간별 자동 백업을 시작합니다.")
            
            success, result = self.backup_manager.create_backup(
                "auto_hourly", 
                f"시간별 자동 백업 - {datetime.now().strftime('%H:%M')}"
            )
            
            if success:
                self.logger.info(f"시간별 백업 완료: {result}")
            else:
                self.logger.error(f"시간별 백업 실패: {result}")
                
        except Exception as e:
            self.logger.error(f"시간별 백업 실행 중 오류: {str(e)}")
    
    def get_next_backup_time(self):
        """다음 백업 예정 시간을 반환합니다"""
        try:
            jobs = schedule.jobs
            if jobs:
                next_run = min(job.next_run for job in jobs)
                return next_run
            else:
                return None
        except Exception:
            return None
    
    def force_backup_now(self):
        """즉시 백업을 실행합니다"""
        try:
            self.logger.info("수동으로 백업을 실행합니다.")
            return self.backup_manager.auto_backup()
        except Exception as e:
            self.logger.error(f"즉시 백업 실행 실패: {str(e)}")
            return False, str(e)
    
    def is_running(self):
        """스케줄러 실행 상태를 반환합니다"""
        return self.running and self.scheduler_thread and self.scheduler_thread.is_alive()
    
    def get_scheduler_status(self):
        """스케줄러 상태 정보를 반환합니다"""
        return {
            "running": self.is_running(),
            "next_backup": self.get_next_backup_time(),
            "scheduled_jobs": len(schedule.jobs),
            "thread_alive": self.scheduler_thread.is_alive() if self.scheduler_thread else False
        }

# 전역 스케줄러 인스턴스
backup_scheduler = BackupScheduler()