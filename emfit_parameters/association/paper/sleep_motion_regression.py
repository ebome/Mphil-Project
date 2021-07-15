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

#############################################################################
# Topological floor plan
#############################################################################

all_dacs_room_matrix = pd.read_csv(r'F:\Sensor_Data_Processing\floor_plan\DACS_Room_Distances.csv')
room_matrix_grouped_list = [item[1] for item in list(all_dacs_room_matrix.groupby(['PID']))]

room_matrix_grouped_double_side_list = []
for each_matrix_cleaned in room_matrix_grouped_list:
    each_matrix_cleaned['PID'] = each_matrix_cleaned['PID'].str.replace('Mar','3')
    room_matrix_grouped_double_side_list.append(each_matrix_cleaned)

# expand room_matrix_grouped_double_side_list to a big df
room_matrix_grouped_double_side_df = pd.DataFrame({})
for each in room_matrix_grouped_double_side_list:
    room_matrix_grouped_double_side_df = room_matrix_grouped_double_side_df.append(each)

# get the user list from room_matrix_grouped_double_side_list
room_matrix_users = [item['PID'].tolist()[0] for item in room_matrix_grouped_double_side_list ]


#------------------------------------------
# if we want to get a triangle topological floor plan
from collections import ChainMap

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
for unit_matrix in room_matrix_grouped_list:
    unit_matrix_cleaned = remove_duplicate_rooms(unit_matrix)
    unit_matrix_cleaned['PID'] = unit_matrix_cleaned['PID'].str.replace('Mar','3')
    reformed_room_matrix_list_temp.append(unit_matrix_cleaned)
    room_matrix_users.append(unit_matrix_cleaned['PID'].tolist()[0])

reformed_room_matrix_df = pd.DataFrame({})
for each in reformed_room_matrix_list_temp:
    reformed_room_matrix_df = reformed_room_matrix_df.append(each)

# group all users' floor plan
all_user_floor_plan = [item[1] for item in list(reformed_room_matrix_df.groupby('PID'))]

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
# Match sensor/sleep PID with floor plan PID
#############################################################################

motion_sensor_user_list = [item[0] for item in list(solitary_dacs_sensor.groupby(['PID']))]
# then take either room_matrix_user or all_user_floor_plan to match users
# remove some users from floor plan df by find the missing PID in floor plan df
missing_users_in_sensor = list(set(room_matrix_users) - set(motion_sensor_user_list))
room_matrix_grouped_double_side_df = room_matrix_grouped_double_side_df[~room_matrix_grouped_double_side_df['PID'].isin(missing_users_in_sensor)]
# Exactly 44 solitary users without ATSM < 7 have floor plan
floor_plan_user_list = [item[0] for item in list(room_matrix_grouped_double_side_df.groupby(['PID']))]
floor_plan_each_user = [item[1] for item in list(room_matrix_grouped_double_side_df.groupby(['PID']))]
# the single side floor plan
reformed_room_matrix_df = reformed_room_matrix_df[reformed_room_matrix_df['PID'].isin(floor_plan_user_list)]
reformed_room_matrix_44_ppl = [item[1] for item in list(reformed_room_matrix_df.groupby(['PID']))]

# get motion/sleep data from 44 people 
solitary_dacs_sensor_44_ppl = solitary_dacs_sensor[solitary_dacs_sensor['PID'].isin(floor_plan_user_list)]
solitary_dacs_sleep_44_ppl = solitary_dacs_sleep[solitary_dacs_sleep['PID'].isin(floor_plan_user_list)]

motion_data_each_unit = [item[1] for item in list(solitary_dacs_sensor_44_ppl.groupby(['PID']))]
motion_data_user_list = [item[0] for item in list(solitary_dacs_sensor_44_ppl.groupby(['PID']))]
sleep_data_each_unit = [item[1] for item in list(solitary_dacs_sleep_44_ppl.groupby(['PID']))]
sleep_data_user_list = [item[0] for item in list(solitary_dacs_sleep_44_ppl.groupby(['PID']))]

# debug
are_user_same = debugging_two_temp_list_value(floor_plan_user_list,sleep_data_user_list)


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
# Apply the above function 
sensor_list=[]
for each_PID in motion_data_each_unit:
    cleaned_each_df = remove_dup_df(each_PID)
    sensor_list.append(cleaned_each_df)

#-----------------------------------------------------------------------------  
# get daily room transition

# find maximal and minimal snesors
max_rooms=0
min_rooms=len(sensor_list[0]['sensor_id'].unique().tolist())
for each_user in sensor_list:
    test_user_room_list = each_user['sensor_id'].unique().tolist()
    if len(test_user_room_list) >= max_rooms:
        max_rooms = len(test_user_room_list)
    if len(test_user_room_list) < min_rooms:
        min_rooms = len(test_user_room_list)
# now we know max_rooms=15, min_rooms=7


#-----------------------------------------------------------------------------  
# Chopped datetime       
base = dt.datetime.strptime('2019-01-01 00:00:00', '%Y-%m-%d %H:%M:%S')
datelist = pd.date_range(base, periods=700).tolist()
choppedTime=[]
for elt in datelist:
    strg = f'{elt:%Y-%m-%d %H:%M:%S}'
    choppedTime.append(strg)
start_time = choppedTime[0]
end_time = choppedTime[-1]

'''
user_index=0
test_user = sensor_list[user_index]
test_user_floor_plan=floor_plan_each_user[user_index]
test_user_room_matrix_single_side = reformed_room_matrix_44_ppl[user_index]

distance_dictionary = get_distance_dict_from_floor_plan(test_user_floor_plan)

# remove wardrobe and pantry
test_user = test_user[~test_user['sensor_name'].str.contains('Pantry')]
test_user = test_user[~test_user['sensor_name'].str.contains('Wardrobe')]

# sum the steps
transition=[]; date_list=[]
PID = test_user['PID'].tolist()[0]
first_date_in_cleaned_ila = test_user['local_timestamp'].tolist()[0]
last_date_in_cleaned_ila = test_user['local_timestamp'].tolist()[-1]
for i in range(len(choppedTime)-1):
    chopped_one_day  = test_user[test_user['local_timestamp'] > choppedTime[i]]
    chopped_day  = chopped_one_day[chopped_one_day['local_timestamp'] < choppedTime[i+1]]
    # The chopped_day is length 0 before the start date
    if first_date_in_cleaned_ila > choppedTime[i+1] or last_date_in_cleaned_ila < choppedTime[i]:
        continue
    # if there is one day missing, just let it go
    if len(chopped_day)==0:
        continue
    
    # starting time of each day's motion data is 6am
    start_time_str = chopped_day['local_timestamp'].tolist()[0][0:10]+' 06:00:00'
    chopped_day_morning_time  = chopped_day[chopped_day['local_timestamp'] > start_time_str]

    if len(chopped_day_morning_time)==0:
        continue


    # get the labels from motion data
    chopped_day_labelled_transition = labels_between_room(chopped_day_morning_time)
    # Now match the motion data labels with distance dict and sum
    steps = [distance_dictionary[key] for key in chopped_day_labelled_transition if key in distance_dictionary]
    transition.append(sum(steps) )
        
    # get the date of this step
    date_of_computed = chopped_day_morning_time['local_timestamp'].tolist()[0][0:10]
    sensor_date = dt.datetime.strptime(date_of_computed, '%Y-%m-%d')
    date_list.append(sensor_date)

num_of_transition = pd.DataFrame({'PID':PID,'date':date_list, 'num_of_transition':transition})
'''



