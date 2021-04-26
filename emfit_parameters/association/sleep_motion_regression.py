import numpy as np
from scipy import stats
import pandas as pd
import matplotlib.pyplot as plt
import datetime as dt
#import mysql.connector
from datetime import timedelta
import math
from scikit_posthocs import posthoc_dunn
import seaborn as sns
from datetime import datetime
import statsmodels.api as sm
import merge_sensors as ms # make sure they are in same dir, run ms first

import seaborn as sns

from sklearn import linear_model
from sklearn.model_selection import cross_val_score, cross_val_predict
from sklearn import metrics

#############################################################################
# Topological floor plan
#############################################################################
from collections import ChainMap

all_dacs_room_matrix = pd.read_csv(r'F:\Sensor_Data_Processing\floor_plan\DACS_Room_Distances.csv')
room_matrix_grouped_list = list(all_dacs_room_matrix.groupby(['PID']))

def getUniqueItems(d):
    result = {}
    for key,value in d.items():
        if value not in result.values():
            result[key] = value
    return result   

def remove_duplicate_rooms(unit_matrix):
    room1_list = unit_matrix['room1_id'].tolist()
    room2_list = unit_matrix['room2_id'].tolist()
    room_to_room_list =list(map(list, zip(room1_list,room2_list)))
    room_to_room_list = [str(sorted(each)) for each in room_to_room_list]
    indexes = unit_matrix.index.tolist()
    room_to_room_dict_list = [{k: v} for k, v in zip(indexes, room_to_room_list)]
    room_to_room_dict =  dict(ChainMap(*room_to_room_dict_list))
    # remove duplicate values from dictionary
    result = getUniqueItems(room_to_room_dict)
    # from result get indexes and keep indexes in dataframe
    aab = unit_matrix.loc[list(result.keys())]
    return aab 

reformed_room_matrix_list_temp=[];room_matrix_users=[]    
for each_unit in room_matrix_grouped_list:
    unit_matrix = each_unit[1]
    unit_matrix_cleaned = remove_duplicate_rooms(unit_matrix)    
    reformed_room_matrix_list_temp.append(unit_matrix_cleaned)
    room_matrix_users.append(unit_matrix_cleaned['PID'].tolist()[0])

reformed_room_matrix_df = pd.DataFrame({})
for each in reformed_room_matrix_list_temp:
    reformed_room_matrix_df = reformed_room_matrix_df.append(each)

# group all users' floor plan
output = [item[1] for item in list(reformed_room_matrix_df.groupby('PID'))]
  
 



user_gender_users = user_gender['record_id'].tolist()
# remove some users by find their index
missing_users_in_sensor = list(set(room_matrix_users) - set(user_gender_users))
reformed_room_matrix_df = reformed_room_matrix_df[~reformed_room_matrix_df['PID'].isin(missing_users_in_sensor)]



###################################################
# Sleep summary data: just use csv file
###################################################
dacs_all_sleep = pd.read_csv(r'F:\data\sleep_data_up_to_Nov.csv')

dacs_all_sleep['start_date'] = [datetime.fromtimestamp(x) for x in dacs_all_sleep['start_time']]
dacs_all_sleep['end_date'] = [datetime.fromtimestamp(x) for x in dacs_all_sleep['end_time']]
# clean some useless columns
dacs_all_sleep = dacs_all_sleep.drop(['sleep_data_id','room_id','sensor_type','sensor_udn',
                                      'sensor_name','sensor_id','device_id','session_id'], axis=1)
# change 'rebaseline' in PID for 3-175, 3-183
dacs_all_sleep['PID'] = [x.replace(' Rebaseline','') for x in dacs_all_sleep['PID']]


# count the number of PID and see how many days of data each PID has
output = dacs_all_sleep.groupby('PID').size()
# Remove the PID with output days less than 40 days from dacs_all_sleep
for PID, days in output.items():
    if days < 15:
        dacs_all_sleep = dacs_all_sleep[(dacs_all_sleep.PID !=PID)]
each_user_sleep_days = dacs_all_sleep.groupby('PID').size()


###################################################
# Motion sensor: steps each day
###################################################
all_dacs_mobility = pd.read_csv(r'F:\Sensor_Data_Processing\all_user_mobility_up_to_Aug.csv')
all_dacs_mobility = all_dacs_mobility[['PID','localTimeMeasured','value']]
# mobility has time format YY-MM-DD but sensor also has hours
all_dacs_mobility['local_timestamp'] = [dt.datetime.strptime(date[0:-9], '%d/%m/%Y').date() for date in all_dacs_mobility['localTimeMeasured']] 

###################################################
# Keep the "solitary residents", Regardless withdraw or not
###################################################
solitary_list_intervention_group = pd.read_excel(r'F:\Sensor_Data_Processing\DACS_users_live_alone.xlsx')
# make sure they live alone
solitary_list_intervention_group = solitary_list_intervention_group[solitary_list_intervention_group['living_arrangments']==1]
# make sure they have sensor installed in home
solitary_list_intervention_group =  solitary_list_intervention_group[solitary_list_intervention_group['randomised_group']==1]
solitary_users = solitary_list_intervention_group['record_id'].tolist()

#------------------------------------------------
# Remove non-solitary users from sensor and mobility data 
solitary_dacs_sleep = dacs_all_sleep[dacs_all_sleep['PID'].isin(solitary_users)]
solitary_dacs_mobility = all_dacs_mobility[all_dacs_mobility['PID'].isin(solitary_users)]

# Check if PID in sleep is same as motion
sleep_pid = solitary_dacs_sleep['PID'].unique().tolist()
motion_pid = solitary_dacs_mobility['PID'].unique().tolist()

# for users not in motion_pid, we have to find them
user_not_in_motion_pid = [elem for elem in motion_pid if elem not in sleep_pid]
# remove these users from motion data
solitary_dacs_mobility = solitary_dacs_mobility[~solitary_dacs_mobility['PID'].isin(user_not_in_motion_pid)]

###################################################
# Group sleep and motion sensor
###################################################
# get mobility
mobility_grouped_list = list(solitary_dacs_mobility.groupby(['PID']))
reformed_mobility_list_temp = []
for each_unit in mobility_grouped_list:
    unit_motiondata = each_unit[1]
    # remove all zeros in mobility
    unit_motiondata = unit_motiondata[unit_motiondata['value']!= 0]
    reformed_mobility_list_temp.append(unit_motiondata)

#-------------------------------------------------
# get users in sleep data
sleep_grouped_list = list(solitary_dacs_sleep.groupby(['PID']))
reformed_sleep_list_temp=[]
for each_PID in sleep_grouped_list:
    reformed_sleep_list_temp.append(each_PID[1])
 
#-------------------------------------------------
# add a bdebugging function to compare whether PID in mobility and
# sleep are the same   
user_list_sleep=[];user_list_sensor=[]
for i in range(len(reformed_mobility_list_temp)):
    user_list_sleep.append(reformed_sleep_list_temp[i]['PID'].tolist()[0])
    user_list_sensor.append(reformed_mobility_list_temp[i]['PID'].tolist()[0])
    
def debugging_two_temp_list_value(a1,a2):
    '''
    a1 and a2 must have same length
    '''
    bool_list=[]
    for i in range(len(a1)):
        if a1[i]==a2[i]:
            bool_list.append(True)
        else:
            bool_list.append(False)
    return bool_list

are_user_same = debugging_two_temp_list_value(user_list_sleep,user_list_sensor)

#############################################################################
# Remove repetitive dates of sleep recording 
#############################################################################
# follow Mahnoosh's suggestion in one user
# split day-by-day, but not from 0am. Instead, split each day from 7pm 
base = dt.datetime.strptime('2019-05-02 19:00:00', '%Y-%m-%d %H:%M:%S')
datelist = pd.date_range(base, periods=580).tolist()
choppedTime=[]
for elt in datelist:
    strg = f'{elt:%Y-%m-%d %H:%M:%S}'
    choppedTime.append(strg)
    
#-----------------------------------------------------
# split the sleep data day-by-day

def keep_record_in_interval(one_day_sleep, start_time):
    # sort the dataframe based on start_date
    one_day_sleep = one_day_sleep.sort_values(by='start_date')
    # the start_time is sure to started at 7pm, but the start_time can also up to 6am
    # i.e. 11 hours from 7pm-6am
    last_of_start_time = start_time + dt.timedelta(hours=11)
    last_of_start_time = last_of_start_time.strftime('%Y-%m-%d %H:%M:%S')
    one_day_sleep = one_day_sleep[one_day_sleep['start_date'] < last_of_start_time]
    return one_day_sleep

def keep_longest_tst_in_episode(one_day_sleep):
    # group the start_date with same values, and keep the longest sleep_duration
    sleep_episodes_list = []
    sleep_episode_grouped_list = list(one_day_sleep.groupby(['start_date']))
    for each_sleep in sleep_episode_grouped_list:
        each_same_start_episode = each_sleep[1]
        one_episode = each_same_start_episode.sort_values('sleep_duration').drop_duplicates(['PID'], keep='last')
        sleep_episodes_list.append(one_episode)
    return sleep_episodes_list

def obtain_summary(sleep_episodes_list):
    # flat the sleep_episodes_list into a big dataframe, and get SOL, bed_exit_duration
    final_big_df = pd.DataFrame({})    
    for each_epi in sleep_episodes_list:
        final_big_df = pd.concat([final_big_df,each_epi])
    
    final_big_df = final_big_df.sort_values('start_date')
    PID = final_big_df['PID'].tolist()[0]
    SOL = (final_big_df['sleep_onset_duration'].tolist()[0])/60
    start_sleep_time = final_big_df['start_date'].tolist()[0]
    finish_sleep_time = final_big_df['end_date'].tolist()[-1]
    TST = final_big_df['sleep_duration'].sum()
    WASO = final_big_df['awake_duration'].sum()
    duraion_in_bed = final_big_df['bed_duration'].sum()
    sleep_efficiency = TST/duraion_in_bed
    toss_turn_count = final_big_df['toss_turn_count'].sum()
    awake_count = final_big_df['awakenings'].sum()
    bed_exit_count = final_big_df['bed_exit_count'].sum()
    bed_exit_count = bed_exit_count + (len(sleep_episodes_list)-1)
    avg_hr = final_big_df['average_heart_rate'].sum()
    avg_hr = avg_hr/len(sleep_episodes_list)
    avg_rr = final_big_df['average_respiration_rate'].sum()
    avg_rr = avg_rr/len(sleep_episodes_list)
    TST = TST/3600; WASO=WASO/60; duraion_in_bed = duraion_in_bed/3600
    
    # ∑ time difference in each episodes, and add the sigma to bed_exit_duration
    inter_episode_bed_exit_duration=0
    for i in range(len(sleep_episodes_list)-1):
        e1_end = sleep_episodes_list[i]['end_time'].tolist()[0]
        e2_start = sleep_episodes_list[i+1]['start_time'].tolist()[0]
        timestamp_diff_e2_e1 = e2_start - e1_end # unit:seconds
        inter_episode_bed_exit_duration = inter_episode_bed_exit_duration + timestamp_diff_e2_e1
    bed_exit_duration = final_big_df['bed_exit_duration'].sum()
    bed_exit_duration = (bed_exit_duration+inter_episode_bed_exit_duration)/60


    return pd.DataFrame({'PID':PID,'start_sleep_time':start_sleep_time,
                         'finish_sleep_time':finish_sleep_time,
                         'TST(hour)':TST, 'WASO(min)':WASO,'SOL(min)':SOL,
                         'SE':sleep_efficiency,'duraion_in_bed':duraion_in_bed,
                         'toss_turn_count':toss_turn_count,
                         'avg_hr':avg_hr,'avg_rr':avg_rr,'awake_count':awake_count,
                         'bed_exit_count':bed_exit_count,
                         'bed_exit_duration(min)':bed_exit_duration}, index=[0])

    
