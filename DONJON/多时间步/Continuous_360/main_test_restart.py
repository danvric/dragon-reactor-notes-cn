import random
from auto_run_restart import evaluate_restart

with open("channels_list.txt", "r") as f:
    valid_channels = [line.strip() for line in f if line.strip()]

print("开始 360 天 Restart 流程测试 (模拟 10 步)...")

history = [] # 用来记录每次的换料

for step in range(1, 11):
    # 随机挑 4 个通道
    chosen = random.sample(valid_channels, 4)
    
    # 传入当前选中的通道，和之前的所有历史换料
    keff, ppf = evaluate_restart(chosen, history=history)
    
    if keff is not None and ppf is not None:
        print(f"Step {step} (Day {step}): 换料 {chosen} -> Keff={keff:.5f}, PPF={ppf:.4f}")
        # 计算成功，将本次换料加入历史记录，供下一步使用
        history.append(chosen)
    else:
        print(f"Step {step}: 计算失败，请检查 temp_run.log 和 Candu6.result。")