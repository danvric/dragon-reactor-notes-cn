import re
import os
import sys

def extract_channels_from_c2m(input_path):
    print(f"🔍 开始处理文件: {input_path}")
    if not os.path.exists(input_path):
        print(f"❌ 找不到文件：{input_path}")
        return []

    with open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # 1. 提取 X 和 Y 的名字列表
    # 使用 find 定位，避开没有分号导致的贪婪匹配灾难
    x_start = content.find("NXNAME")
    y_start = content.find("NYNAME")
    ncomb_start = content.find("NCOMB")
    
    if x_start == -1 or y_start == -1:
        print("❌ 未找到 NXNAME 或 NYNAME")
        return []
        
    x_part = content[x_start:y_start]
    # 如果找不到 NCOMB，就用 MIX 作为 Y 的结束符
    y_end = ncomb_start if ncomb_start != -1 else content.find("MIX")
    y_part = content[y_start:y_end]

    # 把引号里的内容抠出来，例如 '01', 'A'
    x_tokens = re.findall(r"'([^']+)'", x_part)
    y_tokens = re.findall(r"'([^']+)'", y_part)
    
    # 2. 提取 MIX 矩阵
    mix_start = content.find("MIX")
    fuel_start = content.find("FUEL", mix_start)
    if fuel_start == -1:
        fuel_start = content.find("END:", mix_start)
        
    mix_part = content[mix_start:fuel_start]
    
    matrix = []
    for line in mix_part.split('\n'):
        # 把感叹号后面的注释全切掉，例如 "!A 6" 切掉
        line = line.split('!')[0].strip()
        if not line: 
            continue
        
        tokens = line.split()
        # 矩阵每行全是 0 或 1，且列数等于 X 长度（28列）
        if all(t in ('0', '1') for t in tokens) and len(tokens) == len(x_tokens):
            matrix.append(tokens)
            
    # 3. 组合通道名称
    channels = []
    if len(matrix) != len(y_tokens):
        print(f"⚠️ 警告: 矩阵行数({len(matrix)})与Y名称数量({len(y_tokens)})不一致！")
        
    for r_idx, row in enumerate(matrix):
        if r_idx >= len(y_tokens): break
        y_name = y_tokens[r_idx]
        if y_name == '-': continue
        
        for c_idx, val in enumerate(row):
            if c_idx >= len(x_tokens): break
            if val == '1':
                x_name = x_tokens[c_idx]
                if x_name != '-':
                    # 组合成 A01, H06 等格式
                    channels.append(f"{y_name}{x_name}")

    return sorted(list(channels))


if __name__ == '__main__':
    default_file = 'SetFuelMap - 副本.txt' # 你发给我的那个文件名字
    
    # 保留你最喜欢的拖拽输入方式
    if not os.path.exists(default_file):
        target_path = input("请把 c2m 文件拖拽到这里，然后按回车：\n").strip(" '\"\n")
    else:
        target_path = default_file
        
    print(f"\n正在解析: {target_path} ...\n")
    
    try:
        ch_names = extract_channels_from_c2m(target_path)
    except Exception as e:
        print(f"❌ 程序运行发生严重错误: {e}")
        sys.exit(1)
    
    if ch_names:
        print(f"\n✅ 成功提取！共找到 {len(ch_names)} 个合法通道。")
        print("预览前 20 个: ", ch_names[:20])
        
        out_file = 'channels_list.txt'
        with open(out_file, 'w', encoding='utf-8') as save_file:
            for ch in ch_names:
                save_file.write(ch + '\n')
        print(f"✅ 结果已保存到: {os.path.abspath(out_file)}")
    else:
        print("\n❌ 提取失败：没有找到任何合法通道。")