#!/usr/bin/env python3
"""
血糖查询统计脚本
支持查询历史数据、生成图表
"""

import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
import statistics

DATA_FILE = Path("/root/.openclaw/workspace/blood-glucose/data.jsonl")

def load_data(days=7, start_date=None, end_date=None):
    """加载血糖数据"""
    if not DATA_FILE.exists():
        return []
    
    records = []
    
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                record_time = datetime.fromisoformat(record["timestamp"])
                record["_datetime"] = record_time
                
                # 日期筛选
                if start_date and record_time.date() < start_date:
                    continue
                if end_date and record_time.date() > end_date:
                    continue
                
                # 天数筛选
                if days and not (start_date or end_date):
                    cutoff = datetime.now() - timedelta(days=days)
                    if record_time < cutoff:
                        continue
                
                records.append(record)
            except:
                continue
    
    return sorted(records, key=lambda x: x["_datetime"])

def generate_ascii_chart(records, width=50, height=10):
    """生成ASCII趋势图"""
    if not records:
        return "暂无数据"
    
    values = [r["value"] for r in records]
    min_val = max(3.0, min(values) - 1)
    max_val = min(15.0, max(values) + 1)
    
    # 构建图表
    lines = []
    lines.append(f"血糖趋势图 (范围: {min(values):.1f} ~ {max(values):.1f} mmol/L)")
    lines.append("-" * width)
    
    # Y轴标签
    for i in range(height, -1, -1):
        val = min_val + (max_val - min_val) * i / height
        line = f"{val:5.1f} |"
        
        # 绘制数据点
        for j, record in enumerate(records):
            pos = int((record["value"] - min_val) / (max_val - min_val) * height)
            if abs(pos - i) <= 0.5:
                line += " *"
            else:
                line += "  "
        
        lines.append(line)
    
    lines.append("-" * width)
    lines.append("      |" + "  " * len(records))
    
    return "\n".join(lines)

def generate_daily_summary(records):
    """生成每日摘要"""
    daily = defaultdict(lambda: {"fasting": [], "post_meal": [], "other": []})
    
    for r in records:
        date = r["_datetime"].date()
        gtype = r.get("type", "random")
        
        if gtype == "fasting":
            daily[date]["fasting"].append(r["value"])
        elif gtype == "post_meal":
            daily[date]["post_meal"].append(r["value"])
        else:
            daily[date]["other"].append(r["value"])
    
    return daily

def query_stats(days=7, show_chart=True):
    """查询统计信息"""
    records = load_data(days=days)
    
    if not records:
        print("指定时间段内暂无血糖记录")
        return
    
    # 基础统计
    values = [r["value"] for r in records]
    avg = statistics.mean(values)
    min_v = min(values)
    max_v = max(values)
    
    # 按类型统计
    type_stats = defaultdict(list)
    for r in records:
        type_stats[r.get("type", "random")].append(r["value"])
    
    # 日期范围
    start = records[0]["_datetime"].strftime("%Y-%m-%d")
    end = records[-1]["_datetime"].strftime("%Y-%m-%d")
    
    print("=" * 60)
    print(f"📊 血糖统计 ({start} ~ {end}, 共{len(records)}次测量)")
    print("=" * 60)
    
    print(f"\n📈 整体统计")
    print(f"  平均值：{round(avg, 2)} mmol/L")
    print(f"  最高值：{max_v} mmol/L")
    print(f"  最低值：{min_v} mmol/L")
    if len(values) > 1:
        print(f"  标准差：{round(statistics.stdev(values), 2)} mmol/L")
    
    # 各类型详情
    type_names = {
        "fasting": "空腹血糖",
        "post_meal": "餐后血糖",
        "pre_meal": "餐前血糖",
        "random": "随机血糖"
    }
    
    for type_code, type_values in type_stats.items():
        if not type_values:
            continue
        name = type_names.get(type_code, type_code)
        print(f"\n📋 {name}（{len(type_values)}次）")
        print(f"  平均：{round(statistics.mean(type_values), 2)} mmol/L")
        print(f"  范围：{min(type_values)} ~ {max(type_values)} mmol/L")
    
    # ASCII图表
    if show_chart and len(records) <= 30:  # 数据点太多时图表不清晰
        print("\n📉 血糖趋势图")
        print(generate_ascii_chart(records))
    
    # 详细记录
    print("\n📝 详细记录")
    for r in records[-10:]:  # 最近10条
        time_str = r["_datetime"].strftime("%m-%d %H:%M")
        type_str = type_names.get(r.get("type"), r.get("type", ""))
        print(f"  {time_str}  {type_str:8s}  {r['value']:5.1f} mmol/L  {r.get('notes', '')}")
    
    print("=" * 60)

def query_today():
    """查询今日记录"""
    today = datetime.now().date()
    records = load_data(days=1)
    records = [r for r in records if r["_datetime"].date() == today]
    
    if not records:
        print("今日暂无血糖记录")
        return
    
    print("=" * 50)
    print(f"📊 今日血糖记录 ({today})")
    print("=" * 50)
    
    type_names = {
        "fasting": "空腹",
        "post_meal": "餐后",
        "pre_meal": "餐前",
        "random": "随机"
    }
    
    for r in records:
        time_str = r["_datetime"].strftime("%H:%M")
        type_str = type_names.get(r.get("type"), r.get("type", ""))
        print(f"  {time_str}  {type_str:4s}  {r['value']:5.1f} mmol/L")
    
    print("=" * 50)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="查询血糖统计")
    parser.add_argument("--days", "-d", type=int, default=7, help="查询天数")
    parser.add_argument("--today", "-t", action="store_true", help="仅查询今日")
    parser.add_argument("--no-chart", action="store_true", help="不显示图表")
    
    args = parser.parse_args()
    
    if args.today:
        query_today()
    else:
        query_stats(days=args.days, show_chart=not args.no_chart)
