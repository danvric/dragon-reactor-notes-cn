# generate_dataset.py
import os
import csv
import random
import time
from dd_evaluator import evaluate

current_dir = os.path.dirname(os.path.abspath(__file__))
DATASET_FILE = os.path.join(current_dir, 'dataset.csv')
CHANNELS_FILE = os.path.join(current_dir, 'channels_list.txt')

def load_existing_data():
    done_set = set()
    if os.path.exists(DATASET_FILE):
        with open(DATASET_FILE, 'r') as f:
            reader = csv.reader(f)
            next(reader, None)
            for row in reader:
                if len(row) >= 4:
                    done_set.add(tuple(map(int, row[:4])))
    return done_set

def main(num_samples=500):
    with open(CHANNELS_FILE, "r") as f:
        valid_channels = [line.strip() for line in f if line.strip()]
    NUM_CHANNELS = len(valid_channels)

    if not os.path.exists(DATASET_FILE):
        with open(DATASET_FILE, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["ch_idx_1", "ch_idx_2", "ch_idx_3", "ch_idx_4", "Keff", "PPF", "ch_names"])

    done_set = load_existing_data()
    print(f"已有数据量: {len(done_set)} 条。计划目标: {num_samples} 条。")
    count = len(done_set)
    start_time = time.time()
    fail_count = 0  # 新增：失败计数器

    with open(DATASET_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        while count < num_samples:
            chosen_idx = random.sample(range(NUM_CHANNELS), 4)
            if tuple(chosen_idx) in done_set:
                continue
                
            chosen_names = [valid_channels[i] for i in chosen_idx]
            print(f"[{count+1}/{num_samples}] 计算中: {chosen_names} ...", end="", flush=True)
            
            try:
                keff, ppf, _ = evaluate(chosen_names)
                if keff is not None and ppf is not None:
                    print(f" -> Keff={keff:.5f}, PPF={ppf:.4f}")
                    writer.writerow(chosen_idx + [keff, ppf, str(chosen_names)])
                    f.flush()
                    done_set.add(tuple(chosen_idx))
                    count += 1
                    fail_count = 0 # 成功一次，重置失败计数
                else:
                    print(" -> 计算失败")
                    fail_count += 1
            except Exception as e:
                print(f" -> 异常: {e}")
                fail_count += 1
                
            # 新增：连续失败 3 次，强制停止，防止死循环
            if fail_count >= 3:
                print("\n❌ 连续发生 3 次严重异常，为防止死循环，已自动终止！请检查 temp_run_ai.log。")
                break
                
    elapsed = time.time() - start_time
    print(f"\n完成！文件位于: {DATASET_FILE}，耗时 {elapsed/60:.1f} 分钟。")

if __name__ == "__main__":
    main(num_samples=500)