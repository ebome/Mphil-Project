# ref:
# https://blog.csdn.net/u012111465/article/details/82017402


import numpy as np
from statsmodels.tsa.stattools import adfuller as ADF

def trend_desc(inputdata):
    # compute the rank sum of time series
    inputdata = np.array(inputdata)
    n = inputdata.shape[0]
    sum_sgn = 0
    for i in np.arange(n):
        if i <= (n - 1):
            for j in np.arange(i+1,n):
                if inputdata[j] > inputdata[i]:
                    sum_sgn = sum_sgn+1
                elif inputdata[j] < inputdata[i]:
                    sum_sgn = sum_sgn-1
                else:
                    sum_sgn = sum_sgn
    # compute Z value
    if n <= 10:
        Z_value = sum_sgn/(n*(n-1)/2)
    else:
        if sum_sgn > 0:
            Z_value = (sum_sgn-1)/np.sqrt(n*(n-1)*(2*n+5)/18)
        elif sum_sgn == 0:
            Z_value = 0
        else:
            Z_value = (sum_sgn+1)/np.sqrt(n*(n-1)*(2*n+5)/18)
    # stationarity of time series: ADF test
    ADF_result = ADF(inputdata,0)
    # describe trends
    # 99% ——> ±2.576
    # 95% ——> ±1.96
    # 90% ——> ±1.645
    if ADF_result[1]<0.05: # p value of ADF < 0.05:  time series is stationary
        result_desc = 'steady'
    else:
        if np.abs(Z_value) > 1.96 and np.abs(Z_value) <= 2.576:
            if Z_value > 0:
                result_desc = 'increasing'
        else:
                result_desc = 'decresing'
        if np.abs(Z_value) > 2.576:
            if Z_value > 0:
                result_desc = 'sig increasing'
            else:
                result_desc = 'sig decreasing' # significantly decreased
        else:
            result_desc     = 'unobvious trend'
    return result_desc
