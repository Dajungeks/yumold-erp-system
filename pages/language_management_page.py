"""
다국어 관리 페이지
- 3개 언어 완벽 지원 (한국어, 영어, 베트남어)
- 번역 누락 자동 감지 및 수정
- 하드코딩 텍스트 스캔 및 자동 교체
- 새 언어 추가 지원
"""
import streamlit as st
import pandas as pd
from advanced_language_manager import advanced_lang_manager, get_text
from translation_migration_tool import migration_tool
import json
import os

def show_language_management_page():
    """다국어 관리 페이지 표시"""
    
    st.title("🌍 다국어 관리 시스템")
    
    # 탭 구성
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 언어 현황", 
        "🔍 하드코딩 스캔", 
        "✏️ 번역 편집", 
        "🔄 자동 마이그레이션",
        "➕ 언어 추가"
    ])
    
    with tab1:
        show_language_status()
    
    with tab2:
        show_hardcoded_scan()
    
    with tab3:
        show_translation_editor()
    
    with tab4:
        show_auto_migration()
    
    with tab5:
        show_add_language()

def show_language_status():
    """언어 지원 현황 표시"""
    st.header("📊 다국어 지원 현황")
    
    # 완성도 통계
    completion_stats = advanced_lang_manager.get_completion_stats()
    validation_result = advanced_lang_manager.validate_translations()
    
    # 메트릭 표시
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("지원 언어", len(advanced_lang_manager.supported_languages))
    
    with col2:
        st.metric("총 번역 키", validation_result["total_keys"])
    
    with col3:
        avg_completion = sum(completion_stats.values()) / len(completion_stats) if completion_stats else 0
        st.metric("평균 완성도", f"{avg_completion:.1f}%")
    
    with col4:
        current_lang = advanced_lang_manager.current_language
        current_completion = completion_stats.get(current_lang, 0)
        st.metric("현재 언어 완성도", f"{current_completion:.1f}%")
    
    # 언어별 상세 현황
    st.subheader("언어별 완성도")
    
    language_data = []
    for lang_code, lang_info in advanced_lang_manager.supported_languages.items():
        completion = completion_stats.get(lang_code, 0)
        lang_stats = validation_result["languages"].get(lang_code, {})
        
        language_data.append({
            "언어": f"{lang_info['flag']} {lang_info['name']}",
            "코드": lang_code,
            "완성도": f"{completion:.1f}%",
            "번역된 키": lang_stats.get("total_keys", 0),
            "누락된 키": lang_stats.get("missing_count", 0),
            "상태": "🟢 완료" if completion > 95 else "🟡 진행중" if completion > 50 else "🔴 미완성"
        })
    
    df = pd.DataFrame(language_data)
    st.dataframe(df, use_container_width=True)
    
    # 누락된 키 상세 정보
    st.subheader("누락된 번역 키")
    
    missing_keys = validation_result.get("missing_keys", {})
    if any(missing_keys.values()):
        for lang_code, keys in missing_keys.items():
            if keys:
                lang_info = advanced_lang_manager.supported_languages[lang_code]
                st.write(f"**{lang_info['flag']} {lang_info['name']} ({len(keys)}개 누락)**")
                
                # 첫 10개만 표시
                keys_to_show = keys[:10]
                st.write(", ".join(keys_to_show))
                if len(keys) > 10:
                    st.write(f"*(외 {len(keys) - 10}개)*")
                st.write("")
    else:
        st.success("🎉 모든 언어의 번역이 완료되었습니다!")
    
    # 번역 보고서 다운로드
    if st.button("📋 상세 보고서 생성"):
        report = advanced_lang_manager.generate_translation_report()
        st.download_button(
            label="📥 보고서 다운로드",
            data=report,
            file_name="translation_report.md",
            mime="text/markdown"
        )

def show_hardcoded_scan():
    """하드코딩된 텍스트 스캔"""
    st.header("🔍 하드코딩 텍스트 스캔")
    
    st.info("프로젝트 파일에서 하드코딩된 한국어 텍스트를 자동으로 찾아 번역 키로 교체할 위치를 찾습니다.")
    
    if st.button("🔍 프로젝트 스캔 시작", type="primary"):
        with st.spinner("프로젝트 파일들을 스캔하고 있습니다..."):
            scan_results = migration_tool.scan_project_files()
        
        if scan_results:
            total_items = sum(len(items) for items in scan_results.values())
            st.success(f"✅ 스캔 완료: {len(scan_results)}개 파일에서 {total_items}개의 하드코딩 텍스트 발견")
            
            # 파일별 결과 표시
            for file_path, items in scan_results.items():
                with st.expander(f"📄 {file_path} ({len(items)}개 항목)"):
                    for i, item in enumerate(items):
                        col1, col2 = st.columns([1, 2])
                        
                        with col1:
                            st.write(f"**라인 {item['line']}** ({item['type']})")
                            st.code(item['context'], language='python')
                        
                        with col2:
                            st.write("**원본 텍스트:**")
                            st.write(f"`{item['original_text']}`")
                            
                            st.write("**제안된 교체 코드:**")
                            st.code(item['suggested_replacement'], language='python')
                            
                            st.write(f"**번역 키:** `{item['translation_key']}`")
            
            # 마이그레이션 보고서
            st.subheader("📊 마이그레이션 요약")
            report = migration_tool.generate_migration_report()
            st.markdown(report)
            
        else:
            st.success("🎉 하드코딩된 텍스트가 발견되지 않았습니다!")

