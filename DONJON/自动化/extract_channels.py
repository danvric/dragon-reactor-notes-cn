import re
import os
import sys

def extract_channels_from_result(input_path):
    print(f"🔍 开始处理文件: {input_path}")
    if not os.path.exists(input_path):
        print(f"❌ 找不到文件：{input_path}")
        return []

    with open(input_path, 'r', encoding='utf-8', errors='ignore') as in_file:
        content = in_file.read()

    channels = set()

    start_marker = "** CHANNEL POWERS IN RADIAL PLANE (kW) **"
    end_marker = "MAXIMUM BUNDLE POWER"
    
    start_idx = content.find(start_marker)
    end_idx = content.find(end_marker)
    
    if start_idx == -1 or end_idx == -1:
        print("❌ 未能在文件中找到通道功率表格标记！")
        return []

    table_content = content[start_idx:end_idx]
    lines = table_content.split('\n')
    
    # 我们记录当前的表头（左半部/右半部）
    current_headers = []
    
    # 核心映射：告诉程序 01-11 对应数组的哪几个位置，12-22 对应哪几个位置
    col_map_left = [None, None, None, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
    col_map_right = [12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, None, None, None]

    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # 如果这行是以 "-" 或数字开头的，说明它是表头行（如 "- - - 01 02 ..."）
        if re.match(r'^[-0-9\s]+$', line):
            tokens = line.split()
            if len(tokens) == 14: # 确保表头是14列
                current_headers = tokens
            continue
        
        # 如果这行是以大写字母 A-W 开头，说明是数据行
        if re.match(r'^[A-W]\s+', line):
            tokens = line.split()
            letter = tokens[0]
            vals = tokens[1:]
            
            # 如果是数据行，而且前面解析出了表头，且长度一致
            if len(vals) == len(current_headers) and len(vals) == 14:
                for idx, header in enumerate(current_headers):
                    # 如果表头不是 '-'，那就是合法列号
                    if header != '-':
                        col_num = int(header)
                        channels.add(f"{letter}{col_num:02d}")
            else:
                print(f"⚠️ 数据行跳过 (长度不匹配): {line[:40]}...")
                
    return sorted(list(channels))

if __name__ == '__main__':
    default_file = 'Candu6 - 副本.result.txt'
    
    if not os.path.exists(default_file):
        target_path = input("请把 result 文件拖拽到这里，然后按回车：\n").strip(" '\"\n")
    else:
        target_path = default_file
        
    print(f"\n正在解析: {target_path} ...\n")
    
    # 捕获所有可能的异常
    try:
        ch_names = extract_channels_from_result(target_path)
    except Exception as e:
        print(f"❌ 程序运行发生严重错误: {e}")
        sys.exit(1)
    
    if ch_names:
        print(f"\n✅ 成功提取！共找到 {len(ch_names)} 个合法通道。")
        print("预览前 20 个: ", ch_names[:20])
        
        # 强制把文件保存在当前脚本所在目录
        out_file = 'channels_list.txt'
        with open(out_file, 'w', encoding='utf-8') as save_file:
            for ch in ch_names:
                save_file.write(ch + '\n')
        print(f"✅ 结果已保存到: {os.path.abspath(out_file)}")
    else:
        print("\n❌ 提取失败：没有找到任何合法通道。可能是表头格式与预期不符。")