def get_distance_dict_from_floor_plan(test_user_room_matrix_double_side):
    keys=[]; values=[]
    for i in range(len(test_user_room_matrix_double_side)):
        room_previous_sensor = test_user_room_matrix_double_side.iloc[i]['room1_name'] 
        room_next_sensor =  test_user_room_matrix_double_side.iloc[i]['room2_name']
        label = room_previous_sensor+' to '+room_next_sensor
        keys.append(label)
        values.append(test_user_room_matrix_double_side.iloc[i]['distance'])

    dict_sensor_id = [{k: v} for k, v in zip(keys, values)]
    distance_dictionary = {}
    for each_dict in dict_sensor_id:
        distance_dictionary.update(each_dict)
    return distance_dictionary

# dictionary for distance
#distance_dictionary = get_distance_dict_from_floor_plan(test_user_floor_plan)


def labels_between_room(cleaned_ila):
    temp1=[]
    for i in range(0, len(cleaned_ila)-1):
        room_previous_sensor = cleaned_ila.iloc[i]['sensor_name'].strip()
        room_next_sensor =  cleaned_ila.iloc[i+1]['sensor_name'].strip()
        label = room_previous_sensor+' to '+room_next_sensor
        temp1.append(label)
    return temp1 # return a list

# get_transition_arrays will give daily transition numbers
def get_transition_arrays(test_user,choppedTime,distance_dictionary):
    test_user = test_user[~test_user['sensor_name'].str.contains('Pantry')]
    test_user = test_user[~test_user['sensor_name'].str.contains('Wardrobe')]

    # sum the steps
    transition=[]; date_list=[]
    PID = test_user['PID'].tolist()[0]
    
    first_date_in_cleaned_ila = test_user['local_timestamp'].tolist()[0]
    last_date_in_cleaned_ila = test_user['local_timestamp'].tolist()[-1]
    for i in range(len(choppedTime)-1):
        chopped_one_day  = test_user[test_user['local_timestamp'] > choppedTime[i]]
        chopped_day  = chopped_one_day[chopped_one_day['local_timestamp'] < choppedTime[i+1]]
        # The chopped_day is length 0 before the start date
        if first_date_in_cleaned_ila > choppedTime[i+1] or last_date_in_cleaned_ila < choppedTime[i]:
            continue
        # if there is one day missing, just let it go
        if len(chopped_day)==0:
            continue
    
        # starting time of each day's motion data is 6am
        start_time_str = chopped_day['local_timestamp'].tolist()[0][0:10]+' 06:00:00'
        chopped_day_morning_time  = chopped_day[chopped_day['local_timestamp'] > start_time_str]
        if len(chopped_day_morning_time)==0:
            continue

        # get the labels from motion data
        chopped_day_labelled_transition = labels_between_room(chopped_day)
        # Now match the motion data labels with distance dict and sum
        steps = [distance_dictionary[key] for key in chopped_day_labelled_transition if key in distance_dictionary]
        transition.append(sum(steps) )
        
        # get the date of this step
        date_of_computed = chopped_day['local_timestamp'].tolist()[0][0:10]
        sensor_date = dt.datetime.strptime(date_of_computed, '%Y-%m-%d')
        date_list.append(sensor_date)

    num_of_transition = pd.DataFrame({'PID':PID,'date':date_list, 'num_of_transition':transition})
    
    return num_of_transition


### LONG COMPUTING TIME to get the dataframe: 4 min
users_transition=[]
for i in range(len(sensor_list)):
    each_user = sensor_list[i]
    each_user_double_side_floor_plan = floor_plan_each_user[i]
    each_user_dict = get_distance_dict_from_floor_plan(each_user_double_side_floor_plan)
    single_user_transition = get_transition_arrays(each_user,choppedTime,each_user_dict)
    users_transition.append(single_user_transition) 



#flat_transition = [item for sub_df in users_transition for item in sub_df['PID']]
#print('length_flat_transition = ',  len(flat_transition))


###################################################
# Motion sensor: steps each day computed by CSIRO
###################################################
all_dacs_mobility = pd.read_csv(r'F:\Sensor_Data_Processing\all_user_mobility_up_to_Aug.csv')
all_dacs_mobility = all_dacs_mobility[all_dacs_mobility['value']!=0 ]  
all_dacs_mobility = all_dacs_mobility[['PID','localTimeMeasured','value']]
# mobility has time format YY-MM-DD but sensor also has hours
all_dacs_mobility['local_timestamp'] = [dt.datetime.strptime(date[0:-9], '%d/%m/%Y').date() for date in all_dacs_mobility['localTimeMeasured']] 
# use motion_data_user_list to pick the users we need
all_dacs_mobility = all_dacs_mobility[all_dacs_mobility['PID'].isin(motion_data_user_list)]

#---------------------# Match CSIRO mobility dates with my mobility dates
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


# debug individual PID's sleep and mobility dates
'''
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
'''

# get list debugged
matched_date_user_transition_list_length = [len(x) for x in matched_date_user_transition]
all_dacs_mobility_grouped_list_length = [len(x) for x in all_dacs_mobility_grouped]
# NOTE: we do not need two lists to have same length, since when remove 0 from csiro mobility, and remove 0 from my mobility
# we only match my mobolity with csiro, we don't need to match CSIRO mobility with ours
are_length_same = debugging_two_temp_list_value(matched_date_user_transition_list_length,all_dacs_mobility_grouped_list_length)


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
for test_user in sleep_data_each_unit:
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
# Match sleep and motion sensor on the dates
###################################################
# Same, for each unit in reformed_sleep_list_with_no_repetitive and users_transition,remove the 
# dates that in reformed_sleep_list_with_no_nap but not in users_transition
reformed_sleep_list = [];reformed_sensor_list = []
for i in range(len(matched_date_user_transition)):
    each_PID_mobility = matched_date_user_transition[i]
    each_PID_sleep = reformed_sleep_list_no_repetead[i]
    each_PID_mobility['local_timestamp'] = [each_day.date() for each_day in each_PID_mobility['date'].tolist()] 

    # match the days
    # mobility should within dates of sleep
    each_PID_mobility_reformed = each_PID_mobility[each_PID_mobility['local_timestamp'].isin(each_PID_sleep['date_for_this_sleep'].tolist())]
    # sleep should within dates of mobility
    each_PID_sleep_reformed = each_PID_sleep[each_PID_sleep['date_for_this_sleep'].isin(each_PID_mobility_reformed['local_timestamp'].tolist())]

    reformed_sensor_list.append(each_PID_mobility_reformed)
    reformed_sleep_list.append(each_PID_sleep_reformed)


