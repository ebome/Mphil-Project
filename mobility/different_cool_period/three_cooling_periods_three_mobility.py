# Apr 5 to Apr 14
import os
import pandas as pd
import datetime as dt
import numpy as np
from scipy import stats

filepath= os.path.abspath(r'D:/FloorMap/Qing Room/Single Home Motion Sensors.xls')

MotionData = pd.read_excel(filepath)
MotionData = MotionData[MotionData['sensor_value'] == 1]


#############################################################################
# Pre-selecting of useful time and data
#############################################################################
# get sensors names for each room
room_list = MotionData['room_name'].unique().tolist()
store1 =[];store2 =[];dict_sensors = {}
for each_room in room_list:
    temp = MotionData[MotionData['room_name'] == each_room]
    sensors_inRoom = temp['sensor_id'].unique().tolist()
    store1.append(sensors_inRoom)
    sensorsName_inRoom = temp['sensor_name'].unique().tolist()
    store2.append(sensorsName_inRoom)
    di = dict(zip(sensorsName_inRoom, sensors_inRoom))
    dict_sensors.update(di)
    
# get a dictionary for rooms sensor
dict_sensorID = dict(zip(room_list, store1))
dict_sensorName = dict(zip(room_list, store2))

# Use 240s sensor data
MotionData_240s = MotionData[ (MotionData['sensor_id'] == 1896) | (MotionData['sensor_id'] ==1881)\
                    |(MotionData['sensor_id'] ==1960)| (MotionData['sensor_id'] ==1910)\
                    | (MotionData['sensor_id'] ==1866)|(MotionData['sensor_id'] ==2009) ]

# Use 120s sensor data
MotionData_120s = MotionData[ (MotionData['sensor_id'] == 1938) | (MotionData['sensor_id'] ==1950)\
                    |(MotionData['sensor_id'] ==1876)| (MotionData['sensor_id'] ==1891)\
                    | (MotionData['sensor_id'] ==1928)|(MotionData['sensor_id'] ==2019) ]

# Use 10s sensor data
MotionData_10s = MotionData[ (MotionData['sensor_id'] == 1945) | (MotionData['sensor_id'] ==1955)\
                    |(MotionData['sensor_id'] ==1965)| (MotionData['sensor_id'] ==1898)\
                    | (MotionData['sensor_id'] ==1933)]    
    
# Use continuos sensor data
MotionData_c = MotionData[ (MotionData['sensor_id'] == 2001) | (MotionData['sensor_id'] ==5135)\
                |(MotionData['sensor_id'] ==5140)| (MotionData['sensor_id'] ==5130)\
                | (MotionData['sensor_id'] ==5150)|(MotionData['sensor_id'] ==5145) ]
    
#############################################################################
# Get the lists of transition times
#############################################################################
# Remove 'repetitive sensor'
def remove_dup_df(motion_data):
    # drop the duplicates in sensor_id
    drop_dup_df = motion_data.loc[(motion_data['sensor_id'].shift() != motion_data['sensor_id'])]
    return drop_dup_df
