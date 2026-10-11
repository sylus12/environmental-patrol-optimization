# -*- coding: utf-8 -*-
"""
第三步（核心）：督查路线优化 —— CVRPTW 建模与求解
==================================================
业务问题：
    督查中心(0,0)有 3 辆车，明天要处理全市 14 个最紧急的举报点。
    每个点有工作量 demand，每辆车一天最多处理 capacity=12 件；
    每个点必须在处理时限内到达（时间窗）。
    问：每辆车按什么顺序跑哪些点，总行驶里程最短？

数学模型（面试必背，详见 docs/INTERVIEW_PREP.md）：
    决策变量：x_ij^k ∈ {0,1}，车辆 k 是否从点 i 直接开到点 j
    目标函数：min Σ_k Σ_ij d_ij · x_ij^k      （总里程最短）
    约束：
      1) 每个举报点恰好被访问一次（流守恒）
      2) 每辆车从中心出发、回到中心
      3) Σ demand_i ≤ capacity（容量约束）
      4) 到达时间在时间窗内（时间窗约束）

求解工具：Google OR-Tools（JD 中点名的求解器之一）
对比基准：贪心最近邻算法（模拟"凭经验派车"的现状）

运行方式：
    python src/vrp_optimization.py
"""

import pandas as pd
import numpy as np
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

# ---------------- 1. 读取任务数据 ----------------
tasks = pd.read_csv("data/b_pending_tasks.csv")

# 节点 0 是督查中心（车场），节点 1..25 是举报点
coords = [(0.0, 0.0)] + list(zip(tasks["x"], tasks["y"]))
demands = [0] + tasks["workload"].tolist()          # 车场没有工作量
# 时间窗：车场全天开放 [0, 480]；举报点按 deadline 折算上限
# （实际业务中"8 小时时限"含响应排队时间，这里放宽系数避免模型不可行，
#   同时保留"越紧急的点时间窗越紧"的约束结构）
time_windows = [(0, 480)] + [(0, int(d) * 8) for d in tasks["deadline"]]

NUM_VEHICLES = 3
CAPACITY = 12         # 每车每日最多处理 12 件
SPEED = 1.0           # 简化：1 公里 = 1 单位时间

n = len(coords)

# 距离矩阵：欧氏距离（实际业务中会调用地图 API 取路网距离）
dist = [[0] * n for _ in range(n)]
for i in range(n):
    for j in range(n):
        dist[i][j] = int(round(np.hypot(coords[i][0] - coords[j][0],
                                        coords[i][1] - coords[j][1])))

# ---------------- 2. 贪心最近邻基准 ----------------
def greedy_baseline():
    """每辆车从中心出发，反复去'最近且装得下'的点。模拟人工派车。"""
    unvisited = set(range(1, n))
    routes, total = [], 0
    for _ in range(NUM_VEHICLES):
        route, load, cur, length = [0], 0, 0, 0
        while True:
            # 找最近的、容量装得下的未访问点
            cands = [j for j in unvisited if load + demands[j] <= CAPACITY]
            if not cands:
                break
            nxt = min(cands, key=lambda j: dist[cur][j])
            length += dist[cur][nxt]
            load += demands[nxt]
            route.append(nxt)
            unvisited.remove(nxt)
            cur = nxt
        length += dist[cur][0]      # 回车场
        route.append(0)
        routes.append(route)
        total += length
    return routes, total

# ---------------- 3. OR-Tools 求解 CVRPTW ----------------
def solve_vrptw():
    manager = pywrapcp.RoutingIndexManager(n, NUM_VEHICLES, 0)  # 0 号点为车场
    routing = pywrapcp.RoutingModel(manager)

    # 距离回调：告诉求解器任意两点间距离
    def distance_callback(from_index, to_index):
        return dist[manager.IndexToNode(from_index)][manager.IndexToNode(to_index)]

    transit_idx = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_idx)  # 目标 = 总里程最小

    # --- 容量约束 ---
    def demand_callback(from_index):
        return demands[manager.IndexToNode(from_index)]

    demand_idx = routing.RegisterUnaryTransitCallback(demand_callback)
    routing.AddDimensionWithVehicleCapacity(
        demand_idx, 0, [CAPACITY] * NUM_VEHICLES, True, "Capacity"
    )

    # --- 时间窗约束 ---
    def time_callback(from_index, to_index):
        # 行驶时间 + 在 from 点的处理时间（每件 1 单位时间）
        f = manager.IndexToNode(from_index)
        return dist[f][manager.IndexToNode(to_index)] + demands[f]

    time_idx = routing.RegisterTransitCallback(time_callback)
    routing.AddDimension(time_idx, 60, 480, False, "Time")
    time_dim = routing.GetDimensionOrDie("Time")
    for node, (start, end) in enumerate(time_windows):
        idx = manager.NodeToIndex(node)
        time_dim.CumulVar(idx).SetRange(start, end)

    # 搜索策略：PATH_CHEAPEST_ARC 构造初始解 + 引导式局部搜索改进
    params = pywrapcp.DefaultRoutingSearchParameters()
    params.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    params.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )
    params.time_limit.FromSeconds(10)  # 限时 10 秒

    solution = routing.SolveWithParameters(params)
    if not solution:
        return None, None

    routes, total = [], 0
    for v in range(NUM_VEHICLES):
        idx = routing.Start(v)
        route = []
        while not routing.IsEnd(idx):
            route.append(manager.IndexToNode(idx))
            idx = solution.Value(routing.NextVar(idx))
        route.append(0)
        # 单车里程
        r_len = sum(dist[route[i]][route[i + 1]] for i in range(len(route) - 1))
        total += r_len
        routes.append(route)
    return routes, total

# ---------------- 4. 运行并对比 ----------------
if __name__ == "__main__":
    g_routes, g_total = greedy_baseline()
    o_routes, o_total = solve_vrptw()

    print("=" * 50)
    print(f"贪心最近邻基准：总里程 {g_total} km")
    print(f"OR-Tools 优化：  总里程 {o_total} km")
    improvement = (g_total - o_total) / g_total * 100
    print(f"里程降低：{improvement:.1f}%")
    print("=" * 50)
    for i, r in enumerate(o_routes):
        pts = [p for p in r if p != 0]
        print(f"车辆{i + 1}: 中心 -> {' -> '.join(map(str, pts))} -> 中心 "
              f"(处理 {sum(demands[p] for p in pts)} 件)")

    # 保存结果供可视化使用
    np.save("output/greedy_routes.npy", np.array(g_routes, dtype=object), allow_pickle=True)
    np.save("output/optimal_routes.npy", np.array(o_routes, dtype=object), allow_pickle=True)
    with open("output/summary.txt", "w", encoding="utf-8") as f:
        f.write(f"greedy_total={g_total}\noptimal_total={o_total}\nimprovement={improvement:.1f}%\n")
