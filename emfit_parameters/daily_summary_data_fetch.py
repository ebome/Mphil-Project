import numpy as np
from scipy import stats
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime as dt
import mysql.connector


dacs_all_sleep = pd.read_csv(r"D:\Sensor_Data_Processing\dacs_91_sleep_data.csv")

dacs_all_sleep['start_date']=pd.to_datetime(dacs_all_sleep['start_date'])
dacs_all_sleep['end_date']=pd.to_datetime(dacs_all_sleep['end_date'])
# add 'sleep efficiency' column
dacs_all_sleep['sleep_efficiency']=dacs_all_sleep['sleep_duration']/dacs_all_sleep['bed_duration']
# clean some useless columns
dacs_all_sleep = dacs_all_sleep.drop(['sleep_data_id','end_time'], axis=1)

# count the number of PID and see how many days of data each PID has
output = dacs_all_sleep.groupby('PID').size()
# Remove the PID with output days less than 40 days from dacs_all_sleep
for PID, days in output.items():
    if days < 40:
        dacs_all_sleep = dacs_all_sleep[(dacs_all_sleep.PID !=PID)]
output = dacs_all_sleep.groupby('PID').size()


###################################################
# Motion sensor to transition: Fetch from local database
###################################################
mydb = mysql.connector.connect(user ='root', password ='123456')
mycursor = mydb.cursor()
# approximately 3 min to finish loading 5 million lines
data = pd.read_sql("select * from dacs_db_up_to_may.all_dacs_paticipants_motion", con=mydb)
mycursor.close()
mydb.close()

#------------------------------------------------
# remove the features that are not needed
motion_data = data.drop(columns=['sensor_type', 'sensor_udn'])
# remove "chair" since this is for tranfer in ADL




###################################################
# Keep the "solitary residents", Regardless withdraw or not
###################################################
solitary_list_intervention_group = pd.read_excel(r'D:\Sensor_Data_Processing\DACS_users_live_alone.xlsx')
# make sure they live alone
solitary_list_intervention_group = solitary_list_intervention_group[solitary_list_intervention_group['living_arrangments']==1]
# make sure they have sensor installed in home
solitary_list_intervention_group =  solitary_list_intervention_group[solitary_list_intervention_group['randomised_group']==1]
solitary_users = solitary_list_intervention_group['record_id'].tolist()

#------------------------------------------------
# Check if PID in sleep is same as motion
sleep_pid = output.index.tolist()



#------------------------------------------------
# If one room for this user is missing, then this user should be removed

sleep_raw = pd.read_csv(r'D:\emfit_raw_data\001F4C_1592828611_5ef110f8b34caf140c5e7956.csv')
low = sleep_raw['data_lo_band'].tolist()
high = sleep_raw['data_hi_band'].tolist()

# form of low: ['[]'],change the str to list
def split_data_str(low_list):
    newList=[]
    for element in low_list:
        newList.extend(element.split(','))
        # remove "["
    newList[0] = newList[0][1:-1]
    newList[-1] = newList[-1][0:-2]
    newList = [float(x) for x in newList]
    return newList

low = split_data_str(low)
high = split_data_str(high)
low = np.asarray(low)
high = np.asarray(high)

# see how many zeros inside (+0.0, -0.0)
zeros_in_low = np.count_nonzero(low)
zeros_in_high = np.count_nonzero(high)
# see means of high and low band
mean_of_low = np.mean(low)
mean_of_high = np.mean(high)
# see sampling time of high and low band
high_sampling_rate = 100
total_sampling_time_for_high_band = (len(high[0:2000])/high_sampling_rate)
low_sampling_rate = 100
total_sampling_time_for_low_band = (len(low[0:1000])/low_sampling_rate)

# look at shape

t_high = np.linspace(-0.00, total_sampling_time_for_high_band, len(high[0:2000]))
t_low = np.linspace(-0.00, total_sampling_time_for_low_band, len(low[0:1000]))

plt.figure(figsize=(20,5))
plt.plot(t_low,low[0:1000],label='low')
plt.plot(t_high,high[0:2000],label='high')
plt.legend()
plt.xlabel('time (seconds)')
plt.ylabel('no idea for amplitude unit')

# ----------------
# Power spectrum: high band
time = np.linspace(-0.00, len(high)/high_sampling_rate, len(high))
data = high
fourier_transform = np.fft.rfft(data)
abs_fourier_transform = np.abs(fourier_transform)
power_spectrum = np.square(abs_fourier_transform)
frequency = np.linspace(0, high_sampling_rate/2, len(power_spectrum))

plt.figure(figsize=(15,5))
plt.plot(frequency, power_spectrum)
plt.legend()
plt.title('High Band Power Spectrum (FFT)')
plt.xlabel('frquency (Hz)')
plt.ylabel('power/freqeucny (PSD)')

# ----------------
# Power spectrum: low band
time = np.linspace(-0.00, len(low)/low_sampling_rate, len(low))
data = low
fourier_transform = np.fft.rfft(data)
abs_fourier_transform = np.abs(fourier_transform)
power_spectrum = np.square(abs_fourier_transform)
frequency = np.linspace(0, low_sampling_rate/2, len(power_spectrum))

plt.figure(figsize=(15,5))
plt.plot(frequency, power_spectrum)
plt.legend()
plt.title('Low Band Power Spectrum (FFT)')
plt.xlabel('frquency (Hz)')
plt.ylabel('power/freqeucny (PSD)')

