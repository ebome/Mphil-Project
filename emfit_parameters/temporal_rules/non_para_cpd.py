
# Code referece: https://www.twblogs.net/a/5b8e32402b717718834372c0
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd


def Kendall_change_point_detection(inputdata):
    inputdata = np.array(inputdata)
    n=inputdata.shape[0]
    # 正序列計算---------------------------------
    # 定義累計量序列Sk，初始值=0
    Sk             = [0]
    # 定義統計量UFk，初始值 =0
    UFk            = [0]
    # 定義Sk序列元素s，初始值 =0
    s              =  0
    Exp_value      = [0]
    Var_value      = [0]
    # i從1開始，因爲根據統計量UFk公式，i=0時，Sk(0)、E(0)、Var(0)均爲0
    # 此時UFk無意義，因此公式中，令UFk(0)=0
    for i in range(1,n):
        for j in range(i):
            if inputdata[i] > inputdata[j]:
                s = s+1
            else:
                s = s+0
        Sk.append(s)
        Exp_value.append((i+1)*(i+2)/4 )                     # Sk[i]的均值
        Var_value.append((i+1)*i*(2*(i+1)+5)/72 )            # Sk[i]的方差
        UFk.append((Sk[i]-Exp_value[i])/np.sqrt(Var_value[i]))
    # ------------------------------正序列計算
    # 逆序列計算---------------------------------
    # 定義逆序累計量序列Sk2，長度與inputdata一致，初始值=0
    Sk2             = [0]
    # 定義逆序統計量UBk，長度與inputdata一致，初始值=0
    UBk             = [0]
    UBk2            = [0]
    # s歸0
    s2              =  0
    Exp_value2      = [0]
    Var_value2      = [0]
    # 按時間序列逆轉樣本y
    inputdataT = list(reversed(inputdata))
    # i從2開始，因爲根據統計量UBk公式，i=1時，Sk2(1)、E(1)、Var(1)均爲0
    # 此時UBk無意義，因此公式中，令UBk(1)=0
    for i in range(1,n):
        for j in range(i):
            if inputdataT[i] > inputdataT[j]:
                s2 = s2+1
            else:
                s2 = s2+0
        Sk2.append(s2)
        Exp_value2.append((i+1)*(i+2)/4 )                     # Sk[i]的均值
        Var_value2.append((i+1)*i*(2*(i+1)+5)/72 )            # Sk[i]的方差
        UBk.append((Sk2[i]-Exp_value2[i])/np.sqrt(Var_value2[i]))
        UBk2.append(-UBk[i])
    # 由於對逆序序列的累計量Sk2的構建中，依然用的是累加法，即後者大於前者時s加1，
    # 則s的大小表徵了一種上升的趨勢的大小，而序列逆序以後，應當表現出與原序列相反
    # 的趨勢表現，因此，用累加法統計Sk2序列，統計量公式(S(i)-E(i))/sqrt(Var(i))
    #也不應改變，但統計量UBk應取相反數以表徵正確的逆序序列的趨勢
    #  UBk(i)=0-(Sk2(i)-E)/sqrt(Var)
    # ------------------------------逆序列計算
    # 此時上一步的到UBk表現的是逆序列在逆序時間上的趨勢統計量
    # 與UFk做圖尋找突變點時，2條曲線應具有同樣的時間軸，因此
    # 再按時間序列逆轉結果統計量UBk，得到時間正序的UBkT，
    UBkT = list(reversed(UBk2))
    diff = np.array(UFk) - np.array(UBkT)
    K    = list()
    # 找出交叉點
    for k in range(1,n):
        if diff[k-1]*diff[k]<0:
            K.append(k)
    # 做突變檢測圖時，使用UFk和UBkT
#    plt.figure(figsize=(10,5))
#    plt.plot(range(1,n+1) ,UFk  ,label='UFk') # UFk
#    plt.plot(range(1,n+1) ,UBkT ,label='UBk') # UBk
#    plt.ylabel('UFk-UBk')
#    x_lim = plt.xlim()
#    plt.plot(x_lim,[-1.96,-1.96],'m--',color='r')
#    plt.plot(x_lim,[  0  ,  0  ],'m--')
#    plt.plot(x_lim,[+1.96,+1.96],'m--',color='r')
#    plt.legend(loc=2) # 圖例
#    plt.show()
    return K

def Buishand_U_change_point_detection(inputdata):
    inputdata = np.array(inputdata)
    inputdata_mean = np.mean(inputdata)
    n  = inputdata.shape[0]
    k = range(n)
    Sk = [np.sum(inputdata[0:x+1] - inputdata_mean) for x in k]
    sigma = np.sqrt(np.sum((inputdata-np.mean(inputdata))**2)/(n-1))
    U = np.sum((Sk[0:(n - 2)]/sigma)**2)/(n * (n + 1))
    Ska = np.abs(Sk)
    S = np.max(Ska)
    K = list(Ska).index(S) + 1
    Skk = (Sk/sigma)
    return K

def Pettitt_change_point_detection(inputdata):
    inputdata = np.array(inputdata)
    n         = inputdata.shape[0]
    k = range(n)
    inputdataT = pd.Series(inputdata)
    r = inputdataT.rank()
    Uk = [2*np.sum(r[0:x])-x*(n + 1) for x in k]
    Uka = list(np.abs(Uk))
    U = np.max(Uka)
    K = Uka.index(U)
    pvalue         = 2 * np.exp((-6 * (U**2))/(n**3 + n**2))
    if pvalue <= 0.5:
        change_point_desc = 'significant'
    else:
        change_point_desc = 'non-significant'
    #Pettitt_result = {'index of change point':K,'description of change point':change_point_desc}
    return K,change_point_desc


def SNHT_change_point_detection(inputdata):
    inputdata = np.array(inputdata)
    inputdata_mean = np.mean(inputdata)
    n  = inputdata.shape[0]
    k = range(1,n)
    sigma = np.sqrt(np.sum((inputdata-np.mean(inputdata))**2)/(n-1))
    Tk = [x*(np.sum((inputdata[0:x]-inputdata_mean)/sigma)/x)**2 + (n-x)*(np.sum((inputdata[x:n]-inputdata_mean)/sigma)/(n-x))**2 for x in k]
    T = np.max(Tk)
    K = list(Tk).index(T) + 1
    return K








