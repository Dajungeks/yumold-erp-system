# -*- coding: utf-8 -*-
"""
수동 환율 관리 시스템
한국은행 기준 환율을 수동으로 입력하고 관리합니다.
"""

import pandas as pd
import os
from datetime import datetime, timedelta

class ManualExchangeRateManager:
    def __init__(self):
        self.data_file = 'data/manual_exchange_rates.csv'
        self.ensure_data_file()
        
        # 지원 통화 정의 (한국은행 기준)
        self.supported_currencies = {
            'KRW': {'name': '대한민국 원', 'average_rate': 1300.0},
            'CNY': {'name': '중국 위안', 'average_rate': 7.2},
            'VND': {'name': '베트남 동', 'average_rate': 24000.0},
            'THB': {'name': '태국 바트', 'average_rate': 35.0},
            'IDR': {'name': '인도네시아 루피아', 'average_rate': 15500.0}
        }
    
    def ensure_data_file(self):
        """데이터 파일이 존재하는지 확인하고 없으면 생성합니다."""
        os.makedirs('data', exist_ok=True)
        if not os.path.exists(self.data_file):
            df = pd.DataFrame(columns=[
                'rate_id', 'currency_code', 'currency_name', 'rate',
                'base_currency', 'rate_date', 'source', 'input_date', 
                'updated_date', 'input_by'
            ])
            df.to_csv(self.data_file, index=False, encoding='utf-8-sig')
    
    def validate_rate(self, currency_code, rate):
        """입력된 환율이 평균 환율 대비 5% 이내인지 검증합니다."""
        if currency_code not in self.supported_currencies:
            return False, f"지원하지 않는 통화입니다: {currency_code}"
        
        average_rate = self.supported_currencies[currency_code]['average_rate']
        rate_float = float(rate)
        
        # 5% 편차 계산
        lower_bound = average_rate * 0.95
        upper_bound = average_rate * 1.05
        
        if rate_float < lower_bound or rate_float > upper_bound:
            deviation = abs((rate_float - average_rate) / average_rate * 100)
            return False, f"경고: 입력한 환율({rate_float:,.2f})이 평균 환율({average_rate:,.2f}) 대비 {deviation:.1f}% 차이납니다. 한국은행 환율을 다시 확인해주세요."
        
        return True, "환율이 적정 범위 내에 있습니다."
    
    def add_manual_rate(self, currency_code, rate, input_by, rate_date=None):
        """수동으로 환율을 추가합니다."""
        try:
            # 환율 검증
            is_valid, message = self.validate_rate(currency_code, rate)
            
            if rate_date is None:
                rate_date = datetime.now().strftime('%Y-%m-%d')
            
            # 기존 데이터 읽기
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            
            # 같은 날짜의 기존 환율이 있는지 확인
            existing = df[
                (df['currency_code'] == currency_code) & 
                (df['rate_date'] == rate_date)
            ]
            
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            if len(existing) > 0:
                # 기존 데이터 업데이트
                df.loc[
                    (df['currency_code'] == currency_code) & 
                    (df['rate_date'] == rate_date),
                    ['rate', 'updated_date', 'input_by']
                ] = [float(rate), current_time, input_by]
            else:
                # 새 데이터 추가
                new_rate = {
                    'rate_id': f"MR{datetime.now().strftime('%Y%m%d%H%M%S')}{currency_code}",
                    'currency_code': currency_code,
                    'currency_name': self.supported_currencies[currency_code]['name'],
                    'rate': float(rate),
                    'base_currency': 'USD',
                    'rate_date': rate_date,
                    'source': '한국은행 기준 (수동입력)',
                    'input_date': current_time,
                    'updated_date': current_time,
                    'input_by': input_by
                }
                
                df = pd.concat([df, pd.DataFrame([new_rate])], ignore_index=True)
            
            # 저장
            df.to_csv(self.data_file, index=False, encoding='utf-8-sig')
            return True, message, is_valid
            
        except Exception as e:
            return False, f"환율 저장 중 오류: {e}", False
    
    def get_latest_rates(self):
        """최신 환율 데이터를 가져옵니다."""
        try:
            if not os.path.exists(self.data_file):
                return pd.DataFrame()
                
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            
            if len(df) == 0:
                return pd.DataFrame()
            
            # 각 통화별 최신 환율 조회
            latest_rates = []
            for currency in df['currency_code'].unique():
                currency_df = df[df['currency_code'] == currency].copy()
                if len(currency_df) > 0:
                    # 날짜순으로 정렬하여 최신 데이터 선택
                    currency_df = currency_df.sort_values('rate_date')
                    latest_row = currency_df.iloc[-1]
                    latest_rates.append(latest_row.to_dict())
            
            return pd.DataFrame(latest_rates) if latest_rates else pd.DataFrame()
            
        except Exception as e:
            print(f"최신 환율 조회 중 오류: {e}")
            return pd.DataFrame()
    
    def get_rate_history(self, currency_code, days=None):
        """특정 통화의 환율 히스토리를 가져옵니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            
            df['rate_date'] = pd.to_datetime(df['rate_date'])
            
            # 특정 통화만 필터링
            history = df[df['currency_code'] == currency_code].copy()
            
            # 날짜 필터링 (days가 None이면 전체 데이터)
            if days is not None:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days)
                history = history[
                    (history['rate_date'] >= start_date) &
                    (history['rate_date'] <= end_date)
                ]
            
            return history.sort_values('rate_date')
            
        except Exception as e:
            print(f"환율 히스토리 조회 중 오류: {e}")
            return pd.DataFrame()
    
    def get_supported_currencies(self):
        """지원 통화 목록을 반환합니다."""
        return [
            {
                'currency_code': code,
                'currency_name': info['name'],
                'average_rate': info['average_rate']
            }
            for code, info in self.supported_currencies.items()
        ]
    
    def get_rate_statistics(self, currency_code):
        """특정 통화의 환율 통계를 계산합니다."""
        try:
            # 전체 데이터로 통계 계산
            history = self.get_rate_history(currency_code, days=None)
            
            if len(history) == 0:
                return {}
            
            rates = history['rate'].astype(float)
            
            return {
                'current_rate': float(rates.iloc[-1]) if len(rates) > 0 else 0.0,
                'avg_rate': float(rates.mean()) if len(rates) > 0 else 0.0,
                'min_rate': float(rates.min()) if len(rates) > 0 else 0.0,
                'max_rate': float(rates.max()) if len(rates) > 0 else 0.0,
                'data_points': len(rates)
            }
            
        except Exception as e:
            print(f"환율 통계 계산 중 오류: {e}")
            return {}
    
    def delete_rate(self, rate_id):
        """특정 환율 데이터를 삭제합니다."""
        try:
            df = pd.read_csv(self.data_file, encoding='utf-8-sig')
            
            # 해당 ID의 데이터 삭제
            df = df[df['rate_id'] != rate_id]
            df.to_csv(self.data_file, index=False, encoding='utf-8-sig')
            
            return True, "환율 데이터가 삭제되었습니다."
            
        except Exception as e:
            return False, f"삭제 중 오류: {e}"