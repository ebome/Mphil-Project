from scipy import stats
import pandas as pd
import datetime as dt
import numpy as np
from matplotlib import pyplot as plt
import copy



all_dacs_sensor = pd.read_csv(r'D:\DACS\Archive\all_user_motion_sensor_up_to_may.csv')
# remove the features that are not needed
all_dacs_sensor = all_dacs_sensor.drop(columns=['Unnamed: 0','room_id'])
# remove "chair" since this is for tranfer in ADL
all_dacs_sensor = all_dacs_sensor[~all_dacs_sensor['sensor_name'].str.contains('Chair')]
#-----------------------------
all_dacs_mobility = pd.read_csv(r'D:/DACS/Archive/all_user_mobility_up_to_Aug.csv')
all_dacs_mobility = all_dacs_mobility[['PID','localTimeMeasured','value']]
# mobility has time format YY-MM-DD but sensor also has hours
all_dacs_mobility['local_timestamp'] = [dt.datetime.strptime(date[0:-9], '%d/%m/%Y').date() for date in all_dacs_mobility['localTimeMeasured']] 
#-----------------------------
# Create solitray users list
solitary_list_intervention_group = pd.read_excel(r'D:\DACS\Archive\DACS_users_live_alone.xlsx')
solitary_list_intervention_group = solitary_list_intervention_group[solitary_list_intervention_group['living_arrangments']==1]
solitary_list_intervention_group =  solitary_list_intervention_group[solitary_list_intervention_group['randomised_group']==1]
solitary_users = solitary_list_intervention_group['record_id'].tolist()

# Remove non-solitary users from sensor and mobility data 
solitary_dacs_mobility = all_dacs_mobility[all_dacs_mobility['PID'].isin(solitary_users)]
solitary_dacs_sensor = all_dacs_sensor[all_dacs_sensor['PID'].isin(solitary_users)]

# check that '3-4' is in mobility , not sensor, so remove 3-4 from mobility
solitary_dacs_mobility = solitary_dacs_mobility[~solitary_dacs_mobility['PID'].isin(['3-4'])]
people_list_sensor = solitary_dacs_sensor['PID'].unique().tolist()
people_list_mobility = solitary_dacs_mobility['PID'].unique().tolist()

#-----------------------------
# split the whole data into different people/unit
mobility_grouped_list = list(solitary_dacs_mobility.groupby(['PID']))
sensor_grouped_list = list(solitary_dacs_sensor.groupby(['PID']))

#############################################################################
# Group the mobility and sensor data first, pre-selecting of useful time 
# and data in sensor readings by remove 0
#############################################################################
# reform the mobility since cleaned_sensor_list and mobility_list have same PID units
reformed_mobility_list_temp=[]    
for each_unit in mobility_grouped_list:
    unit_motiondata = each_unit[1]
    # remove all zeros in mobility
    unit_motiondata = unit_motiondata[unit_motiondata['value']!= 0]
    reformed_mobility_list_temp.append(unit_motiondata)
    
#-------------------------------------------------
# Delete the '0' signal in sensors, change the dataframe
def reform_df(MotionData_ila):

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
    
reformed_sensor_list_temp=[]
for each_PID in sensor_grouped_list:
    PID_motiondata = each_PID[1]
    reformed_each_df = reform_df(PID_motiondata)
    reformed_sensor_list_temp.append(reformed_each_df)

#-------------------------------------------------
# reformed_mobility_list have removed some users, so the users should be removed
# in reformed_sensor_list as well
reformed_sensor_list = [];reformed_mobility_list=[]
for i in range(len(reformed_mobility_list_temp)):
    if len(reformed_mobility_list_temp[i]) > 10:
        reformed_sensor_list.append(reformed_sensor_list_temp[i])
        reformed_mobility_list.append(reformed_mobility_list_temp[i])

#-------------------------------------------------
# get users in mobility, check whether two are equal
user_list_mob=[];user_list_sensor=[]
for i in range(len(reformed_mobility_list)):
    user_list_mob.append(reformed_mobility_list[i]['PID'].tolist()[0])
    user_list_sensor.append(reformed_sensor_list[i]['PID'].tolist()[0])
    
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

are_user_same = debugging_two_temp_list_value(user_list_mob,user_list_sensor)
    
#----------------------------------------------------------------------------- 
# For each unit in reformed_mobility_list and reformed_sensor_list, remove the 
# dates that in reformed_sensor_list but not in reformed_mobility_list
cleaned_sensor_list = [];deleted_list_for_all_day=[]
for i in range(len(reformed_sensor_list)):
    each_PID = reformed_sensor_list[i]
    each_unit = reformed_mobility_list[i]
    # for the two dataframe, check the time
    mobility_date = each_unit['local_timestamp'].tolist()
    sensor_date = each_PID['exact_time'].tolist()
    # mobility has time format YY-MM-DD but sensor also has hours
    sensor_date = [dt.datetime.strptime(date[0:19], '%Y-%m-%d %H:%M:%S') for date in sensor_date]
    # sensor hours can be removed
    sensor_date_truncated = [each_day.date() for each_day in sensor_date] 
    sensor_date_truncated_distinct = list(set(sensor_date_truncated)) # distinct dates
    # find the days that in mobility but not in sensor reading
    date_not_in_mobility = [elem for elem in sensor_date_truncated_distinct if elem not in mobility_date]
    # remove repetitive items in date_not_in_mobility
    date_notin_mobility = list(set(date_not_in_mobility))
    date_notin_mobility = sorted(date_notin_mobility)
    # transfer the list back to str format
    aaa = [each_date.__str__() for each_date in date_notin_mobility] 

    # after the for loop, each_unit in mobility will have all dates in each_PID
    # just add a for loop to remove each date in aaa(date in sensor but not in mobility)
    deleted_list=[]
    for a in aaa:
        # find the sensor readings that should be deleted
        deleted = each_PID[each_PID['exact_time'].str.contains(a)]
        deleted_list.append(deleted)
        # remove these units from sensor reading dataframe
        each_PID = pd.concat([each_PID, deleted]).drop_duplicates(keep=False)

    cleaned_sensor_list.append(each_PID)
    deleted_list_for_all_day.append(deleted_list)
    
