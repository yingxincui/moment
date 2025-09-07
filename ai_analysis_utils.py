#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI分析工具模块
提供将表格数据转换为AI可分析格式的功能
"""

import streamlit as st
import pandas as pd
import json
from datetime import datetime
import clipboard

def format_data_for_ai(data, data_type="momentum_results"):
    """
    将数据格式化为AI可分析的文本格式
    
    Args:
        data: 要分析的数据
        data_type: 数据类型 (momentum_results, bias_results, trend_data等)
    
    Returns:
        formatted_text: 格式化后的文本
    """
    if data_type == "momentum_results":
        return format_momentum_data_for_ai(data)
    elif data_type == "bias_results":
        return format_bias_data_for_ai(data)
    elif data_type == "trend_data":
        return format_trend_data_for_ai(data)
    else:
        return format_generic_data_for_ai(data)

def format_momentum_data_for_ai(data):
    """格式化动量分析数据"""
    if not data or len(data) == 0:
        return "暂无动量分析数据"
    
    text = f"""# ETF动量策略分析数据
分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 推荐持仓
"""
    
    # 添加推荐持仓信息
    if 'selected_etfs_result' in data and data['selected_etfs_result']:
        text += "当前推荐的前两名ETF:\n"
        for i, etf in enumerate(data['selected_etfs_result'], 1):
            etf_code, etf_name, price, ma_price, momentum = etf
            # 确保数值是Python原生类型
            price = float(price) if hasattr(price, 'item') else price
            ma_price = float(ma_price) if hasattr(ma_price, 'item') else ma_price
            momentum = float(momentum) if hasattr(momentum, 'item') else momentum
            
            text += f"{i}. {etf_code} - {etf_name}\n"
            text += f"   当前价格: {price:.4f}\n"
            text += f"   均线价格: {ma_price:.4f}\n"
            text += f"   动量: {momentum*100:.2f}%\n"
            text += f"   价格-均线: {price - ma_price:.4f}\n\n"
    
    # 添加所有ETF排名
    if 'all_etfs_result' in data and data['all_etfs_result']:
        text += "## 所有ETF动量排名\n"
        text += "排名 | ETF代码 | ETF名称 | 当前价格 | 均线价格 | 动量 | 状态\n"
        text += "-----|---------|---------|----------|----------|------|------\n"
        
        for i, etf in enumerate(data['all_etfs_result'], 1):
            if len(etf) >= 6:
                etf_code, etf_name, price, ma_price, momentum, above_ma = etf
                # 确保数值是Python原生类型
                price = float(price) if hasattr(price, 'item') else price
                ma_price = float(ma_price) if hasattr(ma_price, 'item') else ma_price
                momentum = float(momentum) if hasattr(momentum, 'item') else momentum
                above_ma = bool(above_ma) if hasattr(above_ma, 'item') else above_ma
                
                status = "✅ 推荐" if above_ma and i <= 2 else "❌ 不符合条件"
                text += f"{i} | {etf_code} | {etf_name} | {price:.4f} | {ma_price:.4f} | {momentum*100:.2f}% | {status}\n"
    
    return text

def format_bias_data_for_ai(data):
    """格式化Bias分析数据"""
    if not data or len(data) == 0:
        return "暂无Bias分析数据"
    
    text = f"""# ETF Bias分析数据
分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 偏离度分析结果
"""
    
    for item in data:
        text += f"### {item.get('ETF代码', 'N/A')} - {item.get('ETF名称', 'N/A')}\n"
        text += f"6日偏离度: {item.get('6日偏离度', 'N/A')}\n"
        text += f"12日偏离度: {item.get('12日偏离度', 'N/A')}\n"
        text += f"24日偏离度: {item.get('24日偏离度', 'N/A')}\n"
        text += f"超买超卖结论: {item.get('超买超卖结论', 'N/A')}\n\n"
    
    return text

def format_trend_data_for_ai(data):
    """格式化趋势分析数据"""
    if not data or len(data) == 0:
        return "暂无趋势分析数据"
    
    text = f"""# ETF趋势分析数据
