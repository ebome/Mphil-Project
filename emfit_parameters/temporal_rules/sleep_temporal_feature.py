import numpy as np
from scipy import stats
import pandas as pd
import matplotlib.pyplot as plt
import datetime as dt
#import mysql.connector
from datetime import timedelta
import seaborn as sns
import math
import copy
#import merge_sensors as ms # make sure they are in same dir, run ms first
from datetime import datetime

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
# Motion sensor to transition
###################################################
data = pd.read_csv(r'F:\data\sensor_data_up_to_Nov.csv')

#------------------------------------------------
# remove the features that are not needed
motion_data = data.drop(columns=['Unnamed: 0','room_id','sensor_type','timestamp'])
# remove "chair" since this is for tranfer in ADL
motion_data = motion_data[~motion_data['sensor_name'].str.contains('Chair')]

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
# Remove 'repetitive sensor' and 0,  this function only keeps the first record
def remove_dup_df(motion_data):
    # arrange the time in order
    motion_data = motion_data.sort_values(by='local_timestamp')
    # drop the duplicates in sensor_id
    drop_dup_df = motion_data.loc[(motion_data['sensor_id'].shift() != motion_data['sensor_id'])]
    # remove 0 signal
    drop_dup_df = drop_dup_df[drop_dup_df['sensor_value'] == 1]
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
# now we know max_rooms=10, min_rooms=7

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
    '''
    # count how many rooms in this user's house
    room_num = len(cleaned_ila['changed_sensor_id'].unique().tolist())
    '''
    # print(room_num)
    transition=[]; date_list=[]
    PID = cleaned_ila['PID'].tolist()[0]
    
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
        
        # starting time of each day's motion data is 6am
        start_time_str = choppedila_day['local_timestamp'].tolist()[0][0:10]+' 06:00:00'
        chopped_day_morning_time  = choppedila_day[choppedila_day['local_timestamp'] > start_time_str]
        if len(chopped_day_morning_time)==0:
            continue
        
        # label the transitions and change them to merged transition labels
        ila_lablled = labels_between_room(choppedila_day)
        labels = ila_lablled['label'].values.tolist()
        transition.append(len(labels))
        '''        
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
        '''       
        date_of_computed = choppedila_day['local_timestamp'].tolist()[0][0:10]
        sensor_date = dt.datetime.strptime(date_of_computed, '%Y-%m-%d')
        date_list.append(sensor_date)
        
        num_of_transition = pd.DataFrame({'PID':PID,'date':date_list, 'num_of_transition':transition})
    
    return num_of_transition


### LONG COMPUTING TIME!
users_transition=[]
for each_user in finally_sensor_list:
    single_user_transition = get_transition_arrays(each_user,choppedTime)
    users_transition.append(single_user_transition) 

#====================
# After obtain mobility, remove the dates with mobility=0
users_transition = [each_user[each_user['num_of_transition'] != 0] for each_user in users_transition]

# or if want to get it easier
# num_of_tranistion_45_ppl=pd.read_excel(r'F:\Sensor_Data_Processing\temporal_rules\num_of_tranistion_45_ppl.xlsx') 
# users_transition = list(num_of_tranistion_45_ppl.groupby(['PID']))


#############################################################################
# Remove repetitive dates of sleep recording 
#############################################################################
# follow Mahnoosh's suggestion in one user
# split day-by-day, but not from 0am. Instead, split each day from 7pm 
base = dt.datetime.strptime('2019-05-02 19:00:00', '%Y-%m-%d %H:%M:%S')
datelist = pd.date_range(base, periods=580).tolist()
choppedTime_sleep=[]
for elt in datelist:
    strg = f'{elt:%Y-%m-%d %H:%M:%S}'
    choppedTime_sleep.append(strg)
    
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
def get_one_user_sleep_data(test_user,choppedTime_sleep):

    first_date_in_this_user = test_user['start_date'].tolist()[0]
    last_date_in_this_user = test_user['start_date'].tolist()[-1]

    sleep_summary_one_person = pd.DataFrame({})
    for i in range(len(choppedTime_sleep)-1):
        one_day_sleep  = test_user[test_user['start_date'] > choppedTime_sleep[i]]
        one_day_sleep  = one_day_sleep[one_day_sleep['start_date'] < choppedTime_sleep[i+1]]
               
        # e.g. choppedTime_sleep start  4-26, hence the choppedila_day is length 0 before the start date
        if first_date_in_this_user > datelist[i+1] or last_date_in_this_user < datelist[i]:
            continue    
        if len(one_day_sleep)==0:
            continue

        # one_day_sleep is the records for this day, now 
        # 1. remove the start_date that not within 7pm-6am
        # 2. for the rest episodes, check if they have same start time
        start_time = dt.datetime.strptime(choppedTime_sleep[i],'%Y-%m-%d %H:%M:%S')
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
#sleep_summary_one_person = get_one_user_sleep_data(test_user,choppedTime_sleep)