#----------------------------------------------------------------------------- 
# Same, for each unit in reformed_mobility_list and reformed_sensor_list, remove the 
# dates that in reformed_mobility_list but not in reformed_sensor_list
cleaned_mobility_list = [];
for i in range(len(cleaned_sensor_list)):
    each_PID = cleaned_sensor_list[i]
    each_unit = reformed_mobility_list[i]
    # for the two dataframe, check the time
    mobility_date = each_unit['local_timestamp'].tolist()
    sensor_date = each_PID['exact_time'].tolist()
    #  mobility has time format YY-MM-DD but sensor also has hours
    sensor_date = [dt.datetime.strptime(date[0:19], '%Y-%m-%d %H:%M:%S') for date in sensor_date]
    
    # sensor hours can be removed
    sensor_date_truncated = [each_day.date() for each_day in sensor_date] 
    sensor_date_truncated_distinct = list(set(sensor_date_truncated)) # distinct dates
    
    # find the days that in sensor reading but not in mobility
    date_not_in_sensor = [elem for elem in mobility_date if elem not in sensor_date_truncated_distinct]
    # remove repetitive items in date_not_in_mobility
    date_notin_sensor = list(set(date_not_in_sensor))
    date_notin_sensor = sorted(date_notin_sensor) # date_notin_sensor is a list with date elements
    
    # remove the mobility dates that should be deleted
    keeped_mobility_unit = each_unit[~each_unit['local_timestamp'].isin(date_notin_sensor)]
    cleaned_mobility_list.append(keeped_mobility_unit)


#############################################################################
# Mobility (fixed-distance step, distance travelled): ground truth
#############################################################################
# Ground truth mobility, ignore those who have data less than 29 days
temp_mobility=[]
for each_user_mobility in cleaned_mobility_list:
    aa = each_user_mobility['value'].tolist()
    temp_mobility.append(aa) 
    
flat_mobility = [item for sublist in temp_mobility for item in sublist]
print('flat_mobility = ', len(flat_mobility))
    
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
for each_PID in cleaned_sensor_list:
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
# now we know max_room=10, min_room=6

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
import merge_sensors as ms # make sure they are in same dir, run ms first

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

'''
time span for mobility: 2019/04/26 - 2020/05/26(included) (maximal 376 days in cleaned_mobility_list). 
Just remove the dates that are not in this range for sensor_list
'''    
# Chopped datetime       
base = dt.datetime.strptime('2019-04-26 00:00:00', '%Y-%m-%d %H:%M:%S')
datelist = pd.date_range(base, periods=400).tolist()
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
    transition=[]
    
    first_date_in_cleaned_ila = cleaned_ila['local_timestamp'].tolist()[0]
    last_date_in_cleaned_ila = cleaned_ila['local_timestamp'].tolist()[-1]
    for i in range(len(choppedTime)-1):
        # get daily motion data
        choppedila_day  = cleaned_ila[cleaned_ila['local_timestamp'] > choppedTime[i]]
        choppedila_day  = choppedila_day[choppedila_day['local_timestamp'] < choppedTime[i+1]]
               
        # choppedTime start  4-26, hence the choppedila_day is length 0 before the start date
        if first_date_in_cleaned_ila > choppedTime[i+1] or last_date_in_cleaned_ila < choppedTime[i]:
            continue
        # after the first date, if there is no sensor record in that day, mark the step as 1
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
    
    return transition


### LONG COMPUTING TIME!
temp_transition=[]
for each_user in finally_sensor_list:
    transition = get_transition_arrays(each_user,choppedTime)
    temp_transition.append(transition) 

flat_transition = [item for sublist in temp_transition for item in sublist]
print('flat_transition = ',  len(flat_transition))

# for debug
a_temp_transition=[]
for mob in temp_transition:
    a_temp_transition.append(len(mob))
a_temp_mobility=[]
for trans in temp_mobility:
    a_temp_mobility.append(len(trans))  
    
aaa_indices_mob_trans = debugging_two_temp_list_value(a_temp_transition,a_temp_mobility)
print('if indices has all TRUE in elements, then bug free')

plt.figure(figsize=(18,6))
plt.plot(temp_transition[35])
plt.title('daily room transition as mobility')

#############################################################################
# DEBUG section
# If ground truth mobility have 0 in one day, then num of room transition
# will miss that day, cause its length reduced, so we need to match it with mobility
#############################################################################
temp_transition_copied = copy.deepcopy(temp_transition)

for i in range(len(temp_mobility)):
    if len(temp_transition[i]) == len(temp_mobility[i]):
        continue
    if len(temp_transition[i]) != len(temp_mobility[i]):
        user_sensor_readings = finally_sensor_list[i]
        user_mobility = cleaned_mobility_list[i]
        sensor_date = user_sensor_readings['exact_time'].values.tolist()              
        user_sensor_date = [dt.datetime.strptime(date[0:19], '%Y-%m-%d %H:%M:%S') for date in sensor_date]
        user_sensor_date = [each_day.date() for each_day in user_sensor_date] 
        user_sensor_date_unique = sorted(list(set(user_sensor_date))) # distinct dates
        user_mobility_date_unique = user_mobility['local_timestamp'].values.tolist()
        # compare user_sensor_date_unique and user_mobility_date_unique to find the missing items in user_sensor_date_unique
        missing_days_in_sensor = list(set(user_mobility_date_unique) - set(user_sensor_date_unique))

        missing_days_in_sensor_index_list = []
        for each_day in missing_days_in_sensor:
            missing_days_in_sensor_index = [i for i, x in enumerate(user_mobility_date_unique) if x == each_day]
            missing_days_in_sensor_index_list.append(missing_days_in_sensor_index)

        # add 0 in temp_transition[i] in front of the value
        for index in missing_days_in_sensor_index_list:
            temp_transition_copied[i].insert(index[0], 0)

# for debug
index=5
user_sensor_readings = finally_sensor_list[index]
user_mobility = cleaned_mobility_list[index]
sensor_date = user_sensor_readings['exact_time'].values.tolist()              
user_sensor_date = [dt.datetime.strptime(date[0:19], '%Y-%m-%d %H:%M:%S') for date in sensor_date]
user_sensor_date = [each_day.date() for each_day in user_sensor_date] 
user_sensor_date_unique = sorted(list(set(user_sensor_date))) # distinct dates
user_mobility_date_unique = user_mobility['local_timestamp'].values.tolist()
missing_days_in_sensor = list(set(user_mobility_date_unique) - set(user_sensor_date_unique))
missing_days_in_sensor_index_list = []
for each_day in missing_days_in_sensor:
    missing_days_in_sensor_index = [i for i, x in enumerate(user_mobility_date_unique) if x == each_day]
    missing_days_in_sensor_index_list.append(missing_days_in_sensor_index)

#############################################################################
# Get the total sensor firing counts
#############################################################################
all_total_triggering = []
for each_user in cleaned_sensor_list:
    total_firing = []
    for i in range(len(choppedTime)-1):
        chopped_day  = each_user[each_user['local_timestamp'] > choppedTime[i]]
        choppedila_day  = chopped_day[chopped_day['local_timestamp'] < choppedTime[i+1]]
        total_firing_in_that_day = len(choppedila_day)
        total_firing.append(total_firing_in_that_day)
        final_total_firing = list(filter(lambda a: a != 0, total_firing))
    all_total_triggering.append(final_total_firing)

temp_total_triggering = []
for each_user_total_firing in all_total_triggering:
    temp_total_triggering.append(each_user_total_firing) 
    
