#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
邮件订阅页面
提供邮件订阅管理功能
"""

import streamlit as st
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# 导入认证工具
from auth_utils import require_authentication

# 要求用户必须通过认证
require_authentication()

from email_subscription import render_email_subscription_ui, start_email_scheduler

# 页面配置
st.set_page_config(
    page_title=" 邮件订阅 - ETF动量策略",
    page_icon="",
    layout="wide"
)

# 页面标题
st.title(" 邮件订阅管理")
st.markdown("---")

# 页面说明
st.markdown("""
###  功能说明

**邮件订阅功能**允许您订阅ETF动量策略的每日分析报告，系统将自动发送包含以下内容的邮件：

 **推荐持仓** - 当日动量策略推荐的ETF
 **动量排名** - 所有ETF的动量排名情况  
 **Bias分析** - 超买超卖状态分析
 **市场表现** - 近一年表现统计

### ⚙️ 使用步骤

1. **配置发件人邮箱** - 设置QQ邮箱和授权码
2. **添加订阅** - 选择邮箱地址和ETF组合
3. **测试邮件** - 发送测试邮件验证配置
4. **自动发送** - 系统将按设定频率自动发送报告

###  技术说明

- 使用QQ邮箱SMTP服务发送邮件
- 支持HTML格式的邮件模板
- 自动调度器确保按时发送
- 数据持久化保存订阅信息
""")

# 启动邮件调度器
start_email_scheduler()

# 渲染邮件订阅UI
render_email_subscription_ui()

# 页面底部说明
st.markdown("---")
st.markdown("""
<div style='background-color: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #007bff;'>
    <strong> 注意事项：</strong><br>
    • 首次使用需要配置发件人QQ邮箱和授权码<br>
    • 授权码需要在QQ邮箱设置中开启SMTP服务后获取<br>
    • 建议先发送测试邮件验证配置是否正确<br>
    • 系统默认每天下午6点自动发送报告<br>
    • 可以随时取消订阅或修改订阅设置
</div>
""", unsafe_allow_html=True)
