# Integrated Management System (IMS)

## Overview  
This project is a comprehensive Streamlit-based Integrated Management System (IMS) designed to streamline core business operations for Vietnamese industrial heating, robotics, and spare parts companies. **Major file restructuring completed on 2025-08-21**: Reduced from 91 files to 5 core files in root directory (95% reduction) with systematic folder organization. Its primary purpose is to manage employee information, customer relationships, product catalogs, quotation generation, and various business processes. The system features a modular, multi-language architecture with SQLite database persistence and robust data management capabilities. The vision is to provide a user-friendly, efficient, and integrated platform for small to medium-sized businesses, enhancing operational efficiency and decision-making through centralized data and automated workflows.

## User Preferences
Preferred communication style: Simple, everyday language.
**Critical User Requirement**: Complete conversion of ALL CSV-based systems to SQLite database (emphasized multiple times by user).
**Important**: Document print system must be accessible to all users - moved to main menu level (not under admin section).
**Product Management Workflow**: Removed automatic synchronization between master and sales products. Product registration now only creates entries in master products table, with manual sales product registration available through system settings advanced configuration.
**Data Policy**: ABSOLUTELY NO dummy data insertion unless explicitly requested by user - system must remain empty until user adds data manually. No activation controls or automatic data population.
**Customer ID Format**: Maintained compatibility with existing C001~C442 format. New customers receive sequential IDs starting from C443. Legacy CUST_ format deprecated but preserved for existing records.

## Recent Successful Implementations (2025-09-03 Final)
- **스탬프 기능 완전 구현**: Print Quotation 탭에 "Include Company Stamp" 옵션 추가, 실제 도장 이미지(1.7MB) 사용
- **스탬프 레이아웃 최적화**: 회사명 텍스트 위에 겹치는 절대 위치 배치, 180px 크기, 0.85 투명도로 실제 도장 효과
- **조건부 서명자 표시**: 스탬프 활성화 시에만 서명자 이름 표시, 하드코딩 제거
- **Contact 필드 매핑 문제 완전 해결**: Yumold Temp 01.html 템플릿에서 Contact 필드가 {{sales_rep_name}} 대신 {{sales_rep_email}} 사용하도록 수정
- **중복 템플릿 파일 구조 정리**: display_quotation_for_print() 함수가 실제 사용하는 템플릿 파일 확인 및 수정
- **견적서 리비전 시스템 완벽 동작**: 리비전 생성된 견적서가 견적서 리스트에 정확히 표시, Rev 번호 구분
- **고객 정보 데이터베이스 연동 완료**: 실제 고객 데이터가 HTML 템플릿에 정확히 반영
- **프로젝트 정보 하단 고정**: 프로젝트 정보와 서명란이 제품 목록과 관계없이 견적서 하단에 고정 위치
- **견적서 하드코딩 문제 완전 해결**: 모든 정적 데이터를 동적 변수로 교체, 실제 데이터 표시
- **HTML 템플릿 구조 최적화**: A4 프린트 최적화 및 프로젝트 정보 섹션 page-break-inside: avoid 설정

## 사용자 요구사항 (2025-08-31 재확인)
- **메뉴 위치**: 로그아웃 메뉴를 최하단으로 고정 (다시 이동되지 않도록)
- **견적서 레이아웃**: 프로젝트 정보와 서명 부분을 견적서 하단에 고정 위치
- **프린트 미리보기**: HTML 코드가 아닌 실제 견적서 형태로 표시
- **제품 정보 연동**: DataFrame 처리 오류 해결, .empty 사용
- **Contact 정보**: 선택한 Sales Rep 정보가 견적서에 정확히 반영되어야 함

## System Architecture

### Frontend
The system utilizes the Streamlit framework for its web-based user interface, featuring a multi-tab interface with sidebar navigation. It employs custom CSS for responsive design, dashboard widgets, and supports multi-language capabilities. The UI/UX is designed for a professional and intuitive user experience, featuring a clean, modern PDF template (Studio Modern) with a dark green and light gray color scheme for documents. Mobile optimization has been implemented for seamless usage across various devices.

### Backend
The backend is built around modular manager classes, each responsible for a specific business domain. Core functionalities include role-based access control for authentication, comprehensive employee and customer management, product cataloging with a hierarchical HRCT/HRCS structure for HRC products, and automated quotation generation. Key business processes managed include workflow automation, approval workflows with clear role separation (General Affairs for requests, Corporate Head for approvals), purchase order creation, inventory, shipping, invoicing, cash flow tracking, and general affairs scheduling (e.g., visa, car, permits). A robust backup and restore system is integrated for data safety and easy deployment.

### Data Storage
The system is transitioning from CSV files to SQLite for primary data storage, located in the `/data` directory. This includes all core domains like employees, customers, products, quotations, orders, and expense requests, ensuring data integrity through foreign key relationships and transaction processing.

### Key Features
- **Core Management**: Authentication, Employee, Customer, Product, Quotation, Supplier, and Exchange Rate management.
- **Business Process Automation**: Workflow automation, approval workflows, purchase order creation, inventory, shipping, invoicing, and cash flow tracking.
- **Utility Functions**: PDF template design, standardized product coding, vacation management, notification system, and data migration tools.
- **Comprehensive Pages**: Dashboards, and dedicated pages for Employee, Customer, Product, Quotation, and Business Process management.
- **Advanced Product Management**: System settings include detailed product management with manual sales product registration, product deletion capabilities, and category-based product filtering with HR/HRC distinction.
- **Product Categorization**: Standardized categorization for products with dynamic sub-category selection and hierarchical HRCT/HRCS structure for HRC products.
- **Multi-Currency Support**: Real-time exchange rate integration and multi-currency display for quotations and financial tracking.
- **Yearly Management Exchange Rate System**: SQLite-based yearly management rate system with World Bank WDI data source (PA.NUS.FCRF indicator) for consistent pricing standards.
- **Location Management**: Dynamic country-city selection with comprehensive geographic databases.
- **Reporting & Analytics**: Dashboards with key metrics, charts, and analysis for sales, cash flow, and employee statistics.
- **Security**: Role-based access control and secure password management.
- **Multi-language Support**: Comprehensive three-language support (Korean, English, Vietnamese) with an extensible infrastructure for adding more languages.

## External Dependencies

- **streamlit**: Web application framework.
- **pandas**: Data manipulation and analysis.
- **reportlab**: PDF document generation.
- **plotly**: Interactive charts and visualizations.
- **World Bank WDI (World Development Indicators)**: Exchange rate data source for yearly management rates (Indicator: PA.NUS.FCRF - Official exchange rate, LCU per US$, period average). Unit: Local Currency per USD.
- **Open Exchange Rates API**: Used for real-time currency exchange rates.
- **SQLite**: Primary database for application data.
- **JSON Files**: Used for language internationalization and PDF template configurations.
- **External Font Support**: For multi-language PDF generation (Unicode fonts).