flat_total_firing = [item for sublist in temp_total_triggering for item in sublist]
print('flat_total_firing = ',  len(flat_total_firing))
#############################################################################
# If ground truth mobility have 0 in one day, then total firing
# will miss that day, cause its length reduced, so we need to match it with mobility
#############################################################################
for i in range(len(temp_mobility)):
    if len(temp_total_triggering[i]) == len(temp_mobility[i]):
        continue
    if len(temp_total_triggering[i]) < len(temp_mobility[i]):
        # find where 0 locate in temp_mobility[i], it could be a list or a value
        missing_day_0_mobility_index_list = [i for i, x in enumerate(temp_mobility[i]) if x == 0]
        # add 0 in temp_total_triggering[i] in front of the value
        for index in missing_day_0_mobility_index_list:
            temp_total_triggering[i].insert(index, 0)

#############################################################################
# Get the fixed-speed mobility
#############################################################################
# remove consecutive deuplicats and keep the first and last  
# https://stackoverflow.com/questions/51269456/pandas-delete-consecutive-duplicates-but-keep-the-first-and-last-value
def remove_consecutive_dup(one_user_sensor_data):
    # know how many sensors in this user house
    s = change_sensor_name(one_user_sensor_data)
    num_of_rooms=len(s['changed_sensor_id'].unique().tolist())
    for i in range(num_of_rooms):
        s = s.loc[s['changed_sensor_id'].replace(i,np.nan).ffill(limit=1).bfill(limit=1).notnull()]
    return s

remove_consecutive_dup_motion_data = []
for i in range(len(cleaned_sensor_list)):
    aaa = remove_consecutive_dup(cleaned_sensor_list[i])
    remove_consecutive_dup_motion_data.append(aaa)

'''
For each user, the average time from room A to room B(and room B to room A) is constant by assumption.
(Assume the user is always doing uniform linear motion in a constant speed, this speed is unknown but
should be found from literature. Here we assume all participants have speed 80 beats/minutes. Hence 4/3 step/second)

A --> B is a unit, then the reciprocal of avg A--> B time (e.g. 21 seconds becomes 1/21 unit/second) indicates
the avg time for this user to complete the unit. So the distance between A and B is
4/3 (step/s) /  1/21  (unit/s) = 28 step/unit. Then for each day, the total time for A-->B is known,
so we know how many 'A-->B unit' the user walks. By multiplying the distance we can get steps for 
A--> B
'''
def labelled_room_and_time_diff(cleaned_ila):
    tempDF = pd.DataFrame({})
    temp1=[];temp2=[]
    for i in range(0, len(cleaned_ila)-1):
        room_previous_sensor = cleaned_ila.iloc[i]['changed_sensor_id'] 
        room_next_sensor =  cleaned_ila.iloc[i+1]['changed_sensor_id']
        if room_previous_sensor == room_next_sensor: 
            continue
        
        # only if room_previous_sensor != room_next_sensor indicate room transition
        elif room_previous_sensor != room_next_sensor:
            label = str(int(room_previous_sensor))+' to '+str(int(room_next_sensor)) 
            temp1.append(label)
            room_previous_time = cleaned_ila.iloc[i]['exact_time'][0:19] 
            room_previous_time = dt.datetime.strptime(room_previous_time, '%Y-%m-%d %H:%M:%S')
            room_next_time =  cleaned_ila.iloc[i+1]['exact_time'][0:19]
            room_next_time = dt.datetime.strptime(room_next_time, '%Y-%m-%d %H:%M:%S')
            time_diff =  (room_next_time - room_previous_time).seconds
            temp2.append(time_diff)

    tempDF['label'] = temp1
    tempDF['time difference'] = temp2
    return tempDF


def get_time_diff_list(cleaned_ila,choppedTime):
    room_num = len(cleaned_ila['changed_sensor_id'].unique().tolist())
    transition=[];time_diff_list_all_days=[];day=[]
    for i in range(len(choppedTime)-1):
        # get daily sensor reading
        choppedila_day  = cleaned_ila[cleaned_ila['local_timestamp'] > choppedTime[i]]
        choppedila_day  = choppedila_day[choppedila_day['local_timestamp'] < choppedTime[i+1]]
        # choppedTime start  4-26, hence sometime the choppedila_day could be length 0
        if len(choppedila_day)==0:
            continue
        # label the transitions and change them to merged transition labels
        ila_lablled = labelled_room_and_time_diff(choppedila_day)
        time_diff_list = ila_lablled['time difference'].values.tolist()
        # get choppedila_day dataframe's date
        that_day_list = choppedila_day.local_timestamp.tolist()
        that_day = that_day_list[0][0:10:] # trim datetime hours
        day.append(that_day)

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
    
        # temp has the same length as time_diff_list, they are all for one day
        time_diff_list_all_days.append(time_diff_list)
        transition.append(merge_labelled_ilaList)

    flat_transition = [item for sublist in transition for item in sublist]
    flat_time_diff = [item for sublist in time_diff_list_all_days for item in sublist]
    single_user_transion_time_diff=pd.DataFrame({'transition label':flat_transition,
                                             'time diff':flat_time_diff})
    # make them as dataframe
    single_user_transion_time_diff_with_date=pd.DataFrame({'Day':day,'transition label':transition,
                                             'time diff':time_diff_list_all_days})

    return single_user_transion_time_diff, single_user_transion_time_diff_with_date
#======================================
def get_time_diff_for_one_room_part_A(cleaned_ila,choppedTime):
    room_num = len(cleaned_ila['changed_sensor_id'].unique().tolist())
    transition=[];time_diff_list_all_days=[];day=[]
    for i in range(len(choppedTime)-1):
        # get daily sensor reading
        choppedila_day  = cleaned_ila[cleaned_ila['local_timestamp'] > choppedTime[i]]
        choppedila_day  = choppedila_day[choppedila_day['local_timestamp'] < choppedTime[i+1]]
        # choppedTime start  4-26, hence sometime the choppedila_day could be length 0
        if len(choppedila_day)==0:
            continue
        # label the transitions and change them to merged transition labels
        ila_lablled = labelled_room_and_time_diff(choppedila_day)
        time_diff_list = ila_lablled['time difference'].values.tolist()
        # get choppedila_day dataframe's date
        that_day_list = choppedila_day.local_timestamp.tolist()
        that_day = that_day_list[0][0:10:] # trim datetime hours
        day.append(that_day)

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
    
        # temp has the same length as time_diff_list, they are all for one day
        time_diff_list_all_days.append(time_diff_list)
        transition.append(merge_labelled_ilaList)
    
    return time_diff_list_all_days,transition,day

