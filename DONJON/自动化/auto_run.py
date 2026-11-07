import subprocess
import random
import os
import re

# 1. 读取合法通道
with open("channels_list.txt", "r") as f:
    valid_channels = [line.strip() for line in f if line.strip()]

run_file = "data/Candu6.x2m"
result_file = os.path.join("Linux_x86_64", "Candu6.result")

results_file = open("results.csv", "w")
results_file.write("Run_ID,Channel_1,Channel_2,Channel_3,Channel_4,Keff,Max_Bundle_Power,Max_Channel_Power\n")

for i in range(3):
    chosen = random.sample(valid_channels, 4)
    
    # 拼装换料指令，严格遵守 TINST: 的换行格式
    refuel_lines = ""
    for ch in chosen:
        refuel_lines += f"          REFUEL CHAN {ch}  8\n"

    # 2. 你原本的 x2m 内容（原封不动，没加 ECHO 也没加 GREP POWER）
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
    
    if not os.path.exists("data"):
        os.makedirs("data")

    with open(run_file, "w") as f:
        f.write(x2m_content)
        
    print(f"\n[{i+1}/3] 测试通道: {chosen} ... 运行中")
    
    # 跑之前强杀旧 result
    if os.path.exists(result_file):
        os.remove(result_file)
        
    log_name = f"run_{i+1}.log"
    with open(log_name, "w") as log_file:
        subprocess.run(["./rdonjon", "Candu6.x2m"], stdout=log_file, stderr=subprocess.STDOUT)
    
    keff = "Error"
    max_bundle_power = "Error"
    max_channel_power = "Error"
    
    # 【关键修复】直接去 result 文件里抓数据！
    if os.path.exists(result_file):
        with open(result_file, "r", errors="ignore") as f:
            content = f.read()
            
            # 抓取 K-EFFECTIVE (兼容你代码里的 ECHO 格式)
            match_k = re.search(r"K-EFFECTIVE.*?([0-9]+\.[0-9]+(?:[Ee][+-]?[0-9]+)?)", content)
            if match_k: 
                keff = float(match_k.group(1))
            
            # 抓取 MAXIMUM BUNDLE POWER
            match_b = re.search(r"MAXIMUM BUNDLE POWER\s*=\s*([0-9.]+)", content)
            if match_b: 
                max_bundle_power = float(match_b.group(1))
            
            # 抓取 MAXIMUM CHANNEL POWER
            match_c = re.search(r"MAXIMUM CHANNEL POWER\s*=\s*([0-9.]+)", content)
            if match_c: 
                max_channel_power = float(match_c.group(1))

    # 直接打印在终端
    print(f"-> 结果: Keff={keff}, 最大棒功率={max_bundle_power}, 最大通道功率={max_channel_power}")
    
    # 存入 CSV
    results_file.write(f"{i+1},{chosen[0]},{chosen[1]},{chosen[2]},{chosen[3]},{keff},{max_bundle_power},{max_channel_power}\n")

results_file.close()
print("\n全部跑完！请查看上面的输出。")