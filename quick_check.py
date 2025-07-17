#!/usr/bin/env python3
"""
快速检查今日ArXiv论文类别
"""

import os
import json
import datetime
import pytz
from pathlib import Path


def quick_check():
    """快速检查今日论文"""
    print("🔍 快速检查今日ArXiv论文...")

    # 获取今天的日期
    date = datetime.date.fromtimestamp(datetime.datetime.now(tz=pytz.timezone("America/New_York")).timestamp())
    date_str = date.strftime("%a, %d %b %y")
    print(f"📅 检查日期: {date_str}")

    data_dir = Path("./data")
    if not data_dir.exists():
        print("❌ data目录不存在")
        return

    # 查找数据文件
    files_found = []
    for topic_abbr in ['cs', 'eess', 'math', 'physics', 'stat']:
        file_path = data_dir / f"{topic_abbr}_{date_str}.jsonl"
        if file_path.exists():
            files_found.append((topic_abbr, file_path))

    if not files_found:
        print("❌ 没有找到今日的论文数据文件")
        print("📁 data目录中的文件:")
        for f in data_dir.iterdir():
            print(f"  {f.name}")
        return

    all_subjects = set()
    total_papers = 0

    print(f"\n📊 找到 {len(files_found)} 个数据文件:")

    for topic_abbr, file_path in files_found:
        with open(file_path, 'r', encoding='utf-8') as f:
            papers = [json.loads(line) for line in f]

        print(f"  {topic_abbr}: {len(papers)} 篇论文")
        total_papers += len(papers)

        # 提取subjects
        for paper in papers:
            subjects_str = paper.get('subjects', '')
            if subjects_str:
                # 分割并清理subjects
                subjects = [s.split('(')[0].strip() for s in subjects_str.split(';')]
                all_subjects.update(subjects)

    print(f"\n📈 总计: {total_papers} 篇论文")
    print(f"🏷️ 发现 {len(all_subjects)} 个不同的类别:")

    # 按字母顺序排序并显示
    sorted_subjects = sorted(all_subjects)
    for i, subject in enumerate(sorted_subjects, 1):
        print(f"  {i:2d}. {subject}")

    # 检查配置的类别
    config_categories = [
        "Artificial Intelligence",
        "Machine Learning",
        "Systems and Control",
        "Neural and Evolutionary Computing"
    ]

    print(f"\n🎯 检查配置的类别:")
    found_any = False
    for category in config_categories:
        if category in all_subjects:
            print(f"  ✅ {category} - 找到匹配")
            found_any = True
        else:
            print(f"  ❌ {category} - 未找到")

    if not found_any:
        print(f"\n💡 建议解决方案:")
        print("1. 使用空的categories列表处理所有论文:")
        print("   categories: []")
        print()
        print("2. 或者从上面的列表中选择实际存在的类别")

        # 找一些相关的类别
        ml_related = [s for s in sorted_subjects if any(keyword in s.lower() for keyword in
                                                        ['machine', 'learning', 'artificial', 'intelligence', 'neural',
                                                         'computer', 'algorithm'])]
        if ml_related:
            print("   推荐的相关类别:")
            for cat in ml_related[:5]:
                print(f"     - \"{cat}\"")

    return sorted_subjects, found_any


if __name__ == "__main__":
    quick_check()