#-------------------------------
cleaned_MotionData_c = remove_dup_df(MotionData_c)
cleaned_MotionData_120 = remove_dup_df(MotionData_120s)
cleaned_MotionData_240 = remove_dup_df(MotionData_240s)

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
#-------------------------------
cleaned_MotionData_c = change_sensor_name(cleaned_MotionData_c)
cleaned_MotionData_120 = change_sensor_name(cleaned_MotionData_120)
cleaned_MotionData_240 = change_sensor_name(cleaned_MotionData_240)




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
time span for mobility: 2019/04/06 - 2019/04/14(included) (2019-04-05 is too short for cts senors)
Just remove the dates that are not in this range for sensor_list
'''    
# Chopped datetime       
base = dt.datetime.strptime('2019-04-06 00:00:00', '%Y-%m-%d %H:%M:%S')
datelist = pd.date_range(base, periods=10).tolist()
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
#-------------------------------
transition_c = get_transition_arrays(cleaned_MotionData_c,choppedTime)
transition_120 = get_transition_arrays(cleaned_MotionData_120,choppedTime)
transition_240 = get_transition_arrays(cleaned_MotionData_240,choppedTime)


#############################################################################
# Get the total sensor firing counts
#############################################################################
def get_total_firing(cleaned_ila,choppedTime):
    total_firing = []
    for i in range(len(choppedTime)-1):
        chopped_day  = cleaned_ila[cleaned_ila['local_timestamp'] > choppedTime[i]]
        choppedila_day  = chopped_day[chopped_day['local_timestamp'] < choppedTime[i+1]]
        total_firing_in_that_day = len(choppedila_day)
        total_firing.append(total_firing_in_that_day)

    return total_firing

total_firing_c = get_total_firing(MotionData_c,choppedTime)
total_firing_120 = get_total_firing(MotionData_120s,choppedTime)
total_firing_240 = get_total_firing(MotionData_240s,choppedTime)


#############################################################################
# Get the median of transition time as mobility
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

remove_consecutive_dup_motion_data_c = remove_consecutive_dup(MotionData_c)
remove_consecutive_dup_motion_data_120 = remove_consecutive_dup(MotionData_120s)
remove_consecutive_dup_motion_data_240 = remove_consecutive_dup(MotionData_240s)

'''
For each user, the average time from room A to room B(and room B to room A) is constant by assumption.
(Assume the user is always doing uniform linear motion in a constant speed)
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
            room_previous_time = cleaned_ila.iloc[i]['local_timestamp'][0:19] 
            room_previous_time = dt.datetime.strptime(room_previous_time, '%Y-%m-%d %H:%M:%S')
            room_next_time =  cleaned_ila.iloc[i+1]['local_timestamp'][0:19]
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

        if room_num == 3:
            merge_labelled_ilaList = ms.merge_3_sensors(ila_lablled)
        if room_num == 4:
            merge_labelled_ilaList = ms.merge_4_sensors(ila_lablled)
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
# 7 days median
def find_avg_time_diff_for_labels_7Days(single_user_transion_time_diff):
    # find the avg time diff of each label
    time_diff_grouped_list = list(single_user_transion_time_diff.groupby(['transition label']))

    avg=[];labels=[];median =[];transition_time_every_day=[];
    for each_label in time_diff_grouped_list:
        transition_time_every_day.append(each_label[1]['time diff'].tolist())

        each_label_avg = np.mean(each_label[1]['time diff'].tolist()[0:8])
        each_label_median = np.median(each_label[1]['time diff'].tolist()[0:8])
        avg.append(each_label_avg)
        median.append(each_label_median)
        labels.append(each_label[0])
    avg_time_diff_for_labels = pd.DataFrame({'label':labels,'avg time(s)':avg,
                                             'median time(s)':median,
                                             'transition_time_every_day':transition_time_every_day})
    return avg_time_diff_for_labels
#--------------------------------  
def get_daily_sensor_derived_steps_7Days(avg_and_median_time_diff_for_labels, single_user_transion_time_diff_with_date):
    df = avg_and_median_time_diff_for_labels.copy(deep=True)
    data_dict = dict(zip(df['label'].tolist(), df['median time(s)'].tolist()))

    # find every day room transition time avg/mediian sum 
    all_day_transition_labels = single_user_transion_time_diff_with_date['transition label'].tolist()
    all_days_fixed_speed_mobility=[]
    for daily_transition_labels in all_day_transition_labels:
        split_daily_transition_labels = [x for xs in daily_transition_labels for x in xs.split(',')]
        split_daily_transition_time = [data_dict[x] for x in split_daily_transition_labels]
        
        daily_total_transition_time = sum(split_daily_transition_time)
        daily_sensor_derived_steps = daily_total_transition_time
        all_days_fixed_speed_mobility.append(daily_sensor_derived_steps)
    return all_days_fixed_speed_mobility