'''
# debug individual PID's sleep and mobility dates
each_PID_mobility = users_transition[0]
each_PID_sleep = reformed_sleep_list_no_repetead[0]
each_PID_mobility['local_timestamp'] = [each_day.date() for each_day in each_PID_mobility['date'].tolist()] 

each_PID_mobility_reformed = each_PID_mobility[each_PID_mobility['local_timestamp'].isin(each_PID_sleep['date_for_this_sleep'].tolist())]
each_PID_sleep_reformed = each_PID_sleep[each_PID_sleep['date_for_this_sleep'].isin(each_PID_mobility_reformed['local_timestamp'].tolist())]

print(len(each_PID_mobility_reformed), len(each_PID_sleep_reformed))

from collections import Counter
l1 = each_PID_sleep_reformed['date_for_this_sleep'].tolist()
l2 = each_PID_mobility_reformed['local_timestamp'].tolist()
c1 = Counter(l1)
c2 = Counter(l2)
diff = c2-c1
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
dates = list(range(len(reformed_sensor_list[user_index]['num_of_transition'])))
x_labels_all = [date.strftime('%Y-%m-%d') for date in reformed_sensor_list[user_index]['local_timestamp'].tolist()]
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
user_44_PID_sleep=[each_user_sleep['PID'].tolist()[0] for each_user_sleep in reformed_sleep_list]
user_44_PID_sensor=[each_user_sensor['PID'].tolist()[0] for each_user_sensor in reformed_sensor_list]


# create 44 people's dataframe and later remove the unwanted 
final_big_df=pd.DataFrame({})    
for i in range(len(user_44_PID_sleep)):
    # combine mobility and sleep
    mobility = reformed_sensor_list[i][['local_timestamp','num_of_transition']]
    sleep_features = reformed_sleep_list[i][['PID','start_sleep_time','finish_sleep_time',
                                        'TST(hour)','WASO(min)','SOL(min)','SE',
                                        'duraion_in_bed','toss_turn_count','avg_hr','avg_rr',
                                        'awake_count','bed_exit_count','bed_exit_duration(min)']]
    mobility.reset_index(drop=True, inplace=True)
    sleep_features.reset_index(drop=True, inplace=True)
    merged_df = pd.concat([mobility, sleep_features],axis=1)
    final_big_df = pd.concat([final_big_df,merged_df])

'''
9117 for 44 ppl, 7853 rows for 37 people
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
df = final_big_df[['PID','local_timestamp','num_of_transition','TST(hour)','WASO(min)','SOL(min)','duraion_in_bed',
                    'SE','awake_count','avg_hr','avg_rr','age','gender']]
# group by individuals
a = list(df.groupby(['PID']))
temp_store=[]
for each in a:
    test_user = each[1]
    if len(test_user)>10:
        temp_store.append(test_user)

# if SE is multiplied by 100
temp_store_SE_100=[]
for each in temp_store:
    each['SE'] = each['SE']*100
    temp_store_SE_100.append(each)
       

flat_temp_store_36_ppl = sum([len(each) for each in temp_store])
print('flat_temp_store_36_ppl = ', flat_temp_store_36_ppl)
'''
7847 rows for 36 people
'''

# make temp_store a big merged df
temp_store_merged_df=pd.DataFrame({})    
for each in temp_store:
    temp_store_merged_df = pd.concat([temp_store_merged_df,each])



# see if they have any linear relationship by scatter plots
user_index=17
plt.figure(figsize=(12,6))
plt.subplot(2,3,1)
plt.scatter(reformed_sensor_list[user_index]['num_of_transition'].tolist(), temp_sleep_duration[user_index])
plt.xlabel('mobility');plt.ylabel('total sleep duration (hour)')
plt.subplot(2,3,2)
plt.scatter(reformed_sensor_list[user_index]['num_of_transition'].tolist(), temp_sleep_efficiency[user_index])
plt.xlabel('mobility');plt.ylabel('sleep efficiency')
plt.subplot(2,3,3)
plt.scatter(reformed_sensor_list[user_index]['num_of_transition'].tolist(), temp_sleep_onset_duration[user_index])
plt.xlabel('mobility');plt.ylabel('sleep onset duration (minute)')
plt.subplot(2,3,4)
plt.scatter(reformed_sensor_list[user_index]['num_of_transition'].tolist(), temp_waso[user_index])
plt.xlabel('mobility');plt.ylabel('wake after sleep onset duration (minute)')
plt.subplot(2,3,5)
plt.scatter(reformed_sensor_list[user_index]['num_of_transition'].tolist(), temp_sleep_duration_in_bed[user_index])
plt.xlabel('mobility');plt.ylabel('TIB (minute)')
plt.subplot(2,3,6)
plt.scatter(reformed_sensor_list[user_index]['num_of_transition'].tolist(), temp_sleep_awakeCount[user_index])
plt.xlabel('mobility');plt.ylabel('Awake')


# pearson or spearman plot
test_user = temp_store[9][['num_of_transition','TST(hour)','WASO(min)','SOL(min)','duraion_in_bed',
                    'SE','awake_count']]
test_user = test_user.rename(columns={"num_of_transition": "mobility", "TST(hour)": "TST",'WASO(min)':'WASO',
                                      'SOL(min)':'SOL','duraion_in_bed':'TIB','awake_count':'Awake'})
fig, ax = plt.subplots(figsize=(8,4))
corr= test_user.corr(method='spearman').round(2)
# Getting the Upper Triangle of the co-relation matrix
matrix = np.triu(corr)

# using the upper triangle matrix as mask 
sns.heatmap(corr, annot = True, cbar=False,mask=matrix, 
            center= 0, cmap= 'coolwarm', square=True)
plt.show()

#############################################################################
# Regression model
#############################################################################
test_user=temp_store[5]
X = test_user[['SE','TST(hour)','SOL(min)','WASO(min)','duraion_in_bed','awake_count']]
Y = test_user['num_of_transition']
model = sm.OLS(Y, X).fit()
fig = sm.graphics.plot_ccpr(model, "WASO(min)")
fig.tight_layout(pad=1.0)

