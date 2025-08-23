#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
邮件订阅功能模块
包含用户订阅管理、邮件模板和自动发送功能
"""

import streamlit as st
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import json
import os
from datetime import datetime, timedelta
import schedule
import time
import threading
from typing import List, Dict, Optional
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 邮件配置
EMAIL_CONFIG = {
    'smtp_server': 'smtp.qq.com',  # QQ邮箱SMTP服务器
    'smtp_port': 587,
    'sender_email': '',  # 发件人邮箱（需要配置）
    'sender_password': '',  # 发件人授权码（需要配置）
    'use_tls': True
}

# 订阅数据文件
SUBSCRIPTION_FILE = "email_subscriptions.json"

class EmailSubscriptionManager:
    """邮件订阅管理器"""
    
    def __init__(self):
        self.subscriptions = self.load_subscriptions()
        self.setup_email_config()
    
    def setup_email_config(self):
        """设置邮件配置"""
        # 从环境变量或配置文件读取邮件配置
        if os.getenv('SENDER_EMAIL'):
            EMAIL_CONFIG['sender_email'] = os.getenv('SENDER_EMAIL')
        if os.getenv('SENDER_PASSWORD'):
            EMAIL_CONFIG['sender_password'] = os.getenv('SENDER_PASSWORD')
    
    def load_subscriptions(self) -> Dict:
        """加载订阅数据"""
        if os.path.exists(SUBSCRIPTION_FILE):
            try:
                with open(SUBSCRIPTION_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载订阅数据失败: {e}")
                return {}
        return {}
    
    def save_subscriptions(self):
        """保存订阅数据"""
        try:
            with open(SUBSCRIPTION_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.subscriptions, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存订阅数据失败: {e}")
    
    def add_subscription(self, email: str, etf_pools: List[str], frequency: str = 'daily') -> bool:
        """添加订阅"""
        try:
            if email not in self.subscriptions:
                self.subscriptions[email] = {
                    'etf_pools': etf_pools,
                    'frequency': frequency,
                    'subscribe_date': datetime.now().isoformat(),
                    'last_sent': None,
                    'active': True
                }
            else:
                # 更新现有订阅
                self.subscriptions[email].update({
                    'etf_pools': etf_pools,
                    'frequency': frequency,
                    'active': True
                })
            
            self.save_subscriptions()
            logger.info(f"成功添加订阅: {email}")
            return True
        except Exception as e:
            logger.error(f"添加订阅失败: {e}")
            return False
    
    def remove_subscription(self, email: str) -> bool:
        """取消订阅"""
        try:
            if email in self.subscriptions:
                self.subscriptions[email]['active'] = False
                self.save_subscriptions()
                logger.info(f"成功取消订阅: {email}")
                return True
            return False
        except Exception as e:
            logger.error(f"取消订阅失败: {e}")
            return False
    
    def get_active_subscriptions(self) -> Dict:
        """获取活跃订阅"""
        return {email: data for email, data in self.subscriptions.items() 
                if data.get('active', False)}
    
    def update_last_sent(self, email: str):
        """更新最后发送时间"""
        if email in self.subscriptions:
            self.subscriptions[email]['last_sent'] = datetime.now().isoformat()
            self.save_subscriptions()

class EmailTemplate:
    """邮件模板管理器"""
    
    @staticmethod
    def create_momentum_report_html(etf_pool_name: str, momentum_results: List, 
                                   bias_results: List, trend_summary: Dict) -> str:
        """创建动量报告HTML邮件"""
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>ETF动量策略日报 - {etf_pool_name}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 800px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                .header {{ text-align: center; border-bottom: 3px solid #007bff; padding-bottom: 20px; margin-bottom: 30px; }}
                .header h1 {{ color: #007bff; margin: 0; }}
                .header .date {{ color: #666; font-size: 18px; margin-top: 10px; }}
                .section {{ margin-bottom: 30px; }}
                .section h2 {{ color: #333; border-left: 4px solid #007bff; padding-left: 15px; }}
                .etf-card {{ background-color: #f8f9fa; border-radius: 8px; padding: 15px; margin: 10px 0; border-left: 4px solid #28a745; }}
                .etf-code {{ font-weight: bold; color: #007bff; font-size: 18px; }}
                .etf-name {{ color: #666; margin: 5px 0; }}
                .momentum-value {{ font-size: 20px; font-weight: bold; }}
                .positive {{ color: #28a745; }}
                .negative {{ color: #dc3545; }}
                .neutral {{ color: #6c757d; }}
                .bias-table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
                .bias-table th, .bias-table td {{ border: 1px solid #ddd; padding: 10px; text-align: center; }}
                .bias-table th {{ background-color: #007bff; color: white; }}
                .bias-table tr:nth-child(even) {{ background-color: #f2f2f2; }}
                .summary-stats {{ display: flex; justify-content: space-between; margin: 20px 0; }}
                .stat-item {{ text-align: center; flex: 1; }}
                .stat-value {{ font-size: 24px; font-weight: bold; color: #007bff; }}
                .stat-label {{ color: #666; margin-top: 5px; }}
                .footer {{ text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #666; }}
                .unsubscribe {{ color: #dc3545; text-decoration: none; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1> ETF动量策略日报</h1>
                    <div class="date">{etf_pool_name} - {datetime.now().strftime('%Y年%m月%d日')}</div>
                </div>
                
                <div class="section">
                    <h2> 今日推荐持仓</h2>
                    {EmailTemplate._render_recommended_holdings(momentum_results)}
                </div>
                
                <div class="section">
                    <h2> 动量排名概览</h2>
                    {EmailTemplate._render_momentum_overview(momentum_results)}
                </div>
                
                <div class="section">
                    <h2> Bias分析汇总</h2>
                    {EmailTemplate._render_bias_summary(bias_results)}
                </div>
                
                <div class="section">
                    <h2> 市场表现统计</h2>
                    {EmailTemplate._render_market_summary(trend_summary)}
                </div>
                
                <div class="footer">
                    <p>本邮件由ETF动量策略系统自动生成</p>
                    <p>如需取消订阅，请点击 <a href="#" class="unsubscribe">取消订阅</a></p>
                    <p>发送时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    @staticmethod
    def _render_recommended_holdings(momentum_results: List) -> str:
        """渲染推荐持仓部分"""
        if not momentum_results:
            return "<p>暂无推荐持仓</p>"
        
        html = ""
        for i, etf in enumerate(momentum_results[:3], 1):  # 显示前3名
            if len(etf) >= 5:
                etf_code = etf[0]
                etf_name = etf[1]
                momentum = etf[4] * 100
                momentum_class = "positive" if momentum > 0 else "negative" if momentum < 0 else "neutral"
                
                html += f"""
                <div class="etf-card">
                    <div class="etf-code">#{i} {etf_code}</div>
                    <div class="etf-name">{etf_name}</div>
                    <div class="momentum-value {momentum_class}">{momentum:.2f}%</div>
                </div>
                """
        
        return html
    
    @staticmethod
    def _render_momentum_overview(momentum_results: List) -> str:
        """渲染动量概览部分"""
        if not momentum_results:
            return "<p>暂无动量数据</p>"
        
        # 统计正负动量数量
        positive_count = sum(1 for etf in momentum_results if len(etf) >= 5 and etf[4] > 0)
        negative_count = sum(1 for etf in momentum_results if len(etf) >= 5 and etf[4] < 0)
        total_count = len([etf for etf in momentum_results if len(etf) >= 5])
        
        html = f"""
        <div class="summary-stats">
            <div class="stat-item">
                <div class="stat-value">{positive_count}</div>
                <div class="stat-label">上涨标的</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{negative_count}</div>
                <div class="stat-label">下跌标的</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{total_count}</div>
                <div class="stat-label">总标的数</div>
            </div>
        </div>
        """
        
        return html
    
    @staticmethod
    def _render_bias_summary(bias_results: List) -> str:
        """渲染Bias分析汇总"""
        if not bias_results:
            return "<p>暂无Bias分析数据</p>"
        
        # 统计超买超卖情况
        overbought_count = sum(1 for result in bias_results if '超买' in result.get('超买超卖结论', ''))
        oversold_count = sum(1 for result in bias_results if '超卖' in result.get('超买超卖结论', ''))
        normal_count = len(bias_results) - overbought_count - oversold_count
        
        html = f"""
        <div class="summary-stats">
            <div class="stat-item">
                <div class="stat-value" style="color: #dc3545;">{overbought_count}</div>
                <div class="stat-label">超买标的</div>
            </div>
            <div class="stat-item">
                <div class="stat-value" style="color: #28a745;">{oversold_count}</div>
                <div class="stat-label">超卖标的</div>
            </div>
            <div class="stat-item">
                <div class="stat-value" style="color: #6c757d;">{normal_count}</div>
                <div class="stat-label">正常标的</div>
            </div>
        </div>
        """
        
        return html
    
    @staticmethod
    def _render_market_summary(trend_summary: Dict) -> str:
        """渲染市场表现汇总"""
        if not trend_summary:
            return "<p>暂无市场表现数据</p>"
        
        html = f"""
        <div class="summary-stats">
            <div class="stat-item">
                <div class="stat-value">{trend_summary.get('positive_count', 0)}</div>
                <div class="stat-label">上涨标的</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{trend_summary.get('negative_count', 0)}</div>
                <div class="stat-label">下跌标的</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{trend_summary.get('best_performer', 'N/A')}</div>
                <div class="stat-label">表现最佳</div>
            </div>
        </div>
        """
        
        return html

class EmailSender:
    """邮件发送器"""
    
    def __init__(self):
        self.config = EMAIL_CONFIG
    
    def send_email(self, to_email: str, subject: str, html_content: str, 
                   text_content: str = None) -> bool:
        """发送邮件"""
        try:
            if not self.config['sender_email'] or not self.config['sender_password']:
                logger.error("邮件配置不完整，请先配置发件人邮箱和密码")
                return False
            
            # 创建邮件
            msg = MIMEMultipart('alternative')
            msg['From'] = self.config['sender_email']
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # 添加HTML内容
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            # 添加纯文本内容（备用）
            if text_content:
                text_part = MIMEText(text_content, 'plain', 'utf-8')
                msg.attach(text_part)
            
            # 发送邮件
            with smtplib.SMTP(self.config['smtp_server'], self.config['smtp_port']) as server:
                if self.config['use_tls']:
                    server.starttls()
                server.login(self.config['sender_email'], self.config['sender_password'])
                server.send_message(msg)
            
            logger.info(f"成功发送邮件到: {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"发送邮件失败: {e}")
            return False

class DailyReportScheduler:
    """每日报告调度器"""
    
    def __init__(self, subscription_manager: EmailSubscriptionManager, 
                 email_sender: EmailSender):
        self.subscription_manager = subscription_manager
        self.email_sender = email_sender
        self.running = False
    
    def start_scheduler(self):
        """启动调度器"""
        if self.running:
            return
        
        self.running = True
        
        # 设置每日发送时间（这里设置为每天下午6点）
        schedule.every().day.at("18:00").do(self.send_daily_reports)
        
        # 启动调度器线程
        scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        scheduler_thread.start()
        
        logger.info("邮件调度器已启动")
    
    def stop_scheduler(self):
        """停止调度器"""
        self.running = False
        logger.info("邮件调度器已停止")
    
    def _run_scheduler(self):
        """运行调度器"""
        while self.running:
            schedule.run_pending()
            time.sleep(60)  # 每分钟检查一次
    
    def send_daily_reports(self):
        """发送每日报告"""
        logger.info("开始发送每日报告...")
        
        active_subscriptions = self.subscription_manager.get_active_subscriptions()
        
        for email, subscription_data in active_subscriptions.items():
            try:
                # 这里需要调用动量分析函数获取数据
                # 由于是在后台运行，我们需要从缓存或数据库获取数据
                momentum_results = self._get_cached_momentum_results(subscription_data['etf_pools'])
                bias_results = self._get_cached_bias_results(subscription_data['etf_pools'])
                trend_summary = self._get_cached_trend_summary(subscription_data['etf_pools'])
                
                if momentum_results:
                    # 生成邮件内容
                    etf_pool_name = " + ".join(subscription_data['etf_pools'])
                    html_content = EmailTemplate.create_momentum_report_html(
                        etf_pool_name, momentum_results, bias_results, trend_summary
                    )
                    
                    # 发送邮件
                    subject = f" ETF动量策略日报 - {etf_pool_name} - {datetime.now().strftime('%Y-%m-%d')}"
                    
                    if self.email_sender.send_email(email, subject, html_content):
                        self.subscription_manager.update_last_sent(email)
                        logger.info(f"成功发送每日报告到: {email}")
                    else:
                        logger.error(f"发送每日报告失败: {email}")
                
            except Exception as e:
                logger.error(f"处理订阅 {email} 时出错: {e}")
        
        logger.info("每日报告发送完成")
    
    def _get_cached_momentum_results(self, etf_pools: List[str]) -> List:
        """获取缓存的动量结果（这里需要根据实际缓存机制实现）"""
        # TODO: 实现从缓存获取动量结果的逻辑
        return []
    
    def _get_cached_bias_results(self, etf_pools: List[str]) -> List:
        """获取缓存的Bias结果"""
        # TODO: 实现从缓存获取Bias结果的逻辑
        return []
    
    def _get_cached_trend_summary(self, etf_pools: List[str]) -> Dict:
        """获取缓存的趋势汇总"""
        # TODO: 实现从缓存获取趋势汇总的逻辑
        return {}

def render_email_subscription_ui():
    """渲染邮件订阅UI"""
    st.subheader(" 邮件订阅管理")
    
    # 初始化订阅管理器
    if 'email_subscription_manager' not in st.session_state:
        st.session_state.email_subscription_manager = EmailSubscriptionManager()
    
    subscription_manager = st.session_state.email_subscription_manager
    
    # 订阅表单
    with st.expander("➕ 添加新订阅", expanded=True):
        st.markdown("**订阅设置**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            email = st.text_input(" 邮箱地址", placeholder="your_email@example.com")
            frequency = st.selectbox(" 发送频率", ["daily", "weekly"], 
                                   format_func=lambda x: "每日" if x == "daily" else "每周")
        
        with col2:
            etf_pools = st.multiselect(
                " ETF组合",
                ["默认组合", "科创创业", "全球股市轮动", "明总定制组合"],
                default=["默认组合"]
            )
        
        if st.button(" 订阅", type="primary"):
            if email and etf_pools:
                if subscription_manager.add_subscription(email, etf_pools, frequency):
                    st.success(f" 成功订阅！我们将向 {email} 发送 {', '.join(etf_pools)} 的动量分析报告")
                else:
                    st.error(" 订阅失败，请检查邮箱格式或稍后重试")
            else:
                st.warning(" 请填写邮箱地址并选择至少一个ETF组合")
    
    # 订阅管理
    st.subheader(" 当前订阅")
    
    active_subscriptions = subscription_manager.get_active_subscriptions()
    
    if not active_subscriptions:
        st.info("📭 暂无活跃订阅")
    else:
        for email, data in active_subscriptions.items():
            with st.expander(f" {email}", expanded=False):
                col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
                
                with col1:
                    st.write("**ETF组合:**")
                    for pool in data['etf_pools']:
                        st.write(f"• {pool}")
                
                with col2:
                    st.write("**发送频率:**")
                    freq_text = "每日" if data['frequency'] == 'daily' else "每周"
                    st.write(f"• {freq_text}")
                
                with col3:
                    st.write("**订阅时间:**")
                    subscribe_date = datetime.fromisoformat(data['subscribe_date'])
                    st.write(f"• {subscribe_date.strftime('%Y-%m-%d')}")
                
                with col4:
                    if st.button(" 取消", key=f"cancel_{email}"):
                        if subscription_manager.remove_subscription(email):
                            st.success(" 已取消订阅")
                            st.rerun()
                        else:
                            st.error(" 取消失败")
    
    # 邮件配置
    st.subheader("⚙️ 邮件配置")
    
    with st.expander(" 配置发件人邮箱"):
        st.markdown("""
        **配置说明：**
        1. 使用QQ邮箱作为发件人邮箱
        2. 需要在QQ邮箱设置中开启SMTP服务
        3. 使用授权码而不是登录密码
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            sender_email = st.text_input(" 发件人邮箱", 
                                       value=EMAIL_CONFIG['sender_email'],
                                       placeholder="your_qq@qq.com")
        
        with col2:
            sender_password = st.text_input("🔑 授权码", 
                                          value=EMAIL_CONFIG['sender_password'],
                                          type="password",
                                          placeholder="QQ邮箱授权码")
        
        if st.button("💾 保存配置"):
            EMAIL_CONFIG['sender_email'] = sender_email
            EMAIL_CONFIG['sender_password'] = sender_password
            
            # 保存到环境变量或配置文件
            st.success(" 邮件配置已保存")
    
    # 手动发送测试邮件
    st.subheader("🧪 测试邮件")
    
    test_email = st.text_input(" 测试邮箱地址", placeholder="test@example.com")
    
    if st.button("📤 发送测试邮件"):
        if test_email and EMAIL_CONFIG['sender_email'] and EMAIL_CONFIG['sender_password']:
            email_sender = EmailSender()
            
            # 创建测试邮件内容
            test_html = """
            <html>
            <body>
                <h2>🧪 ETF动量策略系统测试邮件</h2>
                <p>这是一封测试邮件，用于验证邮件配置是否正确。</p>
                <p>发送时间: {}</p>
                <p>如果收到此邮件，说明邮件配置成功！</p>
            </body>
            </html>
            """.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            
            if email_sender.send_email(test_email, "🧪 ETF动量策略系统测试邮件", test_html):
                st.success(" 测试邮件发送成功！")
            else:
                st.error(" 测试邮件发送失败，请检查邮件配置")
        else:
            st.warning(" 请填写测试邮箱地址并确保邮件配置完整")

def start_email_scheduler():
    """启动邮件调度器"""
    if 'email_scheduler' not in st.session_state:
        subscription_manager = EmailSubscriptionManager()
        email_sender = EmailSender()
        scheduler = DailyReportScheduler(subscription_manager, email_sender)
        st.session_state.email_scheduler = scheduler
        scheduler.start_scheduler()

# 在应用启动时启动邮件调度器
if __name__ == "__main__":
    start_email_scheduler()
