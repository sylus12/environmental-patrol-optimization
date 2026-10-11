# -*- coding: utf-8 -*-
"""
第四步：可视化 —— 把优化结果画出来
==================================
一张"优化前后路线对比图"是简历和面试里最有说服力的东西。

运行方式：
    python src/visualize.py
运行结果：
    output/route_comparison.png
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

tasks = pd.read_csv("data/b_pending_tasks.csv")
coords = [(0.0, 0.0)] + list(zip(tasks["x"], tasks["y"]))

greedy_routes = np.load("output/greedy_routes.npy", allow_pickle=True)
optimal_routes = np.load("output/optimal_routes.npy", allow_pickle=True)

with open("output/summary.txt", encoding="utf-8") as f:
    summary = dict(line.strip().split("=") for line in f)

vehicle_colors = ["#378ADD", "#1D9E75", "#EF9F27"]

fig, axes = plt.subplots(1, 2, figsize=(13, 6), sharex=True, sharey=True)

for ax, routes, name, key in [
    (axes[0], greedy_routes, "优化前：贪心派车", "greedy_total"),
    (axes[1], optimal_routes, "优化后：OR-Tools 求解", "optimal_total"),
]:
    # 画举报点
    xs = [c[0] for c in coords[1:]]
    ys = [c[1] for c in coords[1:]]
    ax.scatter(xs, ys, c="#888780", s=40, zorder=2, label="举报点")
    # 画车场
    ax.scatter([0], [0], marker="s", c="#D85A30", s=160, zorder=3, label="督查中心")
    # 画每辆车的路线
    for v, route in enumerate(routes):
        path_x = [coords[p][0] for p in route]
        path_y = [coords[p][1] for p in route]
        ax.plot(path_x, path_y, c=vehicle_colors[v], lw=1.6, alpha=0.9,
                zorder=1, label=f"车辆{v + 1}")
    ax.set_title(f"{name}\n总里程 {summary[key]} km")
    ax.set_xlabel("x (km)")
    ax.legend(fontsize=9, loc="upper left")

axes[0].set_ylabel("y (km)")
fig.suptitle(f"督查路线优化对比：里程降低 {summary['improvement']}", fontsize=14)
plt.tight_layout()
plt.savefig("output/route_comparison.png", dpi=150)
print("对比图已保存 -> output/route_comparison.png")