分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 近一年表现对比
"""
    
    for item in data:
        text += f"### {item.get('ETF代码', 'N/A')} - {item.get('ETF名称', 'N/A')}\n"
        text += f"当前累计涨跌幅: {item.get('当前累计涨跌幅', 'N/A')}\n"
        text += f"期间最高涨幅: {item.get('期间最高涨幅', 'N/A')}\n"
        text += f"期间最大跌幅: {item.get('期间最大跌幅', 'N/A')}\n"
        text += f"最大回撤: {item.get('最大回撤', 'N/A')}\n"
        text += f"夏普比率: {item.get('夏普比率', 'N/A')}\n"
        text += f"年化波动率: {item.get('年化波动率', 'N/A')}\n\n"
    
    return text

def format_generic_data_for_ai(data):
    """格式化通用数据"""
    if isinstance(data, pd.DataFrame):
        return f"""# 数据表格
分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 数据内容
{data.to_string()}
"""
    elif isinstance(data, dict):
        # 特殊处理完整分析数据
        if 'selected_etfs_result' in data and 'all_etfs_result' in data:
            return format_complete_analysis_data(data)
        
        # 递归处理字典中的numpy类型
        def convert_numpy_types(obj):
            if isinstance(obj, dict):
                return {key: convert_numpy_types(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy_types(item) for item in obj]
            elif isinstance(obj, tuple):
                return tuple(convert_numpy_types(item) for item in obj)
            elif hasattr(obj, 'item'):  # numpy标量
                return obj.item()
            elif hasattr(obj, 'tolist'):  # numpy数组
                return obj.tolist()
            elif hasattr(obj, '__class__') and 'numpy' in str(obj.__class__):
                # 处理其他numpy类型
                try:
                    return obj.item()
                except:
                    return str(obj)
            else:
                return obj
        
        converted_data = convert_numpy_types(data)
        return f"""# 数据字典
分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 数据内容
{json.dumps(converted_data, ensure_ascii=False, indent=2)}
"""
    else:
        return f"""# 分析数据
分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 数据内容
{str(data)}
"""

def format_complete_analysis_data(data):
    """格式化完整分析数据"""
    text = f"""# ETF动量策略完整分析数据
分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
页面: {data.get('page_name', '未知')}