# NON-STEPWISE REGRESSION
rsquared_adj_list=[]
parameters_list=[]
p_val_list=[]
valid_len=[]
age_list=[]
gender_list=[]
for test_user in temp_store:
    X = test_user[['SE','TST(hour)','SOL(min)','WASO(min)','duraion_in_bed','awake_count']]
    Y = test_user['num_of_transition']
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
	def stepwise(self, df, response, intercept=False, normalize=False, criterion='rsquared_adj', 
              f_pvalue_enter=.05, p_value_enter=.05, direction='backward', show_step=True, 
              criterion_enter=None, criterion_remove=None, max_iter=200, **kw):
		"""
		parameters of stepwise regression
		----
		df : dataframe
			for data analysis, 'response' is the 1st column
		response : str
			the variables in regression model
		intercept : bool, default is True
			if the model has intercept
		criterion : str, default 'bic'
			the rule of stepwise regression
		f_pvalue_enter : float, default is 0.05
			when set criterion='ssr', the model add/remove the threshold of the varaible's f_pvalue
		p_value_enter : float, default is 0.05
			when set derection='both'，remove threshold of the varaible's pvalue
		direction : str, default is 'backward'
			direction of stepwise regression
		show_step : bool, default is True
			show steps of stepwise regression
		criterion_enter : float, default is None
			when set derection='both' or 'forward', the model add varaible's threshold criterion
		criterion_remove : float, default is None
			when set derection='backward', the model remove varaible's threshold criterion
		max_iter : int, default is 200
			the meximal interation number of the model
		"""
		criterion_list = ['bic', 'aic', 'ssr', 'rsquared', 'rsquared_adj']
		if criterion not in criterion_list:
			raise IOError('please enter correct criterion, it has to be:', '\n', criterion_list)

		direction_list = ['backward', 'forward', 'both']
		if direction not in direction_list:
			raise IOError('please enter correct direction, it has to be:', '\n', direction_list)

		# default p_enter
		p_enter = {'bic': 0.0, 'aic': 0.0, 'ssr': 0.05, 'rsquared': 0.05, 'rsquared_adj': -0.05}
		if criterion_enter:  
			p_enter[criterion] = criterion_enter

		# default p_remove
		p_remove = {'bic': 0.01, 'aic': 0.01, 'ssr': 0.1, 'rsquared': 0.05, 'rsquared_adj': -0.05}
		if criterion_remove:  
			p_remove[criterion] = criterion_remove

		if normalize:  # if we need normalized data
			intercept = False  # set intercept = 0
			df_std = StandardScaler().fit_transform(df)
			df = pd.DataFrame(df_std, columns=df.columns, index=df.index)

		""" forward """
		if direction == 'forward':
			remaining = list(df.columns)  # variables to be modeled
			remaining.remove(response)
			selected = []  # list of selected variables
			# initialize the score
			if intercept: 
				formula = "{} ~ {} + 1".format(response, remaining[0])
			else:
				formula = "{} ~ {} - 1".format(response, remaining[0])

			result = smf.ols(formula, df).fit()  # OLS regression model
			current_score = eval('result.' + criterion)
			best_new_score = eval('result.' + criterion)

			if show_step:
				print('\nstepwise starting:\n')
			iter_times = 0
			# when var are not finishing removing yet, we need loop to update the latest scores 
			while remaining and (current_score == best_new_score) and (iter_times < max_iter):
				scores_with_candidates = []  # initialize scores and variables as candidates
				for candidate in remaining:  # loop the variables that are not removed into the model
					if intercept: 
						formula = "{} ~ {} + 1".format(response, ' + '.join(selected + [candidate]))
					else:
						formula = "{} ~ {} - 1".format(response, ' + '.join(selected + [candidate]))

					result = smf.ols(formula, df).fit()  
					fvalue = result.fvalue
					f_pvalue = result.f_pvalue
					score = eval('result.' + criterion)
					scores_with_candidates.append((score, candidate, fvalue, f_pvalue))  # store this loop's variables and scores

				if criterion == 'ssr':  # optimize the criterion by taking minimal values
					scores_with_candidates.sort(reverse=True)  # soret scores in descending order
					best_new_score, best_candidate, best_new_fvalue, best_new_f_pvalue = scores_with_candidates.pop()  # get minimal score and its corresponding variable
					if ((current_score - best_new_score) > p_enter[criterion]) and (
							best_new_f_pvalue < f_pvalue_enter):  # if cuurent score larger than latest score
						remaining.remove(best_candidate)  # remove the lestest varaible from variable list
						selected.append(best_candidate)  # put the lestest varaible into selected variable list 
						current_score = best_new_score  # update score
						if show_step: 
							print('Adding %s, SSR = %.3f, Fstat = %.3f, FpValue = %.3e' %
								  (best_candidate, best_new_score, best_new_fvalue, best_new_f_pvalue))
					elif (current_score - best_new_score) >= 0 and (
							best_new_f_pvalue < f_pvalue_enter) and iter_times == 0:  # when difference of scores >=0 and it is 1st iteration
						remaining.remove(best_candidate)
						selected.append(best_candidate)
						current_score = best_new_score
						if show_step:  
							print('Adding %s, %s = %.3f' % (best_candidate, criterion, best_new_score))
					elif (best_new_f_pvalue < f_pvalue_enter) and iter_times == 0:  # when difference of scores < p_enter and it is 1st iteration
						selected.append(remaining[0])
						remaining.remove(remaining[0])
						if show_step: 
							print('Adding %s, %s = %.3f' % (remaining[0], criterion, best_new_score))
				elif criterion in ['bic', 'aic']:  # take the minimal values from these criteria
					scores_with_candidates.sort(reverse=True)  
					best_new_score, best_candidate, best_new_fvalue, best_new_f_pvalue = scores_with_candidates.pop()  
					if (current_score - best_new_score) > p_enter[criterion]:  
						remaining.remove(best_candidate)  
						selected.append(best_candidate) 
						current_score = best_new_score  
						# print(iter_times)
						if show_step:  
							print('Adding %s, %s = %.3f' % (best_candidate, criterion, best_new_score))
					elif (current_score - best_new_score) >= 0 and iter_times == 0:  # when difference of scores >= 0 and it is 1st iteration
						remaining.remove(best_candidate)
						selected.append(best_candidate)
						current_score = best_new_score
						if show_step: 
							print('Adding %s, %s = %.3f' % (best_candidate, criterion, best_new_score))
					elif iter_times == 0:  # when difference of scores < p_enter and it is 1st iteration
						selected.append(remaining[0])
						remaining.remove(remaining[0])
						if show_step:  
							print('Adding %s, %s = %.3f' % (remaining[0], criterion, best_new_score))
				else:
					scores_with_candidates.sort()
					best_new_score, best_candidate, best_new_fvalue, best_new_f_pvalue = scores_with_candidates.pop()
					if (best_new_score - current_score) > p_enter[criterion]:
						remaining.remove(best_candidate)
						selected.append(best_candidate)
						current_score = best_new_score
						print(iter_times, flush=True)
						if show_step: 
							print('Adding %s, %s = %.3f' % (best_candidate, criterion, best_new_score))
					elif (best_new_score - current_score) >= 0 and iter_times == 0:  # when difference of scores >= 0 and it is 1st iteration
						remaining.remove(best_candidate)
						selected.append(best_candidate)
						current_score = best_new_score
						if show_step:  
							print('Adding %s, %s = %.3f' % (best_candidate, criterion, best_new_score))
					elif iter_times == 0:  # when difference of scores < p_enter and it is 1st iteration
						selected.append(remaining[0])
						remaining.remove(remaining[0])
						if show_step:  
							print('Adding %s, %s = %.3f' % (remaining[0], criterion, best_new_score))
				iter_times += 1

			if intercept:  
				formula = "{} ~ {} + 1".format(response, ' + '.join(selected))
			else:
				formula = "{} ~ {} - 1".format(response, ' + '.join(selected))

			self.stepwise_model = smf.ols(formula, df).fit() 

			if show_step: 
				print('\nLinear regression model:', '\n  ', self.stepwise_model.model.formula)
				print('\n', self.stepwise_model.summary())

		""" backward """
		if direction == 'backward':
			remaining, selected = set(df.columns), set(df.columns) # variables to be modeled
			remaining.remove(response)
			selected.remove(response)  
			if intercept:  
				formula = "{} ~ {} + 1".format(response, ' + '.join(selected))
			else:
				formula = "{} ~ {} - 1".format(response, ' + '.join(selected))

			result = smf.ols(formula, df).fit()  
			current_score = eval('result.' + criterion)
			worst_new_score = eval('result.' + criterion)

			if show_step:
				print('\nstepwise starting:\n')
			iter_times = 0
			while remaining and (current_score == worst_new_score) and (iter_times < max_iter):
				scores_with_eliminations = []  
				for elimination in remaining: 
					if intercept:  
						formula = "{} ~ {} + 1".format(response, ' + '.join(selected - set(elimination)))
					else:
						formula = "{} ~ {} - 1".format(response, ' + '.join(selected - set(elimination)))

					result = smf.ols(formula, df).fit()  
					fvalue = result.fvalue
					f_pvalue = result.f_pvalue
					score = eval('result.' + criterion)
					scores_with_eliminations.append((score, elimination, fvalue, f_pvalue)) 

				if criterion == 'ssr':  
					scores_with_eliminations.sort(reverse=False) 
					worst_new_score, worst_elimination, worst_new_fvalue, worst_new_f_pvalue = scores_with_eliminations.pop()  
					if ((worst_new_score - current_score) < p_remove[criterion]) and (
							worst_new_f_pvalue < f_pvalue_enter): 
						remaining.remove(worst_elimination)  
						selected.remove(worst_elimination) 
						current_score = worst_new_score  
						if show_step: 
							print('Removing %s, SSR = %.3f, Fstat = %.3f, FpValue = %.3e' %
								  (worst_elimination, worst_new_score, worst_new_fvalue, worst_new_f_pvalue))
				elif criterion in ['bic', 'aic']:  
					scores_with_eliminations.sort(reverse=False)  
					worst_new_score, worst_elimination, worst_new_fvalue, worst_new_f_pvalue = scores_with_eliminations.pop()  
					if (worst_new_score - current_score) < p_remove[criterion]:  # if the score change is not significant
						remaining.remove(worst_elimination)  
						selected.remove(worst_elimination)  
						current_score = worst_new_score  
						if show_step: 
							print('Removing %s, %s = %.3f' % (worst_elimination, criterion, worst_new_score))
				else:
					scores_with_eliminations.sort(reverse=True)
					worst_new_score, worst_elimination, worst_new_fvalue, worst_new_f_pvalue = scores_with_eliminations.pop()
					if (current_score - worst_new_score) < p_remove[criterion]:
						remaining.remove(worst_elimination)
						selected.remove(worst_elimination)
						current_score = worst_new_score
						if show_step:  
							print('Removing %s, %s = %.3f' % (worst_elimination, criterion, worst_new_score))
				iter_times += 1

			if intercept:  
				formula = "{} ~ {} + 1".format(response, ' + '.join(selected))
			else:
				formula = "{} ~ {} - 1".format(response, ' + '.join(selected))

			self.stepwise_model = smf.ols(formula, df).fit()  

			if show_step:  
				print('\nLinear regression model:', '\n  ', self.stepwise_model.model.formula)
				print('\n', self.stepwise_model.summary())

		""" both """
		if direction == 'both':
			remaining = list(df.columns) # variables to be modeled
			remaining.remove(response)
			selected = []  
			if intercept:  
				formula = "{} ~ {} + 1".format(response, remaining[0])
			else:
				formula = "{} ~ {} - 1".format(response, remaining[0])

			result = smf.ols(formula, df).fit()  
			current_score = eval('result.' + criterion)
			best_new_score = eval('result.' + criterion)

			if show_step:
				print('\nstepwise starting:\n')
			iter_times = 0
			while remaining and (current_score == best_new_score) and (iter_times < max_iter):
				scores_with_candidates = []  
				for candidate in remaining:  
					if intercept:  
						formula = "{} ~ {} + 1".format(response, ' + '.join(selected + [candidate]))
					else:
						formula = "{} ~ {} - 1".format(response, ' + '.join(selected + [candidate]))

					result = smf.ols(formula, df).fit()  
					fvalue = result.fvalue
					f_pvalue = result.f_pvalue
					score = eval('result.' + criterion)
					scores_with_candidates.append((score, candidate, fvalue, f_pvalue)) 

				if criterion == 'ssr':  
					scores_with_candidates.sort(reverse=True) 
					best_new_score, best_candidate, best_new_fvalue, best_new_f_pvalue = scores_with_candidates.pop()    
					if ((current_score - best_new_score) > p_enter[criterion]) and (
							best_new_f_pvalue < f_pvalue_enter):  
						remaining.remove(best_candidate)  
						selected.append(best_candidate)  
						current_score = best_new_score  
						if show_step: 
							print('Adding %s, SSR = %.3f, Fstat = %.3f, FpValue = %.3e' %
								  (best_candidate, best_new_score, best_new_fvalue, best_new_f_pvalue))
					elif (current_score - best_new_score) >= 0 and (
							best_new_f_pvalue < f_pvalue_enter) and iter_times == 0:  
						remaining.remove(best_candidate)
						selected.append(best_candidate)
						current_score = best_new_score
						if show_step:  
							print('Adding %s, %s = %.3f' % (best_candidate, criterion, best_new_score))
					elif (best_new_f_pvalue < f_pvalue_enter) and iter_times == 0: 
						selected.append(remaining[0])
						remaining.remove(remaining[0])
						if show_step:  
							print('Adding %s, %s = %.3f' % (remaining[0], criterion, best_new_score))
				elif criterion in ['bic', 'aic']:  
					scores_with_candidates.sort(reverse=True)  
					best_new_score, best_candidate, best_new_fvalue, best_new_f_pvalue = scores_with_candidates.pop()  
					if (current_score - best_new_score) > p_enter[criterion]: 
						remaining.remove(best_candidate)  
						selected.append(best_candidate)  
						current_score = best_new_score  
						if show_step: 
							print('Adding %s, %s = %.3f' % (best_candidate, criterion, best_new_score))
					elif (current_score - best_new_score) >= 0 and iter_times == 0:  # when difference of scores >= 0 and it is 1st iteration
						remaining.remove(best_candidate)
						selected.append(best_candidate)
						current_score = best_new_score
						if show_step: 
							print('Adding %s, %s = %.3f' % (best_candidate, criterion, best_new_score))
					elif iter_times == 0:  # when difference of scores < p_enter and it is 1st iteration
						selected.append(remaining[0])
						remaining.remove(remaining[0])
						if show_step:  
							print('Adding %s, %s = %.3f' % (remaining[0], criterion, best_new_score))
				else:
					scores_with_candidates.sort()
					best_new_score, best_candidate, best_new_fvalue, best_new_f_pvalue = scores_with_candidates.pop()
					if (best_new_score - current_score) > p_enter[criterion]:  # # when difference of scores > p_enter
						remaining.remove(best_candidate)
						selected.append(best_candidate)
						current_score = best_new_score
						if show_step: 
							print('Adding %s, %s = %.3f' % (best_candidate, criterion, best_new_score))
					elif (best_new_score - current_score) >= 0 and iter_times == 0:  # when difference of scores >= 0 and it is 1st iteration
						remaining.remove(best_candidate)
						selected.append(best_candidate)
						current_score = best_new_score
						if show_step:  
							print('Adding %s, %s = %.3f' % (best_candidate, criterion, best_new_score))
					elif iter_times == 0:  # when difference of scores < p_enter and it is 1st iteration
						selected.append(remaining[0])
						remaining.remove(remaining[0])
						if show_step: 
							print('Adding %s, %s = %.3f' % (remaining[0], criterion, best_new_score))

				if intercept: 
					formula = "{} ~ {} + 1".format(response, ' + '.join(selected))
				else:
					formula = "{} ~ {} - 1".format(response, ' + '.join(selected))

				result = smf.ols(formula, df).fit()  
				if iter_times >= 1:  # check variables's p-value is significant or not when in 2nd loop
					if result.pvalues.max() > p_value_enter:
						var_removed = result.pvalues[result.pvalues == result.pvalues.max()].index[0]
						p_value_removed = result.pvalues[result.pvalues == result.pvalues.max()].values[0]
						selected.remove(result.pvalues[result.pvalues == result.pvalues.max()].index[0])
						if show_step:  
							print('Removing %s, Pvalue = %.3f' % (var_removed, p_value_removed))
				iter_times += 1

			if intercept:  
				formula = "{} ~ {} + 1".format(response, ' + '.join(selected))
			else:
				formula = "{} ~ {} - 1".format(response, ' + '.join(selected))

			self.stepwise_model = smf.ols(formula, df).fit()  
			if show_step: 
				print('\nLinear regression model:', '\n  ', self.stepwise_model.model.formula)
				print('\n', self.stepwise_model.summary())
				# final variables selected
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
for test_user in temp_store_SE_100:
    df = pd.DataFrame({'mobility':test_user.loc[:, 'num_of_transition'],'TST':test_user.loc[:, 'TST(hour)'],
                   'SOL':test_user.loc[:, 'SOL(min)'],'WASO':test_user.loc[:, 'WASO(min)'],
                   'TIB':test_user.loc[:, 'duraion_in_bed'],'Awake':test_user.loc[:, 'awake_count'],
                   'SE':test_user.loc[:, 'SE']
                   })

    the_model = FeatureSelection().stepwise(df=df, response='mobility', direction='both',max_iter=5,criterion='ssr')  # criterion='ssr'是为了移除不合适特征
    # [' bic', 'aic', 'ssr', 'rsquared', 'rsquared_adj'] 
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
new_index = ['TST', 'SOL','WASO', 'Awake', 'TIB','SE']
sol_coefs=[];waso_coefs=[];tst_coefs=[];tib_coefs=[];awake_coefs=[];se_coefs=[]
for each_user_coef in parameters_list:
    each_user_coef = each_user_coef.reindex(new_index,fill_value=np.nan)
    tst_coefs.append(each_user_coef.loc['TST'])
    sol_coefs.append(each_user_coef.loc['SOL'])
    awake_coefs.append(each_user_coef.loc['Awake'])
    tib_coefs.append(each_user_coef.loc['TIB'])
    waso_coefs.append(each_user_coef.loc['WASO'])
    se_coefs.append(each_user_coef.loc['SE'])
