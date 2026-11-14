import random
import csv
from auto_run import evaluate

with open("channels_list.txt", "r") as f:
    valid_channels = [line.strip() for line in f if line.strip()]
NUM_CHANNELS = len(valid_channels)

def calc_score(keff, ppf):
    if keff is None or ppf is None: return -999.0
    # 违规时：重罚（50.0），强迫压回 1.4 以下
    if ppf > 1.4: return keff - 50.0 * (ppf - 1.4)
    # 合规时：Keff 绝对主导，PPF 极小惩罚（0.005），防止死贴红线
    return keff - 0.005 * (ppf - 1.0)

class PSO:
    def __init__(self, num_particles=20, max_iter=20):
        self.particles = []
        for _ in range(num_particles):
            pos = random.sample(range(NUM_CHANNELS), 4)
            self.particles.append({'pos': pos, 'vel': [random.uniform(-1, 1) for _ in range(4)], 'p_best_pos': list(pos), 'p_best_score': -999.0})
        
        self.g_best_pos = None
        self.g_best_score = -1000.0
        self.g_best_keff = None
        self.g_best_ppf = None
        self.max_iter = max_iter
        self.w, self.c1, self.c2 = 0.6, 1.5, 1.5
        
        self.f = open('pso_history.csv', 'w', newline='', encoding='utf-8')
        self.writer = csv.writer(self.f)
        self.writer.writerow(["Generation", "Global_Best_Score", "Global_Best_Keff", "Global_Best_PPF", "Gen_Best_Keff", "Gen_Best_PPF", "Global_Best_Channels"])

    def optimize(self):
        stagnation_counter = 0
        for it in range(self.max_iter):
            update_flag = False
            gen_best_score = -999.0
            gen_best_keff = None
            gen_best_ppf = None
            
            for p in self.particles:
                chosen = [valid_channels[i] for i in p['pos']]
                keff, ppf, _ = evaluate(chosen)
                score = calc_score(keff, ppf)
                
                if score > gen_best_score and keff is not None:
                    gen_best_score = score
                    gen_best_keff = keff
                    gen_best_ppf = ppf
                
                if score > p['p_best_score']:
                    p['p_best_score'] = score
                    p['p_best_pos'] = list(p['pos'])
                
                if score > self.g_best_score and keff is not None:
                    self.g_best_score = score
                    self.g_best_pos = list(p['pos'])
                    self.g_best_keff = keff
                    self.g_best_ppf = ppf
                    update_flag = True

            if self.g_best_pos:
                ch_str = str([valid_channels[i] for i in self.g_best_pos])
                self.writer.writerow([it+1, self.g_best_score, self.g_best_keff, self.g_best_ppf, gen_best_keff, gen_best_ppf, ch_str])
                self.f.flush()
                print(f"Gen {it+1}: Global_Keff={self.g_best_keff:.5f}, Gen_Keff={gen_best_keff:.5f}, PPF={gen_best_ppf:.4f}")

            if update_flag:
                stagnation_counter = 0
            else:
                stagnation_counter += 1
                
            if stagnation_counter >= 5:
                print(f"  [警告] 连续 5 代未突破，基于全局最优进行局部扰动打散！")
                stagnation_counter = 0
                for p in self.particles:
                    new_pos = list(self.g_best_pos)
                    num_to_change = random.choice([1, 2, 3])
                    idxs = random.sample(range(4), num_to_change)
                    for idx in idxs:
                        remain = [x for x in range(NUM_CHANNELS) if x not in new_pos]
                        new_pos[idx] = random.choice(remain)
                    
                    p['pos'] = new_pos
                    p['vel'] = [random.uniform(-2, 2) for _ in range(4)]
                continue

            for p in self.particles:
                for i in range(4):
                    r1, r2 = random.random(), random.random()
                    p['vel'][i] = (self.w * p['vel'][i] + 
                                   self.c1 * r1 * (p['p_best_pos'][i] - p['pos'][i]) +
                                   self.c2 * r2 * (self.g_best_pos[i] - p['pos'][i]))
                    p['pos'][i] = int(p['pos'][i] + p['vel'][i])
                
                p['pos'] = [max(0, min(NUM_CHANNELS - 1, x)) for x in p['pos']]
                p['pos'] = list(set(p['pos']))
                if len(p['pos']) < 4:
                    remain = [i for i in range(NUM_CHANNELS) if i not in p['pos']]
                    p['pos'].extend(random.sample(remain, 4 - len(p['pos'])))
        self.f.close()

if __name__ == "__main__":
    pso = PSO(num_particles=20, max_iter=20)
    pso.optimize()
    print(f"\n最优序列: {[valid_channels[i] for i in pso.g_best_pos]}")