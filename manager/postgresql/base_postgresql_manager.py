# -*- coding: utf-8 -*-
"""
PostgreSQL 기반 매니저 베이스 클래스
"""

import os
import psycopg2
import psycopg2.extras
import psycopg2.pool
import pandas as pd
from datetime import datetime
import logging
import threading

logger = logging.getLogger(__name__)

class BasePostgreSQLManager:
    _connection_pool = None
    _pool_lock = threading.Lock()
    
    def __init__(self):
        """PostgreSQL 기반 매니저 베이스 초기화"""
        self.database_url = os.getenv('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL 환경변수가 설정되지 않았습니다.")
        self._ensure_connection_pool()
    
    def _ensure_connection_pool(self):
        """연결 풀 초기화 (한 번만 실행)"""
        with self._pool_lock:
            if self._connection_pool is None:
                try:
                    self._connection_pool = psycopg2.pool.ThreadedConnectionPool(
                        minconn=5,  # 최소 연결 수 증가
                        maxconn=50, # 최대 연결 수 대폭 증가
                        dsn=self.database_url
                    )
                    logger.info("PostgreSQL 연결 풀이 생성되었습니다.")
                except Exception as e:
                    logger.error(f"연결 풀 생성 오류: {e}")
                    raise
    
    def get_connection(self):
        """PostgreSQL 데이터베이스 연결 반환 (풀에서)"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if self._connection_pool:
                    conn = self._connection_pool.getconn()
                    if conn:
                        # 연결 상태 확인
                        if self._test_connection(conn):
                            return conn
                        else:
                            # 연결이 죽어있으면 풀에서 제거하고 새로 생성
                            try:
                                self._connection_pool.putconn(conn, close=True)
                            except:
                                pass
                
                # 풀에서 연결 실패 시 또는 연결이 죽어있는 경우 직접 연결
                conn = psycopg2.connect(self.database_url)
                if self._test_connection(conn):
                    return conn
                    
            except Exception as e:
                logger.warning(f"PostgreSQL 연결 시도 {attempt + 1}/{max_retries} 실패: {e}")
                if attempt == max_retries - 1:
                    logger.error(f"PostgreSQL 연결 오류 (최종): {e}")
                    raise
                
        raise Exception("PostgreSQL 연결을 가져올 수 없습니다")
    
    def _test_connection(self, connection):
        """연결 상태 확인"""
        try:
            if connection.closed:
                return False
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            return True
        except:
            return False
    
    def return_connection(self, connection):
        """연결을 풀로 반환"""
        if not connection:
            return
            
        try:
            if self._connection_pool:
                if self._test_connection(connection):
                    # 정상 연결인 경우만 풀로 반환
                    try:
                        self._connection_pool.putconn(connection)
                    except Exception as e:
                        # putconn 실패 시 연결 직접 종료
                        try:
                            connection.close()
                        except:
                            pass
                else:
                    # 연결이 죽어있으면 직접 종료
                    try:
                        connection.close()
                    except:
                        pass
            else:
                # 풀이 없으면 직접 종료
                try:
                    connection.close()
                except:
                    pass
        except Exception as e:
            # 모든 오류에 대해 연결 직접 종료
            try:
                connection.close()
            except:
                pass
    
    def get_cursor(self, connection=None):
        """딕셔너리 형태 결과를 반환하는 커서 생성"""
        if connection is None:
            connection = self.get_connection()
        return connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    def execute_query(self, query, params=None, fetch_one=False, fetch_all=False):
        """쿼리 실행 헬퍼 함수 (연결 풀 사용, 재시도 로직 포함)"""
        connection = None
        max_retries = 2
        
        for attempt in range(max_retries):
            try:
                connection = self.get_connection()
                with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                    # 파라미터가 None이면 빈 tuple로 대체
                    safe_params = params if params is not None else ()
                    cursor.execute(query, safe_params)
                    
                    if fetch_one:
                        result = cursor.fetchone()
                        # INSERT, UPDATE, DELETE 쿼리인 경우 자동 commit
                        if query.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE')):
                            connection.commit()
                        return dict(result) if result else None
                    elif fetch_all:
                        results = cursor.fetchall()
                        # INSERT, UPDATE, DELETE 쿼리인 경우 자동 commit
                        if query.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE')):
                            connection.commit()
                        return [dict(row) for row in results]
                    else:
                        connection.commit()
                        return cursor.rowcount
                        
            except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
                logger.warning(f"연결 오류 발생 (시도 {attempt + 1}/{max_retries}): {e}")
                
                # 연결을 닫고 풀에서 제거
                if connection:
                    try:
                        self._connection_pool.putconn(connection, close=True)
                    except:
                        pass
                    connection = None
                
                # 마지막 시도가 아니면 재시도
                if attempt < max_retries - 1:
                    continue
                else:
                    logger.error(f"쿼리 실행 오류 (최종): {e}")
                    logger.error(f"쿼리: {query}")
                    logger.error(f"파라미터: {params}")
                    raise
                    
            except Exception as e:
                logger.error(f"쿼리 실행 오류: {e}")
                logger.error(f"쿼리: {query}")
                logger.error(f"파라미터: {params}")
                raise
            finally:
                # 연결 반환 - 더 안전한 처리
                if connection:
                    try:
                        self.return_connection(connection)
                    except Exception as e:
                        logger.warning(f"연결 반환 중 오류: {e}")
                        # 연결을 직접 닫기
                        try:
                            connection.close()
                        except:
                            pass
            
            # 성공하면 루프 탈출
            break
    
    def execute_many(self, query, params_list):
        """대량 데이터 삽입/업데이트"""
        try:
            with self.get_connection() as conn:
                with self.get_cursor(conn) as cursor:
                    cursor.executemany(query, params_list)
                    conn.commit()
                    return cursor.rowcount
        except Exception as e:
            logger.error(f"대량 쿼리 실행 오류: {e}")
            raise
    
    def to_dataframe(self, query, params=None):
        """쿼리 결과를 DataFrame으로 반환"""
        try:
            with self.get_connection() as conn:
                return pd.read_sql_query(query, conn, params=params)
        except Exception as e:
            logger.error(f"DataFrame 변환 오류: {e}")
            return pd.DataFrame()
    
    def log_info(self, message):
        """정보 로그 출력"""
        logger.info(message)
        print(f"INFO: {message}")
    
    def log_error(self, message):
        """오류 로그 출력"""
        logger.error(message)
        print(f"ERROR: {message}")
    
    def log_warning(self, message):
        """경고 로그 출력"""
        logger.warning(message)
        print(f"WARNING: {message}")
    
    def table_exists(self, table_name):
        """테이블 존재 여부 확인"""
        query = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = %s
            );
        """
        try:
            result = self.execute_query(query, (table_name,), fetch_one=True)
            return result.get('exists', False) if result else False
        except Exception as e:
            logger.error(f"테이블 존재 확인 오류: {e}")
            return False
    
    def get_table_columns(self, table_name):
        """테이블 컬럼 정보 조회"""
        query = """
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = %s
            ORDER BY ordinal_position;
        """
        try:
            return self.execute_query(query, (table_name,), fetch_all=True)
        except Exception as e:
            logger.error(f"테이블 컬럼 조회 오류: {e}")
            return []
    
    def create_table_if_not_exists(self, table_name, create_sql):
        """테이블이 존재하지 않으면 생성"""
        if not self.table_exists(table_name):
            try:
                self.execute_query(create_sql)
                logger.info(f"테이블 {table_name} 생성 완료")
                return True
            except Exception as e:
                logger.error(f"테이블 {table_name} 생성 오류: {e}")
                raise
        else:
            logger.info(f"테이블 {table_name}이 이미 존재합니다")
            return False
    
    def backup_table_data(self, table_name):
        """테이블 데이터 백업"""
        if self.table_exists(table_name):
            query = f"SELECT * FROM {table_name}"
            return self.to_dataframe(query)
        return pd.DataFrame()
    
    @staticmethod
    def format_timestamp(dt=None):
        """PostgreSQL 타임스탬프 형식으로 변환"""
        if dt is None:
            dt = datetime.now()
        return dt.strftime('%Y-%m-%d %H:%M:%S')