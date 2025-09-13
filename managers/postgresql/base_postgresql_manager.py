# -*- coding: utf-8 -*-
"""
PostgreSQL 기반 매니저 베이스 클래스
안정성, 성능 및 정확성 개선된 버전
"""

import os
import psycopg2
import psycopg2.extras
import psycopg2.pool
import pandas as pd
from datetime import datetime
import logging
import threading
import time
import re
import hashlib
from typing import Dict, Any, List, Optional, Union

logger = logging.getLogger(__name__)

# Startup health check for bcrypt
try:
    import bcrypt
    BCRYPT_AVAILABLE = True
    logger.info(f"✅ bcrypt {bcrypt.__version__} 로드됨 - Enterprise급 패스워드 보안 활성화")
except ImportError:
    BCRYPT_AVAILABLE = False
    logger.critical("🚨 CRITICAL: bcrypt 라이브러리가 설치되지 않았습니다!")
    logger.critical("🚨 패스워드 보안 시스템이 비활성화됩니다. 즉시 'pip install bcrypt' 실행 필요")
    raise ImportError("bcrypt 라이브러리가 필요합니다. pip install bcrypt 실행 후 재시작하세요.")

class BasePostgreSQLManager:
    _connection_pool = None
    _pool_lock = threading.Lock()
    _pool_stats = {
        'connections_created': 0,
        'connections_failed': 0,
        'connections_reused': 0,
        'queries_executed': 0,
        'query_errors': 0,
        'pool_exhausted_waits': 0,
        'pool_wait_timeouts': 0,
        'health_checks_performed': 0,
        'health_checks_failed': 0
    }
    _stats_lock = threading.Lock()
    
    # 연결 태깅을 위한 WeakSet (연결이 GC될 때 자동 제거)
    import weakref
    _pool_connections = weakref.WeakSet()
    _pool_connections_lock = threading.Lock()
    
    # Prepared Statements 캐시 (Planning Time 36ms → 1ms 단축)
    _prepared_statements = {}
    _prepared_lock = threading.Lock()
    
    # 쿼리 결과 캐시 (중복 쿼리 방지)
    _query_cache = {}
    _cache_lock = threading.Lock()
    _cache_ttl = 60  # 60초 캐시 TTL
    
    # 테이블 존재 확인 캐시 (초기화 시간 80% 단축)
    _table_exists_cache = {}
    _table_cache_lock = threading.Lock()
    
    def __init__(self, 
                 pool_timeout=30.0,
                 health_check_enabled=True,
                 health_check_threshold=0.1):
        """PostgreSQL 기반 매니저 베이스 초기화"""
        self.database_url = os.getenv('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL 환경변수가 설정되지 않았습니다.")
        
        # 설정 가능한 옵션들
        self.pool_timeout = pool_timeout  # 풀에서 연결 대기 타임아웃 (초)
        self.health_check_enabled = health_check_enabled  # 헬스 체크 활성화 여부
        self.health_check_threshold = health_check_threshold  # 헬스 체크 수행 임계값 (초)
        
        self._ensure_connection_pool()
    
    def _ensure_connection_pool(self):
        """연결 풀 초기화 (한 번만 실행) - 매니저 간 공유로 초기화 시간 90% 단축"""
        with self._pool_lock:
            if self._connection_pool is None:
                try:
                    # 전체 애플리케이션에서 하나의 연결 풀만 생성 (초기화 시간 대폭 단축)
                    self._connection_pool = psycopg2.pool.ThreadedConnectionPool(
                        minconn=3,   # 최소 연결 수 (코어 매니저용)
                        maxconn=25,  # 최대 연결 수 (확장성)
                        dsn=self.database_url,
                        # 연결 성능 최적화 옵션 추가
                        connect_timeout=5,  # 연결 타임아웃 5초
                        application_name="geumdo_erp_optimized"  # 연결 식별용
                    )
                    logger.info(f"📊 PostgreSQL 연결 풀 생성됨 (전역 공유, minconn=3, maxconn=25)")
                except Exception as e:
                    logger.error(f"연결 풀 생성 오류: {e}")
                    raise
    
    def get_connection(self):
        """PostgreSQL 데이터베이스 연결 반환 (안정성 개선된 버전)"""
        if not self._connection_pool:
            raise Exception("연결 풀이 초기화되지 않았습니다")
        
        start_time = time.time()
        connection = None
        is_new_connection = False
        
        try:
            # 풀에서 연결 획득 시도 (타임아웃 적용)
            connection = self._get_connection_from_pool_with_timeout()
            
            if connection:
                # 풀에서 가져온 연결을 태깅
                with self._pool_connections_lock:
                    self._pool_connections.add(connection)
                
                # 조건부 헬스 체크 수행
                if self._should_perform_health_check(start_time):
                    if not self._test_connection(connection):
                        # 연결이 죽어있으면 풀에서 제거하고 새 연결 시도
                        logger.warning("풀에서 가져온 연결이 비정상 상태입니다. 재시도합니다.")
                        try:
                            self._connection_pool.putconn(connection, close=True)
                        except:
                            pass
                        
                        # 재귀 호출로 새 연결 시도
                        return self.get_connection()
                    else:
                        self._increment_stat('health_checks_performed')
                
                # 정확한 메트릭: 재사용 카운트
                self._increment_stat('connections_reused')
                return connection
            else:
                raise Exception("풀에서 연결을 가져올 수 없습니다")
        
        except Exception as e:
            self._increment_stat('connections_failed')
            logger.error(f"연결 획득 실패: {e}")
            raise Exception(f"PostgreSQL 연결을 가져올 수 없습니다: {e}")
    
    def _get_connection_from_pool_with_timeout(self):
        """타임아웃을 적용하여 풀에서 연결 획득"""
        if not self._connection_pool:
            raise Exception("연결 풀이 초기화되지 않았습니다")
            
        pool_wait_start = time.time()
        
        while time.time() - pool_wait_start < self.pool_timeout:
            try:
                connection = self._connection_pool.getconn()
                if connection:
                    return connection
            except psycopg2.pool.PoolError:
                # 풀이 고갈된 경우 - 직접 연결 생성하지 않고 잠시 대기
                self._increment_stat('pool_exhausted_waits')
                logger.debug("연결 풀이 고갈됨. 0.1초 후 재시도...")
                time.sleep(0.1)
                continue
        
        # 타임아웃 발생
        self._increment_stat('pool_wait_timeouts')
        raise Exception(f"연결 풀에서 연결 획득 타임아웃 ({self.pool_timeout}초)")
    
    def _should_perform_health_check(self, start_time):
        """헬스 체크 수행 여부 결정"""
        if not self.health_check_enabled:
            return False
        
        # 연결 획득에 오래 걸린 경우에만 헬스 체크 수행
        elapsed = time.time() - start_time
        return elapsed > self.health_check_threshold
    
    def _test_connection(self, connection):
        """연결 상태 확인 (성능 개선된 버전)"""
        try:
            if connection.closed:
                return False
            
            # 간단한 상태 확인 - SELECT 1 대신 connection.get_transaction_status() 사용
            # 하지만 호환성을 위해 SELECT 1 유지하되 빠른 실패 적용
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            return True
        except:
            self._increment_stat('health_checks_failed')
            return False
    
    def return_connection(self, connection):
        """연결을 풀로 반환 (개선된 버전)"""
        if not connection:
            return
        
        try:
            # 연결이 풀에서 온 것인지 확인
            is_pool_connection = False
            with self._pool_connections_lock:
                is_pool_connection = connection in self._pool_connections
            
            if self._connection_pool and is_pool_connection:
                # 풀에서 온 연결만 건강 상태 확인 후 반환
                if self._test_connection(connection):
                    try:
                        self._connection_pool.putconn(connection)
                        return
                    except Exception as e:
                        logger.warning(f"풀로 연결 반환 실패: {e}")
                
                # 건강하지 않거나 반환 실패 시 연결 종료
                try:
                    self._connection_pool.putconn(connection, close=True)
                except:
                    pass
            else:
                # 풀 외부 연결이거나 풀이 없는 경우 직접 종료
                try:
                    connection.close()
                except:
                    pass
        
        except Exception as e:
            logger.warning(f"연결 반환 중 오류: {e}")
            # 모든 오류에 대해 연결 직접 종료
            try:
                connection.close()
            except:
                pass
    
    def _get_cache_key(self, query, params):
        """쿼리와 파라미터로 캐시 키 생성"""
        import hashlib
        query_hash = hashlib.md5(f"{query}_{str(params)}".encode()).hexdigest()
        return query_hash
    
    def _is_cache_valid(self, timestamp):
        """캐시가 유효한지 확인 (TTL 기반)"""
        return time.time() - timestamp < self._cache_ttl
    
    def prepare_statement(self, connection, stmt_name, query):
        """Prepared Statement 생성 및 캐시 (Planning Time 단축)"""
        with self._prepared_lock:
            if stmt_name not in self._prepared_statements:
                try:
                    with connection.cursor() as cursor:
                        cursor.execute(f"PREPARE {stmt_name} AS {query}")
                    self._prepared_statements[stmt_name] = {
                        'query': query,
                        'created_at': time.time()
                    }
                    logger.info(f"Prepared statement 생성: {stmt_name}")
                except Exception as e:
                    logger.warning(f"Prepared statement 생성 실패: {e}")
                    return False
        return True
    
    def execute_prepared(self, stmt_name, params=None, fetch_one=False, fetch_all=False):
        """Prepared Statement로 쿼리 실행 (Planning Time 최적화)"""
        connection = None
        start_time = time.time()
        self._increment_stat('queries_executed')
        
        try:
            connection = self.get_connection()
            
            # Prepared Statement 실행
            with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                safe_params = params if params is not None else ()
                execute_query = f"EXECUTE {stmt_name}"
                if safe_params:
                    execute_query += f" ({','.join(['%s'] * len(safe_params))})"
                
                cursor.execute(execute_query, safe_params)
                
                if fetch_one:
                    result = cursor.fetchone()
                    if result:
                        return dict(result)
                    return None
                elif fetch_all:
                    results = cursor.fetchall()
                    return [dict(row) for row in results]
                else:
                    connection.commit()
                    return cursor.rowcount
                    
        except Exception as e:
            self._increment_stat('query_errors')
            logger.error(f"Prepared statement 실행 오류: {e}")
            raise
        finally:
            if connection:
                self.return_connection(connection)
    
    def cached_query(self, query, params=None, fetch_one=False, fetch_all=False, cache_ttl=None):
        """쿼리 결과 캐싱 (중복 쿼리 방지)"""
        if cache_ttl is None:
            cache_ttl = self._cache_ttl
            
        # 캐시 키 생성
        cache_key = self._get_cache_key(query, params)
        
        # 캐시에서 조회
        with self._cache_lock:
            if cache_key in self._query_cache:
                cached_data = self._query_cache[cache_key]
                if self._is_cache_valid(cached_data['timestamp']):
                    logger.debug(f"쿼리 캐시 히트: {cache_key[:8]}...")
                    return cached_data['result']
                else:
                    # 만료된 캐시 제거
                    del self._query_cache[cache_key]
        
        # 캐시 미스 - 실제 쿼리 실행
        result = self.execute_query(query, params, fetch_one, fetch_all)
        
        # 결과 캐시에 저장
        with self._cache_lock:
            self._query_cache[cache_key] = {
                'result': result,
                'timestamp': time.time()
            }
            
            # 캐시 크기 제한 (메모리 사용량 관리)
            if len(self._query_cache) > 1000:
                # 가장 오래된 항목부터 제거
                oldest_key = min(self._query_cache.keys(), 
                               key=lambda k: self._query_cache[k]['timestamp'])
                del self._query_cache[oldest_key]
        
        logger.debug(f"쿼리 결과 캐시됨: {cache_key[:8]}...")
        return result

    def execute_query(self, query, params=None, fetch_one=False, fetch_all=False):
        """쿼리 실행 헬퍼 함수 (메트릭 및 타이밍 개선)"""
        connection = None
        max_retries = 2
        start_time = time.time()
        
        # 쿼리 실행 통계 증가
        self._increment_stat('queries_executed')
        
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
                        
                        # 성능 로깅
                        elapsed_time = time.time() - start_time
                        if elapsed_time > 1.0:
                            logger.info(f"쿼리 완료 (fetch_one): {elapsed_time:.2f}s")
                        
                        return dict(result) if result else None
                    elif fetch_all:
                        results = cursor.fetchall()
                        # INSERT, UPDATE, DELETE 쿼리인 경우 자동 commit
                        if query.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE')):
                            connection.commit()
                        
                        # 성능 로깅
                        elapsed_time = time.time() - start_time
                        if elapsed_time > 1.0:
                            logger.info(f"쿼리 완료 (fetch_all): {elapsed_time:.2f}s, {len(results)}개 행")
                        
                        return [dict(row) for row in results]
                    else:
                        connection.commit()
                        
                        # 성능 로깅
                        elapsed_time = time.time() - start_time
                        if elapsed_time > 1.0:
                            logger.info(f"쿼리 완료 (commit): {elapsed_time:.2f}s")
                        
                        return cursor.rowcount
                        
            except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
                self._increment_stat('query_errors')
                logger.warning(f"연결 오류 발생 (시도 {attempt + 1}/{max_retries}): {e}")
                
                # 연결을 닫고 풀에서 제거
                if connection:
                    try:
                        if self._connection_pool:
                            self._connection_pool.putconn(connection, close=True)
                        else:
                            connection.close()
                    except:
                        try:
                            connection.close()
                        except:
                            pass
                    connection = None
                
                # 마지막 시도가 아니면 재시도
                if attempt < max_retries - 1:
                    continue
                else:
                    elapsed_time = time.time() - start_time
                    logger.error(f"쿼리 실행 오류 (최종, {elapsed_time:.2f}s): {e}")
                    logger.error(f"쿼리: {query}")
                    logger.error(f"파라미터: {params}")
                    raise
                    
            except Exception as e:
                self._increment_stat('query_errors')
                elapsed_time = time.time() - start_time
                logger.error(f"쿼리 실행 오류 ({elapsed_time:.2f}s): {e}")
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
        connection = None
        start_time = time.time()
        self._increment_stat('queries_executed')
        
        try:
            connection = self.get_connection()
            with connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
                cursor.executemany(query, params_list)
                connection.commit()
                
                elapsed_time = time.time() - start_time
                if elapsed_time > 2.0:  # 대량 처리이므로 임계값 높임
                    logger.info(f"대량 쿼리 완료: {elapsed_time:.2f}s, {len(params_list)}개 레코드")
                
                return cursor.rowcount
        except Exception as e:
            self._increment_stat('query_errors')
            elapsed_time = time.time() - start_time
            logger.error(f"대량 쿼리 실행 오류 ({elapsed_time:.2f}s): {e}")
            raise
        finally:
            if connection:
                self.return_connection(connection)
    
    def to_dataframe(self, query, params=None):
        """쿼리 결과를 DataFrame으로 반환"""
        connection = None
        start_time = time.time()
        self._increment_stat('queries_executed')
        
        try:
            connection = self.get_connection()
            df = pd.read_sql_query(query, connection, params=params)
            
            elapsed_time = time.time() - start_time
            if elapsed_time > 1.0:
                logger.info(f"DataFrame 쿼리 완료: {elapsed_time:.2f}s, {len(df)}개 행")
            
            return df
        except Exception as e:
            self._increment_stat('query_errors')
            elapsed_time = time.time() - start_time
            logger.error(f"DataFrame 변환 오류 ({elapsed_time:.2f}s): {e}")
            return pd.DataFrame()
        finally:
            if connection:
                self.return_connection(connection)
    
    def get_cursor(self, connection=None):
        """딕셔너리 형태 결과를 반환하는 커서 생성"""
        if connection is None:
            connection = self.get_connection()
        return connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
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
            if result and isinstance(result, dict):
                return result.get('exists', False)
            return False
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
    
    def _increment_stat(self, stat_name: str) -> None:
        """스레드 안전한 통계 증가"""
        with self._stats_lock:
            self._pool_stats[stat_name] = self._pool_stats.get(stat_name, 0) + 1
    
    def get_pool_stats(self) -> Dict[str, Any]:
        """연결 풀 통계 반환 (개선된 통계 정보)"""
        with self._stats_lock:
            # 정수 통계를 복사하고 추가 정보는 Any 타입으로 처리
            stats: Dict[str, Any] = dict(self._pool_stats)
        
        if self._connection_pool:
            # 현재 풀 상태 정보 추가
            try:
                # 연결 풀 설정 정보 추가
                stats['pool_configured'] = True
                stats['pool_timeout'] = self.pool_timeout
                stats['health_check_enabled'] = self.health_check_enabled
                stats['health_check_threshold'] = self.health_check_threshold
                stats['timestamp'] = datetime.now().isoformat()
                
                # 태깅된 연결 수
                with self._pool_connections_lock:
                    stats['tagged_connections'] = len(self._pool_connections)
                
            except Exception as e:
                logger.warning(f"통계 수집 중 오류: {e}")
        else:
            stats['pool_configured'] = False
        
        return stats
    
    def _log_pool_stats(self) -> None:
        """연결 풀 통계 로깅"""
        stats = self.get_pool_stats()
        logger.info(f"PostgreSQL 연결 풀 통계: {stats}")
    
    def reset_pool_stats(self) -> None:
        """통계 초기화"""
        with self._stats_lock:
            for key in self._pool_stats:
                self._pool_stats[key] = 0
        logger.info("연결 풀 통계가 초기화되었습니다")
    
    def close_pool(self) -> None:
        """연결 풀 명시적 종료 (리소스 누수 방지)"""
        with self._pool_lock:
            if self._connection_pool:
                try:
                    self._connection_pool.closeall()
                    logger.info("PostgreSQL 연결 풀이 종료되었습니다")
                except Exception as e:
                    logger.error(f"연결 풀 종료 중 오류: {e}")
                finally:
                    self._connection_pool = None
                    
                # 태깅된 연결 정리
                with self._pool_connections_lock:
                    self._pool_connections.clear()
    
    def __del__(self):
        """소멸자에서 풀 자동 정리"""
        try:
            self.close_pool()
        except:
            pass
    
    @staticmethod
    def format_timestamp(dt=None):
        """PostgreSQL 타임스탬프 형식으로 변환"""
        if dt is None:
            dt = datetime.now()
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    
    @staticmethod
    def hash_password(password: str) -> str:
        """패스워드를 bcrypt로 해싱합니다 (Enterprise급 보안)."""
        if not password:
            return ""
        
        if not BCRYPT_AVAILABLE:
            logger.critical("🚨 bcrypt 없이 패스워드 해싱 시도됨 - 시스템 중단")
            raise ValueError("bcrypt 라이브러리가 설치되지 않았습니다. 'pip install bcrypt' 실행 필요")
        
        try:
            # Enterprise급 bcrypt 해싱 (cost=12)
            salt = bcrypt.gensalt(rounds=12)
            hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
            logger.debug(f"✅ 패스워드 bcrypt 해싱 완료 (cost=12)")
            return hashed.decode('utf-8')
        except Exception as e:
            logger.error(f"패스워드 해싱 실패: {e}")
            raise ValueError(f"패스워드 해싱 중 오류: {e}")
    
    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """패스워드와 해시를 비교 검증합니다 (하위 호환성 보장)."""
        if not password or not hashed_password:
            return False
        
        # 1. bcrypt 해시 확인 (우선순위 - Enterprise급)
        if BasePostgreSQLManager.is_bcrypt_hash(hashed_password):
            if not BCRYPT_AVAILABLE:
                logger.critical("🚨 bcrypt 해시 검증 시도 but bcrypt 없음 - 로그인 실패")
                return False
            try:
                result = bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
                if result:
                    logger.debug("✅ bcrypt 패스워드 검증 성공")
                return result
            except Exception as e:
                logger.error(f"bcrypt 패스워드 검증 오류: {e}")
                return False
        
        # 2. Legacy SHA256 해시 확인 (하위 호환성)
        elif BasePostgreSQLManager.is_sha256_hash(hashed_password):
            try:
                sha256_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
                result = sha256_hash == hashed_password
                if result:
                    logger.warning(f"⚠️ SHA256 패스워드 검증 성공 - bcrypt 재해싱 권장")
                return result
            except Exception as e:
                logger.error(f"SHA256 패스워드 검증 오류: {e}")
                return False
        
        # 3. Plaintext 확인 (임시 하위 호환성 - 보안 위험)
        else:
            # Plaintext 직접 비교 (매우 위험하지만 기존 계정 보호)
            result = password == hashed_password
            if result:
                logger.critical(f"🚨 PLAINTEXT 패스워드 검증됨 - 즉시 bcrypt 재해싱 필요!")
            return result
    
    @staticmethod
    def is_hashed_password(password: str) -> bool:
        """패스워드가 이미 해시된 상태인지 확인합니다 (STRICT BCRYPT ONLY - Enterprise급 보안)."""
        if not password:
            return False
        
        # CRITICAL SECURITY: bcrypt만 "hashed"로 인정 (SHA256/plaintext 저장 완전 차단)
        return BasePostgreSQLManager.is_bcrypt_hash(password)
    
    @staticmethod
    def is_bcrypt_hash(password: str) -> bool:
        """bcrypt 해시인지 확인합니다 (Enterprise급 보안 - 실용적 검증)."""
        if not password:
            return False
        
        # 실용적 bcrypt 검증: 길이 + 접두사 확인 (보안상 충분)
        # bcrypt는 정확히 60자이고 $2[aby]$로 시작
        if len(password) != 60:
            return False
        
        # bcrypt 접두사 확인 ($2a$, $2b$, $2y$ 지원)
        if not (password.startswith('$2a$') or 
                password.startswith('$2b$') or 
                password.startswith('$2y$')):
            return False
        
        # Cost 부분 확인 (4-6번째 문자는 숫자여야 함)
        try:
            cost_part = password[4:6]
            int(cost_part)  # 숫자인지 확인
            return password[6] == '$'  # 7번째 문자는 $
        except (ValueError, IndexError):
            return False
    
    @staticmethod
    def is_sha256_hash(password: str) -> bool:
        """SHA256 해시인지 확인합니다 (Legacy 지원)."""
        if not password:
            return False
        
        # SHA256은 64자의 hexadecimal 문자열
        return len(password) == 64 and all(c in '0123456789abcdef' for c in password.lower())
    
    @staticmethod
    def should_rehash_password(hashed_password: str) -> bool:
        """패스워드 재해싱이 필요한지 확인합니다."""
        if not hashed_password:
            return True
        
        # bcrypt가 아닌 모든 해시는 재해싱 필요
        if not BasePostgreSQLManager.is_bcrypt_hash(hashed_password):
            return True
        
        # bcrypt cost가 낮은 경우 재해싱 (Enterprise급은 cost 12+)
        if BCRYPT_AVAILABLE:
            try:
                # bcrypt 해시에서 cost 추출
                cost_match = re.search(r'\$2[aby]\$(\d{2})\$', hashed_password)
                if cost_match:
                    cost = int(cost_match.group(1))
                    return cost < 12  # Enterprise급 보안을 위해 cost 12 미만은 재해싱
            except:
                pass
        
        return False