# create a df to store results
OLS_result_stepwise = pd.DataFrame({'age':age_list,'gender':gender_list,'data_points(days)':valid_len,
                           'R_squared_adj':models_adj_r_squared,'coef_TST':tst_coefs,
                           'coef_SOL':sol_coefs,'coef_WASO':waso_coefs,'coef_TIB':tib_coefs,
                           'coef_Awake':awake_coefs,'coef_SE':se_coefs,'p_value':p_val_list})    
'''
test_user=temp_store[13]
df = pd.DataFrame({'mobility':test_user.loc[:, 'num_of_transition'],'TST':test_user.loc[:, 'TST(hour)'],
                   'SOL':test_user.loc[:, 'SOL(min)'],'WASO':test_user.loc[:, 'WASO(min)'],
                   'TIB':test_user.loc[:, 'duraion_in_bed'],'Awake':test_user.loc[:, 'awake_count'],
                   'SE':test_user.loc[:, 'SE']
                   })

#plt.scatter(df['WASO'],df['mobility'])    

the_model = FeatureSelection().stepwise(df=df, response='mobility', direction='both',max_iter=5,criterion='ssr')  
# criterion='ssr'is to remove coef with p-val>0.05
fig = sm.graphics.plot_ccpr(the_model.stepwise_model, "TIB")
fig.tight_layout(pad=1.0)    
'''
 

