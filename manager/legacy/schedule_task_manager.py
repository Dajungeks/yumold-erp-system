"""
총무 일정 관리 시스템
- 외국인 비자 관리
- 자동차 점검 및 신고 관리  
- 기타 주기적 업무 관리
"""

import pandas as pd
import os
from datetime import datetime, timedelta
import uuid

class ScheduleTaskManager:
    def __init__(self):
        self.data_dir = "data"
        self.tasks_file = os.path.join(self.data_dir, "schedule_tasks.csv")
        self.categories_file = os.path.join(self.data_dir, "task_categories.csv")
        
        # 데이터 디렉토리 생성
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
        
        # 기본 카테고리 설정
        self.default_categories = [
            {
                'category_id': 'VISA',
                'category_name': '비자 관리',
                'description': '외국인 직원 비자 신청, 갱신, 연장 등',
                'default_interval_days': 365,
                'notification_days': [30, 14, 7, 1]
            },
            {
                'category_id': 'VEHICLE',
                'category_name': '자동차 관리',
                'description': '자동차 검사, 보험 갱신, 등록 등',
                'default_interval_days': 365,
                'notification_days': [60, 30, 14, 7]
            },
            {
                'category_id': 'LICENSE',
                'category_name': '인허가 관리',
                'description': '사업자등록, 각종 면허 갱신',
                'default_interval_days': 365,
                'notification_days': [90, 30, 14, 7]
            },
            {
                'category_id': 'INSURANCE',
                'category_name': '보험 관리',
                'description': '각종 보험 가입 및 갱신',
                'default_interval_days': 365,
                'notification_days': [60, 30, 14, 7]
            },
            {
                'category_id': 'CONTRACT',
                'category_name': '계약 관리',
                'description': '임대료, 유지보수 계약 등',
                'default_interval_days': 365,
                'notification_days': [30, 14, 7]
            },
            {
                'category_id': 'MAINTENANCE',
                'category_name': '정기 점검',
                'description': '시설, 장비 정기 점검 및 유지보수',
                'default_interval_days': 90,
                'notification_days': [14, 7, 3, 1]
            }
        ]
        
        self.task_statuses = ['예정', '진행중', '완료', '연기', '취소']
        self.priority_levels = ['낮음', '보통', '높음', '긴급']
        
        self._initialize_files()
    
    def _initialize_files(self):
        """CSV 파일 초기화"""
        try:
            # 카테고리 파일 초기화
            if not os.path.exists(self.categories_file):
                categories_df = pd.DataFrame(self.default_categories)
                categories_df.to_csv(self.categories_file, index=False, encoding='utf-8-sig')
            
            # 일정 작업 파일 초기화
            if not os.path.exists(self.tasks_file):
                columns = [
                    'task_id', 'task_title', 'category_id', 'description',
                    'assigned_person', 'responsible_department', 'priority',
                    'due_date', 'completion_date', 'status',
                    'next_due_date', 'interval_days', 'is_recurring',
                    'notification_sent', 'notes', 'documents',
                    'created_date', 'updated_date', 'created_by'
                ]
                empty_df = pd.DataFrame(columns=columns)
                empty_df.to_csv(self.tasks_file, index=False, encoding='utf-8-sig')
                
        except Exception as e:
            print(f"파일 초기화 오류: {e}")
    
    def add_task(self, task_data):
        """새로운 일정 작업 추가"""
        try:
            df = pd.read_csv(self.tasks_file, encoding='utf-8-sig')
            
            task_id = f"TASK_{datetime.now().strftime('%Y%m%d')}_{str(uuid.uuid4())[:8].upper()}"
            
            new_task = {
                'task_id': task_id,
                'task_title': task_data.get('task_title', ''),
                'category_id': task_data.get('category_id', ''),
                'description': task_data.get('description', ''),
                'assigned_person': task_data.get('assigned_person', ''),
                'responsible_department': task_data.get('responsible_department', ''),
                'priority': task_data.get('priority', '보통'),
                'due_date': task_data.get('due_date', ''),
                'completion_date': '',
                'status': '예정',
                'next_due_date': task_data.get('next_due_date', '') if task_data.get('is_recurring') else '',
                'interval_days': task_data.get('interval_days', 0),
                'is_recurring': task_data.get('is_recurring', False),
                'notification_sent': False,
                'notes': task_data.get('notes', ''),
                'documents': task_data.get('documents', ''),
                'created_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'updated_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'created_by': task_data.get('created_by', '')
            }
            
            new_df = pd.DataFrame([new_task])
            df = pd.concat([df, new_df], ignore_index=True)
            
            df.to_csv(self.tasks_file, index=False, encoding='utf-8-sig')
            
            return True, task_id
            
        except Exception as e:
            print(f"작업 추가 오류: {e}")
            return False, None
    
    def get_all_tasks(self):
        """모든 일정 작업 조회"""
        try:
            return pd.read_csv(self.tasks_file, encoding='utf-8-sig')
        except FileNotFoundError:
            return pd.DataFrame()
        except Exception as e:
            print(f"작업 조회 오류: {e}")
            return pd.DataFrame()
    
    def get_tasks_by_category(self, category_id):
        """카테고리별 작업 조회"""
        try:
            df = self.get_all_tasks()
            if df.empty:
                return df
            return df[df['category_id'] == category_id]
        except Exception as e:
            print(f"카테고리별 작업 조회 오류: {e}")
            return pd.DataFrame()
    
    def get_upcoming_tasks(self, days_ahead=30):
        """임박한 작업 조회"""
        try:
            df = self.get_all_tasks()
            if df.empty:
                return df
            
            today = datetime.now().date()
            future_date = today + timedelta(days=days_ahead)
            
            df['due_date'] = pd.to_datetime(df['due_date']).dt.date
            
            upcoming = df[
                (df['due_date'] >= today) & 
                (df['due_date'] <= future_date) &
                (df['status'].isin(['예정', '진행중']))
            ]
            
            return upcoming.sort_values('due_date')
            
        except Exception as e:
            print(f"임박한 작업 조회 오류: {e}")
            return pd.DataFrame()
    
    def get_overdue_tasks(self):
        """연체된 작업 조회"""
        try:
            df = self.get_all_tasks()
            if df.empty:
                return df
            
            today = datetime.now().date()
            df['due_date'] = pd.to_datetime(df['due_date']).dt.date
            
            overdue = df[
                (df['due_date'] < today) & 
                (df['status'].isin(['예정', '진행중']))
            ]
            
            return overdue.sort_values('due_date')
            
        except Exception as e:
            print(f"연체 작업 조회 오류: {e}")
            return pd.DataFrame()
    
    def update_task_status(self, task_id, status, notes=None, completion_date=None):
        """작업 상태 업데이트"""
        try:
            df = pd.read_csv(self.tasks_file, encoding='utf-8-sig')
            
            if task_id not in df['task_id'].values:
                return False, "작업을 찾을 수 없습니다."
            
            idx = df[df['task_id'] == task_id].index[0]
            df.at[idx, 'status'] = status
            df.at[idx, 'updated_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            if notes:
                df.at[idx, 'notes'] = notes
            
            if completion_date:
                df.at[idx, 'completion_date'] = completion_date
            
            # 완료된 반복 작업인 경우 다음 일정 생성
            if status == '완료' and df.at[idx, 'is_recurring'] and df.at[idx, 'interval_days'] > 0:
                self._create_next_recurring_task(df.iloc[idx])
            
            df.to_csv(self.tasks_file, index=False, encoding='utf-8-sig')
            
            return True, "작업 상태가 업데이트되었습니다."
            
        except Exception as e:
            print(f"작업 상태 업데이트 오류: {e}")
            return False, f"업데이트 오류: {e}"
    
    def _create_next_recurring_task(self, completed_task):
        """반복 작업의 다음 일정 생성"""
        try:
            next_due_date = datetime.strptime(completed_task['due_date'], '%Y-%m-%d').date()
            next_due_date += timedelta(days=int(completed_task['interval_days']))
            
            next_task_data = {
                'task_title': completed_task['task_title'],
                'category_id': completed_task['category_id'],
                'description': completed_task['description'],
                'assigned_person': completed_task['assigned_person'],
                'responsible_department': completed_task['responsible_department'],
                'priority': completed_task['priority'],
                'due_date': next_due_date.strftime('%Y-%m-%d'),
                'interval_days': completed_task['interval_days'],
                'is_recurring': True,
                'notes': f"이전 작업({completed_task['task_id']})에서 자동 생성됨",
                'created_by': completed_task['created_by']
            }
            
            return self.add_task(next_task_data)
            
        except Exception as e:
            print(f"반복 작업 생성 오류: {e}")
            return False, None
    
    def get_categories(self):
        """카테고리 목록 조회"""
        try:
            return pd.read_csv(self.categories_file, encoding='utf-8-sig')
        except FileNotFoundError:
            return pd.DataFrame(self.default_categories)
        except Exception as e:
            print(f"카테고리 조회 오류: {e}")
            return pd.DataFrame()
    
    def get_task_statistics(self):
        """작업 통계 조회"""
        try:
            df = self.get_all_tasks()
            if df.empty:
                return {}
            
            today = datetime.now().date()
            df['due_date'] = pd.to_datetime(df['due_date']).dt.date
            
            stats = {
                'total_tasks': len(df),
                'pending_tasks': len(df[df['status'] == '예정']),
                'in_progress_tasks': len(df[df['status'] == '진행중']),
                'completed_tasks': len(df[df['status'] == '완료']),
                'overdue_tasks': len(df[(df['due_date'] < today) & (df['status'].isin(['예정', '진행중']))]),
                'upcoming_tasks': len(df[(df['due_date'] >= today) & (df['due_date'] <= today + timedelta(days=30))]),
                'by_category': df.groupby('category_id').size().to_dict(),
                'by_priority': df.groupby('priority').size().to_dict(),
                'by_status': df.groupby('status').size().to_dict()
            }
            
            return stats
            
        except Exception as e:
            print(f"통계 조회 오류: {e}")
            return {}
    
    def get_task_statuses(self):
        """작업 상태 목록 반환"""
        return self.task_statuses
    
    def get_priority_levels(self):
        """우선순위 레벨 목록 반환"""
        return self.priority_levels
    
    def add_category(self, category_data):
        """새로운 카테고리 추가"""
        try:
            categories_df = pd.read_csv(self.categories_file, encoding='utf-8-sig')
            
            # 중복 ID 확인
            if category_data['category_id'] in categories_df['category_id'].values:
                return False, f"카테고리 ID '{category_data['category_id']}'가 이미 존재합니다."
            
            # 새 카테고리 추가
            new_category = pd.DataFrame([category_data])
            categories_df = pd.concat([categories_df, new_category], ignore_index=True)
            
            # CSV 파일에 저장
            categories_df.to_csv(self.categories_file, index=False, encoding='utf-8-sig')
            
            return True, f"카테고리 '{category_data['category_name']}'가 성공적으로 추가되었습니다."
            
        except Exception as e:
            print(f"카테고리 추가 오류: {e}")
            return False, f"카테고리 추가 중 오류 발생: {e}"
    
    def update_category(self, category_id, updated_data):
        """카테고리 정보 업데이트"""
        try:
            categories_df = pd.read_csv(self.categories_file, encoding='utf-8-sig')
            
            # 카테고리 찾기
            category_idx = categories_df[categories_df['category_id'] == category_id].index
            if len(category_idx) == 0:
                return False, "카테고리를 찾을 수 없습니다."
            
            # 데이터 업데이트
            for key, value in updated_data.items():
                categories_df.loc[category_idx[0], key] = value
            
            # CSV 파일에 저장
            categories_df.to_csv(self.categories_file, index=False, encoding='utf-8-sig')
            
            return True, f"카테고리 '{updated_data['category_name']}'가 성공적으로 수정되었습니다."
            
        except Exception as e:
            print(f"카테고리 수정 오류: {e}")
            return False, f"카테고리 수정 중 오류 발생: {e}"
    
    def delete_category(self, category_id):
        """카테고리 삭제"""
        try:
            # 해당 카테고리를 사용하는 작업이 있는지 확인
            tasks_df = self.get_all_tasks()
            if not tasks_df.empty:
                related_tasks = tasks_df[tasks_df['category_id'] == category_id]
                if not related_tasks.empty:
                    return False, f"이 카테고리를 사용하는 {len(related_tasks)}개의 작업이 있어 삭제할 수 없습니다."
            
            # 기본 카테고리인지 확인 (삭제 방지)
            default_category_ids = [cat['category_id'] for cat in self.default_categories]
            if category_id in default_category_ids:
                return False, "기본 카테고리는 삭제할 수 없습니다."
            
            categories_df = pd.read_csv(self.categories_file, encoding='utf-8-sig')
            
            # 카테고리 찾기 및 삭제
            category_idx = categories_df[categories_df['category_id'] == category_id].index
            if len(category_idx) == 0:
                return False, "카테고리를 찾을 수 없습니다."
            
            category_name = categories_df.loc[category_idx[0], 'category_name']
            categories_df = categories_df.drop(category_idx)
            
            # CSV 파일에 저장
            categories_df.to_csv(self.categories_file, index=False, encoding='utf-8-sig')
            
            return True, f"카테고리 '{category_name}'가 성공적으로 삭제되었습니다."
            
        except Exception as e:
            print(f"카테고리 삭제 오류: {e}")
            return False, f"카테고리 삭제 중 오류 발생: {e}"