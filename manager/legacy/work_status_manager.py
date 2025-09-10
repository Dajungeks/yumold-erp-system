import pandas as pd
import os
from datetime import datetime
import json

class WorkStatusManager:
    def __init__(self):
        self.data_dir = "data"
        self.work_status_file = os.path.join(self.data_dir, "work_status_board.csv")
        self.ensure_data_dir()
        self.ensure_work_status_file()
    
    def ensure_data_dir(self):
        """데이터 디렉토리 확인 및 생성"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def ensure_work_status_file(self):
        """업무 상태 파일 확인 및 생성"""
        if not os.path.exists(self.work_status_file):
            df = pd.DataFrame(columns=[
                'status_id', 'title', 'description', 'status', 
                'priority', 'assigned_to', 'created_by', 'created_date', 
                'updated_date', 'due_date', 'progress', 'category', 'tags', 'comments'
            ])
            df.to_csv(self.work_status_file, index=False, encoding='utf-8-sig')
    
    def generate_status_id(self):
        """새로운 상태 ID 생성"""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return f"WS{timestamp}"
    
    def create_work_status(self, title, description, status="진행중", 
                          priority="보통", assigned_to="", created_by="", 
                          due_date="", category="일반", tags="", progress=0):
        """새로운 업무 상태 생성"""
        try:
            df = pd.read_csv(self.work_status_file, encoding='utf-8-sig')
            
            new_status = {
                'status_id': self.generate_status_id(),
                'title': title,
                'description': description,
                'status': status,
                'priority': priority,
                'assigned_to': assigned_to,
                'created_by': created_by,
                'created_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'updated_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'due_date': due_date,
                'progress': progress,
                'category': category,
                'tags': tags,
                'comments': '[]'
            }
            
            # DataFrame에 새 행 추가
            df = pd.concat([df, pd.DataFrame([new_status])], ignore_index=True)
            df.to_csv(self.work_status_file, index=False, encoding='utf-8-sig')
            
            return True, "업무 상태가 성공적으로 생성되었습니다."
            
        except Exception as e:
            return False, f"업무 상태 생성 오류: {str(e)}"
    
    def get_all_work_status(self):
        """모든 업무 상태 조회"""
        try:
            if os.path.exists(self.work_status_file):
                df = pd.read_csv(self.work_status_file, encoding='utf-8-sig')
                return df.to_dict('records')
            return []
        except Exception as e:
            print(f"업무 상태 조회 오류: {e}")
            return []
    
    def get_work_status_by_id(self, status_id):
        """특정 상태 ID의 업무 상태 조회"""
        try:
            df = pd.read_csv(self.work_status_file, encoding='utf-8-sig')
            filtered_df = df[df['status_id'] == status_id]
            if not filtered_df.empty:
                return filtered_df.iloc[0].to_dict()
            return None
        except Exception as e:
            return None
    
    def update_work_status(self, update_data):
        """업무 상태 업데이트"""
        try:
            df = pd.read_csv(self.work_status_file, encoding='utf-8-sig')
            
            status_id = update_data.get('status_id')
            if not status_id:
                return False, "상태 ID가 필요합니다."
            
            # 해당 상태 찾기
            mask = df['status_id'] == status_id
            if not mask.any():
                return False, "해당 업무 상태를 찾을 수 없습니다."
            
            # 업데이트 적용
            for key, value in update_data.items():
                if key in df.columns and key != 'status_id':
                    df.loc[mask, key] = value
            
            # 업데이트 시간 갱신
            df.loc[mask, 'updated_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            df.to_csv(self.work_status_file, index=False, encoding='utf-8-sig')
            return True, "업무 상태가 업데이트되었습니다."
            
        except Exception as e:
            return False, f"업무 상태 업데이트 오류: {str(e)}"
    
    def delete_work_status(self, status_id):
        """업무 상태 삭제"""
        try:
            df = pd.read_csv(self.work_status_file, encoding='utf-8-sig')
            
            # 해당 상태 제거
            df = df[df['status_id'] != status_id]
            df.to_csv(self.work_status_file, index=False, encoding='utf-8-sig')
            
            return True, "업무 상태가 삭제되었습니다."
            
        except Exception as e:
            return False, f"업무 상태 삭제 오류: {str(e)}"
    
    def add_comment(self, status_id, comment, author):
        """업무 상태에 댓글 추가"""
        try:
            df = pd.read_csv(self.work_status_file, encoding='utf-8-sig')
            
            # 해당 상태 찾기
            mask = df['status_id'] == status_id
            if not mask.any():
                return False, "해당 업무 상태를 찾을 수 없습니다."
            
            # 기존 댓글 가져오기
            current_comments = df.loc[mask, 'comments'].iloc[0]
            try:
                comments_list = json.loads(current_comments) if current_comments else []
            except:
                comments_list = []
            
            # 새 댓글 추가
            new_comment = {
                'author': author,
                'comment': comment,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            comments_list.append(new_comment)
            
            # 댓글 업데이트
            df.loc[mask, 'comments'] = json.dumps(comments_list, ensure_ascii=False)
            df.loc[mask, 'updated_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            df.to_csv(self.work_status_file, index=False, encoding='utf-8-sig')
            return True, "댓글이 추가되었습니다."
            
        except Exception as e:
            return False, f"댓글 추가 오류: {str(e)}"
    
    def get_status_by_priority(self, priority):
        """우선순위별 업무 상태 조회"""
        try:
            df = pd.read_csv(self.work_status_file, encoding='utf-8-sig')
            filtered_df = df[df['priority'] == priority]
            return filtered_df.to_dict('records')
        except Exception as e:
            return []
    
    def get_status_by_assignee(self, assigned_to):
        """담당자별 업무 상태 조회"""
        try:
            df = pd.read_csv(self.work_status_file, encoding='utf-8-sig')
            filtered_df = df[df['assigned_to'] == assigned_to]
            return filtered_df.to_dict('records')
        except Exception as e:
            return []