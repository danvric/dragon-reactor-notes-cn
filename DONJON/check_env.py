#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
环境自检：确认这台机器能不能跑 DONJON 部分的代码。

用法（必须在 DONJON 根目录执行，即能看到 rdonjon / data/ / Linux_x86_64/ 的那一层）：

    python3 check_env.py           # 只查文件和环境
    python3 check_env.py --smoke   # 额外真跑一次官方 CANDU6 算例（约 5 秒）

只读检查，不修改任何文件；--smoke 会写 Linux_x86_64/Candu6.result，但不会动 data/Candu6.x2m。
"""

import os
import re
import shutil
import subprocess
import sys

EXPECT_KEFF = 0.99625
EXPECT_CHANNELS = 380


def ok(msg):
    print(f"[ OK ] {msg}")


def warn(msg):
    print(f"[WARN] {msg}")


def bad(msg):
    print(f"[FAIL] {msg}")


def check_python():
    v = sys.version_info
    if v >= (3, 8):
        ok(f"Python {v.major}.{v.minor}.{v.micro} (>= 3.8)")
        return True
    bad(f"Python {v.major}.{v.minor}.{v.micro} 太旧，需要 >= 3.8")
    return False


def check_packages():
    problems = 0
    for name, needed_by in [
        ("numpy", "predict_numpy.py / 全部算法"),
        ("pandas", "train_bp.py / generate_dataset.py"),
        ("matplotlib", "plot_*.py"),
    ]:
        try:
            mod = __import__(name)
            ver = getattr(mod, "__version__", "?")
            ok(f"{name} {ver}（{needed_by}）")
        except Exception:
            bad(f"缺少 {name}（{needed_by}）：pip install {name}")
            problems += 1
    try:
        import torch  # noqa: F401
        ok("torch 可用（可以重训代理模型）")
    except Exception:
        warn("没装 torch：不影响跑闭环，只影响 train_bp.py 重训")
    return problems


def check_donjon():
    problems = 0
    if shutil.which("./rdonjon") or os.path.exists("./rdonjon"):
        ok("./rdonjon 找到了")
    else:
        bad("./rdonjon 不存在：当前目录不是 DONJON 根目录，或 DONJON 没编译好")
        problems += 1

    for path, why in [
        ("data/Candu6.x2m", "官方 CANDU6 输入卡（脚本会覆盖它，先备份）"),
        ("Candu6_proc/SetFuelMap.c2m", "提取合法通道清单的来源"),
        ("Linux_x86_64", "结果输出目录"),
    ]:
        if os.path.exists(path):
            ok(f"{path} 存在（{why}）")
        else:
            bad(f"{path} 不存在（{why}）")
            problems += 1

    if os.path.exists("data/Candu6.x2m.bak"):
        ok("data/Candu6.x2m.bak 备份在")
    else:
        warn("没看到 data/Candu6.x2m.bak：脚本会覆盖输入卡，建议先 cp data/Candu6.x2m data/Candu6.x2m.bak")
    return problems


def check_channels():
    path = "channels_list.txt"
    if not os.path.exists(path):
        bad("channels_list.txt 不存在：先跑 自动化/extract_from_c2m.py，输入 Candu6_proc/SetFuelMap.c2m")
        return 1
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        lines = [x.strip() for x in f if x.strip()]
    if len(lines) == EXPECT_CHANNELS:
        ok(f"channels_list.txt 共 {len(lines)} 个通道，与代理模型假设的 {EXPECT_CHANNELS} 一致")
        return 0
    warn(f"channels_list.txt 共 {len(lines)} 个通道，但 weights.npz 训练时假设 {EXPECT_CHANNELS} 个 → 索引会错位，需要重训或确认清单来源")
    return 0


def check_ai_files():
    problems = 0
    ai_dir = os.path.join("多时间步", "ai_accelerator")
    if not os.path.isdir(ai_dir):
        bad(f"{ai_dir} 不存在：脚本没拷到运行目录")
        return 1
    for name, needed in [
        ("weights.npz", "闭环搜索必需；仓库里在 SOMESTUFFS/Material/BP/"),
        ("dataset.csv", "只有重训时才需要"),
    ]:
        p = os.path.join(ai_dir, name)
        if os.path.exists(p):
            ok(f"{p} 存在")
        elif needed.startswith("闭环"):
            bad(f"{p} 不存在 → 从 SOMESTUFFS/Material/BP/{name} 拷过来")
            problems += 1
        else:
            warn(f"{p} 不存在（只有重训需要）")
    return problems


def check_layout():
    problems = 0
    for d in ["自动化", "多时间步", "DBO"]:
        if os.path.isdir(d):
            ok(f"{d}/ 在")
        else:
            bad(f"{d}/ 不在：把仓库 DONJON 下的目录拷到当前目录")
            problems += 1
    return problems


def smoke_test():
    print("\n-- 冒烟测试：真跑一次官方 CANDU6 算例（约 5 秒，不会改输入卡）--")
    if not os.path.exists("./rdonjon"):
        bad("没有 ./rdonjon，跳过")
        return 1
    with open("temp_smoke.log", "w") as log:
        subprocess.run(["./rdonjon", "Candu6.x2m"], stdout=log, stderr=subprocess.STDOUT)
    result = os.path.join("Linux_x86_64", "Candu6.result")
    if not os.path.exists(result):
        bad(f"没生成 {result}，看 temp_smoke.log")
        return 1
    with open(result, "r", errors="ignore") as f:
        content = f.read()
    m = re.search(r"K-EFFECTIVE.*?([0-9]+\.[0-9]+(?:[Ee][+-]?[0-9]+)?)", content)
    if not m:
        bad("result 里没抓到 K-EFFECTIVE")
        return 1
    keff = float(m.group(1))
    if abs(keff - EXPECT_KEFF) < 1e-4:
        ok(f"官方算例 Keff = {keff:.5f}，与基准 {EXPECT_KEFF} 一致 → 环境没问题")
        return 0
    warn(f"官方算例 Keff = {keff:.5f}，与基准 {EXPECT_KEFF} 有偏差 → 检查群常数库 / 输入卡是否被改过")
    return 0


def main():
    print("=" * 62)
    print(" DONJON 科研代码 环境自检")
    print(f" 当前目录: {os.getcwd()}")
    print("=" * 62)
    problems = 0
    problems += 0 if check_python() else 1
    print("\n-- Python 依赖 --")
    problems += check_packages()
    print("\n-- DONJON 本体与算例 --")
    problems += check_donjon()
    print("\n-- 脚本目录 --")
    problems += check_layout()
    print("\n-- 通道清单 --")
    problems += check_channels()
    print("\n-- 代理模型文件 --")
    problems += check_ai_files()

    if "--smoke" in sys.argv:
        problems += smoke_test()

    print("\n" + "=" * 62)
    if problems == 0:
        print(" 结论：可以跑。下一步 python3 自动化/pso_optimizer.py（约 25 分钟）")
    else:
        print(f" 结论：还有 {problems} 个问题要修，先看上面 [FAIL] 行")
    print("=" * 62)
    return 0 if problems == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
