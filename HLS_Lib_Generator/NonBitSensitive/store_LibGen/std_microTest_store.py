import os
import sys
import re
import time
import json
import time

start = time.time()

def search_file(path,name):
    for root, dirs, files in os.walk(path):  # path 为根目录
        if name in dirs or name in files:
            flag = 1      #判断是否找到文件
            root = str(root)
            dirs = str(dirs)
            return os.path.join(root, dirs)
    return -1

def find_value_in_report(line,target):
    target = "<"+target+" ="
    tmpA = line[line.find(target)+len(target)+1:]
    tmpB = tmpA[:tmpA.find(">")+len(">")-1]
    return tmpB

path_str_split = os.path.abspath(sys.argv[0]).split("/")
pathHead = os.path.abspath(sys.argv[0]).replace('microTest_store.py',"")

source_file_name = pathHead + "top.cc"
tcl_file_name = pathHead + "run.tcl"
dump_resource_file_name = pathHead + "resource.json"
dump_timing_file_name = pathHead + "timing.json"
overview_file_name = pathHead + "overview"



source_file = open(source_file_name, "w")
tcl_file = open(tcl_file_name, "w")

template_source_code = """
#include<cstdio>
#include<iostream>
#include<ap_int.h>
#include "ap_utils.h"

using namespace std;

int top(int a,int A[100])
{
	A[a]=a;
    return 0;
}
"""

tcl_source_code = """
open_project microBench_store
set_top top
add_files FFFFF
open_solution "solution1"
set_part {platform-name}
create_clock -period CLKCLK -name default
csynth_design
exit
"""


resource_dict = dict()
delay_dict = dict()


dump_resource_file = open(dump_resource_file_name,'a')
dump_timing_file = open(dump_timing_file_name,'a')
overview_file = open(overview_file_name,'w')

platform_name = ""

input_settings = path_str_split[-2]
if (len(re.findall(r"^store_-*[0-9]+_-*[0-9]+_",input_settings))>0):
    paras = input_settings.replace("store_","").split("_")
    startBitwidth = int(paras[0])
    endBitwidth = int(paras[1])
    platform_name = paras[2]
        

if (platform_name==""):
    assert(False and "failed to parse the name of directory")

tcl_source_code = tcl_source_code.replace("platform-name",platform_name)

for oprandC in range(startBitwidth,endBitwidth+1):
        
    oprandB = oprandC
    oprandA = oprandC
    source_code_string = template_source_code.replace("XXXXX",str(oprandA)).replace("YYYYY",str(oprandB)).replace("ZZZZZ",str(oprandC))               
    check1 = ""
    check2 = ""
    check3 = ""
    check4 = ""
    for clock_rate in [3,4,5,6,7,8,9,10,12.5,15,16,17.5,20,25,30]:

        # generate source code and corresponging tcl commands

        print("==========================================================")
        print("trying "+str(oprandA)+"x"+str(oprandB)+"=>"+str(oprandC)+"    @clk_period="+str(clock_rate))
        print("==========================================================")

        source_file = open(source_file_name, "w")
        tcl_file = open(tcl_file_name, "w") 

        tcl_string = tcl_source_code.replace("CLKCLK",str(clock_rate)).replace("FFFFF",source_file_name)
        print(source_code_string,file=source_file)
        print(tcl_string,file=tcl_file)

        source_file.close()
        tcl_file.close()

        # execute HLS
        # os.system("vivado_hls -f "+tcl_file_name+"> hls_log")
        os.system(("(cd PATH; vivado_hls -f "+tcl_file_name+"> hls_log)").replace("PATH",pathHead))

        # find the report
        result_rpt = re.sub("\[.*\]","top.verbose.rpt",str(search_file(pathHead,"top.verbose.rpt")))

        print("find report:        "+result_rpt)

        # get the cost in the report

        report_file = open(result_rpt, "r")
        report_content = []

        for line in report_file.readlines():
            report_content.append(line)
        
        report_file.close()

        # resource

        for line in report_content:
            if (line.find("Operation")>=0 and line.find("Functional Unit")>=0):
                list_obj = line.split("|")

        start_check = 0
        DSP48E_N = 0
        FF_N = 0
        LUT_N = 0

        # delay

        # delay
        flag = 0
        for line in report_content:
            if (line.find("    | min | max | min | max")>=0):
                flag = 1
                continue
            if (flag):
                flag = flag + 1
                if (flag!=3):
                    continue
                split_tmp = line.split("|")
                lat_tmp = int(split_tmp[1])
                delay_tmp = float(0)
                II_tmp = int(split_tmp[3])
                Core_tmp = str("---")
                delay_dict[str(oprandA)+" "+str(oprandB)+" "+str(clock_rate)] = [lat_tmp, delay_tmp, II_tmp, Core_tmp]                
                break

        flag = 0
  
        if (1):
            for line in report_content:
                if (line.find(" |  Clock | Target| Estimated| Uncertainty|")>=0):
                    flag = 1
                    continue
                if (flag):
                    flag = flag + 1
                    if (flag!=3):
                        continue
                    split_tmp = line.split("|")
                    delay_tmp = float(split_tmp[3])
                    delay_dict[str(oprandA)+" "+str(oprandB)+" "+str(clock_rate)] = [lat_tmp, delay_tmp, II_tmp, Core_tmp]                
                    break

        check = str(oprandA)+" "+str(oprandB)+" "+str(oprandC)+" "+str(clock_rate)+" "+str(DSP48E_N)+" "+str(FF_N)+" "+str(LUT_N)+" "+str(lat_tmp)+" "+str(delay_tmp)+" "+str(II_tmp)+" "+str(Core_tmp)
        check5 = str(oprandA)+" "+str(oprandB)+" "+str(oprandC)+" "+str(DSP48E_N)+" "+str(FF_N)+" "+str(LUT_N)+" "+str(lat_tmp)+" "+str(delay_tmp)+" "+str(II_tmp)+" "+str(Core_tmp)
        
        overview_file.write(str(oprandB)+" "+str(oprandA)+" "+str(oprandC)+" "+str(clock_rate)+" "+str(DSP48E_N)+" "+str(FF_N)+" "+str(LUT_N)+" "+str(lat_tmp)+" "+str(delay_tmp)+" "+str(II_tmp)+" "+str(Core_tmp)+"\n")
        overview_file.flush()
        print("===================== "+ check)
        
        end = time.time()
        print("time:"+str((end - start)))

json.dump(resource_dict,dump_resource_file,ensure_ascii=False)
dump_resource_file.write('\n')
dump_resource_file.close()

json.dump(delay_dict,dump_timing_file,ensure_ascii=False)
dump_timing_file.write('\n')
dump_timing_file.close()

overview_file.close()
            