#OLS_result_stepwise.to_excel(r'F:/OLS_reuslts_36_individuals_backward_selection_highest_R_squared.xlsx',index=False)
'''
OLS_result_stepwise.loc[OLS_result_stepwise['gender'] ==1, 'gender'] = 'male'
OLS_result_stepwise.loc[OLS_result_stepwise['gender'] ==2, 'gender'] = 'female'
OLS_result_stepwise.loc[(OLS_result_stepwise['age'] >=70) & (OLS_result_stepwise['age'] <80), 'age'] = 70
OLS_result_stepwise.loc[(OLS_result_stepwise['age'] >=80) & (OLS_result_stepwise['age'] <90), 'age'] = 80
OLS_result_stepwise.loc[(OLS_result_stepwise['age'] >=90) & (OLS_result_stepwise['age'] <100), 'age'] = 90
OLS_result_stepwise.loc[OLS_result_stepwise['age'] ==70, 'age'] = '70s'
OLS_result_stepwise.loc[OLS_result_stepwise['age'] ==80, 'age'] = '80s'
OLS_result_stepwise.loc[OLS_result_stepwise['age'] ==90, 'age'] = '90s'


a = OLS_result_stepwise.loc[OLS_result_stepwise['gender'] =='male', 'R_squared_adj']
b = OLS_result_stepwise.loc[OLS_result_stepwise['gender'] =='female', 'R_squared_adj']
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
'''

#############################################################################
# non param tests
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
    
#selected_df_female_70s['home_care_package_level'].describe()
#selected_df_female['home_care_package_level'].describe()
#selected_df_male['ATSM'].describe()

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
mann_whitney_test_results = pd.DataFrame({'index':list_index,'U_stats':pstat,'p_val':pval})
print(mann_whitney_test_results)