## 策略参数
"""
    
    if 'strategy_params' in data:
        params = data['strategy_params']
        text += f"动量周期: {params.get('momentum_period', 'N/A')}天\n"
        text += f"均线周期: {params.get('ma_period', 'N/A')}天\n"
        text += f"最大持仓: {params.get('max_positions', 'N/A')}只\n\n"
    
    # 推荐持仓
    if 'selected_etfs_result' in data and data['selected_etfs_result']:
        text += "## 推荐持仓\n"
        text += "当前推荐的前两名ETF:\n"
        for i, etf in enumerate(data['selected_etfs_result'], 1):
            etf_code, etf_name, price, ma_price, momentum = etf
            # 确保数值是Python原生类型
            price = float(price) if hasattr(price, 'item') else price
            ma_price = float(ma_price) if hasattr(ma_price, 'item') else ma_price
            momentum = float(momentum) if hasattr(momentum, 'item') else momentum
            
            text += f"{i}. {etf_code} - {etf_name}\n"
            text += f"   当前价格: {price:.4f}\n"
            text += f"   均线价格: {ma_price:.4f}\n"
            text += f"   动量: {momentum*100:.2f}%\n"
            text += f"   价格-均线: {price - ma_price:.4f}\n\n"
    
    # 所有ETF排名
    if 'all_etfs_result' in data and data['all_etfs_result']:
        text += "## 所有ETF动量排名\n"
        text += "排名 | ETF代码 | ETF名称 | 当前价格 | 均线价格 | 动量 | 状态\n"
        text += "-----|---------|---------|----------|----------|------|------\n"
        
        for i, etf in enumerate(data['all_etfs_result'], 1):
            if len(etf) >= 6:
                etf_code, etf_name, price, ma_price, momentum, above_ma = etf
                # 确保数值是Python原生类型
                price = float(price) if hasattr(price, 'item') else price
                ma_price = float(ma_price) if hasattr(ma_price, 'item') else ma_price
                momentum = float(momentum) if hasattr(momentum, 'item') else momentum
                above_ma = bool(above_ma) if hasattr(above_ma, 'item') else above_ma
                
                status = "✅ 推荐" if above_ma and i <= 2 else "❌ 不符合条件"
                text += f"{i} | {etf_code} | {etf_name} | {price:.4f} | {ma_price:.4f} | {momentum*100:.2f}% | {status}\n"
    
    # Bias分析数据
    if 'bias_results' in data and data['bias_results']:
        text += "\n## Bias超买超卖分析\n"
        text += "ETF代码 | ETF名称 | 6日偏离度 | 12日偏离度 | 24日偏离度 | 超买超卖结论\n"
        text += "--------|---------|-----------|------------|------------|----------------\n"
        
        for bias_item in data['bias_results']:
            if isinstance(bias_item, dict):
                # 处理字典格式的Bias数据
                etf_code = bias_item.get('ETF代码', 'N/A')
                etf_name = bias_item.get('ETF名称', 'N/A')
                bias_6 = bias_item.get('6日偏离度', 'N/A')
                bias_12 = bias_item.get('12日偏离度', 'N/A')
                bias_24 = bias_item.get('24日偏离度', 'N/A')
                conclusion = bias_item.get('超买超卖结论', 'N/A')
                
                text += f"{etf_code} | {etf_name} | {bias_6} | {bias_12} | {bias_24} | {conclusion}\n"
            elif isinstance(bias_item, (list, tuple)) and len(bias_item) >= 6:
                # 处理元组格式的Bias数据（向后兼容）
                etf_code = bias_item[0]
                etf_name = bias_item[1]
                bias_6 = bias_item[2] if len(bias_item) > 2 else "N/A"
                bias_12 = bias_item[3] if len(bias_item) > 3 else "N/A"
                bias_24 = bias_item[4] if len(bias_item) > 4 else "N/A"
                conclusion = bias_item[5] if len(bias_item) > 5 else "N/A"
                
                # 确保数值是Python原生类型
                if hasattr(bias_6, 'item'):
                    bias_6 = f"{float(bias_6):.2f}%"
                elif isinstance(bias_6, (int, float)):
                    bias_6 = f"{bias_6:.2f}%"
                
                if hasattr(bias_12, 'item'):
                    bias_12 = f"{float(bias_12):.2f}%"
                elif isinstance(bias_12, (int, float)):
                    bias_12 = f"{bias_12:.2f}%"
                
                if hasattr(bias_24, 'item'):
                    bias_24 = f"{float(bias_24):.2f}%"
                elif isinstance(bias_24, (int, float)):
                    bias_24 = f"{bias_24:.2f}%"
                
                text += f"{etf_code} | {etf_name} | {bias_6} | {bias_12} | {bias_24} | {conclusion}\n"
    
    return text


def render_compact_ai_button(data, data_type="momentum_results", key_suffix=""):
    """
    渲染紧凑型AI分析按钮（用于表格旁边）
    
    Args:
        data: 要分析的数据
        data_type: 数据类型
        key_suffix: 按钮key后缀
    """
    if data is None or (isinstance(data, (list, dict)) and len(data) == 0):
        return
    
    # 格式化数据
    formatted_text = format_data_for_ai(data, data_type)
    
    # 添加默认提示词
    prompt = "请帮我深入分析如下ETF数据，给出投资建议：\n\n"
    full_text = prompt + formatted_text
    
    # 创建紧凑按钮
    button_key = f"compact_ai_{data_type}_{key_suffix}"
    
    # 使用小按钮
    if st.button("🤖 AI分析", key=button_key, type="secondary", help="点击自动复制数据给AI分析"):
        try:
            # 使用clipboard库复制到剪贴板
            clipboard.copy(full_text)
            st.toast("✅ 数据已自动复制到剪贴板！", icon="✅")
            
            # 显示数据预览（可选）
            with st.expander("📋 查看复制的数据", expanded=False):
                st.text_area(
                    "AI分析数据:", 
                    value=full_text, 
                    height=300, 
                    key=f"ai_data_preview_{key_suffix}",
                    help="数据已复制到剪贴板，可直接粘贴到AI助手"
                )
            
            # 添加使用提示
            st.info("💡 **使用方法**: 数据已复制到剪贴板，直接粘贴到AI助手即可开始分析")
            
        except Exception as e:
            # 如果clipboard失败，使用JavaScript备用方案
            st.toast("⚠️ 自动复制失败，使用备用方案", icon="⚠️")
            
            # 处理特殊字符，避免JavaScript错误
            safe_text = full_text.replace('\\', '\\\\').replace('`', '\\`').replace('$', '\\$').replace('\n', '\\n').replace('\r', '\\r')
            
            st.markdown(f"""
            <script>
            function copyToClipboard() {{
                const text = `{safe_text}`;
                if (navigator.clipboard && window.isSecureContext) {{
                    navigator.clipboard.writeText(text).then(function() {{
                        console.log('数据已复制到剪贴板');
                    }}, function(err) {{
                        console.error('复制失败: ', err);
                        fallbackCopy(text);
                    }});
                }} else {{
                    fallbackCopy(text);
                }}
            }}
            
            function fallbackCopy(text) {{
                const textArea = document.createElement('textarea');
                textArea.value = text;
                textArea.style.position = 'fixed';
                textArea.style.left = '-999999px';
                textArea.style.top = '-999999px';
                document.body.appendChild(textArea);
                textArea.focus();
                textArea.select();
                try {{
                    document.execCommand('copy');
                    console.log('备用复制成功');
                }} catch (err) {{
                    console.error('备用复制失败: ', err);
                }}
                document.body.removeChild(textArea);
            }}
            
            copyToClipboard();
            </script>
            """, unsafe_allow_html=True)
            
            # 显示手动复制选项
            st.text_area(
                "如果自动复制失败，请手动复制以下数据:", 
                value=full_text, 
                height=300, 
                key=f"manual_copy_{key_suffix}",
                help="选中所有内容后按Ctrl+C复制"
            )


def get_ai_analysis_prompt(data_type="momentum_results"):
    """
    获取AI分析提示词
    
    Args:
        data_type: 数据类型
    
    Returns:
        prompt: 分析提示词
    """
    prompts = {
        "momentum_results": """
