import subprocess
import os
import re

def evaluate(chosen_channels):
    run_file = "data/Candu6.x2m"
    result_file = os.path.join("Linux_x86_64", "Candu6.result")
    
    refuel_lines = ""
    for ch in chosen_channels:
        refuel_lines += f"          REFUEL CHAN {ch}  8\n"

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
        
    if os.path.exists(result_file):
        os.remove(result_file)
        
    log_name = "temp_run.log"
    with open(log_name, "w") as log_file:
        subprocess.run(["./rdonjon", "Candu6.x2m"], stdout=log_file, stderr=subprocess.STDOUT)
    
    keff = None
    ppf = None
    max_channel_power = None
    
    if os.path.exists(result_file):
        with open(result_file, "r", errors="ignore") as f:
            content = f.read()
            
            # 抓 Keff
            match_k = re.search(r"K-EFFECTIVE.*?([0-9]+\.[0-9]+(?:[Ee][+-]?[0-9]+)?)", content)
            if match_k: keff = float(match_k.group(1))
            
            # 抓 PPF (Max/Avg 比值)
            match_p = re.search(r"BUNDLE-POWER FORM FACTOR.*?MAX/AVG\s*=\s*([0-9.]+)", content)
            if match_p: ppf = float(match_p.group(1))
            
            # 抓最大通道功率
            match_c = re.search(r"MAXIMUM CHANNEL POWER\s*=\s*([0-9.]+)", content)
            if match_c: max_channel_power = float(match_c.group(1))
            
    return keff, ppf, max_channel_power