#--------------------------------visualization
'''
# male and female distributions, gender is fixed
kwargs = dict(alpha=0.5, bins=50)
c1='#00aaff';c2='y'
male_label = 'male'
female_label = 'female'

plt.figure(figsize=(8,15))
plt.subplot(4,2,1)
plt.hist([item for sublist in mobility_data_male for item in sublist],**kwargs, color=c1, label=male_label+' mobility')
plt.hist([item for sublist in mobility_data_female for item in sublist],**kwargs, color=c2, label=female_label+' mobility')
plt.xlabel('steps');plt.legend()
plt.subplot(4,2,2)
plt.hist([item for sublist in sleep_tst_male for item in sublist],**kwargs, color=c1, label=male_label+' TST')
plt.hist([item for sublist in sleep_tst_female for item in sublist],**kwargs, color=c2, label=female_label+' TST')
plt.xlabel('TST(hour)');plt.legend()
plt.subplot(4,2,3)
plt.hist([item for sublist in sleep_sol_male for item in sublist],**kwargs, color=c1, label=male_label+' SOL')
plt.hist([item for sublist in sleep_sol_female for item in sublist],**kwargs, color=c2, label=female_label+' SOL')
plt.xlabel('SOL(min)');plt.legend()
plt.subplot(4,2,4)
plt.hist([item for sublist in sleep_waso_male for item in sublist],**kwargs, color=c1, label=male_label+' WASO')
plt.hist([item for sublist in sleep_waso_female for item in sublist],**kwargs, color=c2, label=female_label+' WASO')
plt.xlabel('WASO(min)');plt.legend()
plt.subplot(4,2,5)
plt.hist([item for sublist in sleep_duration_in_bed_male for item in sublist],**kwargs, color=c1, label=male_label+' TIB')
plt.hist([item for sublist in sleep_duration_in_bed_female for item in sublist],**kwargs, color=c2, label=female_label+' TIB')
plt.xlabel('TIB(hour)');plt.legend()
plt.subplot(4,2,6)
plt.hist([item for sublist in sleep_awake_male for item in sublist],**kwargs, color=c1, label=male_label+' Awake')
plt.hist([item for sublist in sleep_awake_female for item in sublist],**kwargs, color=c2, label=female_label+' Awake')
plt.xlabel('awakenings');plt.legend()
plt.subplot(4,2,7)
plt.hist([item for sublist in sleep_effi_male for item in sublist],**kwargs, color=c1, label=male_label+' SE')
plt.hist([item for sublist in sleep_effi_female for item in sublist],**kwargs, color=c2, label=female_label+' SE')
plt.xlabel('SE');plt.legend()

'''


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
age_70s=[mobility_data_70s,sleep_tst_70s,sleep_sol_70s,sleep_effi_70s,sleep_waso_70s,
      sleep_duration_in_bed_70s,sleep_awake_70s  ]


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
age_80s=[mobility_data_80s,sleep_tst_80s,sleep_sol_80s,sleep_effi_80s,sleep_waso_80s,
      sleep_duration_in_bed_80s,sleep_awake_80s  ]

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
age_90s=[mobility_data_90s,sleep_tst_90s,sleep_sol_90s,sleep_effi_90s,sleep_waso_90s,
      sleep_duration_in_bed_90s,sleep_awake_90s  ]

#--------------
# test 3 groups are different
def three_group_kruskal_ttest(group_a, group_b,group_c):
    a = [item for sublist in group_a for item in sublist]
    b = [item for sublist in group_b for item in sublist]
    c = [item for sublist in group_c for item in sublist]
    ttest,pval = stats.kruskal(a,b,c)
    return ttest,pval

def kruskal_test_print_results(age_list1,age_list2,age_list3):
    '''gender_list: list_of_parameter_from_a_selected_group'''
    stats=[];p_val=[]
    for i in range(len(age_list1)):
        each_para_age1 = age_list1[i]
        each_para_age2 = age_list2[i]
        each_para_age3 = age_list3[i]
        u,pval = three_group_kruskal_ttest(each_para_age1, each_para_age2, each_para_age3)
        stats.append("{:.2f}".format(u))
        p_val.append("{:.4f}".format(pval))
    return stats,p_val

pstat,pval = kruskal_test_print_results(age_70s,age_80s,age_90s)
list_index=['mobility','TST','SOL','SE','WASO','TIB','Awake']
kruskal_test_results = pd.DataFrame({'index':list_index,'H_stats':pstat,'p_val':pval})
print(kruskal_test_results)
#--------------- post hoc
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

post_hoc_dunn_result = pd.concat([post_hoc_dunn_result0,post_hoc_dunn_result1,post_hoc_dunn_result2,post_hoc_dunn_result3,
           post_hoc_dunn_result4,post_hoc_dunn_result5,post_hoc_dunn_result6], sort=False)    
print(post_hoc_dunn_result)



# Mann-Whitney t tests

u,p = two_group_Mann_Whitney_test(mobility_data_70s, mobility_data_80s)


#--------------Visualization
'''
kwargs = dict(alpha=0.5, bins=100)
plt.figure(figsize=(8,15))
plt.subplot(4,2,1)
plt.hist([item for sublist in mobility_data_70s for item in sublist],**kwargs, color='b', label='70s mobility')
plt.hist([item for sublist in mobility_data_80s for item in sublist],**kwargs, color='r', label='80s mobility')
plt.hist([item for sublist in mobility_data_90s for item in sublist],**kwargs, color='g', label='90s mobility')
plt.legend()
plt.subplot(4,2,2)
plt.hist([item for sublist in sleep_tst_70s for item in sublist],**kwargs, color='b', label='70s TST')
plt.hist([item for sublist in sleep_tst_80s for item in sublist],**kwargs, color='r', label='80s TST')
plt.hist([item for sublist in sleep_tst_90s for item in sublist],**kwargs, color='g', label='90s TST')
plt.legend()
plt.subplot(4,2,3)
plt.hist([item for sublist in sleep_sol_70s for item in sublist],**kwargs, color='b', label='70s SOL')
plt.hist([item for sublist in sleep_sol_80s for item in sublist],**kwargs, color='r', label='80s SOL')
plt.hist([item for sublist in sleep_sol_90s for item in sublist],**kwargs, color='g', label='90s SOL')
plt.legend()
plt.subplot(4,2,4)
plt.hist([item for sublist in sleep_waso_70s for item in sublist],**kwargs, color='b', label='70s WASO')
plt.hist([item for sublist in sleep_waso_80s for item in sublist],**kwargs, color='r', label='80s WASO')
plt.hist([item for sublist in sleep_waso_90s for item in sublist],**kwargs, color='g', label='90s WASO')
plt.legend()
plt.subplot(4,2,5)
plt.hist([item for sublist in sleep_duration_in_bed_70s for item in sublist],**kwargs, color='b', label='70s TIB')
plt.hist([item for sublist in sleep_duration_in_bed_80s for item in sublist],**kwargs, color='r', label='80s TIB')
plt.hist([item for sublist in sleep_duration_in_bed_90s for item in sublist],**kwargs, color='g', label='90s TIB')
plt.legend()
plt.subplot(4,2,6)
plt.hist([item for sublist in sleep_awake_70s for item in sublist],**kwargs, color='b', label='70s Awake')
plt.hist([item for sublist in sleep_awake_80s for item in sublist],**kwargs, color='r', label='80s Awake')
plt.hist([item for sublist in sleep_awake_90s for item in sublist],**kwargs, color='g', label='90s Awake')
plt.legend()
plt.subplot(4,2,7)
plt.hist([item for sublist in sleep_effi_70s for item in sublist],**kwargs, color='b', label='70s SE')
plt.hist([item for sublist in sleep_effi_80s for item in sublist],**kwargs, color='r', label='80s SE')
plt.hist([item for sublist in sleep_effi_90s for item in sublist],**kwargs, color='g', label='90s SE')
plt.legend()
'''