# NOTE: we should use start_date ALL THE TIME, since end_date is not necessary
def get_one_user_sleep_data(test_user,choppedTime):

    first_date_in_this_user = test_user['start_date'].tolist()[0]
    last_date_in_this_user = test_user['start_date'].tolist()[-1]

    sleep_summary_one_person = pd.DataFrame({})
    for i in range(len(choppedTime)-1):
        one_day_sleep  = test_user[test_user['start_date'] > choppedTime[i]]
        one_day_sleep  = one_day_sleep[one_day_sleep['start_date'] < choppedTime[i+1]]
               
        # e.g. choppedTime start  4-26, hence the choppedila_day is length 0 before the start date
        if first_date_in_this_user > datelist[i+1] or last_date_in_this_user < datelist[i]:
            continue    
        if len(one_day_sleep)==0:
            continue

        # one_day_sleep is the records for this day, now 
        # 1. remove the start_date that not within 7pm-6am
        # 2. for the rest episodes, check if they have same start time
        start_time = dt.datetime.strptime(choppedTime[i],'%Y-%m-%d %H:%M:%S')
        one_day_sleep_with_episodes = keep_record_in_interval(one_day_sleep, start_time)
        if len(one_day_sleep_with_episodes)==0:
            continue
    
        sleep_episodes_list = keep_longest_tst_in_episode(one_day_sleep_with_episodes)

        # now for each episode in sleep_episodes_list, process each parameter
        daily_summary = obtain_summary(sleep_episodes_list)    
        sleep_summary_one_person = pd.concat([sleep_summary_one_person,daily_summary])
        abab = sleep_summary_one_person.reset_index().drop(columns=['index'])

    return abab

#test_user = reformed_sleep_list_temp[18]
#test_user = test_user.dropna(subset=['sleep_duration'])
#sleep_summary_one_person = get_one_user_sleep_data(test_user,choppedTime)

reformed_sleep_list_no_nap = []
for test_user in reformed_sleep_list_temp:
    # drop rows with nan sleep_duration
    test_user = test_user.dropna(subset=['sleep_duration'])
    # apply function to merge multi-episodic sleep records
    sleep_summary_one_person = get_one_user_sleep_data(test_user,choppedTime)
    reformed_sleep_list_no_nap.append(sleep_summary_one_person)
    
#------------------
# there are repetitive date appear in reformed_sleep_list_no_nap, so change them

reformed_sleep_list_no_repetitive=[] 
for each_user_sleep in reformed_sleep_list_no_nap:
    start_sleep_aaaa = each_user_sleep['start_sleep_time'].tolist()
    end_sleep_aaaa = each_user_sleep['finish_sleep_time'].tolist()
    # create the non-repetitive list, each date means sleep starts from that date's night
    start_sleep_dates = [] 
    for i in range(len(start_sleep_aaaa)):
        a = start_sleep_aaaa[i]
        b = end_sleep_aaaa[i]

        time_division_today = dt.datetime(a.year,a.month,a.day,23,59,59)
        time_division_tmr = dt.datetime(a.year,a.month,a.day,0,0,0)
        time_division_7pm = dt.datetime(a.year,a.month,a.day,19,0,0)
        time_division_6am = dt.datetime(a.year,a.month,a.day,6,0,0)
        
        start_sleep_only_date = dt.datetime(a.year,a.month,a.day)
        end_sleep_only_date = dt.datetime(b.year,b.month,b.day)
        
        # If start sleep time is between 7pm-11:59pm, and end sleep time is  
        # next day, count this sleep as next day
        if a <= time_division_today and a>=time_division_7pm and start_sleep_only_date!=end_sleep_only_date:
            each_sleep_date = a.date() + timedelta(days=1)
            start_sleep_dates.append(each_sleep_date)

        # If start sleep time is between 7pm-11:59pm, and end sleep time is  
        # same day, count this sleep as this day
        ##### if not adding this line, user_index= 23 line 325,line 326 would be same day
        if a <= time_division_today and a>=time_division_7pm and start_sleep_only_date==end_sleep_only_date:
            each_sleep_date = a.date()
            start_sleep_dates.append(each_sleep_date)

        # If start sleep time is between 0am-6am, and end sleep time is  
        # same day, count this sleep as this day
        if a >= time_division_tmr and a<=time_division_6am and start_sleep_only_date==end_sleep_only_date:
            each_sleep_date = a.date()
            start_sleep_dates.append(each_sleep_date)

    each_user_sleep['date_for_this_sleep'] = start_sleep_dates
    reformed_sleep_list_no_repetitive.append(each_user_sleep)   

#------------------
# In reformed_sleep_list_no_repetitive, there could be repeated days that one have short TST, one have longer TST
# Since one day may be recorded twice, once from 7pm-11:59pm, and once recorded from 7pm-6am

reformed_sleep_list_no_repetead=[] 
for each_user_sleep in reformed_sleep_list_no_repetitive:
    
    sleep_episode_grouped_list = list(each_user_sleep.groupby(['date_for_this_sleep']))
    
    # Keep the longest TST in that day
    sleep_episodes_list = pd.DataFrame({})
    for each_sleep in sleep_episode_grouped_list:
        each_same_start_episode = each_sleep[1]
        one_episode = each_same_start_episode.sort_values('TST(hour)').drop_duplicates(['PID'], keep='last')
        sleep_episodes_list = pd.concat([sleep_episodes_list,one_episode])
    
    reformed_sleep_list_no_repetead.append(sleep_episodes_list)


###################################################
# Match sleep and motion sensor on the dates
###################################################
# Same, for each unit in reformed_sleep_list_with_no_repetitive and users_transition,remove the 
# dates that in reformed_sleep_list_with_no_nap but not in users_transition
reformed_sleep_list = [];reformed_sensor_list = []
for i in range(len(reformed_mobility_list_temp)):
    each_PID_mobility = reformed_mobility_list_temp[i]
    each_PID_sleep = reformed_sleep_list_no_repetead[i]

    # match the days
    # mobility should within dates of sleep
    each_PID_mobility_reformed = each_PID_mobility[each_PID_mobility['local_timestamp'].isin(each_PID_sleep['date_for_this_sleep'].tolist())]
    # sleep should within dates of mobility
    each_PID_sleep_reformed = each_PID_sleep[each_PID_sleep['date_for_this_sleep'].isin(each_PID_mobility_reformed['local_timestamp'].tolist())]

    reformed_sensor_list.append(each_PID_mobility_reformed)
    reformed_sleep_list.append(each_PID_sleep_reformed)


'''
# debug individual PID's sleep and mobility dates
each_PID_mobility = reformed_mobility_list_temp[15]
each_PID_sleep = reformed_sleep_list_no_repetitive[15]

each_PID_mobility_reformed = each_PID_mobility[each_PID_mobility['local_timestamp'].isin(each_PID_sleep['date_for_this_sleep'].tolist())]
each_PID_sleep_reformed = each_PID_sleep[each_PID_sleep['date_for_this_sleep'].isin(each_PID_mobility_reformed['local_timestamp'].tolist())]

from collections import Counter
l1 = each_PID_sleep_reformed['date_for_this_sleep'].tolist()
l2 = each_PID_mobility_reformed['local_timestamp'].tolist()
c1 = Counter(l1)
c2 = Counter(l2)
diff = c1-c2
print(list(diff.elements()))
'''


# get list debugged
reformed_sleep_list_length = [len(x) for x in reformed_sleep_list]
reformed_sensor_list_length = [len(x) for x in reformed_sensor_list]
are_length_same = debugging_two_temp_list_value(reformed_sleep_list_length,reformed_sensor_list_length)


#############################################################################
# CODE age and gender into each user
#############################################################################
# from users get their ages
user_gender = pd.read_csv(r'F:\Sensor_Data_Processing\gender_label\survey_labels.csv')
user_list_sleep=[]
for i in range(len(reformed_sleep_list_no_nap)):
    user_list_sleep.append(reformed_sleep_list_no_nap[i]['PID'].tolist()[0])