def get_time_diff_for_one_room_part_B(time_diff_list_all_days,transition,day,room_str):
    # now get the index for the room_label
    one_room_time_diff_by_days=[]
    for j in range(len(transition)):
        each_day_s_transition_label = transition[j]
        indices = []
        for i in range(len(each_day_s_transition_label)):
            if each_day_s_transition_label[i] == room_str:
                indices.append(i)
        
        store_list = []
        each_day_s_time_diff_one_room = time_diff_list_all_days[j]
        for each_index in indices:
           store_list.append(each_day_s_time_diff_one_room[each_index])
           
        one_room_time_diff_by_days.append(store_list)
    
    # make them as dataframe
    one_room_time_diff_with_date=pd.DataFrame({'Day':day,
                                             'one_room_time_diff':one_room_time_diff_by_days})

    return one_room_time_diff_with_date

#--------------------------------  
test_user = remove_consecutive_dup_motion_data[20]
single_user_transion_time_diff, single_user_transion_time_diff_with_date = get_time_diff_list(test_user,choppedTime)
aaa = single_user_transion_time_diff_with_date['transition label'].tolist()[0]
aaab = [x for xs in aaa for x in xs.split(',')]


def get_28day_allday_time_diff(one_user,choppedTime):
    time_diff_list_all_days,transition,day = get_time_diff_for_one_room_part_A(one_user,choppedTime)
    # get all room_str from 'transition'
    flat_transition = [item for sublist in transition for item in sublist]
    all_room_strs = list(set(flat_transition))
    # loop all_room_strs
    time_diff_for_all_room_pair=[]
    for room_str in all_room_strs:
        one_room_time_diff_with_date = get_time_diff_for_one_room_part_B(time_diff_list_all_days,transition,day,room_str)
        flat_one_room_time_diff_28day = [item for sublist in one_room_time_diff_with_date[0:29]['one_room_time_diff'].tolist() for item in sublist]
        avg_28day = np.asarray(flat_one_room_time_diff_28day).mean()
        flat_one_room_time_diff_Allday = [item for sublist in one_room_time_diff_with_date['one_room_time_diff'].tolist() for item in sublist]
        avg_Allday = np.asarray(flat_one_room_time_diff_Allday).mean()
        time_diff_for_all_room_pair.append(avg_Allday-avg_28day)
    return time_diff_for_all_room_pair

all_user_time_diff =[]
for each_user in remove_consecutive_dup_motion_data:
    time_diff_for_all_room_pair = get_28day_allday_time_diff(each_user,choppedTime)
    all_user_time_diff.append(time_diff_for_all_room_pair)

falt_all_user_time_diff= [item for sublist in all_user_time_diff for item in sublist]
cleanedList = [x for x in falt_all_user_time_diff if str(x) != 'nan']
plt.hist(cleanedList,bins=50)
cleanedList2 = [x for x in cleanedList if abs(x) < 240]
x = list(range(len(cleanedList2)))

plt.figure(figsize=(10,10))
plt.scatter(x,cleanedList2,c='r',s=10)
plt.xlabel('room pairs')


#---------------------------------------
def get_accumulate_avg_time(ploting_data_with_14_lists):
    indices = list(range(1,len(ploting_data_with_14_lists)+1))
    print(indices)
    avg_time_accumulation =[]
    for x in indices:
        flat_ploting_data_with_14_lists = [item for sublist in ploting_data_with_14_lists[0:x] for item in sublist]
        accumulate_avg = np.asarray(flat_ploting_data_with_14_lists).mean()
        avg_time_accumulation.append(accumulate_avg)
    return avg_time_accumulation

time_diff_list_all_days,transition,day = get_time_diff_for_one_room_part_A(test_user,choppedTime)
room_str = '1 to 2'
one_room_time_diff_with_date = get_time_diff_for_one_room_part_B(time_diff_list_all_days,transition,day,room_str)
day_length = 14
ploting_dates= one_room_time_diff_with_date.iloc[0:day_length+1]['Day'].tolist()
ploting_data= one_room_time_diff_with_date.iloc[0:day_length+1]['one_room_time_diff'].tolist()
avg_time_accumulation = get_accumulate_avg_time(ploting_data)
plt.plot(avg_time_accumulation);plt.xlabel('Days');plt.ylabel('Accumulative mean transiton time for two rooms')
plt.title(room_str+' transition time accumulative mean plot')

plt.figure(figsize=(10,5))
for xe, ye in zip(ploting_dates, ploting_data):
    plt.scatter([xe] * len(ye), ye, s=9, c='r')
plt.yscale('log')    
plt.title('user 3-175 '+room_str+' transition time')
plt.xlabel('First 14 days')
plt.ylabel('Log(Transition duration (seconds))')
plt.xticks(list(range(len(ploting_dates))))
plt.axes().set_xticklabels(ploting_dates,rotation='vertical')
#--------------------------------  
def find_avg_time_diff_for_labels(single_user_transion_time_diff,first_x_days):
    # find the avg time diff of each label
    time_diff_grouped_list = list(single_user_transion_time_diff.groupby(['transition label']))

    avg=[];labels=[];median =[];transition_time_every_day=[];
    for each_label in time_diff_grouped_list:
        transition_time_every_day.append(each_label[1]['time diff'].tolist())

        each_label_avg = np.array(each_label[1]['time diff'].tolist()[0:first_x_days+1]).mean()
        each_label_median = np.median(np.array(each_label[1]['time diff'].tolist()[0:first_x_days+1]))
        avg.append(each_label_avg)
        median.append(each_label_median)
        labels.append(each_label[0])
    avg_time_diff_for_labels = pd.DataFrame({'label':labels,'avg time(s)':avg,
                                             'median time(s)':median,
                                             'transition_time_every_day':transition_time_every_day})
    return avg_time_diff_for_labels
#--------------------------------  
avg_and_median_time_diff_for_labels = find_avg_time_diff_for_labels(single_user_transion_time_diff,28)
df = avg_and_median_time_diff_for_labels.copy(deep=True)
data_dict = dict(zip(df['label'].tolist(), df['median time(s)'].tolist()))
[data_dict[x] for x in aaab]
#--------------------------------  
def get_daily_sensor_derived_steps(avg_and_median_time_diff_for_labels, single_user_transion_time_diff_with_date):
    step_speed = 1.57 # value with unit: steps/second
    df = avg_and_median_time_diff_for_labels.copy(deep=True)
    data_dict = dict(zip(df['label'].tolist(), df['avg time(s)'].tolist()))

    # find every day room transition time avg/mediian sum 
    all_day_transition_labels = single_user_transion_time_diff_with_date['transition label'].tolist()
    all_days_fixed_speed_mobility=[]
    for daily_transition_labels in all_day_transition_labels:
        split_daily_transition_labels = [x for xs in daily_transition_labels for x in xs.split(',')]
        split_daily_transition_time = [data_dict[x] for x in split_daily_transition_labels]
        
        daily_total_transition_time = sum(split_daily_transition_time)
        daily_sensor_derived_steps = step_speed * daily_total_transition_time
        all_days_fixed_speed_mobility.append(daily_sensor_derived_steps)
    return all_days_fixed_speed_mobility

