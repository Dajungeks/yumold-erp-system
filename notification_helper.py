# notification_helper.py
import streamlit as st
from typing import Optional, Dict, Any
import logging

class NotificationHelper:
    """알림 도우미 클래스"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def show_success(self, message: str, duration: int = 5):
        """성공 메시지 표시"""
        st.success(message)
        self.logger.info(f"Success notification: {message}")
    
    def show_error(self, message: str, duration: int = 5):
        """오류 메시지 표시"""
        st.error(message)
        self.logger.error(f"Error notification: {message}")
    
    def show_warning(self, message: str, duration: int = 5):
        """경고 메시지 표시"""
        st.warning(message)
        self.logger.warning(f"Warning notification: {message}")
    
    def show_info(self, message: str, duration: int = 5):
        """정보 메시지 표시"""
        st.info(message)
        self.logger.info(f"Info notification: {message}")

# 전역 인스턴스
notification_helper = NotificationHelper()
