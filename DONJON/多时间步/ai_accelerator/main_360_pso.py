# main_360_pso.py (闭环终极版)
import random
import csv
import time
from dd_restart_evaluator import evaluate_restart
from predict_numpy import predict

with open("channels_list.txt", "r") as f:
    valid_channels = [line.strip() for line in f if line.strip()]
NUM_CHANNELS = len(valid_channels)

def calc_fitness(keff, ppf, pos_indices, history, bad_combinations):
    """刘仕倡罚函数 + 历史物理约束"""
    if keff is None or ppf is None: return -999.0
    
    # 1. 如果是被拉黑的组合，直接零分
    if tuple(sorted(pos_indices)) in bad_combinations:
        return -9999.0
        
    # 2. 历史防重惩罚：如果通道在最近 15 步内换过料，狠狠扣分
    recent_channels = [ch for step in history[-15:] for ch in step]
    recent_indices = set([valid_channels.index(ch) for ch in recent_channels if ch in valid_channels])
    
    history_penalty = 0.0
    for idx in pos_indices:
        if idx in recent_indices:
            history_penalty += 50.0  # 极重的惩罚，逼迫 PSO 去找没换过的通道
            
    # 3. 空间聚集惩罚（王德营特征）
    sorted_pos = sorted(pos_indices)
    min_dist = min(sorted_pos[1] - sorted_pos[0], sorted_pos[2] - sorted_pos[1], sorted_pos[3] - sorted_pos[2])
    cluster_penalty = (8 - min_dist) * 0.05 if min_dist < 8 else 0.0
    
    # 4. 刘仕倡罚函数
    if ppf > 1.35: # AI 红线收紧
        return keff - 50.0 * (ppf - 1.35) - cluster_penalty - history_penalty
    
    return keff - 0.005 * (ppf - 1.0) - cluster_penalty - history_penalty

def run_pso(history, bad_combinations, num_particles=30, max_iter=30):
    """纯正离散 PSO 搜索"""
    particles = []
    for _ in range(num_particles):
        pos = random.sample(range(NUM_CHANNELS), 4)
        particles.append({
            'pos': pos, 
            'vel': [random.uniform(-1, 1) for _ in range(4)],
            'p_best_pos': list(pos), 
            'p_best_fit': -999.0
        })
    
    g_best_pos = None
    g_best_fit = -10000.0

    for it in range(max_iter):
        for p in particles:
            pred_keff, pred_ppf = predict(p['pos'])
            fit = calc_fitness(pred_keff, pred_ppf, p['pos'], history, bad_combinations)
            
            if fit > p['p_best_fit']:
                p['p_best_fit'] = fit
                p['p_best_pos'] = list(p['pos'])
            if fit > g_best_fit:
                g_best_fit = fit
                g_best_pos = list(p['pos'])
                
        for p in particles:
            for i in range(4):
                r1, r2 = random.random(), random.random()
                p['vel'][i] = 0.5 * p['vel'][i] + 1.5 * r1 * (p['p_best_pos'][i] - p['pos'][i]) + 1.5 * r2 * (g_best_pos[i] - p['pos'][i])
                p['pos'][i] = int(p['pos'][i] + p['vel'][i])
                p['pos'][i] = max(0, min(NUM_CHANNELS - 1, p['pos'][i]))
            
            p['pos'] = list(set(p['pos']))
            if len(p['pos']) < 4:
                remain = [i for i in range(NUM_CHANNELS) if i not in p['pos']]
                p['pos'].extend(random.sample(remain, 4 - len(p['pos'])))
                
    return [valid_channels[i] for i in g_best_pos], g_best_pos

if __name__ == "__main__":
    print("=======================================")
    print(" 开始 360 天 PSO 闭环智能连续换料模拟 ")
    print("=======================================")
    
    csv_file = open('optimization_history_closedloop.csv', 'w', newline='', encoding='utf-8')
    writer = csv.writer(csv_file)
    writer.writerow(["Day", "Real_Keff", "Real_PPF", "Channels"])

    history = []
    total_steps = 180 
    
    for step in range(1, total_steps + 1):
        print(f"\n>>> 第 {step} 次换料 (Day {step*2}) 开始 <<<")
        
        # 闭环搜索机制：最多尝试 5 次重新搜索，直到真实 PPF 合格
        bad_combinations = set()
        success = False
        
        for attempt in range(5):
            # 1. PSO 智能搜索
            best_channels, pos_indices = run_pso(history, bad_combinations)
            print(f"  [PSO 第 {attempt+1} 次搜索] 选定通道: {best_channels}")
            
            # 2. 真实 DD 校验
            print(f"  [DD 真实验证] ...", end="", flush=True)
            real_keff, real_ppf = evaluate_restart(best_channels, history=history)
            
            if real_keff is not None:
                print(f" -> 真实 Keff={real_keff:.5f}, PPF={real_ppf:.4f}")
                
                if real_ppf <= 1.4:
                    print(f"  ✅ 方案通过安全限值！")
                    writer.writerow([step*2, real_keff, real_ppf, str(best_channels)])
                    csv_file.flush()
                    history.append(best_channels)
                    success = True
                    break
                else:
                    print(f"  ❌ PPF 超标！将组合拉入黑名单，PSO 重新搜索...")
                    bad_combinations.add(tuple(sorted(pos_indices)))
            else:
                print(" -> 计算失败")
                break
                
        if not success:
            print(f"  🚨 连续 5 次搜索仍然无法满足 PPF <= 1.4。为了程序不中断，强行记录当前历史最优状态。")
            # 如果实在没招了，用 DD 计算结果（虽然超标，但记录真相）
            writer.writerow([step*2, real_keff, real_ppf, str(best_channels)])
            csv_file.flush()
            history.append(best_channels)
            
    csv_file.close()
    print(f"\n=======================================")
    print(f" 模拟结束！真实数据已保存至 optimization_history_closedloop.csv")
    print(f"=======================================")