#--------------------------------
# LONG TIME COMPUTING !! ~ 10 min
temp_sensor_derived_steps=[]
for each_user in remove_consecutive_dup_motion_data:
    single_user_transion_time_diff, single_user_transion_time_diff_with_date = get_time_diff_list(each_user,choppedTime)
    # get the avg time diff for this user 
    avg_and_median_time_diff_for_labels = find_avg_time_diff_for_labels(single_user_transion_time_diff,28)
    # now for this user, every day there is a mobility. In total there are X days mobility
    this_user_all_the_days = get_daily_sensor_derived_steps(avg_and_median_time_diff_for_labels,single_user_transion_time_diff_with_date)
    temp_sensor_derived_steps.append(this_user_all_the_days) 

flat_sensor_derived_steps = [item for sublist in temp_sensor_derived_steps for item in sublist]
print('flat_sensor_derived_steps = ', len(flat_sensor_derived_steps))

# for debug
a_temp_sensor_derived_steps=[]
for fix_speed_mob in temp_sensor_derived_steps:
    a_temp_sensor_derived_steps.append(len(fix_speed_mob))    
aaa_indices_mob_fixspeed = debugging_two_temp_list_value(a_temp_sensor_derived_steps,a_temp_mobility)
print('if indices has all TRUE in elements, then bug free')


#############################################################################
# If ground truth mobility have 0 in one day, then sensor_derived step
# will miss that day, cause its length reduced, so we need to match it with mobility
#############################################################################
for i in range(len(temp_mobility)):
    if len(temp_sensor_derived_steps[i]) == len(temp_mobility[i]):
        continue
    if len(temp_sensor_derived_steps[i]) < len(temp_mobility[i]):
        # find where 0 locate in temp_mobility[i], it could be a list or a value
        missing_day_0_mobility_index_list = [i for i, x in enumerate(temp_mobility[i]) if x == 0]
        # add 0 in temp_sensor_derived_steps[i] in front of the value
        for index in missing_day_0_mobility_index_list:
            temp_sensor_derived_steps[i].insert(index, 0)

#############################################################################
# Boostrap
#############################################################################
def average(data):
    return sum(data) / len(data)

# https://blog.csdn.net/mimicoa/article/details/84723572 
def bootstrap(data, B, c, func):
    """
    get bootstrap confidence interval
    :param data: array to save sampled data
    :param B: amount of sampling, usually B>=1000
    :param c: confidence interval
    :param func: the estimation of samples
    :return: bootstrap confidence interval upper/lower boundary
    """
    array = np.array(data)
    n = len(array)
    if n ==0:
        return (0,0)
    
    sample_result_arr = []
    for i in range(B):
        index_arr = np.random.randint(0, n, size=n)
        data_sample = array[index_arr]
        sample_result = func(data_sample)
        sample_result_arr.append(sample_result)

    a = 1 - c
    k1 = int(B * a / 2)
    k2 = int(B * (1 - a / 2))
    auc_sample_arr_sorted = sorted(sample_result_arr)
    lower = auc_sample_arr_sorted[k1]
    higher = auc_sample_arr_sorted[k2]

    return lower, higher


flat_mobility = [item for sublist in temp_mobility for item in sublist]
flat_sensor_derived_steps = [item for sublist in temp_sensor_derived_steps for item in sublist]
flat_transition = [item for sublist in temp_transition for item in sublist]
flat_total_firing = [item for sublist in temp_total_triggering for item in sublist]

result3 = bootstrap(flat_total_firing, 1000, 0.95, average)
print(result3)

# view each parameter distribution
kwargs = dict(bins=30)
plt.figure(figsize =(12,12))
user = 38
plt.subplot(2,2,1)
plt.xlabel('Travelled Room Distance',fontsize=20, family = 'Times New Roman')
plt.ylabel('Frequency',fontsize=20,family = 'Times New Roman')
plt.xticks(fontsize=15, family='Times New Roman')
plt.yticks(fontsize=15, family='Times New Roman')
plt.hist(temp_mobility[user],**kwargs,color='#66ccff') # [a-b for a,b in zip(rho_list3,rho_list1)]

plt.subplot(2,2,2)
plt.xlabel('Fixed-speed Mobility',fontsize=20, family = 'Times New Roman')
plt.ylabel('Frequency',fontsize=20,family = 'Times New Roman')
plt.xticks(fontsize=15, family='Times New Roman')
plt.yticks(fontsize=15, family='Times New Roman')
plt.hist(temp_sensor_derived_steps[user],**kwargs) # [a-b for a,b in zip(rho_list3,rho_list1)]

plt.subplot(2,2,3)
plt.xlabel('Number of Room Transition',fontsize=20, family = 'Times New Roman')
plt.ylabel('Frequency',fontsize=20,family = 'Times New Roman')
plt.xticks(fontsize=15, family='Times New Roman')
plt.yticks(fontsize=15, family='Times New Roman')
plt.hist(temp_transition[user],**kwargs)

plt.subplot(2,2,4)
plt.xlabel('Total Sensor Firing',fontsize=20, family = 'Times New Roman')
plt.ylabel('Frequency',fontsize=20,family = 'Times New Roman')
plt.xticks(fontsize=15, family='Times New Roman')
plt.yticks(fontsize=15, family='Times New Roman')
plt.hist(temp_total_triggering[user],**kwargs)


#############################################################################
# Linear Regression on each of the individual
#############################################################################

from sklearn.linear_model import LinearRegression
# get the logistic regression for every user
# Y = a0 + a1*X, and we are trying to minimize residual r
# Z = b0 + b1*T, and we are trying to minimize residual r

r_sq_list1=[];intercept_list1=[];coef_list1=[]
r_sq_list2=[];intercept_list2=[];coef_list2=[]
r_sq_list3=[];intercept_list3=[];coef_list3=[]
for i in range(len(temp_sensor_derived_steps)):
    each_drived_step = temp_sensor_derived_steps[i]
    each_mobility = temp_mobility[i]
    each_total_trigger = temp_total_triggering[i]
    each_transition = temp_transition[i]
    
    x = np.array(each_mobility).reshape((-1, 1))
    y = np.array(each_transition)
    z = np.array(each_total_trigger)
    t = np.array(each_drived_step)


    model1 = LinearRegression()
    model1.fit(x, y)
    r_sq1 = model1.score(x, y)
    model2 = LinearRegression()
    model2.fit(x, z)
    r_sq2 = model2.score(x, z)
    model3 = LinearRegression()
    model3.fit(x, t)
    r_sq3 = model3.score(x, t)


    r_sq_list1.append(r_sq1)
    intercept_list1.append(model1.intercept_)
    coef_list1.append(model1.coef_)
    r_sq_list2.append(r_sq2)
    intercept_list2.append(model2.intercept_)
    coef_list2.append(model2.coef_)
    r_sq_list3.append(r_sq3)
    intercept_list3.append(model3.intercept_)
    coef_list3.append(model3.coef_)


