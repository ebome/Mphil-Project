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
import merge_sensors as ms # make sure they are in same dir, run ms first
from datetime import datetime

from sklearn import linear_model
from sklearn.model_selection import cross_val_score, cross_val_predict
from sklearn import metrics
from apyori import apriori
###################################################
# Sleep summary data: just use csv file
###################################################
dacs_all_sleep = pd.read_csv(r'D:\data\sleep_data_up_to_Nov.csv')

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
# Motion sensor to transition
###################################################
data = pd.read_csv(r'D:\data\sensor_data_up_to_Nov.csv')

#------------------------------------------------
# remove the features that are not needed
motion_data = data.drop(columns=['Unnamed: 0','room_id','sensor_type','timestamp'])
# remove "chair" since this is for tranfer in ADL
motion_data = motion_data[~motion_data['sensor_name'].str.contains('Chair')]

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
# Remove non-solitary users from sensor and mobility data 
solitary_dacs_sleep = dacs_all_sleep[dacs_all_sleep['PID'].isin(solitary_users)]
solitary_dacs_sensor = motion_data[motion_data['PID'].isin(solitary_users)]

# Check if PID in sleep is same as motion
sleep_pid = solitary_dacs_sleep['PID'].unique().tolist()
motion_pid = solitary_dacs_sensor['PID'].unique().tolist()

# for users not in motion_pid, we have to find them
user_not_in_motion_pid = [elem for elem in motion_pid if elem not in sleep_pid]
# remove these users from motion data
solitary_dacs_sensor = solitary_dacs_sensor[~solitary_dacs_sensor['PID'].isin(user_not_in_motion_pid)]

###################################################
# Group sleep and motion sensor
###################################################
# Delete the '0' signal in sensors, change the dataframe
def reform_df(MotionData_ila):
    MotionData_ila['sensor_value'] = pd.to_numeric(MotionData_ila['sensor_value'])
    MotionData_ila = MotionData_ila[MotionData_ila['sensor_value'] == 1]
    room_list = MotionData_ila['sensor_name'].unique().tolist()
    # the original sensor id are too complicated, change them to 0,1,2,...
    sensor_id = list(range(len(room_list)))

    allRooms = MotionData_ila['sensor_name'].values.tolist()
    temp=[]
    for i in range(len(allRooms)):
        for j in range(len(room_list)):
            if allRooms[i]==room_list[j]:
                temp.append(sensor_id[j])
            
    MotionData_ila['new_sensor_id'] = temp
    
    # up to this step, we have get the dataframe, but don't forget to convert to time object
    datetime_list = []
    time_list = MotionData_ila["local_timestamp"].values.tolist()
    for elt in time_list:
        elt = elt[0:19] # trim milli seconds
        aa = dt.datetime.strptime(elt, '%Y-%m-%d %H:%M:%S')
        datetime_list.append(aa)
    MotionData_ila['exact_time'] = time_list         
    
    # Sort the datetime 
    aaa = MotionData_ila.sort_values(by="exact_time") 
    return aaa

sensor_grouped_list = list(solitary_dacs_sensor.groupby(['PID']))
reformed_sensor_list_temp=[]
for each_PID in sensor_grouped_list:
    PID_motiondata = each_PID[1]
    reformed_each_df = reform_df(PID_motiondata)
    reformed_sensor_list_temp.append(reformed_each_df)

#-------------------------------------------------
# get users in sleep data
sleep_grouped_list = list(solitary_dacs_sleep.groupby(['PID']))
reformed_sleep_list_temp=[]
for each_PID in sleep_grouped_list:
    reformed_sleep_list_temp.append(each_PID[1])
  
#-------------------------------------------------
# add a bdebugging function to compare whether PID in motion and
# sleep are the same   
user_list_sleep=[];user_list_sensor=[]
for i in range(len(reformed_sensor_list_temp)):
    user_list_sleep.append(reformed_sleep_list_temp[i]['PID'].tolist()[0])
    user_list_sensor.append(reformed_sensor_list_temp[i]['PID'].tolist()[0])
    
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
# Get the num of room transition
#############################################################################
# Remove 'repetitive sensor'， this function only keeps the first record
def remove_dup_df(motion_data):
    # drop the duplicates in sensor_id
    drop_dup_df = motion_data.loc[(motion_data['sensor_id'].shift() != motion_data['sensor_id'])]
    return drop_dup_df
#----------------------------------------------------------------------------- 
sensor_list=[]
for each_PID in reformed_sensor_list_temp:
    cleaned_each_df = remove_dup_df(each_PID)
    sensor_list.append(cleaned_each_df)

#-----------------------------------------------------------------------------  
# get daily room transition

# find maximal and minimal snesors
max_rooms=0
min_rooms=len(sensor_list[0]['new_sensor_id'].unique().tolist())
for each_user in sensor_list:
    test_user_room_list = each_user['new_sensor_id'].unique().tolist()
    if len(test_user_room_list) >= max_rooms:
        max_rooms = len(test_user_room_list)
    if len(test_user_room_list) < min_rooms:
        min_rooms = len(test_user_room_list)
# now we know max_room=10, min_room=7

'''
If we check each PID dataframe, we will realize that some sensors are removed
For example, originally there are 8 sensors (0-7), now after removing there are 
5 sensors(0,2,4,6,7), so we would better change the sensor names to 0-4
'''    
def change_sensor_name(MotionData_ila):
    room_list = MotionData_ila['sensor_name'].unique().tolist()
    # the original sensor id are too complicated, change them to 0,1,2,...
    sensor_id = list(range(len(room_list)))
    allRooms = MotionData_ila['sensor_name'].values.tolist()
    temp=[]
    for i in range(len(allRooms)):
        for j in range(len(room_list)):
            if allRooms[i]==room_list[j]:
                temp.append(sensor_id[j])
            
    MotionData_ila['changed_sensor_id'] = temp
    return MotionData_ila