# contiuous sensor ===================
single_user_transion_time_diff, single_user_transion_time_diff_with_date = get_time_diff_list(remove_consecutive_dup_motion_data_c,choppedTime)
avg_and_median_time_diff_for_labels_7days = find_avg_time_diff_for_labels_7Days(single_user_transion_time_diff)
temp_median_time_steps_7days_c = get_daily_sensor_derived_steps_7Days(avg_and_median_time_diff_for_labels_7days,single_user_transion_time_diff_with_date)

# 120s sensor ===================
single_user_transion_time_diff, single_user_transion_time_diff_with_date = get_time_diff_list(remove_consecutive_dup_motion_data_120,choppedTime)
avg_and_median_time_diff_for_labels_7days = find_avg_time_diff_for_labels_7Days(single_user_transion_time_diff)
temp_median_time_steps_7days_120 = get_daily_sensor_derived_steps_7Days(avg_and_median_time_diff_for_labels_7days,single_user_transion_time_diff_with_date)

# 240s sensor ===================
single_user_transion_time_diff, single_user_transion_time_diff_with_date = get_time_diff_list(remove_consecutive_dup_motion_data_240,choppedTime)
avg_and_median_time_diff_for_labels_7days = find_avg_time_diff_for_labels_7Days(single_user_transion_time_diff)
temp_median_time_steps_7days_240 = get_daily_sensor_derived_steps_7Days(avg_and_median_time_diff_for_labels_7days,single_user_transion_time_diff_with_date)


#############################################################################
# Get ground truth: sensor-to-sensor steps; from contiuos sensors
#############################################################################    
# 6 rooms, 15 combinations

sensor_ids = ['2001 to 5135','2001 to 5140','2001 to 5130','2001 to 5150','2001 to 5145',
                 '5135 to 5140','5135 to 5130','5135 to 5150','5135 to 5145','5140 to 5130',
                 '5140 to 5150','5140 to 5145','5130 to 5150','5130 to 5145','5150 to 5145',
                 
                 '5135 to 2001','5140 to 2001','5130 to 2001','5150 to 2001','5145 to 2001',
                 '5140 to 5135','5130 to 5135','5150 to 5135','5145 to 5135','5130 to 5140',
                 '5150 to 5140','5145 to 5140','5150 to 5130','5145 to 5130','5145 to 5150']

sensor_distances=[6,18,23,27,15,19,24,26,16,5,10,8,11,12,14,
                  6,18,23,27,15,19,24,26,16,5,10,8,11,12,14]

floor_matrix_df = dict(zip(sensor_ids, sensor_distances))   



#-----------------------------------------------------------------------------  
# compute each day mobility
def get_mobility(cleaned_ila,choppedTime,floor_matrix_df):
    steps_count=[]
    
    for i in range(len(choppedTime)-1):
        chopped_day  = cleaned_ila[cleaned_ila['local_timestamp'] > choppedTime[i]]
        choppedila_day  = chopped_day[chopped_day['local_timestamp'] < choppedTime[i+1]]
        
        # for each day's cleaned motion data, sum the steps bewteen two sensors
        sensors = choppedila_day['sensor_id'].tolist()
        steps_in_that_day=0
        for i in range(len(sensors)-1):
            sensor_to_sensor = str(sensors[i])+' to '+str(sensors[i+1])
            step_distance = floor_matrix_df[sensor_to_sensor]
            steps_in_that_day = steps_in_that_day+step_distance
  
        steps_count.append(steps_in_that_day)

    return steps_count

# THIS IS the only ground_truth, no need for cleaned_MotionData_120
mobility_c = get_mobility(cleaned_MotionData_c,choppedTime,floor_matrix_df)


#############################################################################
# Get spearman correlation
#############################################################################

ground_truth = mobility_c
m1=transition_240
m2=total_firing_240
m3=temp_median_time_steps_7days_240

each_rho1,each_p_val1 = stats.pearsonr(ground_truth,m1)
print('rho:',each_rho1,'p val:',each_p_val1)

each_rho1,each_p_val1 = stats.pearsonr(ground_truth,m2)
print('rho:',each_rho1,'p val:',each_p_val1)

each_rho1,each_p_val1 = stats.pearsonr(ground_truth,m3)
print('rho:',each_rho1,'p val:',each_p_val1)