def show_translation_editor():
    """번역 편집기"""
    st.header("✏️ 번역 편집기")
    
    # 언어 선택
    lang_options = advanced_lang_manager.get_language_selector_options()
    selected_lang = st.selectbox(
        "편집할 언어 선택:",
        options=list(lang_options.keys()),
        format_func=lambda x: lang_options[x],
        index=list(lang_options.keys()).index(advanced_lang_manager.current_language)
    )
    
    if selected_lang != advanced_lang_manager.current_language:
        advanced_lang_manager.set_language(selected_lang)
    
    # 번역 카테고리 선택
    categories = ["app", "menu", "buttons", "labels", "messages", "forms", "tables", "dashboard"]
    selected_category = st.selectbox("카테고리 선택:", categories)
    
    # 번역 편집
    translations = advanced_lang_manager.translations.get(selected_lang, {})
    category_data = translations.get(selected_category, {})
    
    if category_data:
        st.subheader(f"📝 {selected_category} 카테고리 편집")
        
        edited_data = {}
        
        def edit_nested_dict(data, prefix=""):
            nonlocal edited_data
            for key, value in data.items():
                if key.startswith('_'):  # 메타데이터 제외
                    continue
                    
                full_key = f"{prefix}.{key}" if prefix else key
                
                if isinstance(value, dict):
                    st.write(f"**{key}** (하위 카테고리)")
                    edit_nested_dict(value, full_key)
                elif isinstance(value, str):
                    new_value = st.text_input(
                        f"{full_key}",
                        value=value,
                        key=f"edit_{selected_lang}_{full_key}"
                    )
                    if new_value != value:
                        advanced_lang_manager._set_nested_key(edited_data, full_key, new_value)
        
        edit_nested_dict(category_data)
        
        # 저장 버튼
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("💾 변경사항 저장"):
                # 변경사항 적용
                for key, value in edited_data.items():
                    advanced_lang_manager._set_nested_key(translations[selected_category], key, value)
                
                # 파일 저장
                if advanced_lang_manager.save_language_file(selected_lang, translations):
                    st.success("✅ 번역이 저장되었습니다!")
                    st.rerun()
                else:
                    st.error("❌ 저장 중 오류가 발생했습니다.")
    else:
        st.info(f"{selected_category} 카테고리에 번역 항목이 없습니다.")
    
    # 새 번역 키 추가
    st.subheader("➕ 새 번역 키 추가")
    
    col1, col2 = st.columns(2)
    with col1:
        new_key = st.text_input("새 번역 키:", placeholder="예: messages.success.data_saved")
    with col2:
        new_value = st.text_input("번역 텍스트:", placeholder="번역할 텍스트를 입력하세요")
    
    if st.button("➕ 번역 키 추가") and new_key and new_value:
        advanced_lang_manager._set_nested_key(translations, new_key, new_value)
        if advanced_lang_manager.save_language_file(selected_lang, translations):
            st.success(f"✅ 새 번역 키 '{new_key}'가 추가되었습니다!")
            st.rerun()
        else:
            st.error("❌ 추가 중 오류가 발생했습니다.")