finally_sensor_list=[]
for test_user in sensor_list:
    user_sensor_reading = change_sensor_name(test_user)
    finally_sensor_list.append(user_sensor_reading)
#-----------------------------------------------------------------------------  

def labels_between_room(cleaned_ila):
    tempDF = pd.DataFrame({})
    temp1=[]
    for i in range(0, len(cleaned_ila)-1):
        room_previous_sensor = cleaned_ila.iloc[i]['changed_sensor_id'] 
        room_next_sensor =  cleaned_ila.iloc[i+1]['changed_sensor_id']
        label = str(int(room_previous_sensor))+' to '+str(int(room_next_sensor)) 
        temp1.append(label)
    tempDF['label'] = temp1
    return tempDF

# Chopped datetime       
base = dt.datetime.strptime('2019-01-01 00:00:00', '%Y-%m-%d %H:%M:%S')
datelist = pd.date_range(base, periods=700).tolist()
choppedTime=[]
for elt in datelist:
    strg = f'{elt:%Y-%m-%d %H:%M:%S}'
    choppedTime.append(strg)
start_time = choppedTime[0]
end_time = choppedTime[-1]

# get_transition_arrays will give daily transition numbers
def get_transition_arrays(cleaned_ila,choppedTime):
    # count how many rooms in this user's house
    room_num = len(cleaned_ila['changed_sensor_id'].unique().tolist())
    # print(room_num)
    transition=[]; date_list=[]
    
    first_date_in_cleaned_ila = cleaned_ila['local_timestamp'].tolist()[0]
    last_date_in_cleaned_ila = cleaned_ila['local_timestamp'].tolist()[-1]
    for i in range(len(choppedTime)-1):
        # get daily motion data
        choppedila_day  = cleaned_ila[cleaned_ila['local_timestamp'] > choppedTime[i]]
        choppedila_day  = choppedila_day[choppedila_day['local_timestamp'] < choppedTime[i+1]]
               
        # choppedTime start  4-26, hence the choppedila_day is length 0 before the start date
        if first_date_in_cleaned_ila > choppedTime[i+1] or last_date_in_cleaned_ila < choppedTime[i]:
            continue
        # if there is one day missing, just let it go
        if len(choppedila_day)==0:
            continue
        
        # label the transitions and change them to merged transition labels
        ila_lablled = labels_between_room(choppedila_day)
        if room_num == 5:
            merge_labelled_ilaList = ms.merge_5_sensors(ila_lablled)
        if room_num == 6:
            merge_labelled_ilaList = ms.merge_6_sensors(ila_lablled)
        if room_num == 7:
            merge_labelled_ilaList = ms.merge_7_sensors(ila_lablled)
        if room_num == 8:
            merge_labelled_ilaList = ms.merge_8_sensors(ila_lablled)
        if room_num == 9:
            merge_labelled_ilaList = ms.merge_9_sensors(ila_lablled)
        if room_num == 10:
            merge_labelled_ilaList = ms.merge_10_sensors(ila_lablled)
        transition.append(len(merge_labelled_ilaList))
        
        date_of_computed = choppedila_day['local_timestamp'].tolist()[0][0:10]
        sensor_date = dt.datetime.strptime(date_of_computed, '%Y-%m-%d')
        date_list.append(sensor_date)
        
        num_of_transition = pd.DataFrame({'date':date_list, 'num_of_transition':transition})
    
    return num_of_transition


### LONG COMPUTING TIME!
users_transition=[]
for each_user in finally_sensor_list:
    single_user_transition = get_transition_arrays(each_user,choppedTime)
    users_transition.append(single_user_transition) 

#flat_transition = [item for sublist in users_transition for item in sublist]
#print('flat_transition = ',  len(flat_transition))

length=[]
for each_user in users_transition:
    length.append(len(each_user))

kwargs = dict(bins=8,color='#BCC3EB',edgecolor='black', linewidth=1.2)
label_font_args = dict(fontsize=10, family='Times New Roman')
axis_font_args = dict(fontsize=12, family='Times New Roman')
plt.figure(figsize =(8,5))
plt.subplot(2,2,1)
plt.xlabel('44 People''s Valid days',**axis_font_args)
plt.ylabel('Number of apperance',**axis_font_args)
plt.xticks(**label_font_args);plt.yticks(**label_font_args)
plt.hist(length,**kwargs) 
plt.title('histogram of valid days')

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

# treat sleep start time within 7pm-6am as the same day sleep    
reformed_sleep_list_no_repetitive=[] 
for each_user_sleep in reformed_sleep_list_no_nap:
    start_sleep_aaaa = each_user_sleep['start_sleep_time'].tolist()
    # create the non-repetitive list, each date means sleep starts from that date's night
    start_sleep_dates = [] 
    for a in start_sleep_aaaa:
        time_division_today = dt.datetime(a.year,a.month,a.day,23,59,59)
        time_division_tmr = dt.datetime(a.year,a.month,a.day,0,0,0)
        time_division_7pm = dt.datetime(a.year,a.month,a.day,19,0,0)
        time_division_6am = dt.datetime(a.year,a.month,a.day,6,0,0)
        if a < time_division_today and a>=time_division_7pm:
            each_sleep_date = a.date()
            start_sleep_dates.append(each_sleep_date)
        if a >= time_division_tmr and a<=time_division_6am:
            each_sleep_date = a.date() - timedelta(days=1)
            start_sleep_dates.append(each_sleep_date)

    each_user_sleep['date_for_this_sleep'] = start_sleep_dates
    reformed_sleep_list_no_repetitive.append(each_user_sleep)   


