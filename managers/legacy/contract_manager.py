# -*- coding: utf-8 -*-
"""
계약서 관리 매니저
계약서 등록, 조회, 수정, 삭제 및 만료 알림 기능을 제공합니다.
"""

import pandas as pd
import os
from datetime import datetime, timedelta
import json

class ContractManager:
    def __init__(self):
        """계약서 매니저 초기화"""
        self.data_dir = 'data'
        self.contracts_file = os.path.join(self.data_dir, 'contracts.csv')
        self.ensure_data_directory()
        self.ensure_contracts_file()
    
    def ensure_data_directory(self):
        """데이터 디렉토리가 존재하는지 확인하고 생성"""
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
    
    def ensure_contracts_file(self):
        """계약서 CSV 파일이 존재하는지 확인하고 생성"""
        if not os.path.exists(self.contracts_file):
            # 기본 컬럼으로 빈 DataFrame 생성
            columns = [
                'contract_id', 'contract_name', 'contract_type', 'counterpart_type',
                'counterpart_id', 'counterpart_name', 'start_date', 'end_date',
                'contract_amount', 'currency', 'payment_terms', 'status',
                'responsible_person', 'file_attachments', 'notes',
                'created_date', 'updated_date'
            ]
            df = pd.DataFrame([], columns=columns)
            df.to_csv(self.contracts_file, index=False, encoding='utf-8-sig')
    
    def get_all_contracts(self):
        """모든 계약서 목록을 가져옵니다."""
        try:
            df = pd.read_csv(self.contracts_file, encoding='utf-8-sig')
            if df.empty:
                return pd.DataFrame()
            
            # 날짜 컬럼 변환
            date_columns = ['start_date', 'end_date', 'created_date', 'updated_date']
            for col in date_columns:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
            
            return df
        except Exception as e:
            print(f"계약서 데이터 로드 오류: {e}")
            return pd.DataFrame()
    
    def add_contract(self, contract_data):
        """새로운 계약서를 추가합니다."""
        try:
            df = self.get_all_contracts()
            
            # 새로운 계약서 ID 생성
            if df.empty:
                new_id = "CON001"
            else:
                max_id = df['contract_id'].str.replace('CON', '').astype(int).max()
                new_id = f"CON{max_id + 1:03d}"
            
            # 계약서 데이터 준비
            new_contract = {
                'contract_id': new_id,
                'contract_name': contract_data.get('contract_name', ''),
                'contract_type': contract_data.get('contract_type', ''),
                'counterpart_type': contract_data.get('counterpart_type', ''),
                'counterpart_id': contract_data.get('counterpart_id', ''),
                'counterpart_name': contract_data.get('counterpart_name', ''),
                'start_date': contract_data.get('start_date', ''),
                'end_date': contract_data.get('end_date', ''),
                'contract_amount': contract_data.get('contract_amount', 0),
                'currency': contract_data.get('currency', 'USD'),
                'payment_terms': contract_data.get('payment_terms', ''),
                'status': contract_data.get('status', '진행중'),
                'responsible_person': contract_data.get('responsible_person', ''),
                'file_attachments': contract_data.get('file_attachments', ''),
                'notes': contract_data.get('notes', ''),
                'created_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'updated_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # DataFrame에 추가
            new_df = pd.DataFrame([new_contract])
            df = pd.concat([df, new_df], ignore_index=True)
            
            # CSV 파일에 저장
            df.to_csv(self.contracts_file, index=False, encoding='utf-8-sig')
            
            return True, new_id
        except Exception as e:
            print(f"계약서 추가 오류: {e}")
            return False, None
    
    def update_contract(self, contract_id, updated_data):
        """계약서 정보를 업데이트합니다."""
        try:
            df = self.get_all_contracts()
            
            if contract_id not in df['contract_id'].values:
                return False, "계약서를 찾을 수 없습니다."
            
            # 계약서 업데이트
            idx = df[df['contract_id'] == contract_id].index[0]
            for key, value in updated_data.items():
                if key in df.columns and key != 'contract_id':
                    # NaN 값 처리 및 타입 변환
                    if pd.isna(value) or value == 'nan':
                        value = '' if df[key].dtype == 'object' else 0.0
                    df.at[idx, key] = value
            
            df.at[idx, 'updated_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # CSV 파일에 저장
            df.to_csv(self.contracts_file, index=False, encoding='utf-8-sig')
            
            return True, "계약서가 성공적으로 업데이트되었습니다."
        except Exception as e:
            print(f"계약서 업데이트 오류: {e}")
            return False, f"업데이트 오류: {e}"
    
    def delete_contract(self, contract_id):
        """계약서를 삭제합니다."""
        try:
            df = self.get_all_contracts()
            
            if contract_id not in df['contract_id'].values:
                return False, "계약서를 찾을 수 없습니다."
            
            # 계약서 삭제
            df = df[df['contract_id'] != contract_id]
            
            # CSV 파일에 저장
            df.to_csv(self.contracts_file, index=False, encoding='utf-8-sig')
            
            return True, "계약서가 성공적으로 삭제되었습니다."
        except Exception as e:
            print(f"계약서 삭제 오류: {e}")
            return False, f"삭제 오류: {e}"
    
    def get_contract_by_id(self, contract_id):
        """계약서 ID로 특정 계약서를 조회합니다."""
        try:
            df = self.get_all_contracts()
            
            if contract_id not in df['contract_id'].values:
                return None
            
            return df[df['contract_id'] == contract_id].iloc[0].to_dict()
        except Exception as e:
            print(f"계약서 조회 오류: {e}")
            return None
    
    def get_expiring_contracts(self, days_ahead=30):
        """만료 예정 계약서 목록을 가져옵니다."""
        try:
            df = self.get_all_contracts()
            
            if df.empty:
                return pd.DataFrame()
            
            # 활성 계약서만 필터링
            active_contracts = df[df['status'].isin(['진행중', '활성'])]
            
            # 만료 날짜 확인
            today = datetime.now()
            expiry_date = today + timedelta(days=days_ahead)
            
            expiring = active_contracts[
                (active_contracts['end_date'] >= today) & 
                (active_contracts['end_date'] <= expiry_date)
            ]
            
            return expiring
        except Exception as e:
            print(f"만료 예정 계약서 조회 오류: {e}")
            return pd.DataFrame()
    
    def get_contract_statistics(self):
        """계약서 통계를 생성합니다."""
        try:
            df = self.get_all_contracts()
            
            if df.empty:
                return {
                    'total_contracts': 0,
                    'active_contracts': 0,
                    'expired_contracts': 0,
                    'total_amount': 0,
                    'contracts_by_type': {},
                    'contracts_by_status': {}
                }
            
            today = datetime.now()
            
            # 기본 통계
            total_contracts = len(df)
            active_contracts = len(df[df['status'].isin(['진행중', '활성'])])
            expired_contracts = len(df[df['end_date'] < today])
            
            # 계약 금액 합계
            total_amount = df['contract_amount'].sum()
            
            # 계약 유형별 통계
            contracts_by_type = df['contract_type'].value_counts().to_dict()
            
            # 계약 상태별 통계
            contracts_by_status = df['status'].value_counts().to_dict()
            
            return {
                'total_contracts': total_contracts,
                'active_contracts': active_contracts,
                'expired_contracts': expired_contracts,
                'total_amount': total_amount,
                'contracts_by_type': contracts_by_type,
                'contracts_by_status': contracts_by_status
            }
        except Exception as e:
            print(f"계약서 통계 생성 오류: {e}")
            return {}
    
    def search_contracts(self, search_term, search_type='all'):
        """계약서를 검색합니다."""
        try:
            df = self.get_all_contracts()
            
            if df.empty or not search_term:
                return df
            
            search_term = str(search_term).lower()
            
            if search_type == 'all':
                # 모든 텍스트 컬럼에서 검색
                text_columns = ['contract_name', 'counterpart_name', 'notes']
                mask = pd.Series([False] * len(df))
                
                for col in text_columns:
                    if col in df.columns:
                        mask |= df[col].astype(str).str.lower().str.contains(search_term, na=False)
                
                return df[mask]
            else:
                # 특정 컬럼에서 검색
                if search_type in df.columns:
                    mask = df[search_type].astype(str).str.lower().str.contains(search_term, na=False)
                    return df[mask]
                else:
                    return df
        except Exception as e:
            print(f"계약서 검색 오류: {e}")
            return pd.DataFrame()
    
    def get_contract_types(self):
        """계약 유형 목록을 반환합니다."""
        return [
            '공급계약', '서비스계약', '임대계약', '고용계약', 
            '유지보수계약', '라이선스계약', '파트너십계약', '기타'
        ]
    
    def get_contract_statuses(self):
        """계약 상태 목록을 반환합니다."""
        return ["준비중", "진행중", "일시정지", "만료", "해지", "완료"]
    
    def get_allowed_status_transitions(self, current_status):
        """현재 상태에서 전환 가능한 상태 목록을 반환합니다."""
        transitions = {
            '준비중': ['진행중', '해지'],
            '진행중': ['일시정지', '완료', '해지', '만료'],
            '일시정지': ['진행중', '해지'],
            '만료': ['진행중', '완료'],  # 연장 또는 완료 처리 시
            '해지': [],  # 최종 상태 - 변경 불가
            '완료': []   # 최종 상태 - 변경 불가
        }
        return transitions.get(current_status, [])
    
    def update_contract_status(self, contract_id, new_status, reason="", updated_by=""):
        """계약서 상태를 업데이트합니다."""
        try:
            df = self.get_all_contracts()
            
            # 계약서 찾기
            contract_idx = df[df['contract_id'] == contract_id].index
            if len(contract_idx) == 0:
                return False, "계약서를 찾을 수 없습니다."
            
            # 현재 상태 확인
            current_status = df.loc[contract_idx[0], 'status']
            
            # 상태 전환 가능한지 확인
            allowed_statuses = self.get_allowed_status_transitions(current_status)
            if new_status not in allowed_statuses and current_status != new_status:
                return False, f"'{current_status}'에서 '{new_status}'로 변경할 수 없습니다."
            
            # 상태 업데이트
            df.loc[contract_idx[0], 'status'] = new_status
            df.loc[contract_idx[0], 'updated_date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 상태 변경 메모 추가
            if reason:
                current_notes = df.loc[contract_idx[0], 'notes']
                status_note = f"[{datetime.now().strftime('%Y-%m-%d')}] 상태변경: {current_status} → {new_status} ({reason})"
                if pd.isna(current_notes) or current_notes == "":
                    df.loc[contract_idx[0], 'notes'] = status_note
                else:
                    df.loc[contract_idx[0], 'notes'] = current_notes + "\n" + status_note
            
            # CSV 파일에 저장
            df.to_csv(self.contracts_file, index=False, encoding='utf-8-sig')
            
            # 상태 변경 히스토리 기록
            self._record_status_history(contract_id, current_status, new_status, reason, updated_by)
            
            return True, f"계약서 상태가 '{new_status}'로 변경되었습니다."
            
        except Exception as e:
            print(f"계약서 상태 업데이트 오류: {e}")
            return False, f"상태 업데이트 중 오류 발생: {e}"
    
    def _record_status_history(self, contract_id, old_status, new_status, reason, updated_by):
        """상태 변경 히스토리를 기록합니다."""
        try:
            history_file = os.path.join(self.data_dir, 'contract_status_history.csv')
            
            # 히스토리 파일이 없으면 생성
            if not os.path.exists(history_file):
                history_df = pd.DataFrame(columns=[
                    'contract_id', 'old_status', 'new_status', 'reason', 
                    'updated_by', 'update_date'
                ])
                history_df.to_csv(history_file, index=False, encoding='utf-8-sig')
            else:
                history_df = pd.read_csv(history_file, encoding='utf-8-sig')
            
            # 새 히스토리 레코드 추가
            new_record = pd.DataFrame([{
                'contract_id': contract_id,
                'old_status': old_status,
                'new_status': new_status,
                'reason': reason,
                'updated_by': updated_by,
                'update_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }])
            
            history_df = pd.concat([history_df, new_record], ignore_index=True)
            history_df.to_csv(history_file, index=False, encoding='utf-8-sig')
            
        except Exception as e:
            print(f"상태 히스토리 기록 오류: {e}")
    
    def get_status_history(self, contract_id=None):
        """상태 변경 히스토리를 조회합니다."""
        try:
            history_file = os.path.join(self.data_dir, 'contract_status_history.csv')
            
            if not os.path.exists(history_file):
                return pd.DataFrame()
            
            history_df = pd.read_csv(history_file, encoding='utf-8-sig')
            
            if contract_id:
                return history_df[history_df['contract_id'] == contract_id]
            
            return history_df
            
        except Exception as e:
            print(f"상태 히스토리 조회 오류: {e}")
            return pd.DataFrame()
    
    def get_currency_options(self):
        """통화 옵션을 반환합니다."""
        return ['USD', 'EUR', 'KRW', 'VND', 'JPY', 'CNY']