reformed_sleep_list_no_nap = []
for test_user in reformed_sleep_list_temp:
    # drop rows with nan sleep_duration
    test_user = test_user.dropna(subset=['sleep_duration'])
    # apply function to merge multi-episodic sleep records
    sleep_summary_one_person = get_one_user_sleep_data(test_user,choppedTime_sleep)
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
        # next day, count this sleep as this day
        if a <= time_division_today and a>=time_division_7pm and start_sleep_only_date!=end_sleep_only_date:
            each_sleep_date = a.date() 
            start_sleep_dates.append(each_sleep_date)

        # If start sleep time is between 7pm-11:59pm, and end sleep time is  
        # same day, count this sleep as this day
        ##### if not adding this line, user_index= 23 line 325,line 326 would be same day
        if a <= time_division_today and a>=time_division_7pm and start_sleep_only_date==end_sleep_only_date:
            each_sleep_date = a.date()
            start_sleep_dates.append(each_sleep_date)

        # If start sleep time is between 0am-6am, and end sleep time is  
        # same day, count this sleep as previous day
        if a >= time_division_tmr and a<=time_division_6am and start_sleep_only_date==end_sleep_only_date:
            each_sleep_date = a.date() - timedelta(days=1)
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
# Match CSIRO mobility dates and motion sensor, then sleep dates
###################################################

# 1: match CSIRO mobility dates with motion sensor
# Motion sensor: steps each day computed by CSIRO
all_dacs_mobility = pd.read_csv(r'F:\Sensor_Data_Processing\all_user_mobility_up_to_Aug.csv')
all_dacs_mobility = all_dacs_mobility[all_dacs_mobility['value']!=0 ]  
all_dacs_mobility = all_dacs_mobility[['PID','localTimeMeasured','value']]
# mobility has time format YY-MM-DD but sensor also has hours
all_dacs_mobility['local_timestamp'] = [dt.datetime.strptime(date[0:-9], '%d/%m/%Y').date() for date in all_dacs_mobility['localTimeMeasured']] 

# use either users_transition or reformed_sleep_list_no_repetead to pick the users we need
users_transition_pid =[]
for each_user_transition in users_transition:
    pid = each_user_transition['PID'].values.tolist()[0]
    users_transition_pid.append(pid)
all_dacs_mobility = all_dacs_mobility[all_dacs_mobility['PID'].isin(users_transition_pid)]

#---------------------
# Match CSIRO mobility dates with my mobility dates
# Group user's mobility
all_dacs_mobility_grouped = [item[1] for item in list(all_dacs_mobility.groupby(['PID']))]

# dates that in users_transition but not in all_dacs_mobility_grouped
matched_date_user_transition = []
for i in range(len(all_dacs_mobility_grouped)):
    each_mobility_my = users_transition[i]
    each_mobility_my = each_mobility_my[each_mobility_my['num_of_transition']!=0]
    each_mobility_csiro = all_dacs_mobility_grouped[i]
    each_mobility_my['local_timestamp'] = [each_day.date() for each_day in each_mobility_my['date'].tolist()] 
    each_PID_mobility_reformed = each_mobility_my[each_mobility_my['local_timestamp'].isin(each_mobility_csiro['local_timestamp'].tolist())]
    matched_date_user_transition.append(each_PID_mobility_reformed)

# debug individual PID's motion and CSIRO mobility dates
i=5
each_mobility_my = users_transition[i]
each_mobility_my = each_mobility_my[each_mobility_my['num_of_transition']!=0]
each_mobility_csiro = all_dacs_mobility_grouped[i]
each_mobility_my['local_timestamp'] = [each_day.date() for each_day in each_mobility_my['date'].tolist()] 
each_PID_mobility_reformed = each_mobility_my[each_mobility_my['local_timestamp'].isin(each_mobility_csiro['local_timestamp'].tolist())]