least_square_result = pd.DataFrame({'User':user_list_mob,'a0':intercept_list1,
                               'a1':coef_list1,'R^2 1':r_sq_list1,
                               'b0':intercept_list2,
                               'b1':coef_list2,'R^2 2':r_sq_list2,
                               'c0':intercept_list3,
                               'c1':coef_list3,'R^2 3':r_sq_list3})

    
least_square_result.to_csv(r'D:\DACS\Individual Participant-linear regression.csv')    
# count number of R^2 
count_small_R_1 = sum(map(lambda x : x<0.5, r_sq_list1))
count_large_R_2 = sum(map(lambda x : x>0.8, r_sq_list2))    

#############################################################################
# Get spearman correlation
#############################################################################
rho_list1=[];rho_list2=[];rho_list3=[];p_val1=[];p_val2=[];p_val3=[];valid_day=[]
for i in range(len(temp_sensor_derived_steps)):
    each_sensor_derived_steps = temp_sensor_derived_steps[i]
    each_mobility = temp_mobility[i]
    each_transition = temp_transition[i]
    each_total_firing = temp_total_triggering[i]

    each_user_rho1,each_user_p_val1 = stats.spearmanr(each_mobility,each_transition)
    each_user_rho2,each_user_p_val2 = stats.spearmanr(each_mobility,each_sensor_derived_steps)
    each_user_rho3,each_user_p_val3 = stats.spearmanr(each_mobility,each_total_firing)
    
    rho_list1.append(each_user_rho1);p_val1.append(each_user_p_val1)
    rho_list2.append(each_user_rho2);p_val2.append(each_user_p_val2)
    rho_list3.append(each_user_rho3);p_val3.append(each_user_p_val3)
    valid_day.append(len(each_mobility))

user_list_mob_added = ['resident '+user for user in user_list_mob]

rho_list1= [float("{:.3f}".format(each_rho)) for each_rho in rho_list1]
rho_list2= [float("{:.3f}".format(each_rho)) for each_rho in rho_list2]
rho_list3= [float("{:.3f}".format(each_rho)) for each_rho in rho_list3]

spearman_result = pd.DataFrame({'User':user_list_mob_added,'Valid days':valid_day,
                                'Rho1 mobility and transition':rho_list1,'p-val 1':p_val1,
                                'Rho2 mobility and fixed-speed':rho_list2,'p-val 2':p_val2,
                                'Rho3 mobility and total_firing':rho_list3,'p-val 3':p_val3})

spearman_result.to_excel(r'D:\DACS\dasc individual correlation coefficients data up to 2020 May.xlsx')     
spearman_result = spearman_result.set_index('User')
# Create a Pandas Excel writer using XlsxWriter as the engine.
excel_file = r'D:\DACS\image_table_type.xlsx'
sheet_name = 'Sheet1'
writer = pd.ExcelWriter(excel_file, engine='xlsxwriter')
spearman_result.to_excel(writer, sheet_name=sheet_name)

# Access the XlsxWriter workbook and worksheet objects from the dataframe.
# This is equivalent to the following using XlsxWriter on its own:
#
#    workbook = xlsxwriter.Workbook('filename.xlsx')
#    worksheet = workbook.add_worksheet()
#
workbook = writer.book
worksheet = writer.sheets[sheet_name]

# Apply a conditional format to the cell range.
worksheet.conditional_format('B2:B48', {'type': '3_color_scale'})
worksheet.conditional_format('C2:C48', {'type': '2_color_scale',
                                         'min_color': '#C5D9F1', # light color
                                         'max_color': '#538ED5'})
worksheet.conditional_format('D2:D48', {'type': '2_color_scale', 'min_color': '#c7f2da','max_color': '#54d68f'})
worksheet.conditional_format('E2:E48', {'type': '2_color_scale','min_color': '#C5D9F1','max_color': '#538ED5'})
worksheet.conditional_format('F2:F48', {'type': '2_color_scale', 'min_color': '#c7f2da','max_color': '#54d68f'})
worksheet.conditional_format('G2:G48', {'type': '2_color_scale','min_color': '#C5D9F1','max_color': '#538ED5'})
worksheet.conditional_format('H2:H48', {'type': '2_color_scale', 'min_color': '#c7f2da','max_color': '#54d68f'})
writer.save()



plt.figure(figsize=(7,17))
plt.scatter(spearman_result['Rho1 mobility and transition'],spearman_result.index,label='travelled room distance & room transitions')
plt.scatter(spearman_result['Rho2 mobility and fixed-speed'],spearman_result.index,label='travelled room distance & fixed-speed mobility')
plt.scatter(spearman_result['Rho3 mobility and total_firing'],spearman_result.index,label='travelled room distance & total sensor firings')
plt.grid(axis='both',alpha=0.3)
plt.xlim([0.2,1])
plt.legend(loc='upper left',shadow=True,prop={'family':'Times New Roman', 'size':11})
plt.xlabel('Spearman Correlation Coefficient',fontsize=20, family = 'Times New Roman')
plt.ylabel('Participants',fontsize=30,family = 'Times New Roman')
plt.xticks(fontsize=15, family='Times New Roman')
plt.yticks(fontsize=13, family='Times New Roman')




# count rho2 and rho3 moderate corr (0.6<rho<0.8)
count_moderate3 = sum(map(lambda x : 0.6<x<0.8, rho_list3))
count_weak3 = sum(map(lambda x : x<0.6, rho_list3))

# se the paired t test between two correlations
ttest,pval = stats.ttest_rel(rho_list1,rho_list2)
print('paired t test = ','%.5f' %ttest, ', p-value = ','%.4f' %pval)
ttest2,pval2 = stats.ttest_rel(rho_list1,rho_list3)
print('paired t test = ','%.5f' %ttest2, ', p-value = ','%.4f' %pval2)

avg_valid_day=np.asarray(valid_day).mean()
avg_valid_day=(np.asarray(valid_day).sum()-29)/46

plt.figure(figsize=(9,6))
plt.hist(valid_day, bins=10)
plt.grid(True,alpha=0.3)
plt.xlabel('Valid Days',fontsize=30, family = 'Times New Roman')
plt.ylabel('Frequency',fontsize=30,family = 'Times New Roman')
plt.xticks(fontsize=20, family='Times New Roman')
plt.yticks(fontsize=20, family='Times New Roman')