请分析以下ETF动量策略数据：

1. 动量排名分析：哪些ETF表现最好，哪些表现较差？
2. 投资建议：基于动量数据，推荐哪些ETF进行投资？
3. 风险提示：当前市场存在哪些风险点？
4. 操作建议：何时买入、卖出或调仓？
5. 市场解读：当前市场环境如何影响ETF表现？

请提供专业、客观的分析，并给出具体的操作建议。
        """,
        "bias_results": """
请分析以下ETF Bias（偏离度）数据：

1. 超买超卖分析：哪些ETF处于超买或超卖状态？
2. 投资机会：是否存在被低估的投资机会？
3. 风险警示：哪些ETF需要谨慎操作？
4. 技术面分析：从技术指标角度分析市场状态
5. 操作建议：基于Bias数据给出具体的买卖建议

请结合技术分析理论，提供专业的投资建议。
        """,
        "trend_data": """
请分析以下ETF趋势数据：

1. 表现对比：哪些ETF近一年表现最好？
2. 风险收益：各ETF的风险收益特征如何？
3. 投资价值：哪些ETF具有长期投资价值？
4. 市场趋势：当前市场处于什么阶段？
5. 配置建议：如何合理配置不同ETF？

请从长期投资角度，提供资产配置建议。
        """,
        "complete_analysis": """
请对以下ETF分析数据进行全面分析：

1. 综合评估：结合动量、Bias、趋势等指标进行综合评估
2. 投资策略：制定适合当前市场的投资策略
3. 风险控制：识别并控制各种投资风险
4. 市场机会：发现并把握市场投资机会
5. 操作计划：制定具体的操作计划和执行步骤

请提供专业、全面的投资分析报告。
        """
    }
    
    return prompts.get(data_type, "请分析以下数据并提供专业建议。")
