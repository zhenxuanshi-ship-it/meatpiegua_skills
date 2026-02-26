#!/usr/bin/env python3
"""
血糖数据录入脚本
自动判断血糖类型，存储数据，返回医学评估
"""

import json
import argparse
import os
from datetime import datetime, time
from pathlib import Path

# 数据存储路径
DATA_DIR = Path("/root/.openclaw/workspace/blood-glucose")
DATA_FILE = DATA_DIR / "data.jsonl"

def ensure_data_dir():
    """确保数据目录存在"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

def parse_time(time_str):
    """解析时间字符串"""
    if not time_str:
        return datetime.now()
    try:
        return datetime.strptime(time_str, "%H:%M")
    except:
        return datetime.now()

def determine_glucose_type(measure_time, description=""):
    """
    根据时间和描述判断血糖类型
    
    返回: (type_code, type_name, meal)
    """
    desc = description.lower()
    hour = measure_time.hour
    
    # 根据描述判断（优先级最高）
    if "空腹" in desc or "fasting" in desc:
        return ("fasting", "空腹血糖", None)
    
    if "餐后" in desc or "post" in desc or "after" in desc:
        if "早" in desc or "breakfast" in desc:
            return ("post_meal", "餐后血糖", "breakfast")
        elif "午" in desc or "lunch" in desc:
            return ("post_meal", "餐后血糖", "lunch")
        elif "晚" in desc or "dinner" in desc:
            return ("post_meal", "餐后血糖", "dinner")
        else:
            return ("post_meal", "餐后血糖", None)
    
    if "餐前" in desc or "pre" in desc:
        return ("pre_meal", "餐前血糖", None)
    
    if "随机" in desc or "random" in desc:
        return ("random", "随机血糖", None)
    
    # 根据时间判断
    # 空腹：早上5-9点
    if 5 <= hour < 9:
        return ("fasting", "空腹血糖", None)
    
    # 餐前：饭前常见时间点
    if (6 <= hour < 9) or (11 <= hour < 13) or (17 <= hour < 20):
        return ("pre_meal", "餐前血糖", None)
    
    # 默认随机血糖
    return ("random", "随机血糖", None)

def evaluate_glucose(value, glucose_type):
    """
    根据血糖值和类型给出医学评估
    
    返回: (status, status_cn, advice)
    """
    # 低血糖判断（通用）
    if value < 3.9:
        if value < 3.0:
            return ("danger", "⚠️ 低血糖（中度）", 
                    "血糖过低！请立即补充糖分（糖果、果汁等），如症状严重请就医。")
        else:
            return ("warning", "⚠️ 低血糖（轻度）", 
                    "血糖偏低，建议适当加餐，监测是否有出汗、心悸等症状。")
    
    # 根据不同类型判断
    if glucose_type == "fasting":
        if value < 6.1:
            return ("normal", "✅ 正常", "空腹血糖正常，继续保持良好的生活习惯。")
        elif value < 7.0:
            return ("warning", "⚠️ 空腹血糖受损", 
                    "空腹血糖略高于正常，建议控制饮食、增加运动，定期监测。")
        else:
            return ("danger", "🚨 糖尿病可能", 
                    "空腹血糖达到糖尿病诊断标准，建议尽快就医确诊。")
    
    elif glucose_type == "post_meal":
        if value < 7.8:
            return ("normal", "✅ 正常", "餐后血糖控制良好，继续保持。")
        elif value < 11.1:
            return ("warning", "⚠️ 糖耐量异常", 
                    "餐后血糖偏高，建议调整饮食结构，减少精制碳水摄入。")
        else:
            return ("danger", "🚨 糖尿病可能", 
                    "餐后血糖达到糖尿病诊断标准，建议尽快就医。")
    
    elif glucose_type == "pre_meal":
        if value < 6.1:
            return ("normal", "✅ 正常", "餐前血糖正常。")
        elif value < 7.0:
            return ("warning", "⚠️ 偏高", "餐前血糖略高，注意下一餐的饮食控制。")
        else:
            return ("danger", "🚨 偏高", "餐前血糖较高，建议咨询医生。")
    
    else:  # random
        if value < 11.1:
            return ("normal", "✅ 正常范围", "随机血糖在正常范围内。")
        else:
            return ("danger", "🚨 糖尿病可能", 
                    "随机血糖达到糖尿病诊断标准，建议尽快就医检查。")

def record_glucose(value, time_str=None, notes="", description=""):
    """
    记录血糖数据
    
    参数:
        value: 血糖值 (mmol/L)
        time_str: 时间字符串 (HH:MM)，默认为当前时间
        notes: 备注
        description: 描述（用于判断血糖类型）
    """
    ensure_data_dir()
    
    # 解析时间
    measure_time = parse_time(time_str)
    
    # 判断血糖类型
    glucose_type, type_name, meal = determine_glucose_type(measure_time, description)
    
    # 医学评估
    status, status_cn, advice = evaluate_glucose(value, glucose_type)
    
    # 构建记录
    record = {
        "timestamp": datetime.now().isoformat(),
        "measure_time": measure_time.strftime("%H:%M"),
        "value": float(value),
        "type": glucose_type,
        "type_name": type_name,
        "meal": meal,
        "notes": notes,
        "status": status
    }
    
    # 追加写入文件
    with open(DATA_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    
    # 输出结果
    print("=" * 50)
    print("📊 血糖记录已保存")
    print("=" * 50)
    print(f"时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"测量时间：{measure_time.strftime('%H:%M')}")
    print(f"类型：{type_name}")
    if meal:
        meal_cn = {"breakfast": "早餐", "lunch": "午餐", "dinner": "晚餐"}.get(meal, meal)
        print(f"餐次：{meal_cn}")
    print(f"数值：{value} mmol/L")
    print("-" * 50)
    print(f"评估：{status_cn}")
    print("-" * 50)
    print(f"💡 建议：{advice}")
    if notes:
        print(f"📝 备注：{notes}")
    print("=" * 50)
    
    return record

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="记录血糖数据")
    parser.add_argument("--value", "-v", type=float, required=True, help="血糖值 (mmol/L)")
    parser.add_argument("--time", "-t", type=str, help="测量时间 (HH:MM)")
    parser.add_argument("--notes", "-n", type=str, default="", help="备注")
    parser.add_argument("--desc", "-d", type=str, default="", help="描述（用于判断类型）")
    
    args = parser.parse_args()
    record_glucose(args.value, args.time, args.notes, args.desc)