###################################################
# Match sleep and motion sensor on the dates
###################################################
# Same, for each unit in reformed_sleep_list_with_no_repetitive and users_transition,remove the 
# dates that in reformed_sleep_list_with_no_nap but not in users_transition
reformed_sleep_list = [];reformed_sensor_list = []
for i in range(len(users_transition)):
    # add the day as index of mobility
    each_PID_mobility = users_transition[i]
    each_PID_mobility['start_day_trucated'] = [each_day.date() for each_day in each_PID_mobility['date'].tolist()] 
    # add the day as index of sleep, change the consecutive cells with reptitive day
    each_PID_sleep = reformed_sleep_list_no_repetitive[i]

    # match the days
    # mobility should within dates of sleep
    each_PID_mobility_reformed = each_PID_mobility[each_PID_mobility['start_day_trucated'].isin(each_PID_sleep['date_for_this_sleep'].tolist())]
    # sleep should within dates of mobility
    each_PID_sleep_reformed = each_PID_sleep[each_PID_sleep['date_for_this_sleep'].isin(each_PID_mobility_reformed['start_day_trucated'].tolist())]

    reformed_sensor_list.append(each_PID_mobility_reformed)
    reformed_sleep_list.append(each_PID_sleep_reformed)

# get list debugged
reformed_sleep_list_length = [len(x) for x in reformed_sleep_list]
reformed_sensor_list_length = [len(x) for x in reformed_sensor_list]
are_length_same = debugging_two_temp_list_value(reformed_sleep_list_length,reformed_sensor_list_length)

#############################################################################
# CODE age and gender into each user
#############################################################################
# from users get their ages
user_gender = pd.read_csv(r'D:\Sensor_Data_Processing\gender_label\survey_labels.csv')
user_list_sleep=[]
for i in range(len(reformed_sleep_list_no_nap)):
    user_list_sleep.append(reformed_sleep_list_no_nap[i]['PID'].tolist()[0])
user_gender = user_gender[user_gender['record_id'].isin(user_list_sleep)]
#--------------------
# the age should be start of trial, that's how longitudinal study does
time_list = user_gender["date_of_birth"].values.tolist()
birthday = [dt.datetime.strptime(x, '%Y-%m-%d').date() for x in time_list]

start_trail_date=[]
for each_user in reformed_sleep_list:
    start_trail_date.append(each_user['date_for_this_sleep'].tolist()[0])

