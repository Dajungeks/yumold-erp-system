"""
노트 위젯 컴포넌트 - 각 페이지에서 사용할 수 있는 노트 작성 위젯
"""

import streamlit as st
from datetime import datetime

def show_page_note_widget(note_manager, page_name, get_text=None):
    """
    페이지별 노트 위젯을 표시합니다.
    
    Args:
        note_manager: SQLiteNoteManager 인스턴스
        page_name: 페이지 식별자 (예: 'dashboard', 'employee_management' 등)
        get_text: 다국어 텍스트 함수 (선택사항)
    """
    
    # 기본 텍스트 설정
    if get_text is None:
        def get_text(key):
            texts = {
                'page_memo': '페이지 메모',
                'memo_placeholder': '이 페이지에 대한 메모를 작성하세요... (최대 200자)',
                'save_memo': '메모 저장',
                'delete_memo': '메모 삭제',
                'memo_saved': '✅ 메모가 저장되었습니다!',
                'memo_deleted': '✅ 메모가 삭제되었습니다!',
                'memo_save_failed': '❌ 메모 저장에 실패했습니다.',
                'memo_delete_failed': '❌ 메모 삭제에 실패했습니다.',
                'last_updated': '마지막 수정'
            }
            return texts.get(key, key)
    
    # 현재 사용자 ID 가져오기
    user_id = st.session_state.get('user_id', 'unknown')
    
    # 사이드바에 노트 위젯 표시
    with st.sidebar:
        st.markdown("---")
        st.subheader(f"📝 {get_text('page_memo')}")
        
        # 기존 노트 내용 로드
        existing_note = note_manager.get_user_note(user_id, page_name)
        current_content = existing_note['content'] if existing_note else ""
        
        # 노트 입력 폼
        with st.form(f"note_form_{page_name}"):
            note_content = st.text_area(
                label="메모 내용",
                label_visibility="collapsed",
                value=current_content,
                placeholder=get_text('memo_placeholder'),
                max_chars=200,
                height=100,
                help="최대 200자까지 입력 가능합니다."
            )
            
            # 버튼들
            col1, col2 = st.columns(2)
            
            with col1:
                save_clicked = st.form_submit_button(
                    f"💾 {get_text('save_memo')}", 
                    type="primary",
                    use_container_width=True
                )
            
            with col2:
                delete_clicked = st.form_submit_button(
                    f"🗑️ {get_text('delete_memo')}", 
                    use_container_width=True
                )
            
            # 저장 처리
            if save_clicked:
                if note_content.strip():
                    success = note_manager.save_user_note(user_id, page_name, note_content.strip())
                    if success:
                        st.success(get_text('memo_saved'))
                        st.rerun()
                    else:
                        st.error(get_text('memo_save_failed'))
                else:
                    # 빈 내용이면 삭제
                    success = note_manager.delete_user_note(user_id, page_name)
                    if success:
                        st.success(get_text('memo_deleted'))
                        st.rerun()
            
            # 삭제 처리
            if delete_clicked:
                success = note_manager.delete_user_note(user_id, page_name)
                if success:
                    st.success(get_text('memo_deleted'))
                    st.rerun()
                else:
                    st.error(get_text('memo_delete_failed'))
        
        # 마지막 수정 시간 표시
        if existing_note and existing_note.get('updated_date'):
            try:
                updated_time = datetime.fromisoformat(existing_note['updated_date']).strftime('%Y-%m-%d %H:%M')
                st.caption(f"{get_text('last_updated')}: {updated_time}")
            except:
                pass

def show_compact_note_widget(note_manager, page_name, container=None):
    """
    컴팩트한 노트 위젯 (메인 페이지 상단에 표시용)
    
    Args:
        note_manager: SQLiteNoteManager 인스턴스
        page_name: 페이지 식별자
        container: Streamlit 컨테이너 (선택사항)
    """
    
    # 컨테이너 설정
    if container is None:
        container = st
    
    user_id = st.session_state.get('user_id', 'unknown')
    
    # 기존 노트 내용 로드
    existing_note = note_manager.get_user_note(user_id, page_name)
    current_content = existing_note['content'] if existing_note else ""
    
    # 노트가 있으면 간략히 표시
    if current_content:
        with container.expander("📝 페이지 메모", expanded=False):
            st.write(current_content)
            
            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button("✏️ 수정", key=f"edit_note_{page_name}"):
                    st.session_state[f'show_note_editor_{page_name}'] = True
    
    # 노트 편집기 표시
    if st.session_state.get(f'show_note_editor_{page_name}', False) or not current_content:
        with container.container():
            st.subheader("📝 페이지 메모 작성")
            
            with st.form(f"compact_note_form_{page_name}"):
                note_content = st.text_area(
                    label="메모 내용",
                    value=current_content,
                    placeholder="이 페이지에 대한 메모를 작성하세요... (최대 200자)",
                    max_chars=200,
                    height=80
                )
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    save_clicked = st.form_submit_button("💾 저장", type="primary")
                
                with col2:
                    if current_content:
                        delete_clicked = st.form_submit_button("🗑️ 삭제")
                    else:
                        delete_clicked = False
                
                with col3:
                    cancel_clicked = st.form_submit_button("❌ 취소")
                
                # 처리
                if save_clicked and note_content.strip():
                    success = note_manager.save_user_note(user_id, page_name, note_content.strip())
                    if success:
                        st.success("✅ 메모가 저장되었습니다!")
                        st.session_state[f'show_note_editor_{page_name}'] = False
                        st.rerun()
                
                if delete_clicked:
                    success = note_manager.delete_user_note(user_id, page_name)
                    if success:
                        st.success("✅ 메모가 삭제되었습니다!")
                        st.session_state[f'show_note_editor_{page_name}'] = False
                        st.rerun()
                
                if cancel_clicked:
                    st.session_state[f'show_note_editor_{page_name}'] = False
                    st.rerun()