print(len(each_PID_mobility_reformed), len(each_mobility_csiro))

from collections import Counter
l1 = each_mobility_csiro['local_timestamp'].tolist()
l2 = each_PID_mobility_reformed['local_timestamp'].tolist()
c1 = Counter(l1)
c2 = Counter(l2)
diff = c1-c2
print(list(diff.elements()))

# get list debugged
matched_date_user_transition_list_length = [len(x) for x in matched_date_user_transition]
all_dacs_mobility_grouped_list_length = [len(x) for x in all_dacs_mobility_grouped]
# NOTE: we do not need two lists to have same length, since when remove 0 from csiro mobility, and remove 0 from my mobility
# we only match my mobility with csiro, we don't need to match CSIRO mobility with ours
are_length_same = debugging_two_temp_list_value(matched_date_user_transition_list_length,all_dacs_mobility_grouped_list_length)

    
#-------------------------------
# Same, for each unit in reformed_sleep_list_with_no_repetitive and matched_date_user_transition,remove the 
# dates that in reformed_sleep_list_with_no_nap but not in matched_date_user_transition
reformed_sleep_list = [];reformed_sensor_list = []
for i in range(len(matched_date_user_transition)):
    # add the day as index of mobility
    each_PID_mobility = matched_date_user_transition[i]
    each_PID_mobility['start_day_trucated'] = [each_day.date() for each_day in each_PID_mobility['date'].tolist()] 
    # add the day as index of sleep, change the consecutive cells with reptitive day
    each_PID_sleep = reformed_sleep_list_no_repetead[i]

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
# Create a big dataframe contain each user's mobility and sleep
#############################################################################
final_df = []
for i in range(len(reformed_sleep_list)):
    example_user_mobility = reformed_sensor_list[i][['PID','start_day_trucated','num_of_transition']]
    example_user_sleep = reformed_sleep_list[i][['date_for_this_sleep','TST(hour)','WASO(min)','SOL(min)','SE','duraion_in_bed']]
    merged_df = example_user_mobility.merge(example_user_sleep,left_on='start_day_trucated',right_on='date_for_this_sleep',
                how = 'inner')[['PID','start_day_trucated','num_of_transition','TST(hour)','WASO(min)','SOL(min)',
                                'SE','duraion_in_bed']]
    if len(merged_df)>10:                         
        final_df.append(merged_df)

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
# user_gender = user_gender[user_gender['home_care_package_level']<4]
user_gender['ATSM'] = [int(x) for x  in user_gender['ATSM'].tolist()]

# removed users that has mental score < 5
# user_gender = user_gender[user_gender['ATSM']>=7]

#############################################################################
# Smoother of data on reformed_sleep_list and reformed_sensor_list
#############################################################################
from statsmodels.nonparametric.smoothers_lowess import lowess


def get_smoothed_time_series(example_user,frac,iteration):
    pid = example_user['PID'].tolist()[0]
    y_mob=np.asarray(example_user['num_of_transition'].tolist() )
    y_tst=np.asarray(example_user['TST(hour)'].tolist() )
    y_waso=np.asarray(example_user['WASO(min)'].tolist() )
    y_sol=np.asarray(example_user['SOL(min)'].tolist() )
    y_se=np.asarray(example_user['SE'].tolist() )
    y_tib=np.asarray(example_user['duraion_in_bed'].tolist() )
    # to run LOWESS, ensure x axis is in correct format
    x = pd.to_datetime(example_user['start_day_trucated'], format='%Y/%m/%d')   

    # get LOWESS smoothed curve for each parameter
    smooth_mob = lowess(y_mob, x, frac=frac, it=iteration)[:,1]
    smooth_tst = lowess(y_tst, x, frac=frac, it=iteration)[:,1]
    smooth_waso = lowess(y_waso, x, frac=frac, it=iteration)[:,1]
    smooth_sol = lowess(y_sol, x, frac=frac, it=iteration)[:,1]
    smooth_se = lowess(y_se, x, frac=frac, it=iteration)[:,1]
    smooth_tib = lowess(y_tib, x, frac=frac, it=iteration)[:,1]

    smooth_df = pd.DataFrame({'PID':pid,'date':x,'mobility':smooth_mob,'TST':smooth_tst,
                              'WASO':smooth_waso,'SOL':smooth_sol,'SE':smooth_se,'TIB':smooth_tib})
    return smooth_df

