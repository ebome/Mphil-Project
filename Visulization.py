import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime as dt

dacs_3_21=pd.read_csv(r"D:\MentalHealth\3-21 sleep data.csv")
dacs_3_37=pd.read_csv(r"D:\MentalHealth\3-37 sleep data.csv")


dacs_3_21["start_date"]=dacs_3_21["start_time"].apply(lambda x: dt.utcfromtimestamp(x).strftime("%Y-%m-%d %H:%M:%S"))
dacs_3_21["end_date"]=dacs_3_21["end_time"].apply(lambda x: dt.utcfromtimestamp(x).strftime("%Y-%m-%d %H:%M:%S"))
dacs_3_21['sleep_efficiency']=dacs_3_21['sleep_duration']/dacs_3_21['bed_duration']

dacs_3_37["start_date"]=dacs_3_37["start_time"].apply(lambda x: dt.utcfromtimestamp(x).strftime("%Y-%m-%d %H:%M:%S"))
dacs_3_37["end_date"]=dacs_3_37["end_time"].apply(lambda x: dt.utcfromtimestamp(x).strftime("%Y-%m-%d %H:%M:%S"))
dacs_3_37['sleep_efficiency']=dacs_3_37['sleep_duration']/dacs_3_37['bed_duration']


dacs_3_21['start_datetime']=pd.to_datetime(dacs_3_21['start_date'])
dacs_3_21 = dacs_3_21.set_index('start_datetime')
new_3_21 = dacs_3_21.drop(columns = ['sleep_data_id','device_id','start_time','end_time','fm_count'])
dacs_3_37['start_datetime']=pd.to_datetime(dacs_3_37['start_date'])
dacs_3_37 = dacs_3_37.set_index('start_datetime')
new_3_37 = dacs_3_37.drop(columns = ['sleep_data_id','device_id','start_time','end_time','fm_count'])

#----------------------------------
new_3_21.plot(x='start_date',y=['bed_duration','sleep_duration'],kind="bar",figsize=(80,10))

new_3_21.plot(x='start_date',y=['sleep_efficiency'],kind="bar",figsize=(80,10))


new_3_21.plot(x='start_date',y=['sleep_score'],kind="bar",figsize=(80,10))

new_3_21.plot(x='start_date',y=['rem_sleep_duration',
                                'light_sleep_duration','deep_sleep_duration'],kind="bar",figsize=(80,10))

new_3_21.plot(x='start_date',y=['awake_duration'],kind="bar",figsize=(80,10))
new_3_21.plot(x='start_date',y=['sleep_onset_duration'],kind="bar",figsize=(80,10))

new_3_21.plot(x='start_date',y=['bed_exit_count'],kind="bar",figsize=(80,10))
new_3_21.plot(x='start_date',y=['bed_exit_duration'],kind="bar",figsize=(80,10))
new_3_21.plot(x='start_date',y=['toss_turn_count'],kind="bar",figsize=(80,10))

new_3_21.plot(x='start_date',y=['average_heart_rate',"min_heart_rate",'max_heart_rate'],kind="bar",figsize=(80,10))
new_3_21.plot(x='start_date',y=['average_respiration_rate',"min_respiration_rate",'max_respiration_rate'],kind="bar",figsize=(80,10))
new_3_21.plot(x='start_date',y=['awakenings'],kind="bar",figsize=(80,10))
new_3_21.plot(x='start_date',y=['average_physical_activity'],kind="bar",figsize=(80,10))


new_3_21.plot(x='start_date',y=['hrv_score','hrv_lf','hrv_hf','hrv_rmssd_evening',
                                'hrv_rmssd_morning'],kind="bar",figsize=(80,10))


#----------------------------------
new_3_37.plot(x='start_date',y=['bed_duration','sleep_duration'],kind="bar",figsize=(80,10))
new_3_37.plot(x='start_date',y=['sleep_efficiency'],kind="bar",figsize=(80,10))


new_3_37.plot(x='start_date',y=['sleep_score'],kind="bar",figsize=(80,10))

new_3_37.plot(x='start_date',y=['rem_sleep_duration',
                                'light_sleep_duration','deep_sleep_duration'],kind="bar",figsize=(80,10))

new_3_37.plot(x='start_date',y=['awake_duration'],kind="bar",figsize=(80,10))
new_3_37.plot(x='start_date',y=['sleep_onset_duration'],kind="bar",figsize=(80,10))

new_3_37.plot(x='start_date',y=['bed_exit_count'],kind="bar",figsize=(80,10))
new_3_37.plot(x='start_date',y=['bed_exit_duration'],kind="bar",figsize=(80,10))
new_3_37.plot(x='start_date',y=['toss_turn_count'],kind="bar",figsize=(80,10))

new_3_37.plot(x='start_date',y=['average_heart_rate',"min_heart_rate",'max_heart_rate'],kind="bar",figsize=(80,10))
new_3_37.plot(x='start_date',y=['average_respiration_rate',"min_respiration_rate",'max_respiration_rate'],kind="bar",figsize=(80,10))
new_3_37.plot(x='start_date',y=['awakenings'],kind="bar",figsize=(80,10))
new_3_37.plot(x='start_date',y=['average_physical_activity'],kind="bar",figsize=(80,10))


new_3_37.plot(x='start_date',y=['hrv_score','hrv_lf','hrv_hf','hrv_rmssd_evening',
                                'hrv_rmssd_morning'],kind="bar",figsize=(80,10))

