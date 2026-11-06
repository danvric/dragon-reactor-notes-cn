import subprocess
import random
import os
import re

# 1. 读取合法通道
with open("channels_list.txt", "r") as f:
    valid_channels = [line.strip() for line in f if line.strip()]

# 【关键修复】必须把运行文件放在 data 目录下！
run_file = "data/Candu6.x2m"
result_file = os.path.join("Linux_x86_64", "Candu6.result")

results_file = open("results.csv", "w")
results_file.write("Run_ID,Channel_1,Channel_2,Channel_3,Channel_4,Keff\n")

for i in range(3):
    chosen = random.sample(valid_channels, 4)
    
    # 生成换料指令，严格遵守 TINST: 的换行格式
    refuel_lines = ""
    for ch in chosen:
        refuel_lines += f"          REFUEL CHAN {ch}  8\n"

    # 2. 完整纯净的 x2m 内容
    x2m_content = f"""PROCEDURE assertS SetModel SetReflPro SetDevPro 
          SetFuelMap SetBurnup SetDevice SetDetect ;
LINKED_LIST GEOM MATEX TRACK DEVICE MACRO FMAP NEWFLUX
            MACROFUEL MACROFUEL2 MACRO3 SYSTEM FLUX POWER DETECT ;
MODULE DSET: CRE: MACINI: TRIVAT: TRIVAA: NEWMAC: DETECT:
       FLUD: FLPOW: TINST: DELETE: GREP: END:   ;
REAL Keff ;
INTEGER MaxR := 30000 ;
GEOM MATEX := SetModel :: <<MaxR>> ;
TRACK := TRIVAT: GEOM :: MAXR <<MaxR>> MCFD 1 ;
DEVICE MATEX := SetDevice MATEX ;
DEVICE := DSET: DEVICE ::
  EDIT 0
  LZC 1 LEVEL .5026 TIME 60. END
  LZC 2 LEVEL .5400 TIME 36. END
  LZC 3 LEVEL .3853 TIME 36. END
  LZC 4 LEVEL .3442 TIME 36. END
  LZC 5 LEVEL .4485 TIME 36. END
  LZC 6 LEVEL .5590 TIME 60. END
  LZC 7 LEVEL .3803 TIME 36. END
  LZC 8 LEVEL .4354 TIME 60. END
  LZC 9 LEVEL .5313 TIME 36. END
  LZC 10 LEVEL .5642 TIME 36. END
  LZC 11 LEVEL .4256 TIME 36. END
  LZC 12 LEVEL .4427 TIME 36. END
  LZC 13 LEVEL .5752 TIME 60. END
  LZC 14 LEVEL .5126 TIME 36. END
 ;
DETECT := SetDetect ;
FMAP MATEX := SetFuelMap MATEX ;
FMAP := SetBurnup FMAP ;
FMAP := TINST: FMAP  ::
          EDIT 0
          TIME 1.0 DAY 
{refuel_lines}          TIME 2.4  DAY  ;
LINKED_LIST CPOREFL ;
SEQ_ASCII CELNAT REFL ;
CPOREFL := REFL ;
MACRO := SetReflPro CPOREFL ;
LINKED_LIST GT ADJ ZCR STRUC ;
SEQ_ASCII GTUBEB RODB ZCPOB MATSTRB ;
GT := GTUBEB  ;
STRUC := MATSTRB ;
ZCR := ZCPOB   ;
ADJ := RODB   ;
MACRO := SetDevPro MACRO GT ADJ ZCR STRUC ;
LINKED_LIST CPOFUEL ;
SEQ_ASCII CELNAT ;
CPOFUEL := CELNAT ;
MACROFUEL := CRE: CPOFUEL FMAP :: EDIT 0 READ
            TABLE CPOFUEL 
            MIX 1 'MIXTRXE    1'
            INST-BURN
            MICRO ALL
            ENDMIX ;
MACROFUEL2 MATEX := MACINI: MATEX MACRO MACROFUEL :: EDIT 0 ;
MACRO3 MATEX := NEWMAC: MATEX MACROFUEL2 DEVICE :: EDIT 0 ;
SYSTEM := TRIVAA: MACRO3 TRACK :: EDIT 0 ;
FLUX := FLUD: SYSTEM TRACK ::  EDIT 0 EXTE 100 1.E-6 ;
POWER NEWFLUX := FLPOW: FMAP FLUX TRACK MATEX :: EDIT 2 PTOT 2061.4 ;
DETECT := DETECT: DETECT NEWFLUX TRACK GEOM :: EDIT 5 REF 0 TIME 0.25 SIMEX ;
SYSTEM MATEX TRACK MACRO MACROFUEL MACROFUEL2 GEOM DETECT
FMAP := DELETE: SYSTEM MATEX TRACK MACRO MACROFUEL MACROFUEL2 DETECT GEOM FMAP ;
GREP: FLUX :: GETVAL "K-EFFECTIVE" 1 >>Keff<< ;
ECHO "K-EFFECTIVE: " Keff ;
END: ;
QUIT .
"""
    
    # 确保 data 目录存在（虽然通常都有）
    if not os.path.exists("data"):
        os.makedirs("data")

    # 写入纯净版 x2m 到 data 目录！
    with open(run_file, "w") as f:
        f.write(x2m_content)
        
    print(f"\n[{i+1}/3] 测试通道: {chosen} ... 运行中")
    
    # 强杀旧的 result 文件
    if os.path.exists(result_file):
        os.remove(result_file)
        
    log_name = f"run_{i+1}.log"
    with open(log_name, "w") as log_file:
        # 【关键修复】调用时带上 data/ 路径
        subprocess.run(["./rdonjon", "Candu6.x2m"], stdout=log_file, stderr=subprocess.STDOUT)
    
    keff = "Error"
    
    # 3. 双保险提取
    if os.path.exists(log_name):
        with open(log_name, "r", errors="ignore") as f:
            content = f.read()
            match = re.search(r"K-EFFECTIVE:\s*([0-9]+\.[0-9]+(?:E[+-]?[0-9]+)?)", content)
            if match:
                keff = match.group(1)
            elif os.path.exists(result_file):
                with open(result_file, "r", errors="ignore") as rf:
                    rc = rf.read()
                    # result 文件里 K-EFFECTIVE 后面通常跟着一堆空格和数字
                    match2 = re.search(r"K-EFFECTIVE\s+([0-9]+\.[0-9]+(?:E[+-]?[0-9]+)?)", rc)
                    if match2:
                        keff = match2.group(1)
                
    print(f"✅ 结果: Keff = {keff}")
    results_file.write(f"{i+1},{chosen[0]},{chosen[1]},{chosen[2]},{chosen[3]},{keff}\n")

results_file.close()
print("\n全部跑完！请查看 results.csv")