#############################################################################
# Paired t test
#############################################################################
ttest_list1=[];pval_list1=[];ttest_list2=[];pval_list2=[];ttest_list3=[];pval_list3=[]
for i in range(len(temp_sensor_derived_steps)):
    each_sensor_derived_steps = temp_sensor_derived_steps[i]
    each_mobility = temp_mobility[i]
    each_transition = temp_transition[i]
    each_total_firing = temp_total_triggering[i]

    ttest1,pval1 = stats.ttest_rel(each_mobility,each_transition)
    ttest2,pval2 = stats.ttest_rel(each_mobility,each_sensor_derived_steps)
    ttest3,pval3 = stats.ttest_rel(each_mobility,each_total_firing)

    ttest_list1.append(ttest1);pval_list1.append(pval1)
    ttest_list2.append(ttest2);pval_list2.append(pval2)
    ttest_list3.append(ttest3);pval_list3.append(pval3)

paire_ttest_result = pd.DataFrame({'User':user_list_mob,'ttest mobility and transition':ttest_list1,'p-val 1':pval_list1,
                                'ttest mobility and fixed-speed':ttest_list2,'p-val 2':pval_list2,
                                'ttest mobility and total_firing':ttest_list3,'p-val 3':pval_list3})

paire_ttest_result.to_csv(r'D:\DACS\Individual Participant paired T test.csv')     
# count rho2 and rho3 moderate corr (0.6<rho<0.8)


#############################################################################
# Case Study
#############################################################################
# get_transition_arrays will give daily transition numbers
# if that day does not exist, then it returns 0
def get_transition_in_dates(cleaned_ila,choppedTime):
    # count how many rooms in this user's house
    room_num = len(cleaned_ila['changed_sensor_id'].unique().tolist())
    # print(room_num)
    transition=[]; day=[]
    for i in range(len(choppedTime)-1):
        # get daily motion data
        choppedila_day  = cleaned_ila[cleaned_ila['local_timestamp'] > choppedTime[i]]
        choppedila_day  = choppedila_day[choppedila_day['local_timestamp'] < choppedTime[i+1]]
        if len(choppedila_day)==0:
            continue
        # label the transitions and change them to merged transition labels
        ila_lablled = labels_between_room(choppedila_day)
        # get choppedila_day dataframe's date
        that_day_list = choppedila_day.local_timestamp.tolist()
        that_day = that_day_list[0][0:10:] # trim datetime hours
        day.append(that_day)
        
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

    merged_df = pd.DataFrame({'Day':day,'num of transition':transition})
    return merged_df

# 3-27: index =27, 3-121: index=6
def create_the_case_df(user_index,choppedTime):
    case = finally_sensor_list[user_index]
    case_df = get_transition_in_dates(case,choppedTime)
    case_df['mobility'] = temp_mobility[user_index]
    case_df['fixed-speed steps'] = temp_sensor_derived_steps[user_index]
    case_df['total firing'] = temp_total_triggering[user_index]
    return case_df

case_df_good = create_the_case_df(0,choppedTime)

# fill the missing dates with nan value
def fill_miss_dates_with_nan(case_df_good):       
    start_time = dt.datetime.strptime(case_df_good['Day'].tolist()[0], '%Y-%m-%d')
    end_time = dt.datetime.strptime(case_df_good['Day'].tolist()[-1], '%Y-%m-%d')
    period_len = (end_time - start_time).days+1
    datelist = pd.date_range(start_time, periods = period_len).tolist()
    # cast dataframe 'Day' to datetime
    case_df_good['Day'] = [dt.datetime.strptime(each, '%Y-%m-%d') for each in case_df_good['Day'].tolist()]
    case_df_good.index = pd.DatetimeIndex(case_df_good['Day'])
    case_df_good = case_df_good.reindex(datelist, fill_value=float('nan'))
    return case_df_good

case_df_bad = create_the_case_df(42,choppedTime)
case_df = fill_miss_dates_with_nan(case_df_bad)


def cumulative_plot(case_df): 
    # case_df should not have missing days, no nan should included
    x = np.array(case_df['mobility'].tolist())
    y = np.array(case_df['fixed-speed steps'].tolist())
    #x = x/np.max(x)
    #y = y/np.max(y)
    cumulative_x = np.cumsum(x)
    cumulative_y = np.cumsum(y)
    plt.plot(cumulative_x,cumulative_y)
    plt.title('3-27 accumulative transitions VS accumulative travelled distance')
    plt.xlabel('accumulative travelled distance')
    plt.ylabel('accumulative number of transitions')

def plot_pattern(user_x):
    user = user_list_mob[user_x]
    case_df_bad = create_the_case_df(user_x,choppedTime)
    case_df = fill_miss_dates_with_nan(case_df_bad)
    # set the plot
    plt.figure(figsize =(12,12))
    plt.subplot(4, 1, 1)
    plt.title(user +' indoor pattern')
    plt.plot(case_df.index, case_df['mobility'],label='Room Distance Travelled', c = 'red')
    plt.grid(alpha=0.5)
    plt.legend(loc='upper left')
    plt.ylabel('Mobility in Steps')
    plt.ylim(0,)
    #plt.xlim(dates[0],dates[-1])
    
    plt.subplot(4, 1, 2)
    plt.plot(case_df.index, case_df['num of transition'],label='Room Transitions',c = 'orange')
    plt.grid(True,alpha=0.5)
    plt.legend(loc='upper left')
    plt.ylabel('Freqeuncy of Room Transition')
    plt.ylim(0,) 
    
    plt.subplot(4, 1, 3)
    plt.plot(case_df.index, case_df['total firing'],label='Total Firings', c = 'green')
    plt.grid(True,alpha=0.5)
    plt.legend(loc='upper left')
    plt.ylabel('Total Firings')
    plt.ylim(0,)
    
    plt.subplot(4, 1, 4)
    plt.plot(case_df.index, case_df['fixed-speed steps'],label='Fix-speed Mobility',c = 'blue')
    plt.grid(True,alpha=0.5)
    plt.legend(loc='upper left')
    plt.ylabel('Fix-speed Mobility')
    plt.ylim(0,)

plot_pattern(43)
plot_pattern(44)
plot_pattern(45)
plot_pattern(46)

#-----------------------
# get linear regression plot
# m = slope, b=intercept
m, b = np.polyfit(case_df['mobility'], case_df['num of transition'], 1)
r_squared1 = r_sq_list1[index]
m2, b2 = np.polyfit(case_df['mobility'], case_df['total firing'], 1)
r_squared2 = r_sq_list3[index]
m3, b3 = np.polyfit(case_df['mobility'], case_df['fixed-speed steps'], 1)
r_squared3 = r_sq_list2[index]

my_font='Times New Roman'

plt.figure(figsize =(15,15))

plt.subplot(3, 1, 1)
plt.plot(case_df['mobility'], m*case_df['mobility'] + b,color="r",label='Y={:.2f}X+{:.2f},R-square={:.2f}'.format(m,b,r_squared1))
plt.legend(loc='lower right', prop = {'size': 20,'family':my_font})
plt.plot(case_df['mobility'], case_df['num of transition'], '+')
plt.grid(True,alpha=0.5)
plt.xticks(fontsize=18, family=my_font);plt.yticks(fontsize=18, family=my_font)
plt.xlabel('Room Distance Travelled',fontsize = 20,family=my_font)
plt.ylabel('Freqeuncy of Room Transition',fontsize = 20,family=my_font)
 