def show_auto_migration():
    """자동 마이그레이션"""
    st.header("🔄 자동 번역 마이그레이션")
    
    st.warning("⚠️ 이 기능은 코드 파일을 직접 수정합니다. 사용 전 백업을 권장합니다.")
    
    # 마이그레이션 옵션
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("1️⃣ 누락된 번역 자동 추가")
        
        source_lang = st.selectbox("원본 언어:", ["ko", "en", "vi"], index=0)
        target_langs = st.multiselect(
            "대상 언어들:", 
            ["ko", "en", "vi"],
            default=["en", "vi"]
        )
        
        if st.button("📝 누락된 번역 자동 추가"):
            results = {}
            for target_lang in target_langs:
                if target_lang != source_lang:
                    result = advanced_lang_manager.auto_translate_missing(target_lang, source_lang)
                    results[target_lang] = result
            
            for lang, result in results.items():
                lang_info = advanced_lang_manager.supported_languages[lang]
                if "added" in result:
                    st.success(f"✅ {lang_info['flag']} {lang_info['name']}: {result['added']}개 번역 추가됨")
                else:
                    st.error(f"❌ {lang_info['name']}: {result.get('error', '알 수 없는 오류')}")
    
    with col2:
        st.subheader("2️⃣ 하드코딩 텍스트 자동 교체")
        
        if st.button("🔄 전체 프로젝트 자동 마이그레이션", type="primary"):
            with st.spinner("하드코딩된 텍스트를 자동으로 교체하고 있습니다..."):
                scan_results = migration_tool.scan_project_files()
                
                if scan_results:
                    success_count = 0
                    error_count = 0
                    
                    for file_path, items in scan_results.items():
                        if migration_tool.apply_automatic_migration(file_path, items):
                            success_count += 1
                        else:
                            error_count += 1
                    
                    if success_count > 0:
                        st.success(f"✅ {success_count}개 파일이 성공적으로 마이그레이션되었습니다!")
                    if error_count > 0:
                        st.error(f"❌ {error_count}개 파일에서 오류가 발생했습니다.")
                else:
                    st.info("🎉 마이그레이션할 하드코딩 텍스트가 없습니다!")
    
    # 백업 및 복원
    st.subheader("💾 백업 및 복원")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📦 번역 파일 백업"):
            backup_dir = "locales/backup"
            os.makedirs(backup_dir, exist_ok=True)
            
            backup_count = 0
            for lang_code in advanced_lang_manager.supported_languages.keys():
                lang_file = f"locales/{lang_code}.json"
                backup_file = f"{backup_dir}/{lang_code}_backup_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.json"
                
                if os.path.exists(lang_file):
                    with open(lang_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    with open(backup_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
                    backup_count += 1
            
            st.success(f"✅ {backup_count}개 언어 파일이 백업되었습니다!")
    
    with col2:
        backup_files = []
        backup_dir = "locales/backup"
        if os.path.exists(backup_dir):
            backup_files = [f for f in os.listdir(backup_dir) if f.endswith('.json')]
        
        if backup_files:
            selected_backup = st.selectbox("복원할 백업 선택:", backup_files)
            if st.button("🔄 백업에서 복원"):
                st.warning("이 기능은 현재 번역을 덮어씁니다. 신중하게 사용하세요.")
        else:
            st.info("사용 가능한 백업이 없습니다.")

def show_add_language():
    """새 언어 추가"""
    st.header("➕ 새 언어 추가")
    
    st.info("현재 지원하는 언어 외에 새로운 언어를 추가할 수 있습니다.")
    
    # 현재 지원 언어 표시
    st.subheader("🌍 현재 지원 언어")
    current_languages = []
    for code, info in advanced_lang_manager.supported_languages.items():
        current_languages.append({
            "코드": code,
            "언어명": info['name'], 
            "국기": info['flag'],
            "상태": "✅ 활성" if info['enabled'] else "❌ 비활성"
        })
    
    df = pd.DataFrame(current_languages)
    st.dataframe(df, use_container_width=True)
    
    # 새 언어 추가 폼
    st.subheader("➕ 새 언어 추가")
    
    with st.form("add_language_form"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            new_lang_code = st.text_input(
                "언어 코드 (ISO 639-1):",
                placeholder="예: ja, zh, th",
                max_chars=2
            )
        
        with col2:
            new_lang_name = st.text_input(
                "언어명:",
                placeholder="예: 日本語, 中文, ไทย"
            )
        
        with col3:
            new_lang_flag = st.text_input(
                "국기 이모지:",
                placeholder="예: 🇯🇵, 🇨🇳, 🇹🇭"
            )
        
        submitted = st.form_submit_button("➕ 언어 추가", type="primary")
        
        if submitted:
            if new_lang_code and new_lang_name and new_lang_flag:
                if len(new_lang_code) == 2:
                    if advanced_lang_manager.add_language(new_lang_code, new_lang_name, new_lang_flag):
                        st.success(f"✅ {new_lang_flag} {new_lang_name} 언어가 추가되었습니다!")
                        
                        # 기본 번역 복사
                        copy_result = advanced_lang_manager.auto_translate_missing(new_lang_code, "ko")
                        st.info(f"📝 한국어에서 {copy_result.get('added', 0)}개 번역이 복사되었습니다. (수동 번역 필요)")
                        
                        st.rerun()
                    else:
                        st.error("❌ 언어 추가 중 오류가 발생했습니다.")
                else:
                    st.error("언어 코드는 2자리여야 합니다. (예: ko, en, ja)")
            else:
                st.error("모든 필드를 입력해주세요.")
    
    # 언어 활성화/비활성화
    st.subheader("⚙️ 언어 활성화 관리")
    
    for code, info in advanced_lang_manager.supported_languages.items():
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.write(f"{info['flag']} {info['name']} ({code})")
        
        with col2:
            current_status = info['enabled']
            new_status = st.checkbox(
                "활성화", 
                value=current_status,
                key=f"enable_{code}"
            )
            
            if new_status != current_status:
                advanced_lang_manager.supported_languages[code]['enabled'] = new_status
                status_text = "활성화" if new_status else "비활성화"
                st.success(f"✅ {info['name']} 언어가 {status_text}되었습니다!")

if __name__ == "__main__":
    show_language_management_page()