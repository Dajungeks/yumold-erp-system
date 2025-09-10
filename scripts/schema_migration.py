# -*- coding: utf-8 -*-
"""
SQLite에서 PostgreSQL로 스키마 마이그레이션 스크립트
"""

import os
import re
import sqlite3
import psycopg2
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SchemaMigrator:
    def __init__(self, sqlite_db_path="erp_system.db"):
        self.sqlite_db_path = sqlite_db_path
        self.postgresql_url = os.getenv('DATABASE_URL')
        if not self.postgresql_url:
            raise ValueError("DATABASE_URL 환경변수가 설정되지 않았습니다.")
    
    def get_sqlite_connection(self):
        """SQLite 연결"""
        return sqlite3.connect(self.sqlite_db_path)
    
    def get_postgresql_connection(self):
        """PostgreSQL 연결"""
        return psycopg2.connect(self.postgresql_url)
    
    def extract_sqlite_schema(self):
        """SQLite에서 테이블 스키마 정보 추출"""
        tables = {}
        
        with self.get_sqlite_connection() as conn:
            cursor = conn.cursor()
            
            # 모든 테이블 목록 조회
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            table_names = [row[0] for row in cursor.fetchall()]
            
            for table_name in table_names:
                # 테이블 스키마 조회
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                
                # 인덱스 정보 조회
                cursor.execute(f"PRAGMA index_list({table_name})")
                indexes = cursor.fetchall()
                
                tables[table_name] = {
                    'columns': columns,
                    'indexes': indexes
                }
        
        return tables
    
    def sqlite_to_postgresql_type(self, sqlite_type):
        """SQLite 타입을 PostgreSQL 타입으로 변환"""
        sqlite_type = sqlite_type.upper()
        
        type_mapping = {
            'INTEGER': 'INTEGER',
            'TEXT': 'TEXT',
            'REAL': 'REAL',
            'BLOB': 'BYTEA',
            'TIMESTAMP': 'TIMESTAMP',
            'DATETIME': 'TIMESTAMP',
            'DATE': 'DATE',
            'TIME': 'TIME',
            'BOOLEAN': 'BOOLEAN',
            'NUMERIC': 'NUMERIC',
            'DECIMAL': 'DECIMAL',
            'FLOAT': 'FLOAT',
            'DOUBLE': 'DOUBLE PRECISION',
            'VARCHAR': 'VARCHAR',
            'CHAR': 'CHAR'
        }
        
        # 기본 타입 매핑 확인
        for sqlite_key, postgresql_type in type_mapping.items():
            if sqlite_key in sqlite_type:
                return postgresql_type
        
        # 기본값은 TEXT
        return 'TEXT'
    
    def generate_postgresql_schema(self, tables):
        """PostgreSQL 스키마 생성 SQL 생성"""
        schema_sql = []
        
        for table_name, table_info in tables.items():
            columns = table_info['columns']
            
            # CREATE TABLE 시작
            create_sql = f"CREATE TABLE IF NOT EXISTS {table_name} (\n"
            column_definitions = []
            
            for col in columns:
                col_id, col_name, col_type, not_null, default_value, is_pk = col
                
                # 컬럼 타입 변환
                pg_type = self.sqlite_to_postgresql_type(col_type)
                
                # 컬럼 정의 생성
                col_def = f"    {col_name} {pg_type}"
                
                # PRIMARY KEY 처리
                if is_pk:
                    if pg_type == 'INTEGER' and 'AUTOINCREMENT' in str(default_value):
                        col_def = f"    {col_name} SERIAL PRIMARY KEY"
                    else:
                        col_def += " PRIMARY KEY"
                
                # NOT NULL 처리
                if not_null and not is_pk:
                    col_def += " NOT NULL"
                
                # DEFAULT 값 처리
                if default_value is not None and not is_pk:
                    if default_value == 'CURRENT_TIMESTAMP':
                        col_def += " DEFAULT CURRENT_TIMESTAMP"
                    elif isinstance(default_value, str):
                        col_def += f" DEFAULT '{default_value}'"
                    else:
                        col_def += f" DEFAULT {default_value}"
                
                column_definitions.append(col_def)
            
            create_sql += ",\n".join(column_definitions)
            create_sql += "\n);"
            
            schema_sql.append(f"-- {table_name} 테이블")
            schema_sql.append(create_sql)
            schema_sql.append("")
        
        return "\n".join(schema_sql)
    
    def create_postgresql_schema(self):
        """PostgreSQL에 스키마 생성"""
        logger.info("SQLite 스키마 추출 중...")
        tables = self.extract_sqlite_schema()
        
        logger.info("PostgreSQL 스키마 생성 중...")
        schema_sql = self.generate_postgresql_schema(tables)
        
        # 스키마 파일 저장
        with open('postgresql_schema.sql', 'w', encoding='utf-8') as f:
            f.write(schema_sql)
        
        logger.info("PostgreSQL 스키마 파일 생성 완료: postgresql_schema.sql")
        
        # PostgreSQL에 실제 스키마 생성
        try:
            with self.get_postgresql_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(schema_sql)
                    conn.commit()
                    logger.info("PostgreSQL 스키마 생성 완료")
        except Exception as e:
            logger.error(f"PostgreSQL 스키마 생성 오류: {e}")
            raise
        
        return tables
    
    def migrate_table_data(self, table_name, batch_size=1000):
        """테이블 데이터 마이그레이션"""
        logger.info(f"테이블 {table_name} 데이터 마이그레이션 시작...")
        
        try:
            # SQLite에서 데이터 조회
            with self.get_sqlite_connection() as sqlite_conn:
                cursor = sqlite_conn.cursor()
                cursor.execute(f"SELECT * FROM {table_name}")
                
                # 컬럼 명 조회
                column_names = [desc[0] for desc in cursor.description]
                
                # PostgreSQL에 데이터 삽입
                with self.get_postgresql_connection() as pg_conn:
                    with pg_conn.cursor() as pg_cursor:
                        # 기존 데이터 삭제 (선택사항)
                        # pg_cursor.execute(f"TRUNCATE TABLE {table_name} CASCADE")
                        
                        # 배치 단위로 데이터 처리
                        batch_count = 0
                        while True:
                            rows = cursor.fetchmany(batch_size)
                            if not rows:
                                break
                            
                            # INSERT 쿼리 생성
                            placeholders = ','.join(['%s'] * len(column_names))
                            insert_sql = f"INSERT INTO {table_name} ({','.join(column_names)}) VALUES ({placeholders})"
                            
                            # 데이터 삽입
                            pg_cursor.executemany(insert_sql, rows)
                            pg_conn.commit()
                            
                            batch_count += len(rows)
                            logger.info(f"{table_name}: {batch_count}행 마이그레이션 완료")
                        
                        logger.info(f"테이블 {table_name} 마이그레이션 완료: 총 {batch_count}행")
                        
        except Exception as e:
            logger.error(f"테이블 {table_name} 마이그레이션 오류: {e}")
            raise
    
    def migrate_all_data(self, tables=None):
        """모든 테이블 데이터 마이그레이션"""
        if tables is None:
            tables = self.extract_sqlite_schema()
        
        for table_name in tables.keys():
            try:
                self.migrate_table_data(table_name)
            except Exception as e:
                logger.error(f"테이블 {table_name} 마이그레이션 실패: {e}")
                continue
    
    def run_full_migration(self):
        """전체 마이그레이션 실행"""
        logger.info("SQLite에서 PostgreSQL로 전체 마이그레이션 시작")
        
        # 1. 스키마 마이그레이션
        tables = self.create_postgresql_schema()
        
        # 2. 데이터 마이그레이션
        self.migrate_all_data(tables)
        
        logger.info("전체 마이그레이션 완료")

if __name__ == "__main__":
    migrator = SchemaMigrator()
    migrator.run_full_migration()