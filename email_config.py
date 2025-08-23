#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
邮件配置文件
包含邮件发送的相关配置
"""

import os
import json
from typing import Dict, Any

# 默认邮件配置
DEFAULT_EMAIL_CONFIG = {
    'smtp_server': 'smtp.qq.com',  # QQ邮箱SMTP服务器
    'smtp_port': 587,              # SMTP端口
    'use_tls': True,               # 是否使用TLS加密
    'sender_email': '',            # 发件人邮箱
    'sender_password': '',         # 发件人授权码
    'daily_send_time': '18:00',   # 每日发送时间（24小时制）
    'weekly_send_day': 'monday',  # 每周发送日期
    'weekly_send_time': '18:00',  # 每周发送时间
    'max_retries': 3,             # 最大重试次数
    'retry_delay': 300,           # 重试延迟（秒）
}

# 配置文件路径
CONFIG_FILE = "email_config.json"

class EmailConfigManager:
    """邮件配置管理器"""
    
    def __init__(self):
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # 合并默认配置和加载的配置
                    config = DEFAULT_EMAIL_CONFIG.copy()
                    config.update(loaded_config)
                    return config
            except Exception as e:
                print(f"加载邮件配置文件失败: {e}")
                return DEFAULT_EMAIL_CONFIG.copy()
        else:
            # 如果配置文件不存在，创建默认配置文件
            self.save_config(DEFAULT_EMAIL_CONFIG)
            return DEFAULT_EMAIL_CONFIG.copy()
    
    def save_config(self, config: Dict[str, Any]):
        """保存配置文件"""
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存邮件配置文件失败: {e}")
    
    def update_config(self, key: str, value: Any):
        """更新配置项"""
        self.config[key] = value
        self.save_config(self.config)
    
    def get_config(self, key: str = None) -> Any:
        """获取配置项"""
        if key is None:
            return self.config
        return self.config.get(key)
    
    def validate_config(self) -> Dict[str, bool]:
        """验证配置完整性"""
        validation_results = {
            'smtp_server': bool(self.config.get('smtp_server')),
            'smtp_port': bool(self.config.get('smtp_port')),
            'sender_email': bool(self.config.get('sender_email')),
            'sender_password': bool(self.config.get('sender_password')),
            'daily_send_time': bool(self.config.get('daily_send_time')),
        }
        
        # 检查邮箱格式
        if self.config.get('sender_email'):
            validation_results['email_format'] = self._is_valid_email(self.config['sender_email'])
        else:
            validation_results['email_format'] = False
        
        return validation_results
    
    def _is_valid_email(self, email: str) -> bool:
        """验证邮箱格式"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def get_smtp_config(self) -> Dict[str, Any]:
        """获取SMTP配置"""
        return {
            'smtp_server': self.config.get('smtp_server'),
            'smtp_port': self.config.get('smtp_port'),
            'use_tls': self.config.get('use_tls', True),
            'sender_email': self.config.get('sender_email'),
            'sender_password': self.config.get('sender_password'),
        }
    
    def is_config_complete(self) -> bool:
        """检查配置是否完整"""
        required_fields = ['smtp_server', 'smtp_port', 'sender_email', 'sender_password']
        return all(self.config.get(field) for field in required_fields)

# 邮件模板配置
EMAIL_TEMPLATE_CONFIG = {
    'company_name': 'ETF动量策略系统',
    'company_website': 'https://example.com',
    'support_email': 'support@example.com',
    'logo_url': '',  # 可以添加公司logo的URL
    'primary_color': '#007bff',
    'secondary_color': '#6c757d',
    'success_color': '#28a745',
    'warning_color': '#ffc107',
    'danger_color': '#dc3545',
}

# 邮件发送配置
EMAIL_SENDING_CONFIG = {
    'batch_size': 10,           # 批量发送大小
    'send_interval': 5,         # 发送间隔（秒）
    'timeout': 30,              # 发送超时时间（秒）
    'enable_logging': True,     # 是否启用日志
    'log_file': 'email_sending.log',  # 日志文件路径
}

# 创建配置管理器实例
email_config_manager = EmailConfigManager()

def get_email_config() -> Dict[str, Any]:
    """获取邮件配置"""
    return email_config_manager.get_config()

def update_email_config(key: str, value: Any):
    """更新邮件配置"""
    email_config_manager.update_config(key, value)

def is_email_config_complete() -> bool:
    """检查邮件配置是否完整"""
    return email_config_manager.is_config_complete()

def validate_email_config() -> Dict[str, bool]:
    """验证邮件配置"""
    return email_config_manager.validate_config()

if __name__ == "__main__":
    # 测试配置管理器
    print("邮件配置测试:")
    print(f"配置完整性: {is_email_config_complete()}")
    print(f"配置验证: {validate_email_config()}")
    print(f"SMTP配置: {email_config_manager.get_smtp_config()}")
