import random
import csv
from auto_run_restart import evaluate_restart

with open("channels_list.txt", "r") as f:
    valid_channels = [line.strip() for line in f if line.strip()]
NUM_CHANNELS = len(valid_channels)

def calc_score(keff, ppf):
    if keff is None or ppf is None: return -999.0
    if ppf > 1.4: return keff - 50.0 * (ppf - 1.4)
    return keff - 0.005 * (ppf - 1.0)

def run_pso_for_step(history, num_particles=3, max_iter=3):
    particles = []
    for _ in range(num_particles):
        pos = random.sample(range(NUM_CHANNELS), 4)
        particles.append({'pos': pos, 'p_best_pos': list(pos), 'p_best_score': -999.0})
    
    g_best_pos = None
    g_best_score = -1000.0
    g_best_keff = None
    g_best_ppf = None
    eval_count = 0

    for it in range(max_iter):
        for p in particles:
            chosen = [valid_channels[i] for i in p['pos']]
            eval_count += 1
            print(f"      [评估 {eval_count}/{num_particles * max_iter}] 正在计算: {chosen} ...", end="", flush=True)
            
            keff, ppf = evaluate_restart(chosen, history=history)
            
            score = calc_score(keff, ppf)
            if keff is not None:
                print(f" -> Keff={keff:.5f}, PPF={ppf:.4f}")
            else:
                print(f" -> 失败")
            
            if score > p['p_best_score']:
                p['p_best_score'] = score
                p['p_best_pos'] = list(p['pos'])
            if score > g_best_score and keff is not None:
                g_best_score = score
                g_best_pos = list(p['pos'])
                g_best_keff = keff
                g_best_ppf = ppf
                
        if g_best_pos is None:
            # 如果这一代全失败了，直接跳出，避免报错
            break
            
        for p in particles:
            for i in range(4):
                if random.random() < 0.3:
                    target = p['p_best_pos'][i]
                    p['pos'][i] = max(0, min(NUM_CHANNELS - 1, target + random.randint(-5, 5)))
                if random.random() < 0.2:
                    target = g_best_pos[i]
                    p['pos'][i] = max(0, min(NUM_CHANNELS - 1, target + random.randint(-5, 5)))
            p['pos'] = list(set(p['pos']))
            if len(p['pos']) < 4:
                remain = [i for i in range(NUM_CHANNELS) if i not in p['pos']]
                p['pos'].extend(random.sample(remain, 4 - len(p['pos'])))
    
    if g_best_pos is None:
        return None, None, None
        
    return [valid_channels[i] for i in g_best_pos], g_best_keff, g_best_ppf

if __name__ == "__main__":
    print("=======================================")
    print("   开始 PSO 驱动的连续换料模拟   ")
    print("=======================================")
    
    csv_file = open('daily_optimization_history.csv', 'w', newline='', encoding='utf-8')
    writer = csv.writer(csv_file)
    writer.writerow(["Day", "Keff", "PPF", "Channels"])

    history = []
    total_steps = 10 # 先跑 10 步看看效果
    
    for step in range(1, total_steps + 1):
        print(f"\n>>> 第 {step} 次换料 (Day {step*3}) 开始 <<<")
        
        best_channels, best_keff, best_ppf = run_pso_for_step(history, num_particles=3, max_iter=3)
        
        if best_channels is not None:
            print(f"  [PSO 结束] 最优通道: {best_channels}, Keff={best_keff:.5f}, PPF={best_ppf:.4f}")
            writer.writerow([step*3, best_keff, best_ppf, str(best_channels)])
            csv_file.flush()
            history.append(best_channels)
        else:
            print(f"❌ 第 {step} 步计算失败，终止模拟。")
            break

    csv_file.close()
    print("\n模拟结束！数据已保存至 daily_optimization_history.csv")