# get smoothed_curve
smooth_final_df=[]
for example_user in final_df:
    smoothed_user = get_smoothed_time_series(example_user,0.05,3)
    smooth_final_df.append(smoothed_user)

# Add demographic information by first flatten the df, match the user_gender, and re-group
flat_final_df=pd.DataFrame({})
for each in smooth_final_df:
    flat_final_df = pd.concat([flat_final_df,each])
merged_df = flat_final_df.merge(user_gender,left_on='PID',right_on='record_id',
                how = 'inner')[['PID','date','mobility','TST','WASO','SOL','SE',
                                'TIB','home_care_package_level', 'gender','age',
                                'ATSM']]
smooth_final_df = [each[1] for each in merged_df.groupby(['PID'])]
                              
# check user demograpic property
user_44_ppl_list = list(set(merged_df['PID'].tolist()))
demogrp_info_44_ppl = user_gender[user_gender['record_id'].isin(user_44_ppl_list)]

demogrp_info_44_ppl[demogrp_info_44_ppl['gender']==1]['age'].describe()


    

'''
# to excel
final_big_df=pd.DataFrame({})    
for each in smooth_final_df:
    final_big_df= pd.concat([final_big_df,each])
final_big_df.to_excel(r'F:\Sensor_Data_Processing\temporal_rules\smoothed_final_df.xlsx')
'''
# final_big_df = pd.read_excel(r'F:\Sensor_Data_Processing\temporal_rules\smoothed_final_df.xlsx')
# smooth_final_df = [each[1] for each in final_big_df.groupby(['PID'])]

'''
#-----------
# example of LOWESS smooth curve
y1=np.asarray(reformed_sensor_list[2]['num_of_transition'].tolist() )
# to run LOWESS, ensure x axis is in correct format
x = pd.to_datetime(reformed_sensor_list[2]['date'], format='%d/%m/%Y  %H:%M')   
smooth_curve = lowess(y1, x, frac=0.15, it=3)[:,1]
data = np.asarray(smooth_curve)

plt.figure(figsize=(9,5))
plt.plot(x, y1, 'r',label='mobility')
plt.plot(x, smooth_curve, 'b',label='LOWESS curve, fraction=0.15, iteration = 3')
plt.legend()
plt.show()
'''
#############################################################################
# Change point detection: local max and min on smooth_final_df
#############################################################################
from scipy.signal import argrelextrema
# from segmented time series, get the trend
import time


