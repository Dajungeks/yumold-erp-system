"""
알림 도우미
"""

import streamlit as st
import logging

logger = logging.getLogger(__name__)

class NotificationHelper:
    @staticmethod
    def show_success(message, key=None):
        """성공 알림"""
        st.success(message, key=key)
        logger.info(f"Success: {message}")
    
    @staticmethod
    def show_error(message, key=None):
        """에러 알림"""
        st.error(message, key=key)
        logger.error(f"Error: {message}")
    
    @staticmethod
    def show_warning(message, key=None):
        """경고 알림"""
        st.warning(message, key=key)
        logger.warning(f"Warning: {message}")
    
    @staticmethod
    def show_info(message, key=None):
        """정보 알림"""
        st.info(message, key=key)
        logger.info(f"Info: {message}")
    
    @staticmethod
    def confirm_action(message):
        """액션 확인"""
        return st.button(message)
    
    @staticmethod
    def show_toast(message, type='info'):
        """토스트 메시지"""
        if type == 'success':
            st.toast(message, icon='✅')
        elif type == 'error':
            st.toast(message, icon='❌')
        else:
            st.toast(message, icon='ℹ️')