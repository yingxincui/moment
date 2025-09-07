#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试clipboard库功能
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(__file__))

def test_clipboard_import():
    """测试clipboard库导入"""
    print("🧪 测试clipboard库导入...")
    
    try:
        import clipboard
        print("✅ clipboard库导入成功")
        return True
    except ImportError:
        print("❌ clipboard库未安装，请运行: pip install clipboard")
        return False
    except Exception as e:
        print(f"❌ clipboard库导入失败: {e}")
        return False

def test_clipboard_functionality():
    """测试clipboard功能"""
    print("🧪 测试clipboard功能...")
    
    try:
        import clipboard
        
        # 测试复制功能
        test_text = "测试文本：ETF动量策略分析数据"
        clipboard.copy(test_text)
        print("✅ clipboard.copy() 执行成功")
        
        # 测试读取功能
        copied_text = clipboard.paste()
        if copied_text == test_text:
            print("✅ clipboard.paste() 验证成功")
            return True
        else:
            print(f"❌ 复制验证失败: 期望 '{test_text}', 实际 '{copied_text}'")
            return False
            
    except Exception as e:
        print(f"❌ clipboard功能测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始测试clipboard库...")
    print("=" * 50)
    
    success1 = test_clipboard_import()
    if success1:
        success2 = test_clipboard_functionality()
    else:
        success2 = False
    
    print("\n" + "=" * 50)
    if success1 and success2:
        print("🎉 clipboard库测试通过！")
        print("💡 现在AI分析功能可以自动复制数据到剪贴板")
    elif success1:
        print("⚠️ clipboard库已安装但功能测试失败")
    else:
        print("❌ 请先安装clipboard库: pip install clipboard")

if __name__ == "__main__":
    main()
