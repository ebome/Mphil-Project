# ref:
# https://blog.csdn.net/u012111465/article/details/82017402
# https://blog.csdn.net/u012111465/article/details/82627185


import numpy as np
from statsmodels.tsa.stattools import adfuller as ADF
from scipy import stats

def trend_desc(inputdata):
    n = inputdata.shape[0]
    if n<5: # one point cannot make sense
        return 'S'  
    
    # stationarity of time series: ADF test
    ADF_result = ADF(inputdata,0)       
    if ADF_result[1]<0.05: # p value of ADF < 0.05:  time series is stationary
        return 'S' # steady
       
        
    # simple linear trend degree (0-1 standardized rawdata)
    inputdataT = (np.array(inputdata)-np.min(inputdata))/(np.max(inputdata)-np.min(inputdata))
    x = list(range(1,len(inputdata)+1))
    xT = 1.0*(np.array(x)-np.min(x))/(np.max(x)-np.min(x))
    clf_result = stats.linregress(xT,inputdataT)
    linearTrendDegree = clf_result[0]
    if linearTrendDegree > 0:
        return 'R' # increasing
    else:
        return 'F' # decresing

    
