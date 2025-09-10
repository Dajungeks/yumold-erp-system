# YUMOLD ERP 시스템

## 개요
YUMOLD VIET NAM COMPANY LIMITED를 위한 통합 ERP 시스템입니다.
직원 관리, 고객 관리, 견적서 생성, 제품 관리 등의 기능을 제공합니다.

## 시스템 요구사항
- Python 3.8 이상
- PostgreSQL 데이터베이스

## 설치 방법

### 1. 의존성 설치
```bash
pip install streamlit pandas plotly psycopg2-binary reportlab requests schedule sqlalchemy bcrypt trafilatura
```

### 2. 데이터베이스 설정
PostgreSQL 데이터베이스를 생성하고 다음 환경변수를 설정하세요:

```bash
export DATABASE_URL="postgresql://username:password@localhost:5432/yumold_erp"
export PGHOST="localhost"
export PGPORT="5432"
export PGUSER="username"
export PGPASSWORD="password"
export PGDATABASE="yumold_erp"
```

### 3. 데이터베이스 복원
포함된 백업 파일로 데이터베이스를 복원하세요:
```bash
psql $DATABASE_URL < database_backup.sql
```

### 4. 애플리케이션 실행
```bash
streamlit run app.py --server.port 5000
```

## 기본 로그인 정보

### 마스터 관리자
- 비밀번호: `master123`

### 직원 로그인
| 사번 | 직원명 | 비밀번호 |
|------|--------|----------|
| 2508001 | 김충성 | kim1234 |
| 2508002 | LƯU THỊ HẰNG | luu5678 |
| 2509001 | NGUYỄN TRUNG THÀNH | nguyen9876 |

## 주요 기능
- 👥 직원 관리 (등록, 수정, 삭제, 비밀번호 관리)
- 🏢 고객 관리 (등록, 수정, 삭제)
- 📝 견적서 생성 및 관리
- 📦 제품 관리 (마스터/영업 제품)
- 💰 현금 흐름 관리
- 📊 월별 매출 관리
- 🔐 권한 기반 접근 제어
- 🌐 다국어 지원 (한국어/영어/베트남어)

## 기술 스택
- **Frontend**: Streamlit
- **Backend**: Python
- **Database**: PostgreSQL
- **PDF Generation**: ReportLab
- **Charts**: Plotly

## 연락처
YUMOLD VIET NAM COMPANY LIMITED
- Tax NO: 0111146237
- Email: vietnam@yumold.com