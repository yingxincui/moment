#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认证工具模块
提供统一的暗号验证和安全检查功能
支持一天内的认证缓存
"""

import streamlit as st
import time
from datetime import datetime, timedelta

def check_authentication():
    """
    检查用户是否已通过暗号验证
    支持一天内的认证缓存
    
    Returns:
        bool: 如果验证通过返回True，否则返回False
    """
    # 检查基本认证状态
    if 'authenticated' not in st.session_state or not st.session_state.authenticated:
        return False
    
    # 检查认证时间戳
    if 'auth_timestamp' not in st.session_state:
        return False
    
    # 检查认证是否在一天内
    try:
        auth_time = datetime.fromtimestamp(st.session_state.auth_timestamp)
        current_time = datetime.now()
        
        # 如果认证时间超过24小时，则认证失效
        if current_time - auth_time > timedelta(hours=24):
            # 清除过期的认证信息
            clear_auth_session()
            return False
            
    except (ValueError, TypeError):
        # 如果时间戳格式不正确，清除认证信息
        clear_auth_session()
        return False
    
    # 检查会话ID匹配（防止会话劫持）
    current_session_id = st.session_state.get('_session_id', 'unknown')
    if st.session_state.get('auth_session_id') != current_session_id:
        return False
    
    return True

def require_authentication():
    """
    要求用户必须通过认证才能访问页面
    
    如果用户未通过认证，会显示错误信息并停止页面执行
    """
    if not check_authentication():
        st.error("🔐 访问被拒绝！请先通过暗号验证。")
        st.info("请返回主页面输入正确的暗号。")
        st.stop()

def set_authentication():
    """
    设置用户认证状态
    记录认证时间戳和会话ID
    """
    current_time = time.time()
    current_session_id = st.session_state.get('_session_id', 'unknown')
    
    st.session_state.authenticated = True
    st.session_state.auth_timestamp = current_time
    st.session_state.auth_session_id = current_session_id

def get_auth_status():
    """
    获取当前认证状态信息
    
    Returns:
        dict: 包含认证状态信息的字典
    """
    auth_time = None
    if 'auth_timestamp' in st.session_state:
        try:
            auth_time = datetime.fromtimestamp(st.session_state.auth_timestamp)
        except (ValueError, TypeError):
            pass
    
    return {
        'authenticated': st.session_state.get('authenticated', False),
        'auth_timestamp': st.session_state.get('auth_timestamp', None),
        'auth_time': auth_time,
        'session_id': st.session_state.get('_session_id', 'unknown'),
        'auth_session_id': st.session_state.get('auth_session_id', None)
    }

def clear_auth_session():
    """
    清除认证会话信息
    """
    if 'authenticated' in st.session_state:
        del st.session_state.authenticated
    if 'auth_timestamp' in st.session_state:
        del st.session_state.auth_timestamp
    if 'auth_session_id' in st.session_state:
        del st.session_state.auth_session_id

def get_remaining_time():
    """
    获取认证剩余时间
    
    Returns:
        str: 剩余时间描述，如果已过期返回None
    """
    if not check_authentication():
        return None
    
    try:
        auth_time = datetime.fromtimestamp(st.session_state.auth_timestamp)
        current_time = datetime.now()
        remaining = timedelta(hours=24) - (current_time - auth_time)
        
        if remaining.total_seconds() <= 0:
            return "已过期"
        
        hours = int(remaining.total_seconds() // 3600)
        minutes = int((remaining.total_seconds() % 3600) // 60)
        
        if hours > 0:
            return f"{hours}小时{minutes}分钟"
        else:
            return f"{minutes}分钟"
            
    except (ValueError, TypeError):
        return None