#############################################################################
# get basic stats and tests
#############################################################################
def get_mean_and_std(group_a):
    a = np.asarray([item for sublist in group_a for item in sublist])
    avg = np.nanmean(a)
    std = np.nanstd(a)
    return avg,std

avg0,std0 = get_mean_and_std(mobility_data_70s)
print("{:.2f}".format(avg0),'±',"{:.2f}".format(std0))
avg1,std1 = get_mean_and_std(mobility_data_80s)
print("{:.2f}".format(avg1),'±',"{:.2f}".format(std1))
avg2,std2 = get_mean_and_std(mobility_data_90s)
print("{:.2f}".format(avg2),'±',"{:.2f}".format(std2))
avg3,std3 = get_mean_and_std(mobility_data_male)
print("{:.2f}".format(avg3),'±',"{:.2f}".format(std3))
avg4,std4 = get_mean_and_std(mobility_data_female)
print("{:.2f}".format(avg4),'±',"{:.3f}".format(std4))

avg0,std0 = get_mean_and_std(sleep_tst_70s)
print("{:.2f}".format(avg0),'±',"{:.2f}".format(std0))
avg1,std1 = get_mean_and_std(sleep_tst_80s)
print("{:.2f}".format(avg1),'±',"{:.2f}".format(std1))
avg2,std2 = get_mean_and_std(sleep_tst_90s)
print("{:.2f}".format(avg2),'±',"{:.2f}".format(std2))
avg3,std3 = get_mean_and_std(sleep_tst_male)
print("{:.2f}".format(avg3),'±',"{:.2f}".format(std3))
avg4,std4 = get_mean_and_std(sleep_tst_female)
print("{:.2f}".format(avg4),'±',"{:.3f}".format(std4))

avg0,std0 = get_mean_and_std(sleep_sol_70s)
print("{:.2f}".format(avg0),'±',"{:.2f}".format(std0))
avg1,std1 = get_mean_and_std(sleep_sol_80s)
print("{:.2f}".format(avg1),'±',"{:.2f}".format(std1))
avg2,std2 = get_mean_and_std(sleep_sol_90s)
print("{:.2f}".format(avg2),'±',"{:.2f}".format(std2))
avg3,std3 = get_mean_and_std(sleep_sol_male)
print("{:.2f}".format(avg3),'±',"{:.2f}".format(std3))
avg4,std4 = get_mean_and_std(sleep_sol_female)
print("{:.2f}".format(avg4),'±',"{:.3f}".format(std4))

avg0,std0 = get_mean_and_std(sleep_waso_70s)
print("{:.2f}".format(avg0),'±',"{:.2f}".format(std0))
avg1,std1 = get_mean_and_std(sleep_waso_80s)
print("{:.2f}".format(avg1),'±',"{:.2f}".format(std1))
avg2,std2 = get_mean_and_std(sleep_waso_90s)
print("{:.2f}".format(avg2),'±',"{:.2f}".format(std2))
avg3,std3 = get_mean_and_std(sleep_waso_male)
print("{:.2f}".format(avg3),'±',"{:.2f}".format(std3))
avg4,std4 = get_mean_and_std(sleep_waso_female)
print("{:.2f}".format(avg4),'±',"{:.3f}".format(std4))

avg0,std0 = get_mean_and_std(sleep_duration_in_bed_70s)
print("{:.2f}".format(avg0),'±',"{:.2f}".format(std0))
avg1,std1 = get_mean_and_std(sleep_duration_in_bed_80s)
print("{:.2f}".format(avg1),'±',"{:.2f}".format(std1))
avg2,std2 = get_mean_and_std(sleep_duration_in_bed_90s)
print("{:.2f}".format(avg2),'±',"{:.2f}".format(std2))
avg3,std3 = get_mean_and_std(sleep_duration_in_bed_male)
print("{:.2f}".format(avg3),'±',"{:.2f}".format(std3))
avg4,std4 = get_mean_and_std(sleep_duration_in_bed_female)
print("{:.2f}".format(avg4),'±',"{:.3f}".format(std4))

avg0,std0 = get_mean_and_std(sleep_awake_70s)
print("{:.2f}".format(avg0),'±',"{:.2f}".format(std0))
avg1,std1 = get_mean_and_std(sleep_awake_80s)
print("{:.2f}".format(avg1),'±',"{:.2f}".format(std1))
avg2,std2 = get_mean_and_std(sleep_awake_90s)
print("{:.2f}".format(avg2),'±',"{:.2f}".format(std2))
avg3,std3 = get_mean_and_std(sleep_awake_male)
print("{:.2f}".format(avg3),'±',"{:.2f}".format(std3))
avg4,std4 = get_mean_and_std(sleep_awake_female)
print("{:.2f}".format(avg4),'±',"{:.3f}".format(std4))

avg0,std0 = get_mean_and_std(sleep_effi_70s)
print("{:.2f}".format(avg0),'±',"{:.2f}".format(std0))
avg1,std1 = get_mean_and_std(sleep_effi_80s)
print("{:.2f}".format(avg1),'±',"{:.2f}".format(std1))
avg2,std2 = get_mean_and_std(sleep_effi_90s)
print("{:.2f}".format(avg2),'±',"{:.2f}".format(std2))
avg3,std3 = get_mean_and_std(sleep_effi_male)
print("{:.2f}".format(avg3),'±',"{:.2f}".format(std3))
avg4,std4 = get_mean_and_std(sleep_effi_female)
print("{:.2f}".format(avg4),'±',"{:.3f}".format(std4))

#male=[mobility_data_male,sleep_tst_male,sleep_sol_male,sleep_effi_male,sleep_waso_male,
#      sleep_duration_in_bed_male,sleep_awake_male
#      ]
#age_70s=[mobility_data_70s,sleep_tst_70s,sleep_sol_70s,sleep_effi_70s,sleep_waso_70s,
#      sleep_duration_in_bed_70s,sleep_awake_70s  ]


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