plt.subplot(3, 1, 2)
plt.plot(case_df['mobility'], m2*case_df['mobility'] + b2,color="r",label='Y={:.2f}X+{:.2f},R-square={:.2f}'.format(m2,b2,r_squared2))
plt.legend(loc='lower right', prop = {'size': 20,'family':my_font})
plt.plot(case_df['mobility'], case_df['num of transition'], '+')
plt.grid(True,alpha=0.5)
plt.xticks(fontsize=18, family=my_font);plt.yticks(fontsize=18, family=my_font)
plt.xlabel('Room Distance Travelled',fontsize = 20,family=my_font)
plt.ylabel('Total Firings',fontsize = 20,family=my_font)
 
plt.subplot(3, 1, 3)
plt.plot(case_df['mobility'],(m3*case_df['mobility'] + b3)/400 ,color="r",label='Y={:.2f}X+{:.2f},R-square={:.2f}'.format(m3,b3,r_squared3))
plt.legend(loc='lower right', prop = {'size': 20,'family':my_font})
plt.plot(case_df['mobility'], case_df['num of transition'], '+')
plt.grid(True,alpha=0.5)
plt.xticks(fontsize=18, family=my_font);plt.yticks(fontsize=18, family=my_font)
#plt.yscale('log')
plt.xlabel('Room Distance Travelled',fontsize = 20,family=my_font)
plt.ylabel('Fix-speed Mobility',fontsize = 20,family=my_font)
plt.xtick()


#---------------------------------
mobility_70s_male_list = [43,23,17,37]
mobility_70s_female_list = [32,10,39,9]
mobility_80s_male_list = [0,1,20,44]
mobility_80s_female_list = [15,38,27,6]

def get_mobility_data(mobility_index_list, temp_mobility):
    temp_mobility_for_selected_group=[]
    for i in mobility_index_list:
        temp_mobility_for_selected_group.append(temp_mobility[i])
    return temp_mobility_for_selected_group

mobility_70s_male = get_mobility_data(mobility_70s_male_list, temp_mobility)
mobility_70s_female = get_mobility_data(mobility_70s_female_list, temp_mobility)
mobility_80s_male = get_mobility_data(mobility_80s_male_list, temp_mobility)
mobility_80s_female = get_mobility_data(mobility_80s_female_list, temp_mobility)

transition_70s_male = get_mobility_data(mobility_70s_male_list, temp_transition)
transition_70s_female = get_mobility_data(mobility_70s_female_list, temp_transition)
transition_80s_male = get_mobility_data(mobility_80s_male_list, temp_transition)
transition_80s_female = get_mobility_data(mobility_80s_female_list, temp_transition)


kwargs = dict(alpha=0.5, bins=100)
plt.hist([item for sublist in transition_80s_male for item in sublist],**kwargs, color='b', label='male room transitions')
plt.hist([item for sublist in transition_80s_female for item in sublist],**kwargs, color='g', label='female room transitions')
plt.legend()
plt.title('Number of room transitions in 80s male and female')

def two_group_ttest(group_a, group_b):
    a = [item for sublist in group_a for item in sublist]
    b = [item for sublist in group_b for item in sublist]
    ttest,pval = stats.ttest_ind(a,b)
    return ttest,pval
    
ttest,pval = two_group_ttest(transition_80s_male, transition_80s_female)
print("{:.2f}".format(ttest),pval)

def get_mean_and_std(group_a):
    a = np.asarray([item for sublist in group_a for item in sublist])
    avg = a.mean()
    std = a.std()
    return avg,std
avg0,std0 = get_mean_and_std(mobility_70s_female)
print("{:.2f}".format(avg0),'±',"{:.2f}".format(std0))


#############################################################################
# Correlation Comparision
#############################################################################
# For all users
flat_mobility = [item for sublist in temp_mobility for item in sublist]
flat_sensor_derived_steps = [item for sublist in temp_sensor_derived_steps for item in sublist]
flat_transition = [item for sublist in temp_transition for item in sublist]
flat_total_firing = [item for sublist in temp_total_triggering for item in sublist]


each_user_rho1,each_user_p_val1 = stats.spearmanr(flat_mobility,flat_transition)
print('spearmanr all_mobility VS all_num_of_transition rho:',each_user_rho1)
print('spearmanr all_mobility VS all_num_of_transition p-val',each_user_p_val1)

each_user_rho2,each_user_p_val2 = stats.spearmanr(flat_mobility,flat_sensor_derived_steps)
print('spearmanr all_mobility VS all_fix_speed_step rho:',each_user_rho2)
print('spearmanr all_mobility VS all_fix_speed_step p-val',each_user_p_val2)

each_user_rho3,each_user_p_val3 = stats.spearmanr(flat_mobility,flat_total_firing)
print('spearmanr all_mobility VS all_total_firing rho:',each_user_rho3)
print('spearmanr all_mobility VS all_total_firing p-val',each_user_p_val3)




#############################################################################
# Room distance
#############################################################################
from collections import ChainMap

all_dacs_room_matrix = pd.read_csv(r'D:\DACS\Archive\DACS_Room_Distances.csv')
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

reformed_room_matrix_list_temp=[]    
for each_unit in room_matrix_grouped_list:
    unit_matrix = each_unit[1]
    unit_matrix_cleaned = remove_duplicate_rooms(unit_matrix)    
#    divisor = max(unit_matrix['distance'].tolist())
#    unit_matrix['distance'] = unit_matrix['distance']/divisor
    reformed_room_matrix_list_temp.append(unit_matrix_cleaned)

room_distances = pd.DataFrame({})
for each in reformed_room_matrix_list_temp:
    room_distances = room_distances.append(each)
    
# the users I suspect
from matplotlib.ticker import PercentFormatter
size = []
for each in reformed_room_matrix_list_temp:
    size.append(each['distance'].tolist())
flat_size = [item for sublist in size for item in sublist]
kwargs = dict(bins=20)
plt.hist(flat_size, weights =np.ones(len(flat_size))/len(flat_size),**kwargs)
plt.gca().yaxis.set_major_formatter(PercentFormatter(1))
plt.xlabel('Room-to-room Distance (Steps)',fontsize=15, family = 'Times New Roman')
plt.ylabel('Percentage',fontsize=15,family = 'Times New Roman')
plt.xticks(fontsize=12, family='Times New Roman')
plt.yticks(fontsize=12, family='Times New Roman')



aaa = list(set(reformed_room_matrix_list_temp[27]['distance'].tolist()))
plt.plot(list(range(len(aaa))),sorted(aaa))

plt.plot([4,6,10,12],[42,56,98,102])







