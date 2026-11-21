# dbo_optimizer.py
import random
import csv
import math
import numpy as np

from auto_run import evaluate

with open("channels_list.txt", "r") as f:
    valid_channels = [line.strip() for line in f if line.strip()]
NUM_CHANNELS = len(valid_channels)


def calc_score(keff, ppf):
    if keff is None or ppf is None:
        return -999.0
    if ppf > 1.4:
        return keff - 50.0 * (ppf - 1.4)
    return keff - 0.005 * (ppf - 1.0)


class DBO:
    def __init__(self, pop_size=20, max_iter=20):
        self.pop_size = pop_size
        self.max_iter = max_iter
        self.dim = 4  # 每次换4个通道

        # 种群初始化：每个个体是4个通道索引
        self.pop = [random.sample(range(NUM_CHANNELS), self.dim)
                    for _ in range(pop_size)]

        # 记录每个个体的历史位置（用于滚球公式里的 pos_old）
        self.pop_old = [list(ind) for ind in self.pop]

        # 适应度
        self.fitness = [-999.0] * pop_size

        # 全局最优
        self.g_best_pos = None
        self.g_best_score = -1000.0
        self.g_best_keff = None
        self.g_best_ppf = None

        # 全局最差（滚球公式需要）
        self.worst_pos = None
        self.worst_score = 1e9

        # 角色比例（滚球20%、繁育20%、小蜣螂25%、偷窃35%）
        n_roll = max(1, int(pop_size * 0.20))
        n_brood = max(1, int(pop_size * 0.20))
        n_small = max(1, int(pop_size * 0.25))
        n_thief = pop_size - n_roll - n_brood - n_small
        if n_thief < 1:
            n_thief = 1
            n_small -= 1

        self.idx_roll = list(range(0, n_roll))
        self.idx_brood = list(range(n_roll, n_roll + n_brood))
        self.idx_small = list(range(n_roll + n_brood, n_roll + n_brood + n_small))
        self.idx_thief = list(range(n_roll + n_brood + n_small, pop_size))

        # 记录CSV
        self.f = open('dbo_history.csv', 'w', newline='', encoding='utf-8')
        self.writer = csv.writer(self.f)
        self.writer.writerow(
            ["Generation", "Best_Score", "Best_Keff", "Best_PPF", "Best_Channels"]
        )

    def _to_discrete(self, continuous_pos):
        """把连续位置裁剪、取整、去重，映射回合法的4个通道索引"""
        discrete = []
        for x in continuous_pos:
            idx = int(round(x))
            idx = max(0, min(NUM_CHANNELS - 1, idx))
            discrete.append(idx)

        discrete = list(set(discrete))
        if len(discrete) < self.dim:
            remain = [i for i in range(NUM_CHANNELS) if i not in discrete]
            discrete.extend(random.sample(remain, self.dim - len(discrete)))
        return discrete[:self.dim]

    def _evaluate(self, pos):
        chosen = [valid_channels[i] for i in pos]
        keff, ppf, _ = evaluate(chosen)
        score = calc_score(keff, ppf)
        return score, keff, ppf

    def optimize(self):
        for it in range(self.max_iter):
            # 1. 评估当前种群
            for i in range(self.pop_size):
                score, keff, ppf = self._evaluate(self.pop[i])
                self.fitness[i] = score

                if score > self.g_best_score and keff is not None:
                    self.g_best_score = score
                    self.g_best_pos = list(self.pop[i])
                    self.g_best_keff = keff
                    self.g_best_ppf = ppf

                if score < self.worst_score:
                    self.worst_score = score
                    self.worst_pos = list(self.pop[i])

            # 记录本代结果
            if self.g_best_pos is not None:
                ch_str = str([valid_channels[i] for i in self.g_best_pos])
                self.writer.writerow(
                    [it + 1, self.g_best_score, self.g_best_keff,
                     self.g_best_ppf, ch_str]
                )
                self.f.flush()
                print(f"Gen {it+1}: Keff={self.g_best_keff:.5f}, "
                      f"PPF={self.g_best_ppf:.4f}, Score={self.g_best_score:.5f}")

            # 2. 按角色更新位置
            new_pop = [list(ind) for ind in self.pop]
            R = 1.0 - it / self.max_iter  # 动态收缩因子

            # ---------- 滚球蜣螂 ----------
            for i in self.idx_roll:
                pos = np.array(self.pop[i], dtype=float)
                pos_old = np.array(self.pop_old[i], dtype=float)

                # α = 1 或 -1
                alpha = 1 if random.random() > 0.5 else -1
                k = 0.1  # 偏转系数 (0, 0.2]
                b = random.random()  # 常数 (0, 1)

                if self.worst_pos is not None:
                    delta_x = np.abs(pos - np.array(self.worst_pos, dtype=float))
                else:
                    delta_x = np.zeros(self.dim)

                if random.random() < 0.9:
                    # 无障碍：直线滚球
                    new_pos = pos + alpha * k * (pos - pos_old) + b * delta_x
                else:
                    # 有障碍：跳舞转向
                    theta = random.uniform(0, math.pi)
                    new_pos = pos + math.tan(theta) * np.abs(pos - pos_old)

                new_pop[i] = self._to_discrete(new_pos)

            # ---------- 繁育蜣螂 ----------
            if self.g_best_pos is not None:
                best = np.array(self.g_best_pos, dtype=float)
                Lb = np.zeros(self.dim)
                Ub = np.full(self.dim, NUM_CHANNELS - 1, dtype=float)

                Lb_star = np.maximum(best * (1 - R), Lb)
                Ub_star = np.minimum(best * (1 - R), Ub)

                for i in self.idx_brood:
                    pos = np.array(self.pop[i], dtype=float)
                    b1 = np.random.random(self.dim)
                    b2 = np.random.random(self.dim)
                    new_pos = best + b1 * (pos - Lb_star) + b2 * (pos - Ub_star)
                    new_pop[i] = self._to_discrete(new_pos)

            # ---------- 小蜣螂（觅食） ----------
            if self.g_best_pos is not None:
                best = np.array(self.g_best_pos, dtype=float)
                Lb = np.zeros(self.dim)
                Ub = np.full(self.dim, NUM_CHANNELS - 1, dtype=float)

                Lbb = np.maximum(best * (1 - R), Lb)
                Ubb = np.minimum(best * (1 - R), Ub)

                for i in self.idx_small:
                    pos = np.array(self.pop[i], dtype=float)
                    C1 = np.random.randn(self.dim)  # 正态分布
                    C2 = np.random.random(self.dim)  # (0,1) 均匀分布
                    new_pos = pos + C1 * (pos - Lbb) + C2 * (pos - Ubb)
                    new_pop[i] = self._to_discrete(new_pos)

            # ---------- 偷窃蜣螂 ----------
            if self.g_best_pos is not None and self.worst_pos is not None:
                best = np.array(self.g_best_pos, dtype=float)
                worst = np.array(self.worst_pos, dtype=float)

                for i in self.idx_thief:
                    pos = np.array(self.pop[i], dtype=float)
                    g = np.random.randn(self.dim)  # 正态分布向量
                    S = 0.5
                    new_pos = best + S * g * (np.abs(pos - best) + np.abs(pos - worst))
                    new_pop[i] = self._to_discrete(new_pos)

            # 3. 保存历史位置，进入下一代
            self.pop_old = [list(ind) for ind in self.pop]
            self.pop = new_pop

        self.f.close()


if __name__ == "__main__":
    dbo = DBO(pop_size=20, max_iter=20)
    dbo.optimize()
    print(f"\n最优序列: {[valid_channels[i] for i in dbo.g_best_pos]}")