user_gender = user_gender[user_gender['record_id'].isin(user_list_sleep)]
#--------------------
# the age should be start of trial, that's how longitudinal study does
time_list = user_gender["date_of_birth"].values.tolist()
birthday = [dt.datetime.strptime(x, '%Y-%m-%d').date() for x in time_list]
start_trail_date=user_gender["p_date_completed_b"].values.tolist()
start_dates = [dt.datetime.strptime(x, '%Y-%m-%d %H:%M:%S').date() for x in start_trail_date]
age_list =[(x1 - x2)//dt.timedelta(days=365.2425) for (x1, x2) in zip(start_dates, birthday)]
user_gender['age'] = age_list 
user_gender.to_csv(r'F:\Sensor_Data_Processing\gender_label\user_demographic.csv')


start_trail_date=[]
for each_user in reformed_sleep_list:
    start_trail_date.append(each_user['date_for_this_sleep'].tolist()[0])

age_list =[(x1 - x2)//dt.timedelta(days=365.2425) for (x1, x2) in zip(start_trail_date, birthday)]
user_gender['age'] = age_list 
#--------------------
user_gender = user_gender.sort_values(by=['record_id']).reset_index()
user_gender['home_care_package_level'].loc[(user_gender['home_care_package_level']==6)] = 1
# add mental score to user_gender
user_mental_score = pd.read_csv(r'F:\Sensor_Data_Processing\gender_label\eq5d_and_mood_and_mental_scores.csv')
user_mental_score = user_mental_score[user_mental_score['PID'].isin(user_gender['record_id'].tolist())]
user_gender = user_gender.merge(user_mental_score,left_on='record_id',right_on='PID', 
     how = 'inner')[['record_id', 'living_area', 'home_care_package_level', 'gender',
                     'age','ATSM']]
user_gender = user_gender[user_gender['home_care_package_level']<4]
user_gender['ATSM'] = [int(x) for x  in user_gender['ATSM'].tolist()]

# removed users that has mental score < 5
user_gender = user_gender[user_gender['ATSM']>=7]

#############################################################################
# Sleep parameter selection
# Ground truth mobility, ignore those who have data less than 29 days
def get_temp_sleep_parameter(reformed_sleep_list,sleep_para):
    temp_sleep_duration=[]
    for each_user_mobility in reformed_sleep_list:
        aa = each_user_mobility[sleep_para].tolist()
        temp_sleep_duration.append(aa) 
    return temp_sleep_duration

temp_sleep_duration = get_temp_sleep_parameter(reformed_sleep_list,'TST(hour)')
temp_sleep_onset_duration = get_temp_sleep_parameter(reformed_sleep_list,'SOL(min)')
temp_sleep_efficiency = get_temp_sleep_parameter(reformed_sleep_list,'SE')
temp_waso = get_temp_sleep_parameter(reformed_sleep_list,'WASO(min)')
temp_sleep_duration_in_bed = get_temp_sleep_parameter(reformed_sleep_list,'duraion_in_bed')
temp_sleep_bedexit = get_temp_sleep_parameter(reformed_sleep_list,'bed_exit_duration(min)')
temp_sleep_ttc = get_temp_sleep_parameter(reformed_sleep_list,'toss_turn_count')
temp_sleep_avg_hr = get_temp_sleep_parameter(reformed_sleep_list,'avg_hr')
temp_sleep_avg_rr = get_temp_sleep_parameter(reformed_sleep_list,'avg_rr')
temp_sleep_awakeCount = get_temp_sleep_parameter(reformed_sleep_list,'awake_count')
temp_sleep_exitCount = get_temp_sleep_parameter(reformed_sleep_list,'bed_exit_count')

   

flat_sleep_duration = [item for sublist in temp_sleep_duration for item in sublist]
print('flat_sleep_duration = ', len(flat_sleep_duration))
    
list(map(tuple, np.where( np.isnan( np.asarray(flat_sleep_duration) ) )))
  
avg_of_sleep_duration = np.mean(np.asarray(flat_sleep_duration))
print('avg_of_sleep_duration =',avg_of_sleep_duration)

#-----------------------------------------
# Visualization of motion/sleep
#def moving_average(a, n=3) :
#    ret = np.cumsum(a, dtype=float)
#    ret[n:] = ret[n:] - ret[:-n]
#    return ret[n - 1:] / n


user_index=1
dates = list(range(len(reformed_sensor_list[user_index]['value'])))
x_labels_all = [date.strftime('%Y-%m-%d') for date in reformed_sensor_list[user_index]['local_timestamp'].tolist()]
x_labels = x_labels_all[0:len(dates):10]
xInput = list(range(0,len(dates),10))

plt.figure(figsize=(12,10))
plt.subplot(4,2,1)
plt.plot(reformed_sensor_list[user_index]['value'].tolist(),
         color='r')
#plt.plot(moving_average(reformed_sensor_list[user_index]['num_of_transition'].tolist(), n=7),label = '7-day moving average')
plt.ylabel("mobility")

plt.subplot(4,2,2)
plt.plot(temp_sleep_duration[user_index])
plt.ylabel("TST(hour)")

plt.subplot(4,2,3)
plt.plot(temp_sleep_onset_duration[user_index])
plt.ylabel("SOL(minute)")

plt.subplot(4,2,4)
plt.plot(temp_sleep_efficiency[user_index])
plt.ylabel("sleep efficiency")

plt.subplot(4,2,5)
plt.plot(temp_waso[user_index])
plt.ylabel("WASO(minute)")

plt.subplot(4,2,6)
plt.plot(temp_sleep_duration_in_bed[user_index])
plt.ylabel("duration in bed(hour)")

plt.subplot(4,2,7)
plt.plot(temp_sleep_avg_hr[user_index])
plt.ylabel("mean sleep HR(bpm)")

plt.subplot(4,2,8)
plt.plot(temp_sleep_avg_rr[user_index])
plt.ylabel("mean sleep RR(bpm)")
plt.xticks(xInput,x_labels, rotation='vertical')


# see the moving avg of one parameter
from scipy.signal import medfilt
volume = reformed_sensor_list[user_index]['value'].tolist()
filtered = medfilt(volume, kernel_size=7)
plt.figure(figsize=(8,5))
plt.plot(volume, label='mobility')
plt.plot(filtered, label='k=7 filtered')
plt.legend()



# see if they have any linear relationship by scatter plots
plt.figure(figsize=(12,12))
plt.subplot(2,2,1)
plt.scatter(reformed_sensor_list[user_index]['value'].tolist(), temp_sleep_duration[user_index])
plt.xlabel('mobility');plt.ylabel('total sleep duration (hour)')
plt.subplot(2,2,2)
plt.scatter(reformed_sensor_list[user_index]['value'].tolist(), temp_sleep_efficiency[user_index])
plt.xlabel('mobility');plt.ylabel('sleep efficiency')
plt.subplot(2,2,3)
plt.scatter(reformed_sensor_list[user_index]['value'].tolist(), temp_sleep_onset_duration[user_index])
plt.xlabel('mobility');plt.ylabel('sleep onset duration (minute)')
plt.subplot(2,2,4)
plt.scatter(reformed_sensor_list[user_index]['value'].tolist(), temp_waso[user_index])
plt.xlabel('mobility');plt.ylabel('wake after sleep onset duration (minute)')



#############################################################################
# From user_gender Dataframe, merge selected users' sleep and mobility
#############################################################################
user_45_PID=[]
for each_user_sleep in reformed_sleep_list_no_nap:
    user_45_PID.append( each_user_sleep['PID'].tolist()[0])

# create 45 people's dataframe and later remove the unwanted 
final_big_df=pd.DataFrame({})    
for i in range(len(user_45_PID)):
    # combine mobility and sleep
    mobility = reformed_sensor_list[i][['local_timestamp','value']]
    sleep_features = reformed_sleep_list[i][['PID','start_sleep_time','finish_sleep_time',
                                        'TST(hour)','WASO(min)','SOL(min)','SE',
                                        'duraion_in_bed','toss_turn_count','avg_hr','avg_rr',
                                        'awake_count','bed_exit_count','bed_exit_duration(min)']]
    mobility.reset_index(drop=True, inplace=True)
    sleep_features.reset_index(drop=True, inplace=True)
    merged_df = pd.concat([mobility, sleep_features],axis=1)
    final_big_df = pd.concat([final_big_df,merged_df])

'''
9188 rows for 45 people, 7900 rows for 37 people
'''

# remove the unwanted people
user_gender_37_people = user_gender['record_id'].tolist()  
final_big_df = final_big_df[final_big_df['PID'].isin(user_gender_37_people)]
# add gender and age into the df
final_big_df = final_big_df.merge(user_gender, left_on='PID',right_on='record_id',how = 'inner')
# remove NaN values if ANY row contains it
final_big_df = final_big_df.dropna(axis=0, how='any')
print(len(final_big_df))


######################################################
# Multivariate regression
######################################################
# Samplping of data
df = final_big_df[['PID','local_timestamp','value','TST(hour)','WASO(min)','SOL(min)','duraion_in_bed',
                    'SE','awake_count','avg_hr','avg_rr','age','gender']]
# group by individuals
a = list(df.groupby(['PID']))
temp_store=[]
for each in a:
    test_user = each[1]
    if len(test_user)>10:
        temp_store.append(test_user)



# see if they have any linear relationship by scatter plots
user_index=17
plt.figure(figsize=(12,6))
plt.subplot(2,3,1)
plt.scatter(reformed_sensor_list[user_index]['value'].tolist(), temp_sleep_duration[user_index])
plt.xlabel('mobility');plt.ylabel('total sleep duration (hour)')
plt.subplot(2,3,2)
plt.scatter(reformed_sensor_list[user_index]['value'].tolist(), temp_sleep_efficiency[user_index])
plt.xlabel('mobility');plt.ylabel('sleep efficiency')
plt.subplot(2,3,3)
plt.scatter(reformed_sensor_list[user_index]['value'].tolist(), temp_sleep_onset_duration[user_index])
plt.xlabel('mobility');plt.ylabel('sleep onset duration (minute)')
plt.subplot(2,3,4)
plt.scatter(reformed_sensor_list[user_index]['value'].tolist(), temp_waso[user_index])
plt.xlabel('mobility');plt.ylabel('wake after sleep onset duration (minute)')
plt.subplot(2,3,5)
plt.scatter(reformed_sensor_list[user_index]['value'].tolist(), temp_sleep_duration_in_bed[user_index])
plt.xlabel('mobility');plt.ylabel('TIB (minute)')
plt.subplot(2,3,6)
plt.scatter(reformed_sensor_list[user_index]['value'].tolist(), temp_sleep_awakeCount[user_index])
plt.xlabel('mobility');plt.ylabel('Awake')


# pearson or spearman plot
test_user = temp_store[9][['value','TST(hour)','WASO(min)','SOL(min)','duraion_in_bed',
                    'SE','awake_count']]
test_user = test_user.rename(columns={"value": "mobility", "TST(hour)": "TST",'WASO(min)':'WASO',
                                      'SOL(min)':'SOL','duraion_in_bed':'TIB','awake_count':'Awake'})
fig, ax = plt.subplots(figsize=(8,4))
corr= test_user.corr(method='spearman').round(2)
# Getting the Upper Triangle of the co-relation matrix
matrix = np.triu(corr)

# using the upper triangle matrix as mask 
sns.heatmap(corr, annot = True, cbar=False,mask=matrix, 
            center= 0, cmap= 'coolwarm', square=True)
plt.show()

T=AAA()

#==============================
def get_sampling_dataset(temp_store_list,d):    
# d: d is the day after sleep, d=1 means mobility is just after that day of sleep
    each_user_sampled_list =[]
    for each_user in temp_store_list:
        each_user_mob = each_user.iloc[list(range(d,len(each_user))),[0,1,2]]
        each_user_sleep = each_user.iloc[list(range(len(each_user)-d)),list(range(3,len(each_user.columns)))]
        each_user_mob.reset_index(drop=True, inplace=True)
        each_user_sleep.reset_index(drop=True, inplace=True)
        each_user_sampled = pd.concat([each_user_mob, each_user_sleep], axis=1,ignore_index=True)
        # up to this step, each_user_sampled miss the column name, so add columns name
        each_user_sampled.columns = each_user.columns
        each_user_sampled_list.append(each_user_sampled)
        
    # now put the list back to a big df 
    final_big_df=pd.DataFrame({})    
    for each in each_user_sampled_list:
        each.reset_index(drop=True, inplace=True)
        final_big_df = pd.concat([final_big_df,each])

    return final_big_df
     
sampled_df_day_0 = get_sampling_dataset(temp_store,1)
sampled_df_day_1 = get_sampling_dataset(temp_store,2)
sampled_df_day_2 = get_sampling_dataset(temp_store,3)
sampled_df_day_3 = get_sampling_dataset(temp_store,4)

#############################################################################
# Regression model
#############################################################################

X = test_user[['TST','Awake','SE']]
Y = test_user['mobility']
model = sm.OLS(Y, X).fit()
print(model.summary())

plt.scatter(X,Y)

fig = sm.graphics.plot_ccpr(model, "Awake")
fig.tight_layout(pad=1.0)



rsquared_adj_list=[]
parameters_list=[]
p_val_list=[]
valid_len=[]
age_list=[]
gender_list=[]
for test_user in temp_store:
    X = test_user[['SE','TST(hour)','SOL(min)','WASO(min)','duraion_in_bed','awake_count']]
    Y = test_user['value']
    model = sm.OLS(Y, X).fit()
    predictions = model.predict(X)
    rsquared_adj_list.append(model.rsquared_adj)
    parameters_list.append(model.params)
    p_val_list.append( round(model.pvalues,4) )
    valid_len.append(len(Y))
    age_list.append(test_user['age'].tolist()[0])
    gender_list.append(test_user['gender'].tolist()[0])
# split each ceof from parameter_list
sol_coefs=[];waso_coefs=[];tst_coefs=[];tib_coefs=[];awake_coefs=[];se_coefs=[]
for each_user_coef in parameters_list:
    tst_coefs.append(each_user_coef.loc['TST(hour)'])
    sol_coefs.append(each_user_coef.loc['SOL(min)'])
    awake_coefs.append(each_user_coef.loc['awake_count'])
    tib_coefs.append(each_user_coef.loc['duraion_in_bed'])
    waso_coefs.append(each_user_coef.loc['WASO(min)'])
    se_coefs.append(each_user_coef.loc['SE'])


# create a df to store results
OLS_result = pd.DataFrame({'age':age_list,'gender':gender_list,'data_points(days)':valid_len,
                           'adj_R_squared':rsquared_adj_list,'coef_TST':tst_coefs,
                           'coef_SOL':sol_coefs,'coef_WASO':waso_coefs,'coef_time_in_bed':tib_coefs,
                           'coef_awake':awake_coefs,'coef_SE':se_coefs,'p_values':p_val_list})    
#OLS_result.to_excel(r'F:/OLS_reuslts_36_individuals.xlsx',index=False)

#=======================================
# Stepwise regression
from sklearn.preprocessing import StandardScaler
import statsmodels.formula.api as smf 
class FeatureSelection(): 
	def stepwise(self, df, response, intercept=False, normalize=False, criterion='rsquared_adj', f_pvalue_enter=.05, p_value_enter=.05, direction='backward', show_step=True, criterion_enter=None, criterion_remove=None, max_iter=200, **kw):
		"""
		逐步回归。

		参数
		----
		df : dataframe
			分析用数据框，response为第一列。
		response : str
			回归分析相应变量。
		intercept : bool, 默认是True
			模型是否有截距项。
		criterion : str, 默认是'bic'
			逐步回归优化规则。
		f_pvalue_enter : float, 默认是.05
			当选择criterion=’ssr‘时，模型加入或移除变量的f_pvalue阈值。
		p_value_enter : float, 默认是.05
			当选择derection=’both‘时，移除变量的pvalue阈值。
		direction : str, 默认是'backward'
			逐步回归方向。
		show_step : bool, 默认是True
			是否显示逐步回归过程。
		criterion_enter : float, 默认是None
			当选择derection=’both‘或'forward'时，模型加入变量的相应的criterion阈值。
		criterion_remove : float, 默认是None
			当选择derection='backward'时，模型移除变量的相应的criterion阈值。
		max_iter : int, 默认是200
			模型最大迭代次数。
		"""
		criterion_list = ['bic', 'aic', 'ssr', 'rsquared', 'rsquared_adj']
		if criterion not in criterion_list:
			raise IOError('请输入正确的criterion, 必须是以下内容之一：', '\n', criterion_list)

		direction_list = ['backward', 'forward', 'both']
		if direction not in direction_list:
			raise IOError('请输入正确的direction, 必须是以下内容之一：', '\n', direction_list)

		# 默认p_enter参数
		p_enter = {'bic': 0.0, 'aic': 0.0, 'ssr': 0.05, 'rsquared': 0.05, 'rsquared_adj': -0.05}
		if criterion_enter:  # 如果函数中对p_remove相应key传参，则变更该参数
			p_enter[criterion] = criterion_enter

		# 默认p_remove参数
		p_remove = {'bic': 0.01, 'aic': 0.01, 'ssr': 0.1, 'rsquared': 0.05, 'rsquared_adj': -0.05}
		if criterion_remove:  # 如果函数中对p_remove相应key传参，则变更该参数
			p_remove[criterion] = criterion_remove

		if normalize:  # 如果需要标准化数据
			intercept = False  # 截距强制设置为0
			df_std = StandardScaler().fit_transform(df)
			df = pd.DataFrame(df_std, columns=df.columns, index=df.index)

		""" forward """
		if direction == 'forward':
			remaining = list(df.columns)  # 自变量集合
			remaining.remove(response)
			selected = []  # 初始化选入模型的变量列表
			# 初始化当前评分,最优新评分
			if intercept:  # 是否有截距
				formula = "{} ~ {} + 1".format(response, remaining[0])
			else:
				formula = "{} ~ {} - 1".format(response, remaining[0])

			result = smf.ols(formula, df).fit()  # 最小二乘法回归模型拟合
			current_score = eval('result.' + criterion)
			best_new_score = eval('result.' + criterion)

			if show_step:
				print('\nstepwise starting:\n')
			iter_times = 0
			# 当变量未剔除完，并且当前评分更新时进行循环
			while remaining and (current_score == best_new_score) and (iter_times < max_iter):
				scores_with_candidates = []  # 初始化变量以及其评分列表
				for candidate in remaining:  # 在未剔除的变量中每次选择一个变量进入模型，如此循环
					if intercept:  # 是否有截距
						formula = "{} ~ {} + 1".format(response, ' + '.join(selected + [candidate]))
					else:
						formula = "{} ~ {} - 1".format(response, ' + '.join(selected + [candidate]))

					result = smf.ols(formula, df).fit()  # 最小二乘法回归模型拟合
					fvalue = result.fvalue
					f_pvalue = result.f_pvalue
					score = eval('result.' + criterion)
					scores_with_candidates.append((score, candidate, fvalue, f_pvalue))  # 记录此次循环的变量、评分列表

				if criterion == 'ssr':  # 这几个指标取最小值进行优化
					scores_with_candidates.sort(reverse=True)  # 对评分列表进行降序排序
					best_new_score, best_candidate, best_new_fvalue, best_new_f_pvalue = scores_with_candidates.pop()  # 提取最小分数及其对应变量
					if ((current_score - best_new_score) > p_enter[criterion]) and (
							best_new_f_pvalue < f_pvalue_enter):  # 如果当前评分大于最新评分
						remaining.remove(best_candidate)  # 从剩余未评分变量中剔除最新最优分对应的变量
						selected.append(best_candidate)  # 将最新最优分对应的变量放入已选变量列表
						current_score = best_new_score  # 更新当前评分
						if show_step:  # 是否显示逐步回归过程
							print('Adding %s, SSR = %.3f, Fstat = %.3f, FpValue = %.3e' %
								  (best_candidate, best_new_score, best_new_fvalue, best_new_f_pvalue))
					elif (current_score - best_new_score) >= 0 and (
							best_new_f_pvalue < f_pvalue_enter) and iter_times == 0:  # 当评分差大于等于0，且为第一次迭代
						remaining.remove(best_candidate)
						selected.append(best_candidate)
						current_score = best_new_score
						if show_step:  # 是否显示逐步回归过程
							print('Adding %s, %s = %.3f' % (best_candidate, criterion, best_new_score))
					elif (best_new_f_pvalue < f_pvalue_enter) and iter_times == 0:  # 当评分差小于p_enter，且为第一次迭代
						selected.append(remaining[0])
						remaining.remove(remaining[0])
						if show_step:  # 是否显示逐步回归过程
							print('Adding %s, %s = %.3f' % (remaining[0], criterion, best_new_score))
				elif criterion in ['bic', 'aic']:  # 这几个指标取最小值进行优化
					scores_with_candidates.sort(reverse=True)  # 对评分列表进行降序排序
					best_new_score, best_candidate, best_new_fvalue, best_new_f_pvalue = scores_with_candidates.pop()  # 提取最小分数及其对应变量
					if (current_score - best_new_score) > p_enter[criterion]:  # 如果当前评分大于最新评分
						remaining.remove(best_candidate)  # 从剩余未评分变量中剔除最新最优分对应的变量
						selected.append(best_candidate)  # 将最新最优分对应的变量放入已选变量列表
						current_score = best_new_score  # 更新当前评分
						# print(iter_times)
						if show_step:  # 是否显示逐步回归过程
							print('Adding %s, %s = %.3f' % (best_candidate, criterion, best_new_score))
					elif (current_score - best_new_score) >= 0 and iter_times == 0:  # 当评分差大于等于0，且为第一次迭代
						remaining.remove(best_candidate)
						selected.append(best_candidate)
						current_score = best_new_score
						if show_step:  # 是否显示逐步回归过程
							print('Adding %s, %s = %.3f' % (best_candidate, criterion, best_new_score))
					elif iter_times == 0:  # 当评分差小于p_enter，且为第一次迭代
						selected.append(remaining[0])
						remaining.remove(remaining[0])
						if show_step:  # 是否显示逐步回归过程
							print('Adding %s, %s = %.3f' % (remaining[0], criterion, best_new_score))
				else:
					scores_with_candidates.sort()
					best_new_score, best_candidate, best_new_fvalue, best_new_f_pvalue = scores_with_candidates.pop()
					if (best_new_score - current_score) > p_enter[criterion]:
						remaining.remove(best_candidate)
						selected.append(best_candidate)
						current_score = best_new_score
						print(iter_times, flush=True)
						if show_step:  # 是否显示逐步回归过程
							print('Adding %s, %s = %.3f' % (best_candidate, criterion, best_new_score))
					elif (best_new_score - current_score) >= 0 and iter_times == 0:  # 当评分差大于等于0，且为第一次迭代
						remaining.remove(best_candidate)
						selected.append(best_candidate)
						current_score = best_new_score
						if show_step:  # 是否显示逐步回归过程
							print('Adding %s, %s = %.3f' % (best_candidate, criterion, best_new_score))
					elif iter_times == 0:  # 当评分差小于p_enter，且为第一次迭代
						selected.append(remaining[0])
						remaining.remove(remaining[0])
						if show_step:  # 是否显示逐步回归过程
							print('Adding %s, %s = %.3f' % (remaining[0], criterion, best_new_score))
				iter_times += 1

			if intercept:  # 是否有截距
				formula = "{} ~ {} + 1".format(response, ' + '.join(selected))
			else:
				formula = "{} ~ {} - 1".format(response, ' + '.join(selected))

			self.stepwise_model = smf.ols(formula, df).fit()  # 最优模型拟合

			if show_step:  # 是否显示逐步回归过程
				print('\nLinear regression model:', '\n  ', self.stepwise_model.model.formula)
				print('\n', self.stepwise_model.summary())

		""" backward """
		if direction == 'backward':
			remaining, selected = set(df.columns), set(df.columns)  # 自变量集合
			remaining.remove(response)
			selected.remove(response)  # 初始化选入模型的变量列表
			# 初始化当前评分,最优新评分
			if intercept:  # 是否有截距
				formula = "{} ~ {} + 1".format(response, ' + '.join(selected))
			else:
				formula = "{} ~ {} - 1".format(response, ' + '.join(selected))

			result = smf.ols(formula, df).fit()  # 最小二乘法回归模型拟合
			current_score = eval('result.' + criterion)
			worst_new_score = eval('result.' + criterion)

			if show_step:
				print('\nstepwise starting:\n')
			iter_times = 0
			# 当变量未剔除完，并且当前评分更新时进行循环
			while remaining and (current_score == worst_new_score) and (iter_times < max_iter):
				scores_with_eliminations = []  # 初始化变量以及其评分列表
				for elimination in remaining:  # 在未剔除的变量中每次选择一个变量进入模型，如此循环
					if intercept:  # 是否有截距
						formula = "{} ~ {} + 1".format(response, ' + '.join(selected - set(elimination)))
					else:
						formula = "{} ~ {} - 1".format(response, ' + '.join(selected - set(elimination)))

					result = smf.ols(formula, df).fit()  # 最小二乘法回归模型拟合
					fvalue = result.fvalue
					f_pvalue = result.f_pvalue
					score = eval('result.' + criterion)
					scores_with_eliminations.append((score, elimination, fvalue, f_pvalue))  # 记录此次循环的变量、评分列表

				if criterion == 'ssr':  # 这几个指标取最小值进行优化
					scores_with_eliminations.sort(reverse=False)  # 对评分列表进行降序排序
					worst_new_score, worst_elimination, worst_new_fvalue, worst_new_f_pvalue = scores_with_eliminations.pop()  # 提取最小分数及其对应变量
					if ((worst_new_score - current_score) < p_remove[criterion]) and (
							worst_new_f_pvalue < f_pvalue_enter):  # 如果当前评分大于最新评分
						remaining.remove(worst_elimination)  # 从剩余未评分变量中剔除最新最优分对应的变量
						selected.remove(worst_elimination)  # 从已选变量列表中剔除最新最优分对应的变量
						current_score = worst_new_score  # 更新当前评分
						if show_step:  # 是否显示逐步回归过程
							print('Removing %s, SSR = %.3f, Fstat = %.3f, FpValue = %.3e' %
								  (worst_elimination, worst_new_score, worst_new_fvalue, worst_new_f_pvalue))
				elif criterion in ['bic', 'aic']:  # 这几个指标取最小值进行优化
					scores_with_eliminations.sort(reverse=False)  # 对评分列表进行降序排序
					worst_new_score, worst_elimination, worst_new_fvalue, worst_new_f_pvalue = scores_with_eliminations.pop()  # 提取最小分数及其对应变量
					if (worst_new_score - current_score) < p_remove[criterion]:  # 如果评分变动不显著
						remaining.remove(worst_elimination)  # 从剩余未评分变量中剔除最新最优分对应的变量
						selected.remove(worst_elimination)  # 从已选变量列表中剔除最新最优分对应的变量
						current_score = worst_new_score  # 更新当前评分
						if show_step:  # 是否显示逐步回归过程
							print('Removing %s, %s = %.3f' % (worst_elimination, criterion, worst_new_score))
				else:
					scores_with_eliminations.sort(reverse=True)
					worst_new_score, worst_elimination, worst_new_fvalue, worst_new_f_pvalue = scores_with_eliminations.pop()
					if (current_score - worst_new_score) < p_remove[criterion]:
						remaining.remove(worst_elimination)
						selected.remove(worst_elimination)
						current_score = worst_new_score
						if show_step:  # 是否显示逐步回归过程
							print('Removing %s, %s = %.3f' % (worst_elimination, criterion, worst_new_score))
				iter_times += 1

			if intercept:  # 是否有截距
				formula = "{} ~ {} + 1".format(response, ' + '.join(selected))
			else:
				formula = "{} ~ {} - 1".format(response, ' + '.join(selected))

			self.stepwise_model = smf.ols(formula, df).fit()  # 最优模型拟合

			if show_step:  # 是否显示逐步回归过程
				print('\nLinear regression model:', '\n  ', self.stepwise_model.model.formula)
				print('\n', self.stepwise_model.summary())

		""" both """
		if direction == 'both':
			remaining = list(df.columns)  # 自变量集合
			remaining.remove(response)
			selected = []  # 初始化选入模型的变量列表
			# 初始化当前评分,最优新评分
			if intercept:  # 是否有截距
				formula = "{} ~ {} + 1".format(response, remaining[0])
			else:
				formula = "{} ~ {} - 1".format(response, remaining[0])

			result = smf.ols(formula, df).fit()  # 最小二乘法回归模型拟合
			current_score = eval('result.' + criterion)
			best_new_score = eval('result.' + criterion)

			if show_step:
				print('\nstepwise starting:\n')
			# 当变量未剔除完，并且当前评分更新时进行循环
			iter_times = 0
			while remaining and (current_score == best_new_score) and (iter_times < max_iter):
				scores_with_candidates = []  # 初始化变量以及其评分列表
				for candidate in remaining:  # 在未剔除的变量中每次选择一个变量进入模型，如此循环
					if intercept:  # 是否有截距
						formula = "{} ~ {} + 1".format(response, ' + '.join(selected + [candidate]))
					else:
						formula = "{} ~ {} - 1".format(response, ' + '.join(selected + [candidate]))

					result = smf.ols(formula, df).fit()  # 最小二乘法回归模型拟合
					fvalue = result.fvalue
					f_pvalue = result.f_pvalue
					score = eval('result.' + criterion)
					scores_with_candidates.append((score, candidate, fvalue, f_pvalue))  # 记录此次循环的变量、评分列表

				if criterion == 'ssr':  # 这几个指标取最小值进行优化
					scores_with_candidates.sort(reverse=True)  # 对评分列表进行降序排序
					best_new_score, best_candidate, best_new_fvalue, best_new_f_pvalue = scores_with_candidates.pop()    # 提取最小分数及其对应变量
					if ((current_score - best_new_score) > p_enter[criterion]) and (
							best_new_f_pvalue < f_pvalue_enter):  # 如果当前评分大于最新评分
						remaining.remove(best_candidate)  # 从剩余未评分变量中剔除最新最优分对应的变量
						selected.append(best_candidate)  # 将最新最优分对应的变量放入已选变量列表
						current_score = best_new_score  # 更新当前评分
						if show_step:  # 是否显示逐步回归过程
							print('Adding %s, SSR = %.3f, Fstat = %.3f, FpValue = %.3e' %
								  (best_candidate, best_new_score, best_new_fvalue, best_new_f_pvalue))
					elif (current_score - best_new_score) >= 0 and (
							best_new_f_pvalue < f_pvalue_enter) and iter_times == 0:  # 当评分差大于等于0，且为第一次迭代
						remaining.remove(best_candidate)
						selected.append(best_candidate)
						current_score = best_new_score
						if show_step:  # 是否显示逐步回归过程
							print('Adding %s, %s = %.3f' % (best_candidate, criterion, best_new_score))
					elif (best_new_f_pvalue < f_pvalue_enter) and iter_times == 0:  # 当评分差小于p_enter，且为第一次迭代
						selected.append(remaining[0])
						remaining.remove(remaining[0])
						if show_step:  # 是否显示逐步回归过程
							print('Adding %s, %s = %.3f' % (remaining[0], criterion, best_new_score))
				elif criterion in ['bic', 'aic']:  # 这几个指标取最小值进行优化
					scores_with_candidates.sort(reverse=True)  # 对评分列表进行降序排序
					best_new_score, best_candidate, best_new_fvalue, best_new_f_pvalue = scores_with_candidates.pop()  # 提取最小分数及其对应变量
					if (current_score - best_new_score) > p_enter[criterion]:  # 如果当前评分大于最新评分
						remaining.remove(best_candidate)  # 从剩余未评分变量中剔除最新最优分对应的变量
						selected.append(best_candidate)  # 将最新最优分对应的变量放入已选变量列表
						current_score = best_new_score  # 更新当前评分
						if show_step:  # 是否显示逐步回归过程
							print('Adding %s, %s = %.3f' % (best_candidate, criterion, best_new_score))
					elif (current_score - best_new_score) >= 0 and iter_times == 0:  # 当评分差大于等于0，且为第一次迭代
						remaining.remove(best_candidate)
						selected.append(best_candidate)
						current_score = best_new_score
						if show_step:  # 是否显示逐步回归过程
							print('Adding %s, %s = %.3f' % (best_candidate, criterion, best_new_score))
					elif iter_times == 0:  # 当评分差小于p_enter，且为第一次迭代
						selected.append(remaining[0])
						remaining.remove(remaining[0])
						if show_step:  # 是否显示逐步回归过程
							print('Adding %s, %s = %.3f' % (remaining[0], criterion, best_new_score))
				else:
					scores_with_candidates.sort()
					best_new_score, best_candidate, best_new_fvalue, best_new_f_pvalue = scores_with_candidates.pop()
					if (best_new_score - current_score) > p_enter[criterion]:  # 当评分差大于p_enter
						remaining.remove(best_candidate)
						selected.append(best_candidate)
						current_score = best_new_score
						if show_step:  # 是否显示逐步回归过程
							print('Adding %s, %s = %.3f' % (best_candidate, criterion, best_new_score))
					elif (best_new_score - current_score) >= 0 and iter_times == 0:  # 当评分差大于等于0，且为第一次迭代
						remaining.remove(best_candidate)
						selected.append(best_candidate)
						current_score = best_new_score
						if show_step:  # 是否显示逐步回归过程
							print('Adding %s, %s = %.3f' % (best_candidate, criterion, best_new_score))
					elif iter_times == 0:  # 当评分差小于p_enter，且为第一次迭代
						selected.append(remaining[0])
						remaining.remove(remaining[0])
						if show_step:  # 是否显示逐步回归过程
							print('Adding %s, %s = %.3f' % (remaining[0], criterion, best_new_score))

				if intercept:  # 是否有截距
					formula = "{} ~ {} + 1".format(response, ' + '.join(selected))
				else:
					formula = "{} ~ {} - 1".format(response, ' + '.join(selected))

				result = smf.ols(formula, df).fit()  # 最优模型拟合
				if iter_times >= 1:  # 当第二次循环时判断变量的pvalue是否达标
					if result.pvalues.max() > p_value_enter:
						var_removed = result.pvalues[result.pvalues == result.pvalues.max()].index[0]
						p_value_removed = result.pvalues[result.pvalues == result.pvalues.max()].values[0]
						selected.remove(result.pvalues[result.pvalues == result.pvalues.max()].index[0])
						if show_step:  # 是否显示逐步回归过程
							print('Removing %s, Pvalue = %.3f' % (var_removed, p_value_removed))
				iter_times += 1

			if intercept:  # 是否有截距
				formula = "{} ~ {} + 1".format(response, ' + '.join(selected))
			else:
				formula = "{} ~ {} - 1".format(response, ' + '.join(selected))

			self.stepwise_model = smf.ols(formula, df).fit()  # 最优模型拟合
			if show_step:  # 是否显示逐步回归过程
				print('\nLinear regression model:', '\n  ', self.stepwise_model.model.formula)
				print('\n', self.stepwise_model.summary())
				# 最终模型选择的变量
		if intercept:
			self.stepwise_feat_selected_ = list(self.stepwise_model.params.index[1:])
		else:
			self.stepwise_feat_selected_ = list(self.stepwise_model.params.index)
		return self

models_adj_r_squared=[]
parameters_list=[]
valid_len=[]
p_val_list=[]
age_list=[]
gender_list=[]
for test_user in temp_store:
    df = pd.DataFrame({'mobility':test_user.loc[:, 'value'],'TST':test_user.loc[:, 'TST(hour)'],
                   'SOL':test_user.loc[:, 'SOL(min)'],'WASO':test_user.loc[:, 'WASO(min)'],
                   'TIB':test_user.loc[:, 'duraion_in_bed'],'Awake':test_user.loc[:, 'awake_count']              
                   })

    the_model = FeatureSelection().stepwise(df=df, response='mobility', direction='both',max_iter=5,criterion='ssr')  # criterion='ssr'是为了移除不合适特征
    # ['bic', 'aic', 'ssr', 'rsquared', 'rsquared_adj'] 
    # ['backward', 'forward', 'both']
    
    # print the value I would like to know: 
    # https://blog.csdn.net/qq_37890276/article/details/93016165
    models_adj_r_squared.append(the_model.stepwise_model.rsquared_adj)
    parameters_list.append(the_model.stepwise_model.params)
    p_val_list.append(the_model.stepwise_model.pvalues)
    valid_len.append(len(test_user['age']))
    age_list.append(test_user['age'].tolist()[0])
    gender_list.append(test_user['gender'].tolist()[0])
    
    

# split each ceof from parameter_list
new_index = ['TST', 'SOL','WASO', 'Awake', 'TIB']
sol_coefs=[];waso_coefs=[];tst_coefs=[];tib_coefs=[];awake_coefs=[];se_coefs=[]
for each_user_coef in parameters_list:
    each_user_coef = each_user_coef.reindex(new_index,fill_value=np.nan)
    tst_coefs.append(each_user_coef.loc['TST'])
    sol_coefs.append(each_user_coef.loc['SOL'])
    awake_coefs.append(each_user_coef.loc['Awake'])
    tib_coefs.append(each_user_coef.loc['TIB'])
    waso_coefs.append(each_user_coef.loc['WASO'])
    
# create a df to store results
OLS_result_stepwise = pd.DataFrame({'age':age_list,'gender':gender_list,'data_points(days)':valid_len,
                           'R_squared_adj':models_adj_r_squared,'coef_TST':tst_coefs,
                           'coef_SOL':sol_coefs,'coef_WASO':waso_coefs,'coef_TIB':tib_coefs,
                           'coef_Awake':awake_coefs,'p_value':p_val_list})    

    

# OLS_result_stepwise.to_excel(r'F:/OLS_reuslts_36_individuals_backward_selection_highest_R_squared.xlsx',index=False)

OLS_result_stepwise.loc[OLS_result_stepwise['gender'] ==1, 'gender'] = 'male'
OLS_result_stepwise.loc[OLS_result_stepwise['gender'] ==2, 'gender'] = 'female'
OLS_result_stepwise.loc[(OLS_result_stepwise['age'] >=70) & (OLS_result_stepwise['age'] <80), 'age'] = 70
OLS_result_stepwise.loc[(OLS_result_stepwise['age'] >=80) & (OLS_result_stepwise['age'] <90), 'age'] = 80
OLS_result_stepwise.loc[(OLS_result_stepwise['age'] >=90) & (OLS_result_stepwise['age'] <100), 'age'] = 90
OLS_result_stepwise.loc[OLS_result_stepwise['age'] ==70, 'age'] = '70s'
OLS_result_stepwise.loc[OLS_result_stepwise['age'] ==80, 'age'] = '80s'
OLS_result_stepwise.loc[OLS_result_stepwise['age'] ==90, 'age'] = '90s'


a = OLS_result_stepwise.loc[OLS_result_stepwise['gender'] =='male', 'R_squared']
b = OLS_result_stepwise.loc[OLS_result_stepwise['gender'] =='female', 'R_squared']
u,pval = stats.mannwhitneyu(a,b)
print(pval)

a = OLS_result_stepwise.loc[OLS_result_stepwise['gender'] =='male', 'coef_SE']
b = OLS_result_stepwise.loc[OLS_result_stepwise['gender'] =='female', 'coef_SE']
u,pval = stats.mannwhitneyu(a,b)
print(pval)

a = (OLS_result_stepwise.loc[OLS_result_stepwise['age'] =='70s', 'coef_SE']).tolist()
b = (OLS_result_stepwise.loc[OLS_result_stepwise['age'] =='80s', 'coef_SE']).tolist()
c = (OLS_result_stepwise.loc[OLS_result_stepwise['age'] =='90s', 'coef_SE']).tolist()
t = three_group_dunn_ttest(a,b,c)
post_hoc_dunn_result0= pd.DataFrame({'70VS80':t.iloc[0,1],'70VS90':t.iloc[0,2],
                                    '80VS90':t.iloc[1,2]},index=['mobility'])


#############################################################################
# one way ANOVA
#############################################################################

# non-parameteric testing has to be apply on health people
user_gender = user_gender[user_gender['ATSM']>=7]


# mean for male and female age
selected_df_male = user_gender[user_gender['gender']==1]
selected_df_female = user_gender[user_gender['gender']==2]
selected_df_male_70s = selected_df_male.loc[(selected_df_male['age']>=70) & (selected_df_male['age']<80)]
selected_df_male_80s = selected_df_male.loc[(selected_df_male['age']>=80) & (selected_df_male['age']<90)]
selected_df_male_90s = selected_df_male.loc[(selected_df_male['age']>=90) & (selected_df_male['age']<100)]
selected_df_female_70s = selected_df_female.loc[(selected_df_female['age']>=70) & (selected_df_female['age']<80)]
selected_df_female_80s = selected_df_female.loc[(selected_df_female['age']>=80) & (selected_df_female['age']<90)]
selected_df_female_90s = selected_df_female.loc[(selected_df_female['age']>=90) & (selected_df_female['age']<100)]

selected_df_70s = user_gender[(user_gender['age']>=70) & (user_gender['age']<80)]
selected_df_80s = user_gender[(user_gender['age']>=80) & (user_gender['age']<90)]
selected_df_90s = user_gender[(user_gender['age']>=90) & (user_gender['age']<100)]

#selected_df_demented = user_gender[(user_gender['ATSM']<7)]
#selected_df_high_levelCare = user_gender[(user_gender['home_care_package_level']>3)]


    
selected_df_female_70s['home_care_package_level'].describe()
selected_df_female['home_care_package_level'].describe()
selected_df_male['ATSM'].describe()

# ---------------------------------------------------
# split group
# from user_gender, get the index of male and female
def merge_data_mobility(selected_df,reformed_sensor_list):
   mobility_data=[]
   for i in selected_df.index.tolist():
       mobility_data.append(reformed_sensor_list[i]['value'].values.tolist())
   return mobility_data

def merge_data_sleep_para(selected_df,sleep_para):
   sleep_para_data=[]
   for i in selected_df.index.tolist():
       sleep_para_data.append(sleep_para[i])
   return sleep_para_data

#--------------------------------------------
# for 2 group Mann Whitney test data
male_df = selected_df_male
mobility_data_male = merge_data_mobility(male_df,reformed_sensor_list)
sleep_tst_male = merge_data_sleep_para(male_df,temp_sleep_duration)
sleep_sol_male = merge_data_sleep_para(male_df,temp_sleep_onset_duration)
sleep_effi_male = merge_data_sleep_para(male_df,temp_sleep_efficiency)
sleep_awake_male = merge_data_sleep_para(male_df,temp_sleep_awakeCount)
sleep_waso_male = merge_data_sleep_para(male_df,temp_waso)
sleep_duration_in_bed_male = merge_data_sleep_para(male_df,temp_sleep_duration_in_bed)
#sleep_exit_male= merge_data_sleep_para(male_df,temp_sleep_bedexit)
sleep_ttc_male = merge_data_sleep_para(male_df,temp_sleep_ttc)
sleep_avgHR_male = merge_data_sleep_para(male_df,temp_sleep_avg_hr)
sleep_avgRR_male = merge_data_sleep_para(male_df,temp_sleep_avg_rr)
sleep_exit_count_male= merge_data_sleep_para(male_df,temp_sleep_exitCount)
male=[mobility_data_male,sleep_tst_male,sleep_sol_male,sleep_effi_male,sleep_waso_male,
      sleep_duration_in_bed_male,sleep_awake_male
      ]
list_index=['mobility','TST','SOL','SE','WASO','TIB','Awake']


female_df = selected_df_female
mobility_data_female = merge_data_mobility(female_df,reformed_sensor_list)
sleep_tst_female = merge_data_sleep_para(female_df,temp_sleep_duration)
sleep_sol_female = merge_data_sleep_para(female_df,temp_sleep_onset_duration)
sleep_effi_female = merge_data_sleep_para(female_df,temp_sleep_efficiency)
sleep_waso_female = merge_data_sleep_para(female_df,temp_waso)
sleep_duration_in_bed_female = merge_data_sleep_para(female_df,temp_sleep_duration_in_bed)
#sleep_exit_female= merge_data_sleep_para(female_df,temp_sleep_bedexit)
sleep_ttc_female = merge_data_sleep_para(female_df,temp_sleep_ttc)
sleep_avgHR_female = merge_data_sleep_para(female_df,temp_sleep_avg_hr)
sleep_avgRR_female = merge_data_sleep_para(female_df,temp_sleep_avg_rr)
sleep_awake_female = merge_data_sleep_para(female_df,temp_sleep_awakeCount)
sleep_exit_count_female= merge_data_sleep_para(female_df,temp_sleep_exitCount)
female=[mobility_data_female,sleep_tst_female,sleep_sol_female,sleep_effi_female,sleep_waso_female,
      sleep_duration_in_bed_female,sleep_awake_female
      ]

# Mann-Whitney t tests
def two_group_Mann_Whitney_test(group_a, group_b):
    a = [item for sublist in group_a for item in sublist]
    b = [item for sublist in group_b for item in sublist]
    u,pval = stats.mannwhitneyu(a,b)
    return u,pval

def mann_whitney_test_print_results(gender_list1,gender_list2):
    '''gender_list: list_of_parameter_from_a_selected_group'''
    stats=[];p_val=[]
    for i in range(len(gender_list1)):
        each_para_gender1 = gender_list1[i]
        each_para_gender2 = gender_list2[i]
        u,pval = two_group_Mann_Whitney_test(each_para_gender1, each_para_gender2)
        stats.append("{:.2f}".format(u))
        p_val.append("{:.4f}".format(pval))
    return stats,p_val

pstat,pval = mann_whitney_test_print_results(male,female)
mann_whitney_test_results = pd.DataFrame({'index':list_index,'stats':pstat,'p_val':pval})


#--------------------------------
length=[]
mobility_data_37_people = merge_data_mobility(user_gender,reformed_sensor_list)
sleep_data_37_people = merge_data_sleep_para(user_gender,reformed_sleep_list_no_nap)
for each_user in sleep_data_37_people:
    length.append(len(each_user))
plt.hist(length,bins=6,color='#66ccff',edgecolor='black', linewidth=1.2)
plt.xlabel('Length of valid days');plt.ylabel('Number of apperance')


# male and female distributions, gender is fixed
kwargs = dict(alpha=0.5, bins=50)
c1='#00aaff';c2='y'
male_label = '90s male'
female_label = '90s female'

plt.figure(figsize=(8,10))
plt.subplot(3,2,1)
plt.hist([item for sublist in mobility_data_male for item in sublist],**kwargs, color=c1, label=male_label+' mobility')
plt.hist([item for sublist in mobility_data_female for item in sublist],**kwargs, color=c2, label=female_label+' mobility')
plt.xlabel('number of steps');plt.legend()
plt.subplot(3,2,2)
plt.hist([item for sublist in sleep_tst_male for item in sublist],**kwargs, color=c1, label=male_label+' TST')
plt.hist([item for sublist in sleep_tst_female for item in sublist],**kwargs, color=c2, label=female_label+' TST')
plt.xlabel('TST(hour)');plt.legend()
plt.subplot(3,2,3)
plt.hist([item for sublist in sleep_sol_male for item in sublist],**kwargs, color=c1, label=male_label+' SOL')
plt.hist([item for sublist in sleep_sol_female for item in sublist],**kwargs, color=c2, label=female_label+' SOL')
plt.xlabel('SOL(min)');plt.legend()
plt.subplot(3,2,4)
plt.hist([item for sublist in sleep_waso_male for item in sublist],**kwargs, color=c1, label=male_label+' WASO')
plt.hist([item for sublist in sleep_waso_female for item in sublist],**kwargs, color=c2, label=female_label+' WASO')
plt.xlabel('WASO(min)');plt.legend()
plt.subplot(3,2,5)
plt.hist([item for sublist in sleep_effi_male for item in sublist],**kwargs, color=c1, label=male_label+' SE')
plt.hist([item for sublist in sleep_effi_female for item in sublist],**kwargs, color=c2, label=female_label+' SE')
plt.xlabel('SE');plt.legend()
plt.subplot(3,2,6)
plt.hist([item for sublist in sleep_duration_in_bed_male for item in sublist],**kwargs, color=c1, label=male_label+' Awake')
plt.hist([item for sublist in sleep_duration_in_bed_female for item in sublist],**kwargs, color=c2, label=female_label+' Awake')
plt.xlabel('awakenings');plt.legend()





#--------------------------------------------
# input: selected_df_70s, selected_df_female_70s, selected_df_male_70s, selected_df_female_80s...
# at 70s
fixed_gender = selected_df_70s
mobility_data_70s = merge_data_mobility(fixed_gender,reformed_sensor_list)
sleep_tst_70s = merge_data_sleep_para(fixed_gender,temp_sleep_duration)
sleep_sol_70s = merge_data_sleep_para(fixed_gender,temp_sleep_onset_duration)
sleep_effi_70s = merge_data_sleep_para(fixed_gender,temp_sleep_efficiency)
sleep_waso_70s = merge_data_sleep_para(fixed_gender,temp_waso)
sleep_duration_in_bed_70s = merge_data_sleep_para(fixed_gender,temp_sleep_duration_in_bed)
sleep_ttc_70s = merge_data_sleep_para(fixed_gender,temp_sleep_ttc)
sleep_avgHR_70s = merge_data_sleep_para(fixed_gender,temp_sleep_avg_hr)
sleep_avgRR_70s = merge_data_sleep_para(fixed_gender,temp_sleep_avg_rr)
sleep_awake_70s = merge_data_sleep_para(fixed_gender,temp_sleep_awakeCount)
sleep_exit_count_70s = merge_data_sleep_para(fixed_gender,temp_sleep_exitCount)


# at 80s
fixed_gender = selected_df_80s
mobility_data_80s = merge_data_mobility(fixed_gender,reformed_sensor_list)
sleep_tst_80s = merge_data_sleep_para(fixed_gender,temp_sleep_duration)
sleep_sol_80s = merge_data_sleep_para(fixed_gender,temp_sleep_onset_duration)
sleep_effi_80s = merge_data_sleep_para(fixed_gender,temp_sleep_efficiency)
sleep_waso_80s = merge_data_sleep_para(fixed_gender,temp_waso)
sleep_duration_in_bed_80s = merge_data_sleep_para(fixed_gender,temp_sleep_duration_in_bed)
sleep_ttc_80s = merge_data_sleep_para(fixed_gender,temp_sleep_ttc)
sleep_avgHR_80s = merge_data_sleep_para(fixed_gender,temp_sleep_avg_hr)
sleep_avgRR_80s = merge_data_sleep_para(fixed_gender,temp_sleep_avg_rr)
sleep_awake_80s = merge_data_sleep_para(fixed_gender,temp_sleep_awakeCount)
sleep_exit_count_80s = merge_data_sleep_para(fixed_gender,temp_sleep_exitCount)

# at 90s
fixed_gender = selected_df_90s
mobility_data_90s = merge_data_mobility(fixed_gender,reformed_sensor_list)
sleep_tst_90s = merge_data_sleep_para(fixed_gender,temp_sleep_duration)
sleep_sol_90s = merge_data_sleep_para(fixed_gender,temp_sleep_onset_duration)
sleep_effi_90s = merge_data_sleep_para(fixed_gender,temp_sleep_efficiency)
sleep_waso_90s = merge_data_sleep_para(fixed_gender,temp_waso)
sleep_duration_in_bed_90s = merge_data_sleep_para(fixed_gender,temp_sleep_duration_in_bed)
sleep_ttc_90s = merge_data_sleep_para(fixed_gender,temp_sleep_ttc)
sleep_avgHR_90s = merge_data_sleep_para(fixed_gender,temp_sleep_avg_hr)
sleep_avgRR_90s = merge_data_sleep_para(fixed_gender,temp_sleep_avg_rr)
sleep_awake_90s = merge_data_sleep_para(fixed_gender,temp_sleep_awakeCount)
sleep_exit_count_90s = merge_data_sleep_para(fixed_gender,temp_sleep_exitCount)

# Just for caution
u,pval = two_group_Mann_Whitney_test(mobility_data_70s, mobility_data_80s)
print("{:.2f}".format(u),',',pval)
u,pval = two_group_Mann_Whitney_test(mobility_data_80s, mobility_data_90s)
print("{:.2f}".format(u),',',pval)
u,pval = two_group_Mann_Whitney_test(mobility_data_70s, mobility_data_90s)
print("{:.2f}".format(u),',',pval)

u,pval = two_group_Mann_Whitney_test(sleep_tst_70s, sleep_tst_80s)
print("{:.2f}".format(u),',',pval)
u,pval = two_group_Mann_Whitney_test(sleep_tst_80s, sleep_tst_90s)
print("{:.2f}".format(u),',',pval)
u,pval = two_group_Mann_Whitney_test(sleep_tst_70s, sleep_tst_90s)
print("{:.2f}".format(u),',',pval)

def three_group_dunn_ttest(group_a, group_b,group_c):
    a = [item for sublist in group_a for item in sublist]
    b = [item for sublist in group_b for item in sublist]
    c = [item for sublist in group_c for item in sublist]
    data_a = pd.DataFrame({'age_group':'70s','para_value':a})
    data_b = pd.DataFrame({'age_group':'80s','para_value':b})
    data_c = pd.DataFrame({'age_group':'90s','para_value':c})
    data = data_a.append(data_b, ignore_index=True)
    data = data.append(data_c, ignore_index=True)
    test = posthoc_dunn(data,val_col='para_value', group_col='age_group')
    return test
t = three_group_dunn_ttest(mobility_data_70s, mobility_data_80s,mobility_data_90s)
post_hoc_dunn_result0= pd.DataFrame({'70VS80':t.iloc[0,1],'70VS90':t.iloc[0,2],
                                    '80VS90':t.iloc[1,2]},index=['mobility'])
t = three_group_dunn_ttest(sleep_tst_70s,sleep_tst_80s,sleep_tst_90s)
post_hoc_dunn_result1= pd.DataFrame({'70VS80':t.iloc[0,1],'70VS90':t.iloc[0,2],
                                    '80VS90':t.iloc[1,2]},index=['TST'])
t = three_group_dunn_ttest(sleep_sol_70s, sleep_sol_80s,sleep_sol_90s)
post_hoc_dunn_result2= pd.DataFrame({'70VS80':t.iloc[0,1],'70VS90':t.iloc[0,2],
                                    '80VS90':t.iloc[1,2]},index=['SOL'])
t= three_group_dunn_ttest(sleep_effi_70s, sleep_effi_80s,sleep_effi_90s)
post_hoc_dunn_result3= pd.DataFrame({'70VS80':t.iloc[0,1],'70VS90':t.iloc[0,2],
                                    '80VS90':t.iloc[1,2]},index=['SE'])
t = three_group_dunn_ttest(sleep_waso_70s,sleep_waso_80s,sleep_waso_90s)
post_hoc_dunn_result4= pd.DataFrame({'70VS80':t.iloc[0,1],'70VS90':t.iloc[0,2],
                                    '80VS90':t.iloc[1,2]},index=['WASO'])
t = three_group_dunn_ttest(sleep_duration_in_bed_70s,sleep_duration_in_bed_80s,sleep_duration_in_bed_90s)
post_hoc_dunn_result5= pd.DataFrame({'70VS80':t.iloc[0,1],'70VS90':t.iloc[0,2],
                                    '80VS90':t.iloc[1,2]},index=['TIB'])
t = three_group_dunn_ttest(sleep_awake_70s, sleep_awake_80s,sleep_awake_90s)
post_hoc_dunn_result6= pd.DataFrame({'70VS80':t.iloc[0,1],'70VS90':t.iloc[0,2],
                                    '80VS90':t.iloc[1,2]},index=['Awake'])

post_hoc_dunn_result = pd.concat([post_hoc_dunn_result1,post_hoc_dunn_result2,post_hoc_dunn_result3,
           post_hoc_dunn_result4,post_hoc_dunn_result5,post_hoc_dunn_result6], sort=False)    
print(post_hoc_dunn_result)

#--------------
# test 3 groups are different
def three_group_kruskal_ttest(group_a, group_b,group_c):
    a = [item for sublist in group_a for item in sublist]
    b = [item for sublist in group_b for item in sublist]
    c = [item for sublist in group_c for item in sublist]
    ttest,pval = stats.kruskal(a,b,c)
    return ttest,pval
t0,p0 = three_group_kruskal_ttest(mobility_data_70s, mobility_data_80s,mobility_data_90s)
print("{:.2f}".format(t0),',',p0)
t0,p0 = three_group_kruskal_ttest(sleep_tst_70s,sleep_tst_80s,sleep_tst_90s)
print("{:.2f}".format(t0),',',p0)
t0,p0 = three_group_kruskal_ttest(sleep_sol_70s, sleep_sol_80s,sleep_sol_90s)
print("{:.2f}".format(t0),',',p0)
t0,p0 = three_group_kruskal_ttest(sleep_effi_70s, sleep_effi_80s,sleep_effi_90s)
print("{:.2f}".format(t0),',',p0)
t0,p0 = three_group_kruskal_ttest(sleep_waso_70s,sleep_waso_80s,sleep_waso_90s)
print("{:.2f}".format(t0),',',p0)
t0,p0 = three_group_kruskal_ttest(sleep_duration_in_bed_70s,sleep_duration_in_bed_80s,sleep_duration_in_bed_90s)
print("{:.2f}".format(t0),',',p0)
t0,p0 = three_group_kruskal_ttest(sleep_awake_70s, sleep_awake_80s,sleep_awake_90s)
print("{:.2f}".format(t0),',',p0)

#--------------
mobility_data_70s_male = merge_data_mobility(selected_df_male_70s,reformed_sensor_list)
mobility_data_70s_female = merge_data_mobility(selected_df_female_70s,reformed_sensor_list)
mobility_data_80s_male = merge_data_mobility(selected_df_male_80s,reformed_sensor_list)
mobility_data_80s_female = merge_data_mobility(selected_df_female_80s,reformed_sensor_list)
mobility_data_90s_male = merge_data_mobility(selected_df_male_90s,reformed_sensor_list)
mobility_data_90s_female = merge_data_mobility(selected_df_female_90s,reformed_sensor_list)

kwargs = dict(alpha=0.5, bins=100)
plt.figure(figsize=(15,4))
plt.subplot(1,3,1)
plt.hist([item for sublist in mobility_data_70s_male for item in sublist],**kwargs, color='b', label='male 70s mobility')
plt.hist([item for sublist in mobility_data_70s_female for item in sublist],**kwargs, color='r', label='female 70s mobility')
plt.hist([item for sublist in mobility_data_70s for item in sublist],**kwargs, color='g', label='mixed gender 70s mobility')
plt.legend()
plt.subplot(1,3,2)
plt.hist([item for sublist in mobility_data_80s_male for item in sublist],**kwargs, color='b', label='male 80s mobility')
plt.hist([item for sublist in mobility_data_80s_female for item in sublist],**kwargs, color='r', label='female 80s mobility')
plt.hist([item for sublist in mobility_data_80s for item in sublist],**kwargs, color='g', label='mixed gender 80s mobility')
plt.legend()
plt.subplot(1,3,3)
plt.hist([item for sublist in mobility_data_90s_male for item in sublist],**kwargs, color='b', label='male 90s mobility')
plt.hist([item for sublist in mobility_data_90s_female for item in sublist],**kwargs, color='r', label='female 90s mobility')
plt.hist([item for sublist in mobility_data_90s for item in sublist],**kwargs, color='g', label='mixed gender 90s mobility')
plt.legend()

kwargs = dict(alpha=0.5, bins=100)
plt.figure(figsize=(6,12))
plt.subplot(3,1,1)
plt.hist([item for sublist in sleep_tst_70s for item in sublist],**kwargs, color='b', label='female 70s TST')
plt.hist([item for sublist in sleep_tst_90s for item in sublist],**kwargs, color='g', label='female 90s TST')
plt.legend()
plt.subplot(3,1,2)
plt.hist([item for sublist in sleep_duration_in_bed_70s for item in sublist],**kwargs, color='b', label='female 70s duration_in_bed')
plt.hist([item for sublist in sleep_duration_in_bed_90s for item in sublist],**kwargs, color='g', label='female 90s duration_in_bed')
plt.legend()
plt.subplot(3,1,3)
plt.hist([item for sublist in sleep_effi_70s for item in sublist],**kwargs, color='b', label='female 70s SE')
plt.hist([item for sublist in sleep_effi_90s for item in sublist],**kwargs, color='g', label='female 90s SE')
plt.legend()


#############################################################################
# get basic stats and tests
#############################################################################
def get_mean_and_std(group_a):
    a = np.asarray([item for sublist in group_a for item in sublist])
    avg = np.nanmean(a)
    std = np.nanstd(a)
    return avg,std

avg0,std0 = get_mean_and_std(mobility_data_90s)
print("{:.2f}".format(avg0),'±',"{:.2f}".format(std0))
avg1,std1 = get_mean_and_std(sleep_tst_70s)
print("{:.2f}".format(avg1),'±',"{:.2f}".format(std1))
avg2,std2 = get_mean_and_std(sleep_sol_70s)
print("{:.2f}".format(avg2),'±',"{:.2f}".format(std2))
avg3,std3 = get_mean_and_std(sleep_waso_70s)
print("{:.2f}".format(avg3),'±',"{:.2f}".format(std3))
avg4,std4 = get_mean_and_std(sleep_effi_70s)
print("{:.2f}".format(avg4),'±',"{:.3f}".format(std4))
#avg5,std5 = get_mean_and_std(sleep_exit_70s)
#print("{:.2f}".format(avg5),'±',"{:.3f}".format(std5))


avg1,std1 = get_mean_and_std(sleep_tst_80s)
print("{:.2f}".format(avg1),'±',"{:.2f}".format(std1))
avg2,std2 = get_mean_and_std(sleep_sol_80s)
print("{:.2f}".format(avg2),'±',"{:.2f}".format(std2))
avg3,std3 = get_mean_and_std(sleep_waso_80s)
print("{:.2f}".format(avg3),'±',"{:.2f}".format(std3))
avg4,std4 = get_mean_and_std(sleep_effi_80s)
print("{:.2f}".format(avg4),'±',"{:.3f}".format(std4))
#avg5,std5 = get_mean_and_std(sleep_exit_80s)
#print("{:.2f}".format(avg5),'±',"{:.3f}".format(std5))


avg1,std1 = get_mean_and_std(sleep_tst_90s)
print("{:.2f}".format(avg1),'±',"{:.2f}".format(std1))
avg2,std2 = get_mean_and_std(sleep_sol_90s)
print("{:.2f}".format(avg2),'±',"{:.2f}".format(std2))
avg3,std3 = get_mean_and_std(sleep_waso_90s)
print("{:.2f}".format(avg3),'±',"{:.2f}".format(std3))
avg4,std4 = get_mean_and_std(sleep_effi_90s)
print("{:.2f}".format(avg4),'±',"{:.3f}".format(std4))
#avg5,std5 = get_mean_and_std(sleep_exit_90s)
#print("{:.2f}".format(avg5),'±',"{:.3f}".format(std5))

#-----------
avg1,std1 = get_mean_and_std(sleep_tst_female)
print("{:.2f}".format(avg1),'±',"{:.2f}".format(std1))
avg2,std2 = get_mean_and_std(sleep_sol_female)
print("{:.2f}".format(avg2),'±',"{:.2f}".format(std2))
avg3,std3 = get_mean_and_std(sleep_waso_female)
print("{:.2f}".format(avg3),'±',"{:.2f}".format(std3))
avg4,std4 = get_mean_and_std(sleep_effi_female)
print("{:.2f}".format(avg4),'±',"{:.3f}".format(std4))
#avg5,std5 = get_mean_and_std(sleep_exit_female)
#print("{:.2f}".format(avg5),'±',"{:.3f}".format(std5))

avg1,std1 = get_mean_and_std(sleep_tst_male)
print("{:.2f}".format(avg1),'±',"{:.2f}".format(std1))
avg2,std2 = get_mean_and_std(sleep_sol_male)
print("{:.2f}".format(avg2),'±',"{:.2f}".format(std2))
avg3,std3 = get_mean_and_std(sleep_waso_male)
print("{:.2f}".format(avg3),'±',"{:.2f}".format(std3))
avg4,std4 = get_mean_and_std(sleep_effi_male)
print("{:.2f}".format(avg4),'±',"{:.3f}".format(std4))
#avg5,std5 = get_mean_and_std(sleep_exit_male)
#print("{:.2f}".format(avg5),'±',"{:.3f}".format(std5))



# Levene test for equal variances
def two_group_levene_ttest(group_a, group_b):
    a = [item for sublist in group_a for item in sublist]
    b = [item for sublist in group_b for item in sublist]
    ttest,pval = stats.levene(a,b)
    return ttest,pval
t0,p0 = two_group_levene_ttest(mobility_data_male, mobility_data_female)
print("{:.2f}".format(t0),',',p0)


#  Shapiro-Wilk test for normal distribution
def two_group_normality_ttest(group_a):
    a = [item for sublist in group_a for item in sublist]
    a_new = [value for value in a if not math.isnan(value)]
    w,p = stats.shapiro(a_new)
    return w,p
w,p = two_group_normality_ttest(mobility_data_female)
print("{:.2f}".format(w),p)


t1,p1 = three_group_kruskal_ttest(sleep_tst_70s,sleep_tst_80s,sleep_tst_90s)
print("{:.2f}".format(t1),',',p1)
t2,p2 = three_group_kruskal_ttest(sleep_sol_70s, sleep_sol_80s,sleep_sol_90s)
print("{:.2f}".format(t2),',',p2)
t3,p3 = three_group_kruskal_ttest(sleep_waso_70s,sleep_waso_80s,sleep_waso_90s)
print("{:.2f}".format(t3),',',p3)
t4,p4 = three_group_kruskal_ttest(sleep_effi_70s, sleep_effi_80s,sleep_effi_90s)
print("{:.2f}".format(t4),',',p4)


#############################################################################
# get hist plots and one way ANOVA
#############################################################################
kwargs = dict(alpha=0.5, bins=100)
label_70s='70s both gender'
label_80s = '80s both gender'
label_90s = '90s both gender'

plt.figure(figsize=(20,4))
plt.subplot(1,5,1)
plt.hist([item for sublist in mobility_data_70s for item in sublist],**kwargs, color='r', label=label_70s)
plt.hist([item for sublist in mobility_data_80s for item in sublist],**kwargs, color='b', label=label_80s)
plt.hist([item for sublist in mobility_data_90s for item in sublist],**kwargs, color='g', label=label_90s)
plt.legend();plt.title('mobility')
plt.subplot(1,5,2)
plt.hist([item for sublist in sleep_tst_70s for item in sublist],**kwargs, color='r', label=label_70s)
plt.hist([item for sublist in sleep_tst_80s for item in sublist],**kwargs, color='b', label=label_80s)
plt.hist([item for sublist in sleep_tst_90s for item in sublist],**kwargs, color='g', label=label_90s)
plt.legend();plt.title('TST')
plt.subplot(1,5,3)
plt.hist([item for sublist in sleep_sol_70s for item in sublist],**kwargs, color='r', label=label_70s)
plt.hist([item for sublist in sleep_sol_80s for item in sublist],**kwargs, color='b', label=label_80s)
plt.hist([item for sublist in sleep_sol_90s for item in sublist],**kwargs, color='g', label=label_90s)
plt.legend();plt.title('SOL')
plt.subplot(1,5,4)
plt.hist([item for sublist in sleep_waso_70s for item in sublist],**kwargs, color='r', label=label_70s)
plt.hist([item for sublist in sleep_waso_80s for item in sublist],**kwargs, color='b', label=label_80s)
plt.hist([item for sublist in sleep_waso_90s for item in sublist],**kwargs, color='g', label=label_90s)
plt.legend();plt.title('WASO')
plt.subplot(1,5,5)
plt.hist([item for sublist in sleep_effi_70s for item in sublist],**kwargs, color='r', label=label_70s)
plt.hist([item for sublist in sleep_effi_80s for item in sublist],**kwargs, color='b', label=label_80s)
plt.hist([item for sublist in sleep_effi_90s for item in sublist],**kwargs, color='g', label=label_90s)
plt.legend();plt.title('SE')


from statsmodels.stats.multicomp import MultiComparison
from statsmodels.formula.api import ols
from statsmodels.stats.anova import anova_lm

def get_df_for_three_group(group_a,group_b,group_c):
    a = [item for sublist in group_a for item in sublist]
    a_new = [value for value in a if not math.isnan(value)]
    b = [item for sublist in group_b for item in sublist]
    b_new = [value for value in b if not math.isnan(value)]
    c = [item for sublist in group_c for item in sublist]
    c_new = [value for value in c if not math.isnan(value)]
    data_a = pd.DataFrame({'age_group':'70s','para_value':a_new})
    data_b = pd.DataFrame({'age_group':'80s','para_value':b_new})
    data_c = pd.DataFrame({'age_group':'90s','para_value':c_new})
    data = data_a.append(data_b, ignore_index=True)
    data = data.append(data_c, ignore_index=True)
    return data

mobility_data_all_age = get_df_for_three_group(mobility_data_70s,mobility_data_80s,mobility_data_90s)
sleep_tst_data_all_age = get_df_for_three_group(sleep_tst_70s,sleep_tst_80s,sleep_tst_90s)
sleep_sol_data_all_age = get_df_for_three_group(sleep_sol_70s,sleep_sol_80s,sleep_sol_90s)
sleep_waso_data_all_age = get_df_for_three_group(sleep_waso_70s,sleep_waso_80s,sleep_waso_90s)
sleep_effi_data_all_age = get_df_for_three_group(sleep_effi_70s,sleep_effi_80s,sleep_effi_90s)

#=================================================
data = sleep_effi_data_all_age
linea_model = ols('para_value ~ age_group', data = data).fit()
anovat = anova_lm(linea_model)
print(anovat)

data = sleep_effi_data_all_age
MultiComp = MultiComparison(data['para_value'], data['age_group'])
comp = MultiComp.allpairtest(stats.ttest_ind, method='Holm')
print (comp[0])

'''
# another way to do one way ANOVA
f, p = stats.f_oneway(data[data['age_group'] == '70s'].para_value,
                      data[data['age_group'] == '80s'].para_value,
                      data[data['age_group'] == '90s'].para_value)
 
print ('One-way ANOVA')
print ('=============')
 
print ('F value:', f)
print ('P value:', p, '\n')
'''

#############################################################################
# Correlation analysis
#############################################################################
# male VS female
mobility_male = merge_data_mobility(selected_df_90s,reformed_sensor_list)
sleep_tst_male = merge_data_sleep_para(selected_df_90s,temp_sleep_duration)
sleep_sol_male = merge_data_sleep_para(selected_df_90s,temp_sleep_onset_duration)
sleep_se_male = merge_data_sleep_para(selected_df_90s,temp_sleep_efficiency)
sleep_waso_male = merge_data_sleep_para(selected_df_90s,temp_waso)

mobility_female = merge_data_mobility(selected_df_female,reformed_sensor_list)
sleep_tst_female = merge_data_sleep_para(selected_df_female,temp_sleep_duration)
sleep_sol_female = merge_data_sleep_para(selected_df_female,temp_sleep_onset_duration)
sleep_se_female = merge_data_sleep_para(selected_df_female,temp_sleep_efficiency)
sleep_waso_female = merge_data_sleep_para(selected_df_female,temp_waso)

def flat_list_of_lists(mob):
    new_list = [item for sublist in mob for item in sublist]
    return new_list

def get_merged_df(mob,tst,sol,waso,se):
    # each input is a list of lists
    df =pd.DataFrame({'mobility':flat_list_of_lists(mob),'TST':flat_list_of_lists(tst),
                  'SOL':flat_list_of_lists(sol),'WASO':flat_list_of_lists(waso),
                  'SE':flat_list_of_lists(se)})   
    return df

male_df = get_merged_df(mobility_male,sleep_tst_male,sleep_sol_male,
                        sleep_waso_male,sleep_se_male)
female_df = get_merged_df(mobility_female,sleep_tst_female,sleep_sol_female,
                        sleep_waso_female,sleep_se_female)



# https://heartbeat.fritz.ai/seaborn-heatmaps-13-ways-to-customize-correlation-matrix-visualizations-f1c49c816f07
fig, ax = plt.subplots(figsize=(6,6))
sns.heatmap(male_df.corr(method='pearson'), annot = True, cbar=False, ax=ax,fmt='.2g',
            center= 0, cmap= 'coolwarm', linewidths=1, linecolor='black',square=True)
plt.show()
