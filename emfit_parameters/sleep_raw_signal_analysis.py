import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

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
low_sampling_rate = 50
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
plt.plot(frequency[0:25000], power_spectrum[0:25000])
plt.legend()
plt.title('Low Band Power Spectrum (FFT) at 50Hz' )
plt.xlabel('frquency (Hz)')
plt.ylabel('power/freqeucny (PSD)')
