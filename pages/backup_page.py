"""
시스템 백업 및 복원 관리 페이지
UTF-8 인코딩 문제 없이 안전한 백업/복원 기능 제공
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from managers.backup_manager import BackupManager
import os
import json

def show_backup_page(auth_manager=None, get_text=lambda x: x):
    """백업 관리 페이지를 표시합니다"""
    
    # 권한 확인 (관리자만 접근 가능)
    current_user_type = st.session_state.get('user_type', '')
    current_user_id = st.session_state.get('user_id', '')
    
    if current_user_type != 'master':
        st.error("🔒 백업 관리는 관리자만 접근할 수 있습니다.")
        st.info("관리자 계정으로 로그인해주세요.")
        return
    
    st.title("💾 시스템 백업 및 복원")
    st.caption("전체 시스템의 데이터베이스, 설정 파일, 템플릿을 안전하게 백업하고 복원합니다")
    
    # 백업 매니저 초기화
    try:
        backup_manager = BackupManager()
        system_info = backup_manager.get_system_info()
    except Exception as e:
        st.error(f"백업 시스템 초기화 실패: {str(e)}")
        return
    
    # 시스템 상태 표시
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        db_status = "✅ 정상" if system_info.get("database_exists") else "❌ 없음"
        st.metric("데이터베이스", db_status)
    
    with col2:
        db_size = system_info.get("database_size", 0) / 1024 / 1024  # MB 변환
        st.metric("DB 크기", f"{db_size:.1f} MB")
    
    with col3:
        st.metric("언어 파일", f"{system_info.get('languages_count', 0)}개")
    
    with col4:
        st.metric("사용 가능한 백업", f"{system_info.get('backup_count', 0)}개")
    
    st.divider()
    
    # 탭 구성
    tab1, tab2, tab3 = st.tabs(["🆕 백업 생성", "📂 백업 관리", "🔄 복원"])
    
    # 탭 1: 백업 생성
    with tab1:
        show_backup_creation_tab(backup_manager)
    
    # 탭 2: 백업 목록
    with tab2:
        show_backup_list_tab(backup_manager)
    
    # 탭 3: 복원
    with tab3:
        show_restore_tab(backup_manager)

def show_backup_creation_tab(backup_manager):
    """백업 생성 탭"""
    st.subheader("🆕 새 백업 생성")
    
    # 백업 카테고리 선택
    backup_items = backup_manager.get_backup_items()
    
    st.markdown("### 백업할 항목 선택")
    
    selected_categories = []
    
    col1, col2 = st.columns(2)
    
    with col1:
        for category, config in list(backup_items.items())[:3]:
            if st.checkbox(f"**{config['description']}**", key=f"backup_{category}", value=True):
                selected_categories.append(category)
                st.caption(f"포함: {', '.join(config.get('files', []) + config.get('directories', []))}")
    
    with col2:
        for category, config in list(backup_items.items())[3:]:
            if st.checkbox(f"**{config['description']}**", key=f"backup_{category}", value=True):
                selected_categories.append(category)
                st.caption(f"포함: {', '.join(config.get('files', []) + config.get('directories', []))}")
    
    st.divider()
    
    # 백업 생성 버튼
    col_center = st.columns([1, 2, 1])
    
    with col_center[1]:
        if st.button("💾 백업 생성", type="primary", use_container_width=True):
            if not selected_categories:
                st.error("❌ 최소 하나의 항목을 선택해주세요.")
                return
            
            with st.spinner("백업을 생성하는 중..."):
                try:
                    result = backup_manager.create_backup(selected_categories)
                    
                    if result["status"] == "success":
                        st.success("✅ 백업이 성공적으로 생성되었습니다!")
                        
                        # 백업 결과 상세 정보
                        st.info(f"📁 백업 파일: {result['filename']}")
                        st.info(f"📊 총 파일 수: {result['total_files']}개")
                        st.info(f"💾 총 크기: {result['total_size'] / 1024 / 1024:.1f} MB")
                        
                        if result.get("errors"):
                            st.warning("⚠️ 일부 파일에서 오류가 발생했습니다:")
                            for error in result["errors"][:5]:  # 최대 5개만 표시
                                st.write(f"- {error}")
                        
                        # 자동 새로고침을 위한 rerun
                        st.rerun()
                    else:
                        st.error(f"❌ 백업 생성 실패: {result.get('error', '알 수 없는 오류')}")
                
                except Exception as e:
                    st.error(f"❌ 백업 생성 중 오류 발생: {str(e)}")

def show_backup_list_tab(backup_manager):
    """백업 목록 탭"""
    st.subheader("📂 백업 목록")
    
    try:
        backups = backup_manager.list_backups()
        
        if not backups:
            st.info("생성된 백업이 없습니다.")
            return
        
        # 백업 목록 표시
        for i, backup in enumerate(backups):
            with st.expander(f"📦 {backup['filename']} ({backup['created'].strftime('%Y-%m-%d %H:%M:%S')})"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**생성일시:** {backup['created'].strftime('%Y-%m-%d %H:%M:%S')}")
                    st.write(f"**파일 크기:** {backup['size'] / 1024 / 1024:.1f} MB")
                    
                    # 메타데이터 정보 표시
                    if 'metadata' in backup:
                        metadata = backup['metadata']
                        st.write(f"**포함 파일:** {metadata.get('total_files', 0)}개")
                        if metadata.get('errors'):
                            st.write(f"**오류:** {len(metadata['errors'])}개")
                
                with col2:
                    # 다운로드 버튼
                    try:
                        with open(backup['path'], 'rb') as f:
                            backup_data = f.read()
                            st.download_button(
                                label="💾 다운로드",
                                data=backup_data,
                                file_name=backup['filename'],
                                mime="application/zip",
                                key=f"download_{i}",
                                use_container_width=True
                            )
                    except Exception as e:
                        st.error(f"파일 읽기 오류: {str(e)}")
                
                # 하단 버튼들 (별도 행으로)
                col_btn1, col_btn2 = st.columns(2)
                
                with col_btn1:
                    if st.button("🔍 상세 정보", key=f"info_{i}", use_container_width=True):
                        show_backup_details(backup)
                
                with col_btn2:
                    if st.button("🗑️ 삭제", key=f"delete_{i}", use_container_width=True):
                        if st.session_state.get(f'confirm_delete_backup_{i}', False):
                            # 삭제 실행
                            try:
                                result = backup_manager.delete_backup(backup['filename'])
                                if result['status'] == 'success':
                                    st.success("백업이 삭제되었습니다.")
                                    st.rerun()
                                else:
                                    st.error(f"삭제 실패: {result['error']}")
                            except Exception as e:
                                st.error(f"삭제 중 오류: {str(e)}")
                        else:
                            # 삭제 확인
                            st.session_state[f'confirm_delete_backup_{i}'] = True
                            st.warning("정말 삭제하시겠습니까? 다시 클릭하면 삭제됩니다.")
    
    except Exception as e:
        st.error(f"백업 목록 조회 실패: {str(e)}")

def show_backup_details(backup):
    """백업 상세 정보 표시"""
    st.markdown("### 📋 백업 상세 정보")
    
    if 'metadata' in backup:
        metadata = backup['metadata']
        
        # 백업 항목별 정보
        for category, info in metadata.get('items', {}).items():
            st.markdown(f"**{category}:**")
            st.write(f"- 파일 수: {info['count']}개")
            st.write(f"- 크기: {info['size'] / 1024 / 1024:.1f} MB")
            
            if info['files']:
                with st.expander(f"{category} 파일 목록"):
                    for file_info in info['files'][:10]:  # 최대 10개만 표시
                        st.write(f"- {file_info['path']} ({file_info['size'] / 1024:.1f} KB)")
                    
                    if len(info['files']) > 10:
                        st.write(f"... 및 {len(info['files']) - 10}개 더")

def show_restore_tab(backup_manager):
    """복원 탭"""
    st.subheader("🔄 시스템 복원")
    
    st.warning("⚠️ **주의사항**")
    st.write("- 복원하면 현재 데이터가 백업 데이터로 덮어씌워집니다")
    st.write("- 복원 전에 현재 시스템을 백업하는 것을 권장합니다")
    st.write("- 복원 후 시스템이 다시 시작될 수 있습니다")
    
    st.divider()
    
    try:
        backups = backup_manager.list_backups()
        
        if not backups:
            st.info("복원할 백업이 없습니다.")
            return
        
        # 백업 선택
        backup_options = [
            f"{backup['filename']} ({backup['created'].strftime('%Y-%m-%d %H:%M')})"
            for backup in backups
        ]
        
        selected_backup_idx = st.selectbox(
            "복원할 백업 선택",
            range(len(backup_options)),
            format_func=lambda x: backup_options[x]
        )
        
        if selected_backup_idx is not None:
            selected_backup = backups[selected_backup_idx]
            
            st.markdown("### 선택된 백업 정보")
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**파일명:** {selected_backup['filename']}")
                st.write(f"**생성일시:** {selected_backup['created'].strftime('%Y-%m-%d %H:%M:%S')}")
            
            with col2:
                st.write(f"**크기:** {selected_backup['size'] / 1024 / 1024:.1f} MB")
                if 'metadata' in selected_backup:
                    st.write(f"**파일 수:** {selected_backup['metadata'].get('total_files', 0)}개")
            
            st.divider()
            
            # 복원 카테고리 선택
            st.markdown("### 복원할 항목 선택")
            
            backup_items = backup_manager.get_backup_items()
            restore_categories = []
            
            col1, col2 = st.columns(2)
            
            with col1:
                for category, config in list(backup_items.items())[:3]:
                    if st.checkbox(f"**{config['description']}**", key=f"restore_{category}", value=True):
                        restore_categories.append(category)
            
            with col2:
                for category, config in list(backup_items.items())[3:]:
                    if st.checkbox(f"**{config['description']}**", key=f"restore_{category}", value=True):
                        restore_categories.append(category)
            
            st.divider()
            
            # 복원 실행
            col_center = st.columns([1, 2, 1])
            
            with col_center[1]:
                if st.button("🔄 복원 실행", type="primary", use_container_width=True):
                    if not restore_categories:
                        st.error("❌ 최소 하나의 항목을 선택해주세요.")
                        return
                    
                    # 복원 확인
                    if not st.session_state.get('confirm_restore', False):
                        st.session_state['confirm_restore'] = True
                        st.warning("⚠️ 정말로 복원하시겠습니까? 현재 데이터가 덮어씌워집니다.")
                        st.info("다시 한 번 클릭하면 복원이 시작됩니다.")
                        return
                    
                    with st.spinner("시스템을 복원하는 중..."):
                        try:
                            result = backup_manager.restore_backup(
                                selected_backup['filename'], 
                                restore_categories
                            )
                            
                            if result["status"] == "success":
                                st.success("✅ 시스템이 성공적으로 복원되었습니다!")
                                st.info(f"📊 복원된 파일: {result['total_files']}개")
                                
                                if result.get("errors"):
                                    st.warning("⚠️ 일부 파일에서 오류가 발생했습니다:")
                                    for error in result["errors"][:5]:
                                        st.write(f"- {error}")
                                
                                st.info("🔄 변경사항을 적용하기 위해 시스템을 다시 시작해주세요.")
                                
                                # 확인 상태 리셋
                                st.session_state['confirm_restore'] = False
                                
                            else:
                                st.error(f"❌ 복원 실패: {result.get('error', '알 수 없는 오류')}")
                        
                        except Exception as e:
                            st.error(f"❌ 복원 중 오류 발생: {str(e)}")
    
    except Exception as e:
        st.error(f"복원 준비 중 오류: {str(e)}")