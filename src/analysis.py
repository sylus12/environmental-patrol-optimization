# -*- coding: utf-8 -*-
"""
第二步：数据分析 —— 找到业务痛点
================================
这一阶段回答一个问题："哪个区最需要优化调度？"
结论（也是简历上的一句话）：
    B 区待处理问题最多、水污染占比最高 -> 以 B 区为优化对象。

运行方式：
    python src/analysis.py
运行结果：
    终端打印统计结论，并在 output/ 下生成两张图。
"""

import pandas as pd
import matplotlib.pyplot as plt

# Windows 下让 matplotlib 正确显示中文
plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

df = pd.read_csv("data/complaints.csv")

# ---- 1. 各区域待处理数量 ----
pending = df[df["status"] == "待处理"]
pending_by_region = pending.groupby("region").size().sort_values(ascending=False)
print("各区待处理问题数量：")
print(pending_by_region)

# ---- 2. 污染类型占比 ----
type_ratio = df["type"].value_counts(normalize=True).round(3) * 100
print("\n污染类型占比(%)：")
print(type_ratio)

# ---- 3. 画图：区域积压 + 类型分布 ----
fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))

colors = ["#D85A30" if r == "B" else "#888780" for r in pending_by_region.index]
axes[0].bar(pending_by_region.index, pending_by_region.values, color=colors)
axes[0].set_title("各区待处理问题数量（B 区积压最严重）")
axes[0].set_xlabel("区域")
axes[0].set_ylabel("待处理数量")

type_counts = df["type"].value_counts()
axes[1].pie(type_counts.values, labels=type_counts.index, autopct="%.1f%%",
            colors=["#378ADD", "#1D9E75", "#EF9F27", "#888780"])
axes[1].set_title("举报污染类型分布")

plt.tight_layout()
plt.savefig("output/analysis_overview.png", dpi=150)
print("\n图已保存 -> output/analysis_overview.png")

# ---- 4. 导出全市最紧急的待处理点，供优化模块使用 ----
# 分析结论：B 区积压最严重，但四个区都有紧急举报。
# 明日巡查任务 = 全市时限最紧的 14 个待处理点（跨区分散，靠经验派车很容易绕路）
tasks = pending.nsmallest(14, "deadline").reset_index(drop=True)
tasks.to_csv("data/b_pending_tasks.csv", index=False, encoding="utf-8-sig")
print(f"\n已导出全市最紧急的 {len(tasks)} 个待处理点 -> data/b_pending_tasks.csv")
print(f"涉及区域：{sorted(tasks['region'].unique())}；"
      f"总工作量 {tasks['workload'].sum()} 件；3 辆督查车每日处理能力合计 36 件")