import trendet
def from_pd_to_trend_entity(example_user,column_name,n):
    df = pd.DataFrame(example_user, columns=[column_name])
    
    # index of each user must be ensured to start from day 0
    df.reset_index(drop=True, inplace=True)

    # Find local peaks
    df['min'] = df.iloc[argrelextrema(df[column_name].values, np.less_equal,
                    order=n)[0]][column_name]
    df['max'] = df.iloc[argrelextrema(df[column_name].values, np.greater_equal,
                    order=n)[0]][column_name]

    # get indexes of all local min and max, don't forget to add the first index and last index
    index_min = df.loc[df['min']>0].index.tolist()
    index_max = df.loc[df['max']>0].index.tolist()
    index_seg = sorted(list(set(index_min + index_max+[0])))
    
    # get trend temporal abstraction
    trends = []
    each_trend_tuple=[]
    
    for i in range(len(index_seg)-1):
        previous_point = index_seg[i]+1
        next_point = index_seg[i+1]    
        # we define a trend episode from index of min and max points: 
        # trend.start=previous_point index , so this means the last point in a time series is not counted
        # trend.end = next_point index +1
        result_desc = trendet.trend_desc(df[column_name].values[previous_point:next_point])
        
        
        if column_name=='mobility':
            result_desc = result_desc+'_mob'
        if column_name=='TST':
            result_desc = result_desc+'_tst'    
        if column_name=='SOL':
            result_desc = result_desc+'_sol'    
        if column_name=='WASO':
            result_desc = result_desc+'_wa'    
        if column_name=='SE':
            result_desc = result_desc+'_se'    
        if column_name=='TIB':
            result_desc = result_desc+'_tib'    
        
        trends.append((result_desc))
        each_trend_tuple.append( (previous_point,next_point) )
    
    
    # if two consecutive segments have same trends,merge them into one
    # create four lists wth same lengths
    temp_trends=[trends[0],]
    temp_each_trend_tuple=[each_trend_tuple[0],]
    flags_trend=[0,]
    flags_tuple=[0,]
    for i in range(len(trends)-1):
        
        if trends[i] != trends[i+1]:
            flags_trend.append(0)
            flags_tuple.append(0)
            temp_each_trend_tuple.append(each_trend_tuple[i+1])
            temp_trends.append(trends[i+1])
        
        if trends[i] == trends[i+1]:
            flags_trend.append(1)
            temp_trends.append(trends[i+1])

            flags_tuple.append(0)
            flags_tuple[i]=1 # the flag in [i] should be erected
            # the [i+1]th tuple in temp_each_trend_tuple should be combined
            temp_each_trend_tuple.append( (each_trend_tuple[i][0],each_trend_tuple[i+1][-1]) )
    
    # Remove trends where flags_trend=1
    trend_combined=[]
    for i in range(len(temp_trends)):
        if flags_trend[i]==0:
            trend_combined.append(temp_trends[i])
        
    tuple_combined=[]
    for i in range(len(temp_each_trend_tuple)):
        if flags_tuple[i]==0:
            tuple_combined.append(temp_each_trend_tuple[i])
        
            
    # put tuples of episodes of same trend to same list
    # Hint: trends and each_trend_tuple have same number of elements, so we can use index of trends to get tuples
    trend_pd =pd.DataFrame({'trend':trend_combined,'episode':tuple_combined})
    values_list=[each_trend[1]['episode'].tolist() for each_trend in list(trend_pd.groupby(['trend']))]   
    keys_list=[each_trend[0] for each_trend in list(trend_pd.groupby(['trend']))]
    trend_dict_one_ts = dict(zip(keys_list, values_list))
   
    return trend_dict_one_ts

example_user = smooth_final_df[0]
n=7
trend_dict_mob=from_pd_to_trend_entity(example_user,'TST',n)

# Apply the function to each of the parameters
'''
n = 7  # number of points to be checked before and after
example_user = smooth_final_df[1]

trend_dict_mob=from_pd_to_trend_entity(example_user,'mobility',n)
trend_dict_tst=from_pd_to_trend_entity(example_user,'TST',n)
trend_dict_sol=from_pd_to_trend_entity(example_user,'SOL',n)
trend_dict_wa=from_pd_to_trend_entity(example_user,'WASO',n)
trend_dict_se=from_pd_to_trend_entity(example_user,'SE',n)
trend_dict_tib=from_pd_to_trend_entity(example_user,'TIB',n)

entity_list={}
entity_list.update(trend_dict_mob)
entity_list.update(trend_dict_tst)
entity_list.update(trend_dict_sol)
entity_list.update(trend_dict_wa)
entity_list.update(trend_dict_se) 
entity_list.update(trend_dict_tib) 
'''
# merged_df_selected = merged_df[merged_df['age']>=90]
# merged_df_selected = merged_df_selected[merged_df_selected['age']<100]
merged_df_selected = merged_df[merged_df['home_care_package_level']<4]
merged_df_selected = merged_df_selected[merged_df_selected['ATSM']>=7]
# merged_df_selected = merged_df[merged_df['age']>=90]
# merged_df_selected = merged_df_selected[merged_df_selected['age']<100]
smooth_df_selected = [each[1] for each in merged_df_selected.groupby(['PID'])]

