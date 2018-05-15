###############################在python下获取数据################################################

import pandas as pd
import numpy as np
import math
import time 
import matplotlib.pylab as plt
from matplotlib.pylab import rcParams

#读取txt文件
total=pd.DataFrame(pd.read_csv('D:/wosai/auto_analyze_rollup.txt',names=["level1_mapping_name", "level1_name","level2_name","level3_name","level4_name","level5_name","payway","subpayway","terminal_name","amount","cnt","active_store","day"]))

#按照条件筛选、聚合
#定义传入的参数
start_day='20180405'
end_day = time.strftime('%Y%m%d',time.localtime(time.time()))
day_axis=pd.date_range('2018-4-23','2018-5-14')

level1_mapping_name =total['level1_mapping_name'].unique()
level3_name = total['level3_name'].unique()
payway=total['payway'].unique()
subpayway=total['subpayway'].unique()
t_name = total['terminal_name'].unique()
t_name[t_name==('智能POS|A920')]='智能POSA920'

dim = [start_day,end_day,level1_mapping_name,level3_name,payway,subpayway,t_name]

#范围控制
var_name = "df_sh_"
start_str="total[(total['day']>=int(start_day))&(total['level3_name']=='上海')&(total['level1_mapping_name']=='直营')"
#start_str="total[(total['day']>=int(start_day))"
end_str = "].groupby(['day']).sum()"

#payway
payway_list=[]
for i in payway:
    payway_list.append(var_name+"pw"+"_"+i)
    exec (var_name+"pw"+"_"+i+"=" +start_str+"&(total['payway']=="+"'"+i+"'"+")"+end_str)


#subpayway
subpayway_list=[]
for i in subpayway:
    subpayway_list.append(var_name+"subpw"+"_"+i)
    exec (var_name+"subpw"+"_"+i+"=" +start_str+"&(total['subpayway']=="+"'"+i+"'"+")"+end_str)
    

#terminal_name
terminal_list=[]
for i in t_name:
    terminal_list.append(var_name+"t"+"_"+i)
    exec (var_name+"t"+"_"+i+"=" +start_str+"&(total['terminal_name']=="+"'"+i.replace('智能POSA920','智能POS|A920')+"'"+")"+end_str)
    
    import rpy2.robjects as robjects
from rpy2.robjects import pandas2ri
pandas2ri.activate()
#py_decompose=pandas2ri.ri2py(decompose)

#引入R的函数
stl=robjects.r['stl']
ts=robjects.r['ts']
c=robjects.r['c']
plot =robjects.r['plot']

#数据分解函数

def decompose_signal(observed,start_day,end_day,day_axis,dim_name):
    
    if(len(observed)==len(day_axis)):
        #根据R中stl函数的要求，把金额数据做成周期性的。利用ts函数把金额序列做成周期数据，方便tsl函数调用
        observed_periodic=ts(observed,frequency=7,start=c(1,1))
        decompose=stl(observed_periodic,"per")
        #分解出decompose结果中，seasonal, trend,residual。 
        lenth = len(decompose[0])
        seasonal=decompose[0][0:int(lenth/3)]
        trend=decompose[0][int(lenth/3):int(2*lenth/3)]
        residual = decompose[0][int(2*lenth/3):]
        
        #计算residual的均值和标准差，为异常检测part做准备
        mean=np.mean(residual)
        std=np.std(residual)
        
        #observed
        #amount_observed = pd.DataFrame(result.observed).fillna(method='ffill').fillna(method='bfill')

        #以1.5倍的标准差作为置信区间来判断异常值
        abnormal=[]
        for i in range(len(residual)):
            #轮询，如果residual的值在mean±1.5std之外，则在abnormal中插入一条数据，并赋residual的值；如果不是则插入一条，赋零
            if residual[i] >(mean+1.5*std) or residual[i] <(mean-1.5*std):
                abnormal.append(residual[i])       
            else:
                abnormal.append(0)
        abnormal_df=pd.DataFrame(abnormal)
        
        plt.rcParams['font.sans-serif']=['SimHei'] #用来正常显示中文标签  
        rcParams['figure.figsize'] = 10, 3
        fig = plt.figure()
        fig.suptitle(dim_name, fontsize=12)
        """
        ax = plt.subplot(511)
        #ax.set_title("Title for first plot")
        plt.plot(day_axis,observed, label='Observed')
        plt.legend(loc='best')

        ax = plt.subplot("512")
        #ax.set_title("Title for second plot")
        ax.plot(day_axis,trend, label='trend')
        plt.legend(loc='best')
        
        ax = plt.subplot("513")
        #ax.set_title("Title for second plot")
        ax.plot(day_axis,seasonal, label='seasonal')
        plt.legend(loc='best')
        
        ax = plt.subplot("514")
        #ax.set_title("Title for second plot")
        ax.plot(day_axis,residual, label='residual')
        plt.legend(loc='best')
        """
        #ax = plt.subplot("111")
        #ax.set_title("Title for second plot")
        #ax.plot(day_axis,observed)
        #plt.legend(loc='best')
        plt.plot(day_axis,observed)
        plt.scatter(day_axis[abnormal_df[abnormal_df[0]!=0].index],observed.iloc[abnormal_df[abnormal_df[0]!=0].index],color='red')
       

        """
        #绘制observed 数据
        plt.subplot(515)
        plt.plot(day_axis,observed)
        plt.scatter(day_axis[abnormal_df[abnormal_df[0]!=0].index],observed.iloc[abnormal_df[abnormal_df[0]!=0].index],color='red')
        """
        #增加注释
        num =0
        for i in (abnormal_df[abnormal_df[0]!=0].index):
            plt.annotate(observed.index[i], xy = (day_axis[abnormal_df[abnormal_df[0]!=0].index[num]],observed.iloc[abnormal_df[abnormal_df[0]!=0].index[num]]), xytext = (0,10),textcoords='offset points',arrowprops=dict(arrowstyle='-|>'))  
            #print (df['amount'].index[i])
            num=num+1
        
        plt.show()

analyze_as=["terminal_list","payway_list","subpayway_list"]
analyze_index=["amount","cnt","active_store"]
df=pd.DataFrame()
for i in terminal_list:
    exec("df="+i)
    observed=df['amount']
    decompose_signal(observed,start_day,end_day,day_axis,i.split('_')[3])
   
for i in payway_list:
    exec("df="+i)
    observed=df['amount']
    decompose_signal(observed,start_day,end_day,day_axis,i.split('_')[3])
    
for i in subpayway_list:
    exec("df="+i)
    observed=df['amount']
    decompose_signal(observed,start_day,end_day,day_axis,i.split('_')[3])
