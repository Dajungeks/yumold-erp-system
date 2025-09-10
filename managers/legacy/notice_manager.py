"""
게시판 관리자 - 마스터/대표용 공지사항과 직원용 게시판을 관리합니다.
"""
import pandas as pd
import os
from datetime import datetime
import json

class NoticeManager:
    def __init__(self, data_path="data"):
        self.data_path = data_path
        self.notices_file = os.path.join(data_path, "notices.csv")
        self.employee_posts_file = os.path.join(data_path, "employee_posts.csv")
        
        # 데이터 디렉토리 생성
        if not os.path.exists(data_path):
            os.makedirs(data_path)
        
        # CSV 파일 초기화
        self._initialize_files()
    
    def _initialize_files(self):
        """CSV 파일들을 초기화합니다."""
        # 공지사항 파일 (마스터/대표용)
        if not os.path.exists(self.notices_file):
            notices_data = {
                'notice_id': [],
                'title': [],
                'content': [],
                'author_id': [],
                'author_name': [],
                'created_date': [],
                'updated_date': [],
                'is_important': [],
                'category': [],
                'target_audience': [],
                'status': []
            }
            notices_df = pd.DataFrame(notices_data)
            notices_df.to_csv(self.notices_file, index=False, encoding='utf-8-sig')
        
        # 직원 게시판 파일
        if not os.path.exists(self.employee_posts_file):
            employee_posts_data = {
                'post_id': [],
                'title': [],
                'content': [],
                'author_id': [],
                'author_name': [],
                'created_date': [],
                'updated_date': [],
                'category': [],
                'likes': [],
                'comments_count': [],
                'status': [],
                'visible_to': []  # 특정 사용자에게만 보이는 게시글
            }
            employee_posts_df = pd.DataFrame(employee_posts_data)
            employee_posts_df.to_csv(self.employee_posts_file, index=False, encoding='utf-8-sig')
    
    def create_notice(self, title, content, author_id, author_name, is_important=False, 
                     category="일반", target_audience="전체"):
        """새로운 공지사항을 생성합니다."""
        try:
            df = pd.read_csv(self.notices_file, encoding='utf-8-sig')
            
            # 새로운 공지사항 ID 생성
            if len(df) > 0:
                last_id = df['notice_id'].str.extract('N(\d+)').astype(int).max().values[0]
                new_id = f"N{last_id + 1:05d}"
            else:
                new_id = "N00001"
            
            new_notice = {
                'notice_id': new_id,
                'title': title,
                'content': content,
                'author_id': author_id,
                'author_name': author_name,
                'created_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'updated_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'is_important': is_important,
                'category': category,
                'target_audience': target_audience,
                'status': 'active'
            }
            
            df = pd.concat([df, pd.DataFrame([new_notice])], ignore_index=True)
            df.to_csv(self.notices_file, index=False, encoding='utf-8-sig')
            
            return True, new_id
        except Exception as e:
            print(f"공지사항 생성 중 오류: {e}")
            return False, None
    
    def create_employee_post(self, title, content, author_id, author_name, category="자유게시판", visible_to="전체"):
        """새로운 직원 게시글을 생성합니다."""
        try:
            df = pd.read_csv(self.employee_posts_file, encoding='utf-8-sig')
            
            # 새로운 게시글 ID 생성
            if len(df) > 0:
                last_id = df['post_id'].str.extract('P(\d+)').astype(int).max().values[0]
                new_id = f"P{last_id + 1:05d}"
            else:
                new_id = "P00001"
            
            new_post = {
                'post_id': new_id,
                'title': title,
                'content': content,
                'author_id': author_id,
                'author_name': author_name,
                'created_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'updated_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'category': category,
                'likes': 0,
                'comments_count': 0,
                'status': 'active',
                'visible_to': visible_to
            }
            
            df = pd.concat([df, pd.DataFrame([new_post])], ignore_index=True)
            df.to_csv(self.employee_posts_file, index=False, encoding='utf-8-sig')
            
            return True, new_id
        except Exception as e:
            print(f"직원 게시글 생성 중 오류: {e}")
            return False, None
    
    def get_all_notices(self):
        """모든 공지사항을 가져옵니다."""
        try:
            df = pd.read_csv(self.notices_file, encoding='utf-8-sig')
            return df.to_dict('records')
        except Exception as e:
            print(f"공지사항 목록 조회 중 오류: {e}")
            return []
    
    def get_all_employee_posts(self):
        """모든 직원 게시글을 가져옵니다."""
        try:
            df = pd.read_csv(self.employee_posts_file, encoding='utf-8-sig')
            return df.to_dict('records')
        except Exception as e:
            print(f"직원 게시글 목록 조회 중 오류: {e}")
            return []
    
    def get_notice_by_id(self, notice_id):
        """특정 공지사항을 조회합니다."""
        try:
            df = pd.read_csv(self.notices_file, encoding='utf-8-sig')
            notice = df[df['notice_id'] == notice_id]
            if len(notice) > 0:
                return notice.iloc[0].to_dict()
            return None
        except Exception as e:
            print(f"공지사항 조회 중 오류: {e}")
            return None
    
    def get_employee_post_by_id(self, post_id):
        """특정 직원 게시글을 조회합니다."""
        try:
            df = pd.read_csv(self.employee_posts_file, encoding='utf-8-sig')
            post = df[df['post_id'] == post_id]
            if len(post) > 0:
                return post.iloc[0].to_dict()
            return None
        except Exception as e:
            print(f"직원 게시글 조회 중 오류: {e}")
            return None
    
    def update_notice(self, notice_id, title=None, content=None, is_important=None, 
                     category=None, target_audience=None):
        """공지사항을 수정합니다."""
        try:
            df = pd.read_csv(self.notices_file, encoding='utf-8-sig')
            idx = df[df['notice_id'] == notice_id].index
            
            if len(idx) == 0:
                return False
            
            idx = idx[0]
            if title is not None:
                df.at[idx, 'title'] = title
            if content is not None:
                df.at[idx, 'content'] = content
            if is_important is not None:
                df.at[idx, 'is_important'] = is_important
            if category is not None:
                df.at[idx, 'category'] = category
            if target_audience is not None:
                df.at[idx, 'target_audience'] = target_audience
            
            df.at[idx, 'updated_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            df.to_csv(self.notices_file, index=False, encoding='utf-8-sig')
            return True
        except Exception as e:
            print(f"공지사항 수정 중 오류: {e}")
            return False
    
    def update_employee_post(self, post_id, title=None, content=None, category=None):
        """직원 게시글을 수정합니다."""
        try:
            df = pd.read_csv(self.employee_posts_file, encoding='utf-8-sig')
            idx = df[df['post_id'] == post_id].index
            
            if len(idx) == 0:
                return False
            
            idx = idx[0]
            if title is not None:
                df.at[idx, 'title'] = title
            if content is not None:
                df.at[idx, 'content'] = content
            if category is not None:
                df.at[idx, 'category'] = category
            
            df.at[idx, 'updated_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            df.to_csv(self.employee_posts_file, index=False, encoding='utf-8-sig')
            return True
        except Exception as e:
            print(f"직원 게시글 수정 중 오류: {e}")
            return False
    
    def delete_notice(self, notice_id):
        """공지사항을 삭제합니다."""
        try:
            df = pd.read_csv(self.notices_file, encoding='utf-8-sig')
            df = df[df['notice_id'] != notice_id]
            df.to_csv(self.notices_file, index=False, encoding='utf-8-sig')
            return True
        except Exception as e:
            print(f"공지사항 삭제 중 오류: {e}")
            return False
    
    def delete_employee_post(self, post_id):
        """직원 게시글을 삭제합니다."""
        try:
            df = pd.read_csv(self.employee_posts_file, encoding='utf-8-sig')
            df = df[df['post_id'] != post_id]
            df.to_csv(self.employee_posts_file, index=False, encoding='utf-8-sig')
            return True
        except Exception as e:
            print(f"직원 게시글 삭제 중 오류: {e}")
            return False
    
    def get_notice_categories(self):
        """공지사항 카테고리 목록을 반환합니다."""
        return ["일반", "긴급", "인사", "업무", "시스템", "기타"]
    
    def get_employee_post_categories(self):
        """직원 게시판 카테고리 목록을 반환합니다."""
        return ["자유게시판", "질문/답변", "건의사항", "정보공유", "기타"]
    
    def get_target_audiences(self):
        """공지사항 대상 목록을 반환합니다."""
        return ["전체", "임원진", "관리자", "영업팀", "기술팀", "고객서비스팀"]