import trendet
entity_lists=[]
n=7
for i in range(len(smooth_df_selected)):
    example_user =smooth_df_selected[i]
    trend_dict_mob=from_pd_to_trend_entity(example_user,'mobility',n)
    trend_dict_tst=from_pd_to_trend_entity(example_user,'TST',n)
    trend_dict_sol=from_pd_to_trend_entity(example_user,'SOL',n)
    trend_dict_wa=from_pd_to_trend_entity(example_user,'WASO',n)
    trend_dict_se=from_pd_to_trend_entity(example_user,'SE',n)
    trend_dict_tib=from_pd_to_trend_entity(example_user,'TIB',n)
    entity_list={}
    
    entity_list.update(trend_dict_se)
    # entity_list.update(trend_dict_sol)
    # entity_list.update(trend_dict_wa)
    # entity_list.update(trend_dict_se) 
    # entity_list.update(trend_dict_tib) 
    entity_list.update(trend_dict_mob)
    entity_lists.append(entity_list)
    
    


print('Number of entities:', len(entity_lists))

import KarmaLego as KL
epsilon = 1
max_distance = 30
min_ver_supp = 0.5

start = time.time()
tree = KL.KarmaLego(epsilon, max_distance, min_ver_supp).run(entity_lists)
tree.print()
end = time.time()
print('time to run', round(end - start), 's')


# get number of occurrences of an episode
occurrence = 0
key='F_se'
for each_user_entities in entity_lists:
    # each_user_entities is a dictionary
    if key in each_user_entities.keys():
        tuples = len(each_user_entities[key])
        occurrence = occurrence + tuples
print('occurrence=',occurrence)


# count occurences and nn-repteated occurence
the_indexes_for_complementaryRule = [7, 4, 30, 16, 20, 7, 32, 31, 22, 27, 31]
print(len(the_indexes_for_complementaryRule),'/',
      len(list(set(the_indexes_for_complementaryRule))), '=',
      len(the_indexes_for_complementaryRule)/len(list(set(the_indexes_for_complementaryRule))))

the_indexes_for_aRule = [10, 14, 13, 0, 16, 15, 2]
print(len(the_indexes_for_aRule),'/',
      len(list(set(the_indexes_for_aRule))), '=',
      len(the_indexes_for_aRule)/len(list(set(the_indexes_for_aRule))))

print('unique people in two rules',len(list(set(the_indexes_for_complementaryRule+the_indexes_for_aRule))) )
print(len(list(set(the_indexes_for_complementaryRule+the_indexes_for_aRule)))/len(smooth_df_selected))

#############################################################################
# SAX discratize mobility one by one
# https://github.com/nphoff/saxpy
# https://blog.csdn.net/Tony_Stark_Wang/article/details/88248701
#############################################################################
from SAX import SAX_trans # from a file import a class

# how many alphabets: 3
# how may j eqalluy sized intervals? Granulity = 1 day

def from_pd_to_state_entity(example_user,column_name,alpha):
    ts = pd.DataFrame(example_user, columns=[column_name])
    
    # Convert to SAX form
    x1 = SAX_trans(ts=ts,w=len(ts),alpha=alpha)
    st1 = x1.to_sax()
    sax_list = list(st1)

    # start and end of each episode
    states=[]
    state_change_points=[0] # index of state change points
    for i in range(len(sax_list)-1):
        if sax_list[i]==sax_list[i+1]:
            continue
        if sax_list[i]!=sax_list[i+1]:
            states.append(sax_list[i])
            state_change_points.append(i+1)
    states.append(sax_list[-1]) # this line ensure that last episode is stored

    # get trend temporal abstraction
    each_state_tuple=[]  
    for i in range(len(state_change_points)-1):
        previous_point = state_change_points[i] + 1
        next_point = state_change_points[i+1]     
        each_state_tuple.append((previous_point,next_point))
    each_state_tuple.append((state_change_points[-1],len(sax_list))) # state_change_points[-1] is the start of last episode   
    
    # Adding the name to the segmented time series
    if column_name=='mobility':
        result = [stateTA + '_mob' for stateTA in states]
    if column_name=='TST':
        result = [stateTA + '_tst' for stateTA in states]
    if column_name=='SOL':
        result = [stateTA + '_sol' for stateTA in states]
    if column_name=='WASO':
        result = [stateTA + '_wa' for stateTA in states]  
    if column_name=='SE':
        result = [stateTA + '_se' for stateTA in states]
    if column_name=='TIB':
        result = [stateTA + '_tib' for stateTA in states]
        
    # put tuples of episodes of same state to same list
    # Hint: states and each_state_tuple have same number of elements, so we can use index of states to get tuples
    state_pd =pd.DataFrame({'state':result,'episode':each_state_tuple})
    values_list=[each_state[1]['episode'].tolist() for each_state in list(state_pd.groupby(['state']))]   
    keys_list=[each_state[0] for each_state in list(state_pd.groupby(['state']))]
    state_dict_one_ts = dict(zip(keys_list, values_list))
        
    return state_dict_one_ts

