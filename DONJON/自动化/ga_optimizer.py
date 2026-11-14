import random
import csv
from auto_run import evaluate

with open("channels_list.txt", "r") as f:
    valid_channels = [line.strip() for line in f if line.strip()]
NUM_CHANNELS = len(valid_channels)

def calc_score(keff, ppf):
    if keff is None or ppf is None: return -999.0
    if ppf > 1.4: return keff - 50.0 * (ppf - 1.4)
    return keff - 0.005 * (ppf - 1.0)

class GA:
    def __init__(self, pop_size=20, max_iter=20):
        self.pop = [random.sample(range(NUM_CHANNELS), 4) for _ in range(pop_size)]
        self.max_iter = max_iter
        self.pop_size = pop_size
        self.g_best_score = -999.0
        self.g_best_pos = None
        self.g_best_keff = None
        self.g_best_ppf = None
        
        self.f = open('ga_history.csv', 'w', newline='', encoding='utf-8')
        self.writer = csv.writer(self.f)
        self.writer.writerow(["Generation", "Best_Score", "Best_Keff", "Best_PPF", "Best_Channels"])

    def optimize(self):
        stagnation_counter = 0
        for it in range(self.max_iter):
            scored_pop = []
            update_flag = False
            
            for ind in self.pop:
                chosen = [valid_channels[i] for i in ind]
                keff, ppf, _ = evaluate(chosen)
                score = calc_score(keff, ppf)
                scored_pop.append((score, ind))
                
                if score > self.g_best_score and keff is not None:
                    self.g_best_score = score
                    self.g_best_pos = list(ind)
                    self.g_best_keff = keff
                    self.g_best_ppf = ppf
                    update_flag = True

            if self.g_best_pos:
                ch_str = str([valid_channels[i] for i in self.g_best_pos])
                self.writer.writerow([it+1, self.g_best_score, self.g_best_keff, self.g_best_ppf, ch_str])
                self.f.flush()
                print(f"Gen {it+1}: Keff={self.g_best_keff:.5f}, PPF={self.g_best_ppf:.4f}, Score={self.g_best_score:.5f}")

            if update_flag:
                stagnation_counter = 0
            else:
                stagnation_counter += 1
                
            if stagnation_counter >= 5:
                print(f"  [警告] GA 连续 5 代未突破，强制打散种群！")
                stagnation_counter = 0
                self.pop = [random.sample(range(NUM_CHANNELS), 4) for _ in range(self.pop_size)]
                continue

            scored_pop.sort(key=lambda x: x[0], reverse=True)
            new_pop = [scored_pop[0][1], scored_pop[1][1]]
            
            while len(new_pop) < self.pop_size:
                p1 = random.choice(self.pop)
                p2 = random.choice(self.pop)
                
                child_set = set(p1[:2] + p2[2:])
                child = list(child_set)
                if len(child) < 4:
                    remain = [x for x in range(NUM_CHANNELS) if x not in child]
                    child.extend(random.sample(remain, 4 - len(child)))
                
                if random.random() < 0.15:
                    idx = random.randint(0, 3)
                    cur_set = set(child)
                    cur_set.remove(child[idx])
                    avail = list(set(range(NUM_CHANNELS)) - cur_set)
                    child[idx] = random.choice(avail)
                    
                new_pop.append(child)
                
            self.pop = new_pop
        self.f.close()

if __name__ == "__main__":
    ga = GA(pop_size=20, max_iter=20)
    ga.optimize()
    print(f"\n最优序列: {[valid_channels[i] for i in ga.g_best_pos]}")