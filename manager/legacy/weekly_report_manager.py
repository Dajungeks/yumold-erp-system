"""
주간 보고 게시판 관리자
- 등록된 사용자만 열람 가능한 주간 보고서 시스템
- 권한 관리: 등록된 사람만 보기 가능
"""

import pandas as pd
import os
from datetime import datetime, timedelta
import json

class WeeklyReportManager:
    def __init__(self, data_path="data"):
        self.data_path = data_path
        self.reports_file = os.path.join(data_path, "weekly_reports.csv")
        self.permissions_file = os.path.join(data_path, "report_permissions.csv")
        
        # 데이터 디렉토리 생성
        if not os.path.exists(data_path):
            os.makedirs(data_path)
        
        # CSV 파일 초기화
        self._initialize_files()
    
    def _initialize_files(self):
        """CSV 파일들을 초기화합니다."""
        # 주간 보고서 파일
        if not os.path.exists(self.reports_file):
            reports_data = {
                'report_id': [],
                'week_start_date': [],
                'week_end_date': [],
                'author_id': [],
                'author_name': [],
                'department': [],
                'title': [],
                'content': [],
                'status': [],  # 작성중/제출완료/승인됨/반려
                'created_date': [],
                'updated_date': [],
                'submitted_date': [],
                'approved_by': [],
                'approved_date': [],
                'rejection_reason': []
            }
            reports_df = pd.DataFrame(reports_data)
            reports_df.to_csv(self.reports_file, index=False, encoding='utf-8-sig')
        
        # 권한 관리 파일 (등록된 사용자만)
        if not os.path.exists(self.permissions_file):
            permissions_data = {
                'permission_id': [],
                'report_id': [],
                'authorized_user_id': [],  # 열람 권한이 있는 사용자 ID
                'authorized_user_name': [],
                'access_level': [],  # 읽기전용/편집가능/승인가능
                'granted_by': [],  # 권한 부여자
                'granted_date': [],
                'is_active': []  # 권한 활성화 여부
            }
            permissions_df = pd.DataFrame(permissions_data)
            permissions_df.to_csv(self.permissions_file, index=False, encoding='utf-8-sig')
    
    def get_current_week_dates(self):
        """현재 주의 시작일과 종료일을 반환합니다."""
        today = datetime.now().date()
        # 월요일을 주의 시작으로 설정
        days_since_monday = today.weekday()
        week_start = today - timedelta(days=days_since_monday)
        week_end = week_start + timedelta(days=6)
        return week_start, week_end
    
    def create_report(self, author_id, author_name, department, title, content):
        """새로운 주간 보고서를 생성합니다."""
        try:
            df = pd.read_csv(self.reports_file, encoding='utf-8-sig')
            
            # 새로운 보고서 ID 생성
            if len(df) > 0:
                last_id = df['report_id'].str.extract('WR(\d+)').astype(int).max().values[0]
                new_id = f"WR{last_id + 1:04d}"
            else:
                new_id = "WR0001"
            
            # 현재 주 날짜 계산
            week_start, week_end = self.get_current_week_dates()
            
            new_report = {
                'report_id': new_id,
                'week_start_date': week_start.strftime('%Y-%m-%d'),
                'week_end_date': week_end.strftime('%Y-%m-%d'),
                'author_id': author_id,
                'author_name': author_name,
                'department': department,
                'title': title,
                'content': content,
                'status': '작성중',
                'created_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'updated_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'submitted_date': '',
                'approved_by': '',
                'approved_date': '',
                'rejection_reason': ''
            }
            
            # DataFrame에 추가
            new_df = pd.DataFrame([new_report])
            df = pd.concat([df, new_df], ignore_index=True)
            
            # CSV 파일에 저장
            df.to_csv(self.reports_file, index=False, encoding='utf-8-sig')
            
            return True, new_id
        except Exception as e:
            print(f"주간 보고서 생성 오류: {e}")
            return False, None
    
    def add_authorized_user(self, report_id, authorized_user_id, authorized_user_name, 
                           access_level="읽기전용", granted_by=""):
        """보고서에 열람 권한이 있는 사용자를 추가합니다."""
        try:
            df = pd.read_csv(self.permissions_file, encoding='utf-8-sig')
            
            # 새로운 권한 ID 생성
            if len(df) > 0:
                last_id = df['permission_id'].str.extract('P(\d+)').astype(int).max().values[0]
                new_id = f"P{last_id + 1:04d}"
            else:
                new_id = "P0001"
            
            # 중복 권한 확인
            existing = df[(df['report_id'] == report_id) & 
                         (df['authorized_user_id'] == authorized_user_id) & 
                         (df['is_active'] == True)]
            
            if not existing.empty:
                return False, "이미 등록된 사용자입니다."
            
            new_permission = {
                'permission_id': new_id,
                'report_id': report_id,
                'authorized_user_id': authorized_user_id,
                'authorized_user_name': authorized_user_name,
                'access_level': access_level,
                'granted_by': granted_by,
                'granted_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'is_active': True
            }
            
            # DataFrame에 추가
            new_df = pd.DataFrame([new_permission])
            df = pd.concat([df, new_df], ignore_index=True)
            
            # CSV 파일에 저장
            df.to_csv(self.permissions_file, index=False, encoding='utf-8-sig')
            
            return True, "권한이 추가되었습니다."
        except Exception as e:
            print(f"권한 추가 오류: {e}")
            return False, "권한 추가에 실패했습니다."
    
    def get_accessible_reports(self, user_id):
        """사용자가 열람 가능한 보고서 목록을 반환합니다."""
        try:
            reports_df = pd.read_csv(self.reports_file, encoding='utf-8-sig')
            permissions_df = pd.read_csv(self.permissions_file, encoding='utf-8-sig')
            
            if reports_df.empty:
                return pd.DataFrame()
            
            # 1. 본인이 작성한 보고서
            my_reports = reports_df[reports_df['author_id'] == user_id]
            
            # 2. 권한이 부여된 보고서
            active_permissions = permissions_df[
                (permissions_df['authorized_user_id'] == user_id) & 
                (permissions_df['is_active'] == True)
            ]
            
            if not active_permissions.empty:
                authorized_report_ids = active_permissions['report_id'].tolist()
                authorized_reports = reports_df[reports_df['report_id'].isin(authorized_report_ids)]
            else:
                authorized_reports = pd.DataFrame()
            
            # 두 결과를 합치고 중복 제거
            if not my_reports.empty and not authorized_reports.empty:
                accessible_reports = pd.concat([my_reports, authorized_reports]).drop_duplicates()
            elif not my_reports.empty:
                accessible_reports = my_reports
            elif not authorized_reports.empty:
                accessible_reports = authorized_reports
            else:
                accessible_reports = pd.DataFrame()
            
            return accessible_reports.sort_values('created_date', ascending=False)
        except Exception as e:
            print(f"접근 가능한 보고서 조회 오류: {e}")
            return pd.DataFrame()
    
    def get_report_permissions(self, report_id):
        """특정 보고서의 권한 목록을 반환합니다."""
        try:
            df = pd.read_csv(self.permissions_file, encoding='utf-8-sig')
            return df[(df['report_id'] == report_id) & (df['is_active'] == True)]
        except Exception as e:
            print(f"권한 조회 오류: {e}")
            return pd.DataFrame()
    
    def remove_user_permission(self, report_id, user_id):
        """사용자의 보고서 열람 권한을 제거합니다."""
        try:
            df = pd.read_csv(self.permissions_file, encoding='utf-8-sig')
            
            # 해당 권한을 비활성화
            mask = (df['report_id'] == report_id) & (df['authorized_user_id'] == user_id)
            df.loc[mask, 'is_active'] = False
            
            # CSV 파일에 저장
            df.to_csv(self.permissions_file, index=False, encoding='utf-8-sig')
            
            return True, "권한이 제거되었습니다."
        except Exception as e:
            print(f"권한 제거 오류: {e}")
            return False, "권한 제거에 실패했습니다."
    
    def update_report_status(self, report_id, new_status, approved_by="", rejection_reason=""):
        """보고서 상태를 업데이트합니다."""
        try:
            df = pd.read_csv(self.reports_file, encoding='utf-8-sig')
            
            if report_id not in df['report_id'].values:
                return False, "보고서를 찾을 수 없습니다."
            
            # 보고서 상태 업데이트
            idx = df[df['report_id'] == report_id].index[0]
            df.at[idx, 'status'] = new_status
            df.at[idx, 'updated_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            if new_status == '제출완료':
                df.at[idx, 'submitted_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            elif new_status == '승인됨':
                df.at[idx, 'approved_by'] = approved_by
                df.at[idx, 'approved_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            elif new_status == '반려':
                df.at[idx, 'rejection_reason'] = rejection_reason
            
            # CSV 파일에 저장
            df.to_csv(self.reports_file, index=False, encoding='utf-8-sig')
            
            return True, "상태가 업데이트되었습니다."
        except Exception as e:
            print(f"상태 업데이트 오류: {e}")
            return False, "상태 업데이트에 실패했습니다."
    
    def get_report_statuses(self):
        """보고서 상태 목록을 반환합니다."""
        return ['작성중', '제출완료', '승인됨', '반려']
    
    def get_access_levels(self):
        """접근 권한 레벨 목록을 반환합니다."""
        return ['읽기전용', '편집가능', '승인가능']
    
    def search_reports(self, user_id, search_term="", status_filter="전체", week_filter="전체"):
        """보고서를 검색합니다."""
        try:
            accessible_reports = self.get_accessible_reports(user_id)
            
            if accessible_reports.empty:
                return accessible_reports
            
            # 검색어 필터링
            if search_term:
                mask = (accessible_reports['title'].str.contains(search_term, case=False, na=False) |
                       accessible_reports['content'].str.contains(search_term, case=False, na=False) |
                       accessible_reports['author_name'].str.contains(search_term, case=False, na=False))
                accessible_reports = accessible_reports[mask]
            
            # 상태 필터링
            if status_filter != "전체":
                accessible_reports = accessible_reports[accessible_reports['status'] == status_filter]
            
            return accessible_reports
        except Exception as e:
            print(f"보고서 검색 오류: {e}")
            return pd.DataFrame()