# Apply the function to each of the parameters
'''
alpha = 3
example_user = smooth_final_df[8]

state_dict_mob=from_pd_to_state_entity(example_user,'mobility',alpha)
state_dict_tst=from_pd_to_state_entity(example_user,'TST',alpha)
state_dict_sol=from_pd_to_state_entity(example_user,'SOL',alpha)
state_dict_wa=from_pd_to_state_entity(example_user,'WASO',alpha)
state_dict_se=from_pd_to_state_entity(example_user,'SE',alpha)
state_dict_tib=from_pd_to_state_entity(example_user,'TIB',alpha)

entity_state={}
entity_state.update(state_dict_mob)
entity_state.update(state_dict_tst)
entity_state.update(state_dict_sol)
entity_state.update(state_dict_wa)
entity_state.update(state_dict_se) 
entity_state.update(state_dict_tib) 
'''


# select user groups
merged_df_selected = merged_df[merged_df['ATSM']>=7]
# merged_df_selected = merged_df[merged_df['age']>=90]
# merged_df_selected = merged_df_selected[merged_df_selected['age']<100]
smooth_df_selected = [each[1] for each in merged_df_selected.groupby(['PID'])]

entity_state_lists=[]
alpha = 3
for i in range(len(smooth_df_selected)):
    example_user =smooth_df_selected[i]
    state_dict_mob=from_pd_to_state_entity(example_user,'mobility',alpha)
    state_dict_tst=from_pd_to_state_entity(example_user,'TST',alpha)
    state_dict_sol=from_pd_to_state_entity(example_user,'SOL',alpha)
    state_dict_wa=from_pd_to_state_entity(example_user,'WASO',alpha)
    state_dict_se=from_pd_to_state_entity(example_user,'SE',alpha)
    state_dict_tib=from_pd_to_state_entity(example_user,'TIB',alpha)

    entity_state={}
    
    entity_state.update(state_dict_tib)
    # entity_state.update(state_dict_sol)
    # entity_state.update(state_dict_wa)
    # entity_state.update(state_dict_se) 
    # entity_state.update(state_dict_tib) 
    # Remeber: state_dict_mob should always be the last one to put in
    entity_state.update(state_dict_mob)
    entity_state_lists.append(entity_state)
    




print('Number of entities:', len(entity_state_lists))

import KarmaLego as KL
epsilon = 0
max_distance = 3
min_ver_supp = 0.2

start = time.time()
tree = KL.KarmaLego(epsilon, max_distance, min_ver_supp).run(entity_state_lists)
tree.print()
end = time.time()
print('time to run', round(end - start), 's')

#============================
the_indexes_for_complementaryRule = [1, 3, 27, 7, 39, 6, 39, 6, 20, 16, 41, 17, 4]+[39, 20, 40, 13, 16, 38, 6, 31, 11]
print(len(the_indexes_for_complementaryRule),'/',
      len(list(set(the_indexes_for_complementaryRule))), '=',
      len(the_indexes_for_complementaryRule)/len(list(set(the_indexes_for_complementaryRule))))

the_indexes_for_aRule = [7, 20, 15, 12, 18, 38, 2, 11, 24]+[26, 7, 1, 39, 37, 3, 24, 5, 40, 41, 20]
print(len(the_indexes_for_aRule),'/',
      len(list(set(the_indexes_for_aRule))), '=',
      len(the_indexes_for_aRule)/len(list(set(the_indexes_for_aRule))))

print('unique people in two rules',len(list(set(the_indexes_for_complementaryRule+the_indexes_for_aRule))) )
print(len(list(set(the_indexes_for_complementaryRule+the_indexes_for_aRule)))/42)

#----------------------------








#############################################################################
# Floor plan
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

reformed_room_matrix_df.to_csv(r'F:\Sensor_Data_Processing\floor_plan\37_users_room_distances.csv')
# plot the distribution
plt.hist(reformed_room_matrix_df['distance']);plt.xlabel('room distance (steps)')


