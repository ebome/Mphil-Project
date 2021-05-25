import numpy as np
from scipy import stats
import pandas as pd
import matplotlib.pyplot as plt
import datetime as dt
#import mysql.connector
from datetime import timedelta
import seaborn as sns
#import merge_sensors as ms # make sure they are in same dir, run ms first
from datetime import datetime

from apyori import apriori
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
# Same, for each unit in reformed_sleep_list_with_no_repetitive and users_transition,remove the 
# dates that in reformed_sleep_list_with_no_nap but not in users_transition
reformed_sleep_list = [];reformed_sensor_list = []
for i in range(len(users_transition)):
    # add the day as index of mobility
    each_PID_mobility = users_transition[i]
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





#############################################################################
# Smoother of data & change point detection
#############################################################################
from statsmodels.nonparametric.smoothers_lowess import lowess


y1=np.asarray(users_transition[2]['num_of_transition'].tolist() )
# to run LOWESS, ensure x axis is in correct format
x = pd.to_datetime(users_transition[2]['date'], format='%d/%m/%Y  %H:%M')   

smooth_curve = lowess(y1, x, frac=0.1, it=3)[:,1]
data = np.asarray(smooth_curve)

plt.figure(figsize=(9,5))
plt.plot(x, y1, 'r',label='mobility')
plt.plot(x, smooth_curve, 'b',label='LOWESS curve, fraction=0.05, iteration = 3')
plt.legend()

#---------------------
# Change point: local max and min
from scipy.signal import argrelextrema
df = pd.DataFrame(data, columns=['data'])
n = 7  # number of points to be checked before and after

# Find local peaks
df['min'] = df.iloc[argrelextrema(df.data.values, np.less_equal,
                    order=n)[0]]['data']
df['max'] = df.iloc[argrelextrema(df.data.values, np.greater_equal,
                    order=n)[0]]['data']

# Plot results
plt.figure(figsize=(9,5))
plt.scatter(df.index, df['min'], c='r')
plt.scatter(df.index, df['max'], c='g')
plt.plot(df.index, df['data'],'black',label='smoothed curve')
plt.legend()
plt.xticks(df.index[0:-1:20], x[0:-1:20], rotation='vertical')
plt.ylabel('mobility');plt.xlabel('date')

#---------------------
# from segmented time series, get the trend
import trendet




result_desc = trendet.trend_desc(data[150:200])


print(result_desc)




'''
#-----------------------------------------
# try change point detection
import ruptures as rpt
#Convert the time series values to a numpy 1D array
points=np.array(smooth_curve)
    
#RUPTURES PACKAGE
#Changepoint detection with the Pelt search method
model="rbf"
algo = rpt.Pelt(model=model).fit(points)
result = algo.predict(pen=6) # performs a penalized kernel change point detection
rpt.display(points, result, figsize=(8, 4))
plt.title('Change Point Detection: PELT Search Method')
plt.show()  
    
#Changepoint detection with the Binary Segmentation search method
model = "l2"  
algo = rpt.Binseg(model=model).fit(points)
my_bkps = algo.predict(n_bkps=10) # number of breakpoints
# show results
rpt.show.display(points, my_bkps, figsize=(8, 4)) 
plt.title('Change Point Detection: Binary Segmentation Search Method')
plt.show()
    
#Changepoint detection with window-based search method
model = "l2"  
algo = rpt.Window(width=7, model=model).fit(points)
my_bkps = algo.predict(n_bkps=10)
rpt.show.display(points, my_bkps, figsize=(8, 4))
plt.title('Change Point Detection: Window-Based Search Method, w=7')
plt.show()
    
#Changepoint detection with dynamic programming search method
model = "l1"  
algo = rpt.Dynp(model=model, min_size=3, jump=5).fit(points)
my_bkps = algo.predict(n_bkps=10)
rpt.show.display(points, my_bkps, figsize=(8, 4))
plt.title('Change Point Detection: Dynamic Programming Search Method')
plt.show()
'''

'''
#===================
import non_para_cpd as cpd

dt=smooth_curve
dt_days=users_transition[2]['date'].tolist()
plt.plot(dt_days,dt);plt.xlabel('date'),plt.ylabel('mobility score')


import statsmodels.api as sm

res = sm.tsa.seasonal_decompose(y1, freq=60)
res.plot()

plt.figure(figsize=(9,5))
plt.plot(x, y1, 'r',label='mobility')
plt.plot(x,res.trend,'b',label='moving avg, days=60') 
plt.legend()
    
# set window: https://my.oschina.net/u/4526838/blog/4430983
# pettitt's test
length = len(dt)
locations=[]
for i in range(0,length,1):
    pos,result = cpd.Pettitt_change_point_detection(dt[i:i+199])
    if result == 'significant':
        locations.append(pos+i)
print(set(locations))

plt.figure(figsize=(10,5))
plt.plot(range(len(dt)),[int(i) for i in dt])
for i in locations:
    plt.plot(i,int(dt[i]),'ks')
plt.title('Pettitt, window=30 days')
plt.show()

# Mann-kendall test
length = len(dt)
locations=[]
for i in range(0,length,1):
    pos_list = cpd.Kendall_change_point_detection(dt[i:i+29])
    new_list = [x+i for x in pos_list]
    locations.extend(new_list)
print(set(locations))

plt.figure(figsize=(10,5))
plt.title('Mann-kendall test, window=30 days')
plt.plot(range(len(dt)),[int(i) for i in dt])
for i in locations:
    plt.plot(i,int(dt[i]),'ks',color='r')
plt.show()


# buishand U test
length = len(dt)
locations=[]
for i in range(0,length,1):
    pos = cpd.Buishand_U_change_point_detection(dt[i:i+29])
    locations.append(pos+i)
print(set(locations))

plt.figure(figsize=(10,5))
plt.title('Buishand U test, window=30 days')
plt.plot(range(len(dt)),[int(i) for i in dt])
for i in locations:
    plt.plot(i,dt[i],'o',color='r')
plt.show()

# SNHT test
dt_array = np.asarray(dt)
length = len(dt)
locations=[]
for i in range(0,length-1):
    # input for SNHT_change_point_detection needs to be np array
    pos = cpd.SNHT_change_point_detection(dt_array[i:i+59])
    locations.append(pos+i)
print(set(locations))

plt.figure(figsize=(10,5))
plt.title('SNHT test, window=30 days')
plt.plot(range(len(dt)),[int(i) for i in dt])
for i in locations:
    plt.plot(i,dt[i],'o',color='b')
plt.show()
'''

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
df = final_big_df[['PID','start_day_trucated','num_of_transition','TST(hour)','WASO(min)','SOL(min)',
                    'SE','duraion_in_bed','toss_turn_count','avg_hr','avg_rr','awake_count',
                    'bed_exit_count','bed_exit_duration(min)','age','gender','ATSM']]


#############################################################################
# Samplping of data
#############################################################################
df = final_big_df[['PID','start_day_trucated','num_of_transition','TST(hour)','WASO(min)','SOL(min)',
                    
                    'bed_exit_duration(min)','age','gender','ATSM']]
# group by individuals
a = list(df.groupby(['PID']))
temp_store=[]
for each in a:
    temp_store.append(each[1])

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