age_list =[(x1 - x2)//dt.timedelta(days=365.2425) for (x1, x2) in zip(start_trail_date, birthday)]
user_gender['age'] = age_list 
#--------------------
user_gender = user_gender.sort_values(by=['record_id']).reset_index()
user_gender['home_care_package_level'].loc[(user_gender['home_care_package_level']==6)] = 1
# add mental score to user_gender
user_mental_score = pd.read_csv(r'D:\Sensor_Data_Processing\gender_label\eq5d_and_mood_and_mental_scores.csv')
user_mental_score = user_mental_score[user_mental_score['PID'].isin(user_gender['record_id'].tolist())]
user_gender = user_gender.merge(user_mental_score,left_on='record_id',right_on='PID', 
     how = 'inner')[['record_id', 'living_area', 'home_care_package_level', 'gender',
                     'age','ATSM']]
user_gender = user_gender[user_gender['home_care_package_level']<4]
user_gender['ATSM'] = [int(x) for x in user_gender['ATSM'].tolist()]

# removed users that has mental score < 5
user_gender = user_gender[user_gender['ATSM']>=7]

#############################################################################
# Sleep parameter selection
#############################################################################
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
#temp_sleep_bedexit = get_temp_sleep_parameter(reformed_sleep_list,'bed_exit_duration(min)')
#temp_sleep_ttc = get_temp_sleep_parameter(reformed_sleep_list,'toss_turn_count')
temp_sleep_avg_hr = get_temp_sleep_parameter(reformed_sleep_list,'avg_hr')
temp_sleep_avg_rr = get_temp_sleep_parameter(reformed_sleep_list,'avg_rr')
#temp_sleep_awakeCount = get_temp_sleep_parameter(reformed_sleep_list,'awake_count')
#temp_sleep_exitCount = get_temp_sleep_parameter(reformed_sleep_list,'bed_exit_count')

   

flat_sleep_duration = [item for sublist in temp_sleep_duration for item in sublist]
print('flat_sleep_duration = ', len(flat_sleep_duration))
    
list(map(tuple, np.where( np.isnan( np.asarray(flat_sleep_duration) ) )))

avg_of_sleep_duration = np.mean(np.asarray(flat_sleep_duration))
print('avg_of_sleep_days =',avg_of_sleep_duration)

#-----------------------------------------
# Visualization of motion/sleep
def moving_average(a, n=3) :
    ret = np.cumsum(a, dtype=float)
    ret[n:] = ret[n:] - ret[:-n]
    return ret[n - 1:] / n


user_index=27
dates = list(range(len(reformed_sensor_list[user_index]['num_of_transition'])))
x_labels_all = [date.strftime('%Y-%m-%d') for date in reformed_sensor_list[user_index]['date'].tolist()]
x_labels = x_labels_all[0:len(dates):10]
xInput = list(range(0,len(dates),10))

plt.figure(figsize=(12,10))
plt.subplot(4,2,1)
plt.plot(reformed_sensor_list[user_index]['num_of_transition'].tolist(),
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
plt.xlabel("dates")
plt.xticks(xInput,x_labels, rotation='vertical')


# see if they have any linear relationship by scatter plots
plt.figure(figsize=(12,12))
plt.subplot(2,2,1)
plt.scatter(reformed_sensor_list[user_index]['num_of_transition'].tolist(), temp_sleep_duration[user_index])
plt.xlabel('mobility');plt.ylabel('total sleep duration (hour)')
plt.subplot(2,2,2)
plt.scatter(reformed_sensor_list[user_index]['num_of_transition'].tolist(), temp_sleep_efficiency[user_index])
plt.xlabel('mobility');plt.ylabel('sleep efficiency')
plt.subplot(2,2,3)
plt.scatter(reformed_sensor_list[user_index]['num_of_transition'].tolist(), temp_sleep_onset_duration[user_index])
plt.xlabel('mobility');plt.ylabel('sleep onset duration (minute)')
plt.subplot(2,2,4)
plt.scatter(reformed_sensor_list[user_index]['num_of_transition'].tolist(), temp_waso[user_index])
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
    mobility = reformed_sensor_list[i][['start_day_trucated','num_of_transition']]
    sleep_features = reformed_sleep_list[i][['PID','start_sleep_time','finish_sleep_time',
                                        'TST(hour)','WASO(min)','SOL(min)','SE',
                                        'duraion_in_bed','toss_turn_count','avg_hr','avg_rr',
                                        'awake_count','bed_exit_count','bed_exit_duration(min)']]
    mobility.reset_index(drop=True, inplace=True)
    sleep_features.reset_index(drop=True, inplace=True)
    merged_df = pd.concat([mobility, sleep_features],axis=1)
    final_big_df = pd.concat([final_big_df,merged_df])

'''
9926 rows for 45 people, 8487 rows for 37 people
'''

# remove the unwanted people
user_gender_37_people = user_gender['record_id'].tolist()  
final_big_df = final_big_df[final_big_df['PID'].isin(user_gender_37_people)]
# add gender and age into the df
final_big_df = final_big_df.merge(user_gender, left_on='PID',right_on='record_id',how = 'inner')
# remove NaN values if ANY row contains it
final_big_df = final_big_df.dropna(axis=0, how='any')
print(len(final_big_df))


'''
#======================================
# split final_big_df by time intervals
before_covid = final_big_df[final_big_df['start_day_trucated']<dt.date(year=2020,month=3,day=1)]
during_covid = final_big_df[final_big_df['start_day_trucated']>=dt.date(year=2020,month=3,day=1)]
during_covid = during_covid[during_covid['start_day_trucated']<dt.date(year=2020,month=6,day=1)]
after_covid = final_big_df[final_big_df['start_day_trucated']>=dt.date(year=2020,month=6,day=1)]

# split each timeintervals into different group: 70/80/90, female, male
# we can diretly run Dunn's test on three groups: 70/80/90
# and Mann-Whitney test on 2 groups: female, male

def three_group_dunn_ttest(group_a, group_b,group_c,para_to_test):
    a = group_a[para_to_test].tolist()
    b = group_b[para_to_test].tolist()
    c = group_c[para_to_test].tolist()
    data_a = pd.DataFrame({'age_group':'1before','para_value':a})
    data_b = pd.DataFrame({'age_group':'2during','para_value':b})
    data_c = pd.DataFrame({'age_group':'3after','para_value':c})
    data = data_a.append(data_b, ignore_index=True)
    data = data.append(data_c, ignore_index=True)
    test = posthoc_dunn(data,val_col='para_value', group_col='age_group')
    return test

# before_covid  during_covid  after_covid
para_to_test = 'SE'
group_70s_before = before_covid[(before_covid['age']>=70) & (before_covid['age']<80)]
group_70s_during = during_covid[(during_covid['age']>=70) & (during_covid['age']<80)]
group_70s_after = after_covid[(after_covid['age']>=70) & (after_covid['age']<80)]

group_80s_before = before_covid[(before_covid['age']>=80) & (before_covid['age']<90)]
group_80s_during = during_covid[(during_covid['age']>=80) & (during_covid['age']<90)]
group_80s_after = after_covid[(after_covid['age']>=80) & (after_covid['age']<90)]

group_90s_before = before_covid[(before_covid['age']>=90)]
group_90s_during = during_covid[(during_covid['age']>=90)]
group_90s_after = after_covid[(after_covid['age']>=90)]


t = three_group_dunn_ttest(group_80s_before, group_80s_during,group_80s_after,para_to_test)
print(t)

#----------------------
def two_group_Mann_Whitney_test(group_a, group_b, para_to_test):
    a = group_a[para_to_test].tolist()
    b = group_b[para_to_test].tolist()
    u,pval = stats.mannwhitneyu(a,b)
    return u,pval

# before_covid  during_covid  after_covid
# sleep_features = 'num_of_transition','TST(hour)','WASO(min)','SOL(min)','SE',
# 'duraion_in_bed','toss_turn_count','avg_hr','avg_rr','awake_count','bed_exit_count'
para_to_test = 'SE'
group_male_before = before_covid[before_covid['gender']==1]
group_male_during = during_covid[during_covid['gender']==1]
group_male_after = after_covid[after_covid['gender']==1]

group_female_before = before_covid[before_covid['gender']==2]
group_female_during = during_covid[during_covid['gender']==1]
group_female_after = after_covid[after_covid['gender']==1]

t = three_group_dunn_ttest(group_female_before, group_female_during,group_female_after,para_to_test)
print('pval=',t)

'''
######################################################
# Multivariate regression
#df = final_big_df[['PID','start_day_trucated','num_of_transition','PID','TST(hour)','WASO(min)','SOL(min)',
#                    'SE','duration_in_bed','toss_turn_count','avg_hr','avg_rr','awake_count',
#                    'bed_exit_count','bed_exit_duration','age','gender','ATSM']]

df = final_big_df[['PID','start_day_trucated','num_of_transition','PID','TST(hour)','WASO(min)','SOL(min)',
                    'SE','duration_in_bed','toss_turn_count','avg_hr','avg_rr','awake_count',
                    'bed_exit_count','bed_exit_duration','age','gender','ATSM']]

#df.to_excel(r'D:\Meeting Updates\sleep_mob_39_users.xlsx')

#############################################################################
# Samplping of data
#############################################################################
df = final_big_df[['PID','start_day_trucated','num_of_transition','PID','TST(hour)','WASO(min)','SOL(min)',
                    'SE','duraion_in_bed','toss_turn_count','avg_hr','avg_rr','awake_count',
                    'bed_exit_count','bed_exit_duration','age','gender','ATSM']]
# group by individuals
a = list(df.groupby(['PID']))
temp_store=[]
for each in a:
    temp_store.append(each[1])

#------------------------------
# Baseline
# use mob(d) to predict mob(d+1)
each_user_sampled_list =[]
for each_user in temp_store:
    each_user_mob_day_d = each_user.iloc[list(range(0,len(each_user)-1)),[2]]
    each_user_mob_day_d_1 = each_user.iloc[list(range(1,len(each_user))),[2]]
    each_user_mob_day_d.reset_index(drop=True, inplace=True)
    each_user_mob_day_d_1.reset_index(drop=True, inplace=True)
    each_user_sampled = pd.concat([each_user_mob_day_d, each_user_mob_day_d_1], axis=1,ignore_index=True)
    # up to this step, each_user_sampled miss the column name, so add columns name
    each_user_sampled.columns = ['mob(d)','mob(d+1)']
    each_user_sampled_list.append(each_user_sampled)

mobility_baseline=pd.DataFrame({})    
for each in each_user_sampled_list:
    each.reset_index(drop=True, inplace=True)
    mobility_baseline = pd.concat([mobility_baseline,each])

baseline_mae = metrics.mean_absolute_error(mobility_baseline['mob(d)'], mobility_baseline['mob(d+1)'])
print(baseline_mae)
baseline_r2 = metrics.r2_score(mobility_baseline['mob(d)'], mobility_baseline['mob(d+1)'])
print(baseline_r2)

#==============================
def get_sampling_dataset(temp_store_list,d):    
# d: d is the day after sleep, d=1 means mobility just after that day of sleep
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
sampled_df_day_4 = get_sampling_dataset(temp_store,5)
sampled_df_day_5 = get_sampling_dataset(temp_store,6)
sampled_df_day_6 = get_sampling_dataset(temp_store,7)

#==============================
'''
each_user = temp_store[7]
each_user_sleep = each_user.iloc[:,list(range(3,len(each_user.columns)))]
for c in each_user_sleep.columns:
    each_user_sleep[c] = each_user_sleep[c].rolling(5).mean()
each_user_sleep = each_user_sleep.iloc[list(range(4,len(each_user))),:]

each_user_mob = each_user.iloc[list(range(4,len(each_user))),[0,1,2]]

each_user_mob.reset_index(drop=True, inplace=True)
each_user_sleep.reset_index(drop=True, inplace=True)
each_user_sampled = pd.concat([each_user_mob, each_user_sleep], axis=1,ignore_index=True)
each_user_sampled.columns = each_user.columns
'''

def get_sampling_dataset_from_multiple_sleep_days(temp_store_list,d, sleep_window):    
# d: d is the day after sleep, d=1 means mobility just after that day of sleep
# sleep window: hoe many days of sleep will be averaged
    each_user_sampled_list =[]
    for each_user in temp_store_list:
        
        each_user_sleep = each_user.iloc[:,list(range(3,len(each_user.columns)))]
        for c in each_user_sleep.columns:
            each_user_sleep[c] = each_user_sleep[c].rolling(sleep_window).mean()
        each_user_sleep = each_user_sleep.iloc[list(range(sleep_window-1,len(each_user))),:]

        each_user_mob = each_user.iloc[list(range(sleep_window-1,len(each_user))),[0,1,2]]
        each_user_mob.reset_index(drop=True, inplace=True)
        each_user_sleep.reset_index(drop=True, inplace=True)
        each_user_sampled = pd.concat([each_user_mob, each_user_sleep], axis=1,ignore_index=True)
        
        # consider the window of mobility and sleep
        each_user_mob = each_user_sampled.iloc[list(range(d-1,len(each_user_sampled))),[0,1,2]]
        each_user_sleep = each_user_sampled.iloc[list(range(0,len(each_user_sampled)-d+1)),list(range(3,len(each_user.columns)))]
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

sampled_df_day_0 = get_sampling_dataset_from_multiple_sleep_days(temp_store,1,3)
sampled_df_day_1 = get_sampling_dataset_from_multiple_sleep_days(temp_store,2,3)
sampled_df_day_2 = get_sampling_dataset_from_multiple_sleep_days(temp_store,3,3)
sampled_df_day_3 = get_sampling_dataset_from_multiple_sleep_days(temp_store,4,3)
sampled_df_day_4 = get_sampling_dataset_from_multiple_sleep_days(temp_store,5,3)
sampled_df_day_5 = get_sampling_dataset_from_multiple_sleep_days(temp_store,6,3)
sampled_df_day_6 = get_sampling_dataset_from_multiple_sleep_days(temp_store,7,3)


#############################################################################
# Regression model
#############################################################################
# split train, test sets based on shuffle

df_big = [sampled_df_day_0,sampled_df_day_1,sampled_df_day_2,sampled_df_day_3,sampled_df_day_4,
      sampled_df_day_5,sampled_df_day_6]

mae=[];r_score=[]
for df in df_big:
    X = df.iloc[:,list(range(3,len(df.columns)))]
    Y_true = df['num_of_transition']
#    X_train, X_test, y_train, y_test = train_test_split(X, Y_true, test_size=0.2,random_state=42,shuffle=True)
    
    #====================
    # Fit a model
    lm = linear_model.LinearRegression()

    # 5 fold Cross validation
    scores = cross_val_score(lm, X, Y_true, cv=5)
#    print('Cross-validated scores:', scores)

    # Make cross validated predictions
    predictions = cross_val_predict(lm, X, Y_true, cv=5)

    accuracy = metrics.r2_score(Y_true, predictions)
    accuracy_mae = metrics.mean_absolute_error(Y_true, predictions)
    mae.append("{:.3f}".format(accuracy_mae))
    r_score.append("{:.5f}".format(accuracy))
    
#    print('Cross-Predicted Accuracy MAE:', "{:.3f}".format(accuracy_mae))
#    print('Cross-Predicted Accuracy R2:',"{:.5f}".format(accuracy))


#############################################################################
# SAX discratize mobility one by one
# https://github.com/nphoff/saxpy
# https://blog.csdn.net/Tony_Stark_Wang/article/details/88248701
#############################################################################
from SAX import SAX_trans # from a file import a class

# how many alphabets: 5
# how may j eqalluy sized intervals? Let make it equal to length now
#----------------------------
# label all mobility
ts = df['num_of_transition'].tolist()
x1 = SAX_trans(ts=ts,w=len(ts),alpha=5)
st1 = x1.to_sax()
sax_list = list(st1)
df['labelled_mobility'] = sax_list


#----------------------------
def convert_sax_to_word(sax_list_coverted_to_list):
    x2 = ['level_1' if x=='a' else x for x in sax_list_coverted_to_list]
    x3 = ['level_2' if x=='b' else x for x in x2]
    x4 = ['level_3' if x=='c' else x for x in x3]
    x5 = ['level_4' if x=='d' else x for x in x4]
    x = ['level_5' if x=='e' else x for x in x5]
    return x

# label individual mobility
labelled_mobility=[]
for each_user in temp_store:
#    w = len(each_user['num_of_transition'].tolist())
    w=16
    sax_representation_each_user = pd.DataFrame({})
    # label mobility
    ts = each_user['num_of_transition'].tolist()
    x0 = SAX_trans(ts=ts,w=w,alpha=5)
    sax_representation_each_user['labelled_mobility'] = convert_sax_to_word( list(x0.to_sax()) )

    # label sleep
    x1 = SAX_trans(ts=each_user['sleep_duration'].tolist(),w=w,alpha=5)
    sax_representation_each_user['labelled_tst'] = convert_sax_to_word( list(x1.to_sax()) )
    x2 = SAX_trans(ts=each_user['awake_duration'].tolist(),w=w,alpha=5)
    sax_representation_each_user['labelled_waso'] = convert_sax_to_word( list( x2.to_sax())  )
    x3 = SAX_trans(ts=each_user['sleep_onset_duration'].tolist(),w=w,alpha=5)
    sax_representation_each_user['labelled_sol'] = convert_sax_to_word( list( x3.to_sax() ) )
    x4 = SAX_trans(ts=each_user['sleep_efficiency'].tolist(),w=w,alpha=5)
    sax_representation_each_user['labelled_se'] = convert_sax_to_word( list( x4.to_sax() ) )
    x5 = SAX_trans(ts=each_user['toss_turn_count'].tolist(),w=w,alpha=5)
    sax_representation_each_user['labelled_ttc'] = convert_sax_to_word( list( x5.to_sax() ) )
    x6 = SAX_trans(ts=each_user['average_heart_rate'].tolist(),w=w,alpha=5)
    sax_representation_each_user['labelled_avg_hr'] = convert_sax_to_word( list( x6.to_sax() ) )
    x7 = SAX_trans(ts=each_user['average_respiration_rate'].tolist(),w=w,alpha=5)
    sax_representation_each_user['labelled_avg_rr'] = convert_sax_to_word( list( x7.to_sax() ) )
    x8 = SAX_trans(ts=each_user['awakenings'].tolist(),w=w,alpha=5)
    sax_representation_each_user['labelled_awake'] = convert_sax_to_word( list( x8.to_sax() ) )
    x9 = SAX_trans(ts=each_user['bed_exit_duration'].tolist(),w=w,alpha=5)
    sax_representation_each_user['labelled_ext'] = convert_sax_to_word( list( x9.to_sax() ) )
    
    labelled_mobility.append(sax_representation_each_user)


# select a user
user_df = labelled_mobility[30]
user_labelled_list = []
for (columnName, columnData) in user_df.iteritems():
    user_labelled_list.append(columnData.tolist())




# min_length parameter specifies the minimum number of items that you want in your rules
# Lift of greater than 1 means products A and B are more likely to be bought together. 
rules = list(apriori(transactions=user_labelled_list, min_support = 0.1, min_confidence = 0.3, min_lift =1 , min_length = 4))
for item in rules:
    # first index of the inner list
    # Contains base item and add item
    pair = item[0] 
    items = [x for x in pair]
    print("Rule: " + items[0] + " -> " + items[1])
    #second index of the inner list
    print("Support: " + str(item[1]))
    #third index of the list located at 0th
    #of the third index of the inner list
    print("Confidence: " + str(item[2][0][2]))
    print("Lift: " + str(item[2][0][3]))
    print("=====================================")










supports=[]
confidences=[]
lifts=[]
bases=[]
adds=[]
for r in rules:
    for x in r.ordered_statistics:
        supports.append(r.support)
        confidences.append(x.confidence)
        lifts.append(x.lift)
        bases.append(list(x.items_base))
        adds.append(list(x.items_add))

result = pd.DataFrame({
    'support':supports,
    'confidence':confidences,
    'lift':lifts,
    'base':bases,
    'add':adds
})
result = result[(result['base'].str.len() != 0)]


print('min_support>0.1, min_confidence> 0.3,', 'the number of rules we have:', result.shape[0])





















# merge to a big df
final_big_df_with_SAX=pd.DataFrame({})    
for each in labelled_mobility:
    final_big_df_with_SAX = pd.concat([final_big_df_with_SAX,each])
#final_big_df_with_SAX.to_excel(r'D:\Meeting Updates\sleep_mob_39_users_with_SAX_labelled.xlsx')

final_big_df_with_SAX = final_big_df_with_SAX.assign(num_of_transition=final_big_df_with_SAX['labelled_mobility'])
final_big_df_with_SAX = final_big_df_with_SAX.drop(columns=['labelled_mobility'])

#=======================
# now we can perform classification task: use model one to all SVM
from sklearn.multiclass import OneVsRestClassifier
from sklearn.svm import SVC

a = list(final_big_df_with_SAX.groupby(['PID']))
temp_sax_list=[]
for each in a:
    temp_sax_list.append(each[1])


#----------------------------
sampled_df_day_0 = get_sampling_dataset(temp_sax_list,3)

X = sampled_df_day_0.iloc[:,list(range(3,len(sampled_df_day_0.columns)))]
y = sampled_df_day_0['num_of_transition']

clf = OneVsRestClassifier(SVC()).fit(X, y)
scores = cross_val_score(clf, X, y, cv=5)
predictions = cross_val_predict(clf, X, y, cv=5)

precision_score = metrics.precision_score(y, predictions,average='macro')
f1_score = metrics.f1_score(y, predictions,average='macro')
print('Cross-Predicted precision_score:', "{:.3f}".format(precision_score))
print('Cross-Predicted f1_score:',"{:.5f}".format(f1_score))
 









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
       mobility_data.append(reformed_sensor_list[i]['num_of_transition'].values.tolist())
   return mobility_data

def merge_data_sleep_para(selected_df,sleep_para):
   sleep_para_data=[]
   for i in selected_df.index.tolist():
       sleep_para_data.append(sleep_para[i])
   return sleep_para_data

#--------------------------------------------
# for 2 group t test data
male_df = selected_df_male_80s
mobility_data_male = merge_data_mobility(male_df,reformed_sensor_list)
sleep_tst_male = merge_data_sleep_para(male_df,temp_sleep_duration)
sleep_sol_male = merge_data_sleep_para(male_df,temp_sleep_onset_duration)
sleep_effi_male = merge_data_sleep_para(male_df,temp_sleep_efficiency)
sleep_waso_male = merge_data_sleep_para(male_df,temp_waso)
sleep_duration_in_bed_male = merge_data_sleep_para(male_df,temp_sleep_duration_in_bed)
#sleep_exit_male= merge_data_sleep_para(male_df,temp_sleep_bedexit)
sleep_ttc_male = merge_data_sleep_para(male_df,temp_sleep_ttc)
sleep_avgHR_male = merge_data_sleep_para(male_df,temp_sleep_avg_hr)
sleep_avgRR_male = merge_data_sleep_para(male_df,temp_sleep_avg_rr)
sleep_awake_male = merge_data_sleep_para(male_df,temp_sleep_awakeCount)
sleep_exit_count_male= merge_data_sleep_para(male_df,temp_sleep_exitCount)
male=[mobility_data_male,sleep_tst_male,sleep_sol_male,sleep_effi_male,sleep_waso_male,
      sleep_duration_in_bed_male,sleep_ttc_male,sleep_avgHR_male,sleep_avgRR_male,sleep_awake_male,
      sleep_exit_count_male]

female_df = selected_df_female_80s
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
      sleep_duration_in_bed_female,sleep_ttc_female,sleep_avgHR_female,sleep_avgRR_female,
      sleep_awake_female,sleep_exit_count_female]

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
plt.xlabel('number of room transitions');plt.legend()
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
plt.hist([item for sublist in sleep_duration_in_bed_male for item in sublist],**kwargs, color=c1, label=male_label+' EXT')
plt.hist([item for sublist in sleep_duration_in_bed_female for item in sublist],**kwargs, color=c2, label=female_label+' EXT')
plt.xlabel('bed duration(min)');plt.legend()





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
#sleep_exit_70s = merge_data_sleep_para(fixed_gender,temp_sleep_bedexit)
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
#sleep_exit_80s = merge_data_sleep_para(fixed_gender,temp_sleep_bedexit)
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
#sleep_exit_90s = merge_data_sleep_para(fixed_gender,temp_sleep_bedexit)
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
print(t)
t = three_group_dunn_ttest(sleep_tst_70s,sleep_tst_80s,sleep_tst_90s)
print(t)
t = three_group_dunn_ttest(sleep_sol_70s, sleep_sol_80s,sleep_sol_90s)
print(t)
t= three_group_dunn_ttest(sleep_effi_70s, sleep_effi_80s,sleep_effi_90s)
print(t)
t = three_group_dunn_ttest(sleep_waso_70s,sleep_waso_80s,sleep_waso_90s)
print(t)
t = three_group_dunn_ttest(sleep_duration_in_bed_70s,sleep_duration_in_bed_80s,sleep_duration_in_bed_90s)
print(t)
#t = three_group_dunn_ttest(sleep_exit_70s, sleep_exit_80s,sleep_exit_90s)
#print(t)
t = three_group_dunn_ttest(sleep_ttc_70s, sleep_ttc_80s,sleep_ttc_90s)
print(t)
t = three_group_dunn_ttest(sleep_avgHR_70s, sleep_avgHR_80s,sleep_avgHR_90s)
print(t)
t = three_group_dunn_ttest(sleep_avgRR_70s, sleep_avgRR_80s,sleep_avgRR_90s)
print(t)
t = three_group_dunn_ttest(sleep_awake_70s, sleep_awake_80s,sleep_awake_90s)
print(t)
t = three_group_dunn_ttest(sleep_exit_count_70s, sleep_exit_count_80s,sleep_exit_count_90s)
print(t)

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
#t0,p0 = three_group_kruskal_ttest(sleep_exit_70s, sleep_exit_80s,sleep_exit_90s)
#print("{:.2f}".format(t0),',',p0)
t0,p0 = three_group_kruskal_ttest(sleep_ttc_70s, sleep_ttc_80s,sleep_ttc_90s)
print("{:.2f}".format(t0),',',p0)
t0,p0 = three_group_kruskal_ttest(sleep_avgHR_70s, sleep_avgHR_80s,sleep_avgHR_90s)
print("{:.2f}".format(t0),',',p0)
t0,p0 = three_group_kruskal_ttest(sleep_avgRR_70s, sleep_avgRR_80s,sleep_avgRR_90s)
print("{:.2f}".format(t0),',',p0)
t0,p0 = three_group_kruskal_ttest(sleep_awake_70s, sleep_awake_80s,sleep_awake_90s)
print("{:.2f}".format(t0),',',p0)
t0,p0 = three_group_kruskal_ttest(sleep_exit_count_70s, sleep_exit_count_80s,sleep_exit_count_90s)
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


#  Shapiro-Wilk test for equal variances
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
# Floor plan
#############################################################################
from collections import ChainMap

all_dacs_room_matrix = pd.read_csv(r'D:\Sensor_Data_Processing\floor_plan\DACS_Room_Distances.csv')
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
#    divisor = max(unit_matrix['distance'].tolist())
#    unit_matrix['distance'] = unit_matrix['distance']/divisor
    reformed_room_matrix_list_temp.append(unit_matrix_cleaned)
    room_matrix_users.append(unit_matrix_cleaned['PID'].tolist()[0])

reformed_room_matrix_df = pd.DataFrame({})
for each in reformed_room_matrix_list_temp:
    reformed_room_matrix_df = reformed_room_matrix_df.append(each)

user_gender_users = user_gender['record_id'].tolist()
# remove some users by find their index
missing_users_in_sensor = list(set(room_matrix_users) - set(user_gender_users))
reformed_room_matrix_df = reformed_room_matrix_df[~reformed_room_matrix_df['PID'].isin(missing_users_in_sensor)]

reformed_room_matrix_df.to_csv(r'D:\Sensor_Data_Processing\floor_plan\37_users_room_distances.csv')
# plot the distribution
plt.hist(reformed_room_matrix_df['distance']);plt.xlabel('room distance (steps)')

#############################################################################
# Correlation analysis - Ratio of outlier
#############################################################################


user_index=17


baseline_mobility=reformed_sensor_list[user_index]['num_of_transition'].tolist()[0:15]
baseline_mobility_lower = np.percentile(np.array(baseline_mobility),5)
baseline_mobility_upper = np.percentile(np.array(baseline_mobility),95)
sleep_tst_lower = 6;sleep_tst_upper = 9
sleep_sol_lower = 5;sleep_sol_upper = 31
sleep_waso_upper = 31

def get_num_of_outlier_days_with_2_bounds(lower_bound,upper_bound,this_user_list):
    count_lower = sum(elt < lower_bound for elt in this_user_list)
    count_upper = sum(elt > upper_bound for elt in this_user_list)
    return count_lower+count_upper

def get_num_of_outlier_days_with_upper_bounds(upper_bound,this_user_list):
    count_upper = sum(elt > upper_bound for elt in this_user_list)
    return count_upper

mobility_abnormal_days = get_num_of_outlier_days_with_2_bounds(baseline_mobility_lower,baseline_mobility_upper,reformed_sensor_list[user_index]['num_of_transition'].tolist())
tst_abnormal_days = get_num_of_outlier_days_with_2_bounds(sleep_tst_lower,sleep_tst_upper,temp_sleep_duration[user_index])
sol_abnormal_days = get_num_of_outlier_days_with_2_bounds(sleep_sol_lower,sleep_sol_upper,temp_sleep_onset_duration[user_index])
waso_abnormal_days = get_num_of_outlier_days_with_upper_bounds(sleep_waso_upper,temp_waso[user_index])

def get_ratio(abnormal_days, temp_this_user_list):
    return abnormal_days/len(temp_this_user_list)


all_user_ratio=pd.DataFrame({})
for user_index in range(len(reformed_sensor_list)): 
    # user_index = 0,1,2...
    baseline_mobility=reformed_sensor_list[user_index]['num_of_transition'].tolist()[0:15]
    baseline_mobility_lower = np.percentile(np.array(baseline_mobility),5)
    baseline_mobility_upper = np.percentile(np.array(baseline_mobility),95)
    sleep_tst_lower = 6;sleep_tst_upper = 9
    sleep_sol_lower = 5;sleep_sol_upper = 31
    sleep_waso_upper = 31
    
    mobility_abnormal_days = get_num_of_outlier_days_with_2_bounds(baseline_mobility_lower,baseline_mobility_upper,reformed_sensor_list[user_index]['num_of_transition'].tolist())
    tst_abnormal_days = get_num_of_outlier_days_with_2_bounds(sleep_tst_lower,sleep_tst_upper,temp_sleep_duration[user_index])
    sol_abnormal_days = get_num_of_outlier_days_with_2_bounds(sleep_sol_lower,sleep_sol_upper,temp_sleep_onset_duration[user_index])
    waso_abnormal_days = get_num_of_outlier_days_with_upper_bounds(sleep_waso_upper,temp_waso[user_index])


    mobility_ratio = get_ratio(mobility_abnormal_days, reformed_sensor_list[user_index]['num_of_transition'].tolist())
    tst_ratio = get_ratio(tst_abnormal_days, temp_sleep_duration[user_index])
    sol_ratio = get_ratio(sol_abnormal_days, temp_sleep_onset_duration[user_index])
    waso_ratio = get_ratio(waso_abnormal_days, temp_waso[user_index])

    this_user_ratio = pd.DataFrame({'PID':user_list_sleep[user_index],'mob':mobility_ratio,
                                    'tst':tst_ratio,'sol':sol_ratio,'waso':waso_ratio},index=[0])
    user_demographic_info = user_gender[user_gender['record_id']==user_list_sleep[user_index]]
    user_demographic_info = user_demographic_info[['home_care_package_level','gender','age','ATSM']]
    
    this_user_ratio.reset_index(drop=True, inplace=True)
    user_demographic_info.reset_index(drop=True, inplace=True)
    this_user_ratio_with_age = pd.concat([this_user_ratio, user_demographic_info], axis=1)

    all_user_ratio.append(this_user_ratio_with_age)


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
