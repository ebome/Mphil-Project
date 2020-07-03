# Oct 18 to Oct 23
import os
import pandas as pd
import datetime as dt
from scipy import stats


filepath= os.path.abspath(r'D:/YangTrial/All/Yang_Data_240s.csv')

MotionData = pd.read_csv(filepath)
MotionData = MotionData[MotionData['sensor_value'] == 1]
MotionData['local_timestamp']=pd.to_datetime(MotionData['local_timestamp'], format="%Y-%m-%d %H:%M:%S")


# Store the recoreded single person periods 

t2_1 = dt.datetime.strptime('2019-10-19 11:40:00', '%Y-%m-%d %H:%M:%S')
t2_2 = dt.datetime.strptime('2019-10-19 18:57:00', '%Y-%m-%d %H:%M:%S')

t3_1 = dt.datetime.strptime('2019-10-20 11:06:00', '%Y-%m-%d %H:%M:%S')
t3_2 = dt.datetime.strptime('2019-10-20 13:00:00', '%Y-%m-%d %H:%M:%S')

t4_1 = dt.datetime.strptime('2019-10-21 15:06:00', '%Y-%m-%d %H:%M:%S')
t4_2 = dt.datetime.strptime('2019-10-21 17:25:00', '%Y-%m-%d %H:%M:%S')

t5_1 = dt.datetime.strptime('2019-10-22 09:00:00', '%Y-%m-%d %H:%M:%S')
t5_2 = dt.datetime.strptime('2019-10-22 12:00:00', '%Y-%m-%d %H:%M:%S')

t6_1 = dt.datetime.strptime('2019-10-22 16:10:00', '%Y-%m-%d %H:%M:%S')
t6_2 = dt.datetime.strptime('2019-10-22 19:00:00', '%Y-%m-%d %H:%M:%S')

t7_1 = dt.datetime.strptime('2019-10-23 11:35:00', '%Y-%m-%d %H:%M:%S')
t7_2 = dt.datetime.strptime('2019-10-23 13:00:00', '%Y-%m-%d %H:%M:%S')

t8_1 = dt.datetime.strptime('2019-10-23 13:05:00', '%Y-%m-%d %H:%M:%S')
t8_2 = dt.datetime.strptime('2019-10-23 18:00:00', '%Y-%m-%d %H:%M:%S')


'''

10-19	11:40am-18:57pm
10-20	11:06am-1pm
10-21	3:00pm-5:25pm
10-22	9:00am-12:00pm, 4:10pm -7pm
10-23	11:35am-1pm, 1:05pm-6pm

'''
# Create the time slice
def perdelta(start, end, delta):
    curr = start
    while curr < end:
        yield curr
        curr += delta
# print(perdelta(t1_1, t1_2, dt.timedelta(minutes=30)) )
def get_time_slice(startTime, endTime):
    temp1 = []
    for result in perdelta(startTime, endTime, dt.timedelta(minutes=140)):
        temp1.append(result)
    if startTime not in temp1:
        temp1.append(startTime)
    if endTime not in temp1:
        temp1.append(endTime)
    temp = sorted(temp1)
    return temp
        
def clean_time_slice(startTime, endTime):
    temp_slice_list = get_time_slice(startTime, endTime)
    previous_time = temp_slice_list[-2]
    next_time = temp_slice_list[-1]
    # if time delta is smaller than 10 minutes, remove the previous_time
    if (next_time - previous_time) < dt.timedelta(minutes=30):
        del temp_slice_list[-2]
    return temp_slice_list

temp_slice2 = clean_time_slice(t2_1, t2_2)
temp_slice3 = clean_time_slice(t3_1, t3_2)
temp_slice4 = clean_time_slice(t4_1, t4_2)
temp_slice5 = clean_time_slice(t5_1, t5_2)
temp_slice6 = clean_time_slice(t6_1, t6_2)
temp_slice7 = clean_time_slice(t7_1, t7_2)
temp_slice8 = clean_time_slice(t8_1, t8_2)

time_slice=[temp_slice2,temp_slice3,temp_slice4,temp_slice5,
            temp_slice6,temp_slice7,temp_slice8]
#-----------------------------------------------------------------------------  
# Store the cleaned actigraph data for 'single person time'
wrist_path = os.listdir(r'D:/YangTrial/All/240s/wrist/') # returns a list under the path
pedometer_path = os.listdir(r'D:/YangTrial/All/240s/pedometer/') # returns a list under the path

wrist_path_list=[]
for each in wrist_path:
    path = 'D:/YangTrial/All/240s/wrist/'+each
    wrist_path_list.append(path)

pedo_path_list=[]
for each in pedometer_path:
    path = 'D:/YangTrial/All/240s/pedometer/'+each
    pedo_path_list.append(path)

def get_acti_steps(filepath, time1,time2):
    f1= os.path.abspath(filepath)
    wrist_day = pd.read_csv(f1,usecols=['Date',' Time','Steps'])
    wrist_day['Datetime'] = wrist_day['Date'] + " " + wrist_day[' Time']
    wrist_day['Datetime']=pd.to_datetime(wrist_day['Datetime'], format="%d/%m/%Y %H:%M:%S")
    cleaned_wrist = wrist_day[(wrist_day['Datetime'] >= time1) & (wrist_day['Datetime'] <= time2) ]
    return cleaned_wrist

wrist_day2 = get_acti_steps(wrist_path_list[1],t2_1,t2_2)
wrist_day3 = get_acti_steps(wrist_path_list[2],t3_1,t3_2)
wrist_day4 = get_acti_steps(wrist_path_list[3],t4_1,t4_2)
wrist_day5 = get_acti_steps(wrist_path_list[4],t5_1,t5_2)
wrist_day6 = get_acti_steps(wrist_path_list[5],t6_1,t6_2)
wrist_day7 = get_acti_steps(wrist_path_list[6],t7_1,t7_2)
wrist_day8 = get_acti_steps(wrist_path_list[7],t8_1,t8_2)

wrist_data = [wrist_day2, wrist_day3, wrist_day4, wrist_day5, wrist_day6, 
              wrist_day7, wrist_day8]

pedometer_day2 = get_acti_steps(pedo_path_list[1],t2_1,t2_2)
pedometer_day3 = get_acti_steps(pedo_path_list[2],t3_1,t3_2)
pedometer_day4 = get_acti_steps(pedo_path_list[3],t4_1,t4_2)
pedometer_day5 = get_acti_steps(pedo_path_list[4],t5_1,t5_2)
pedometer_day6 = get_acti_steps(pedo_path_list[5],t6_1,t6_2)
pedometer_day7 = get_acti_steps(pedo_path_list[6],t7_1,t7_2)
pedometer_day8 = get_acti_steps(pedo_path_list[7],t8_1,t8_2)

pedometer_data = [pedometer_day2, pedometer_day3, pedometer_day4, 
                  pedometer_day5, pedometer_day6, pedometer_day7,pedometer_day8 ]
#-----------------------------------------------------------------------------  
# function to slice acti_data
def slice_acti_data(temp_slice, acti_df):
    temp = []
    for i in range(len(temp_slice)-1):
        previous_time = temp_slice[i]
        next_time= temp_slice[i+1]
        temp_df = acti_df[(acti_df['Datetime'] > previous_time)& (acti_df['Datetime'] <= next_time) ]
        temp.append(temp_df)
    return temp
#temp = slice_acti_data(temp_slice1, wrist_day1)

actitime_slice_total=[]
pedotime_slice_total=[]
for i in range(7):
    wrist_day = wrist_data[i] # dataframe
    pedometer_day = pedometer_data[i]  # dataframe
    temp_slice = time_slice[i]  # list
    temp_acti_day = slice_acti_data(temp_slice, wrist_day)
    temp_pedo_day = slice_acti_data(temp_slice, pedometer_day)
    actitime_slice_total.append(temp_acti_day)
    pedotime_slice_total.append(temp_pedo_day)
    
#-----------------------------------------------------------------------------  
#-----------------------------------------------------------------------------  
# select the 'single person time' from Motion Data
MotionData_day2 = MotionData[(MotionData['local_timestamp'] >= t2_1) & (MotionData['local_timestamp'] <= t2_2) ]
MotionData_day3 = MotionData[(MotionData['local_timestamp'] >= t3_1) & (MotionData['local_timestamp'] <= t3_2) ]
MotionData_day4 = MotionData[(MotionData['local_timestamp'] >= t4_1) & (MotionData['local_timestamp'] <= t4_2) ]
MotionData_day5 = MotionData[(MotionData['local_timestamp'] >= t5_1) & (MotionData['local_timestamp'] <= t5_2) ]
MotionData_day6 = MotionData[(MotionData['local_timestamp'] >= t6_1) & (MotionData['local_timestamp'] <= t6_2) ]
MotionData_day7 = MotionData[(MotionData['local_timestamp'] >= t7_1) & (MotionData['local_timestamp'] <= t7_2) ]
MotionData_day8 = MotionData[(MotionData['local_timestamp'] >= t8_1) & (MotionData['local_timestamp'] <= t8_2) ]

Motion_data_list = [MotionData_day2, MotionData_day3, MotionData_day4, 
                    MotionData_day5, MotionData_day6, MotionData_day7, MotionData_day8 ]

# Slice the motion data into pieces
def slice_motion_data(temp_slice, acti_df):
    temp = []
    for i in range(len(temp_slice)-1):
        previous_time = temp_slice[i]
        next_time= temp_slice[i+1]
        temp_df = acti_df[(acti_df['local_timestamp'] > previous_time)& (acti_df['local_timestamp'] <= next_time) ]
        temp.append(temp_df)
    return temp
#temp = slice_motion_data(temp_slice1, MotionData_day1)

motion_timeslice_total=[]
for i in range(7):
    Motion_data_day = Motion_data_list[i] # dataframe
    temp_slice = time_slice[i]  # list
    temp_motion_day = slice_motion_data(temp_slice, Motion_data_day)
    motion_timeslice_total.append(temp_motion_day)

#############################################################################
# Pre-selecting of sensor ID and name if some sensors are not used
#############################################################################
# get sensors names for each room
room_list = MotionData['sensor_name'].unique().tolist()

store1 =[];store2 =[];dict_sensors = {} 
for each_room in room_list:
    temp = MotionData[MotionData['sensor_name'] == each_room]
    sensors_inRoom = temp['sensor_id'].unique().tolist()
    store1.append(sensors_inRoom)
    sensorsName_inRoom = temp['sensor_name'].unique().tolist()
    store2.append(sensorsName_inRoom)
    di = dict(zip(sensorsName_inRoom, sensors_inRoom))
    dict_sensors.update(di)
    
# get a dictionary for rooms sensor
dict_sensorID = dict(zip(room_list, store1))
dict_sensorName = dict(zip(room_list, store2))

#############################################################################
# Get (1)ADL steps and (2)number of room transitions    from Motion Data
#############################################################################
# Remove 'repetitive sensor'
def remove_dup_df(motion_data):
    # drop the duplicates in sensor_id
    return motion_data[(motion_data['sensor_id'].shift() != motion_data['sensor_id'])]


#-----------------------------------------------------------------------------  
# change all the sensor id into 0-6
def reunit_sensor_id(motion_data):
    cleanedData = remove_dup_df(motion_data)
    same_sensor_id = 0
    new_sensors_df = pd.DataFrame({}) 
    for each_room in room_list:
        temp = cleanedData[cleanedData['sensor_name'] == each_room]
        temp['sensor_id'] = same_sensor_id
        new_sensors_df = new_sensors_df.append(temp)
        same_sensor_id = same_sensor_id + 1
    # sort the data frame by exact_time
    new_sensors_df = new_sensors_df.sort_values(by=['local_timestamp'])
    return new_sensors_df

# 0:Bedroom   1:Bathroom  2:Living room  3:Kitchen

motion=[]
for i in range(7):
    MotionData_day = motion_timeslice_total[i] # MotionData_day is dataframe
    for Motion_data in MotionData_day:
        cleanedMotionData_day = reunit_sensor_id(Motion_data)
        motion.append(cleanedMotionData_day)
#-----------------------------------------------------------------------------  
# Add Ground Truth of all rooms
groundTruth_yang =  {'0 to 1':4,'0 to 2':12,'0 to 3':16,
                     '1 to 2':14,'1 to 3':14,'2 to 3':7} 

#-----------------------------------------------------------------------------  
#-----------------------------------------------------------------------------  
# get (1)ADL steps and (2)number of room transitions 
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

'''
finally_sensor_list has repetitive sensor readings. The repetitive readings are removed through 
labelling '1 to 2' etc. If '1 to 1', the label is not in if-else statement
'''
finally_motion=[]
for each_sleiced_time_interval in motion:
    user_sensor_reading = change_sensor_name(each_sleiced_time_interval)
    finally_motion.append(user_sensor_reading)

#--------------------------------  
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


# merge '3 to 4' and '4 to 3'
def merge_labelled_ila(ila_lablled):
    label = ila_lablled['label'].values.tolist()
    temp=[]
    for i in range(0,len(label)):
        if label[i] == '0 to 1' or label[i] == '1 to 0':
            temp.append('0 to 1')
        if label[i] == '0 to 2' or label[i] == '2 to 0':
            temp.append('0 to 2')
        if label[i] == '0 to 3' or label[i] == '3 to 0':
            temp.append('0 to 3')
        if label[i] == '1 to 2' or label[i] == '2 to 1':
            temp.append('1 to 2')
        if label[i] == '1 to 3' or label[i] == '3 to 1':
            temp.append('1 to 3')
        if label[i] == '2 to 3' or label[i] == '3 to 2':
            temp.append('2 to 3')
    return temp

# ila_lablled = labels_between_room(finally_motion[14])
# merge_labelled_ilaList = merge_labelled_ila(ila_lablled)

def get_two_arrays(cleanMotion_list,groundTruth_ila):
    temp_adl_arr1=[];temp_arr2=[]
    for i in range(len(cleanMotion_list)):
        cleaned_motionData = cleanMotion_list[i]
        ila_lablled = labels_between_room(cleaned_motionData)
        merge_labelled_ilaList = merge_labelled_ila(ila_lablled)
        temp_arr2.append(len(merge_labelled_ilaList))
        
        # add ground truth to ADL
        summation_ADL = 0
        for each_label in merge_labelled_ilaList: # each label is the key
            steps = groundTruth_ila[each_label]
            summation_ADL = summation_ADL+steps
            
        # get the total ADL for one day
        temp_adl_arr1.append(summation_ADL)
    return temp_adl_arr1, temp_arr2 

# Get the 2 arrays from motion data

mobility_steps,num_of_transitions = get_two_arrays(finally_motion,groundTruth_yang)

#############################################################################
# Get (3)average_speed steps from sensor data (set speed = 2 steps/second) 
#############################################################################
'''
The average time from room A to room B(and room B to room A) is constant by assumption.
(Assume the user is always doing uniform linear motion in a constant speed)

A --> B is a unit, then the reciprocal of avg A--> B time (e.g. 21 seconds becomes 1/21 unit/second) indicates
the avg time for this user to complete the unit. So the distance between A and B is
4/3 (step/s) /  1/21  (unit/s) = 28 step/unit. Then for each day, the total time for A-->B is known,
so we know how many 'A-->B unit' the user walks. By multiplying the distance we can get steps for 
A--> B
'''

# flat the dataframe in Motion_data_list to one big dataframe
flatted_signle_user_time_motion = pd.DataFrame({})    
for each_time_interval in Motion_data_list:  # Motion_data_list has been chopped to keep my own motion
    flatted_signle_user_time_motion = pd.concat([flatted_signle_user_time_motion,each_time_interval])
# remove duplicates in dataframe
flatted_signle_user_time_motion = flatted_signle_user_time_motion.loc[(flatted_signle_user_time_motion['sensor_id'].shift() != flatted_signle_user_time_motion['sensor_id'])]
# simpilify sensor ID
flatted_signle_user_time_motion = change_sensor_name(flatted_signle_user_time_motion)

#--------------------------------  
def labelled_room_and_time_diff(cleaned_ila):
    tempDF = pd.DataFrame({})
    temp1=[];temp2=[]
    for i in range(0, len(cleaned_ila)-1):
        room_previous_sensor = cleaned_ila.iloc[i]['changed_sensor_id'] 
        room_next_sensor =  cleaned_ila.iloc[i+1]['changed_sensor_id']
        label = str(int(room_previous_sensor))+' to '+str(int(room_next_sensor)) 
        temp1.append(label)
        
        room_previous_time = cleaned_ila.iloc[i]['local_timestamp'] 
        room_next_time =  cleaned_ila.iloc[i+1]['local_timestamp']
        time_diff =  (room_next_time - room_previous_time).seconds
        temp2.append(time_diff)

    tempDF['label'] = temp1
    tempDF['time difference'] = temp2
    return tempDF


ila_lablled = labelled_room_and_time_diff(flatted_signle_user_time_motion)

#--------------------------------  
def get_time_diff_list(cleaned_ila,choppedTime):
    transition=[];time_diff_list_all_days=[];day=[]
    for i in range(len(choppedTime)-1):
        # get daily sensor reading
        choppedila_day  = cleaned_ila[cleaned_ila['local_timestamp'] > choppedTime[i]]
        choppedila_day  = choppedila_day[choppedila_day['local_timestamp'] < choppedTime[i+1]]
        # choppedTime start  4-26, hence sometime the choppedila_day could be length 0
        if len(choppedila_day)==0:
            time_diff_list_all_days.append([])
            transition.append([])
            day.append([])
            continue
        # label the transitions and change them to merged transition labels
        ila_lablled = labelled_room_and_time_diff(choppedila_day)
        time_diff_list = ila_lablled['time difference'].values.tolist()
        # get choppedila_day dataframe's date
        that_day_list = choppedila_day.local_timestamp.tolist()
        that_day = that_day_list[0].strftime('%Y-%m-%d %H:%M:%S')[0:10:] # trim datetime hours
        day.append(that_day)

        merge_labelled_ilaList = merge_labelled_ila(ila_lablled)

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

#--------------------------------  
def find_avg_time_diff_for_labels(single_user_transion_time_diff):
    # find the avg time diff of each label
    time_diff_grouped_list = list(single_user_transion_time_diff.groupby(['transition label']))

    avg=[];labels=[]
    for each_label in time_diff_grouped_list:
        each_label_avg = each_label[1]['time diff'].mean()
        avg.append(each_label_avg)
        labels.append(each_label[0])
    
    reciprocal =[]
    for i in avg:
        if i !=0:
            recip = 1/i 
            reciprocal.append(recip)
        if i==0:
            reciprocal.append(0)
    avg_time_diff_for_labels = pd.DataFrame({'label':labels,'avg time(s)':avg,
                                             'reciprocal(unit/s)':reciprocal})
    return avg_time_diff_for_labels

#--------------------------------  
# For each day, the total time for A-->B can be computed from single_user_transion_time_diff_with_date  
def get_daily_time_diff_sum(single_user_transion_time_diff_with_date):
    all_the_days=[]
    for row in single_user_transion_time_diff_with_date.iterrows(): # row is a tuple
        time_diff_list_that_day = row[1]['time diff']
        label_list_that_day = row[1]['transition label']
        temp_df_that_day = pd.DataFrame({'transition label':label_list_that_day,
                            'time diff':time_diff_list_that_day})
    
        temp_df_that_day_grouped = list(temp_df_that_day.groupby(['transition label']))
        total_time_diff_for_that_label=[];temp_label=[]
    
        for each_label in temp_df_that_day_grouped:
            each_label_time_diff_sum = each_label[1]['time diff'].sum()
            total_time_diff_for_that_label.append(each_label_time_diff_sum)
            temp_label.append(each_label[0])

        daily_time_diff_sum = pd.DataFrame({'label':temp_label,
                'daily time diff sum(s)':total_time_diff_for_that_label})
        
        all_the_days.append(daily_time_diff_sum)
    return all_the_days

#--------------------------------
# daily_time_diff_sum = get_daily_time_diff_sum(single_user_transion_time_diff_with_date)
def get_daily_sensor_derived_steps(all_the_days):
    step_speed = 1
    this_user_all_the_days=[]
    for daily_time_diff_sum in all_the_days:
        # Combine daily time diff sums with the avg_time_diff_for_labels
        merged_time_diff_df = pd.merge(avg_time_diff_for_labels, daily_time_diff_sum, on="label")
        merged_time_diff_df['daily units walked'] = merged_time_diff_df['reciprocal(unit/s)'] * merged_time_diff_df['daily time diff sum(s)']
        merged_time_diff_df['total steps'] = merged_time_diff_df['daily units walked'] * step_speed
        daily_sensor_derived_steps = merged_time_diff_df['total steps'].sum()
        this_user_all_the_days.append(daily_sensor_derived_steps)
    return this_user_all_the_days

# a and a1 for debug
a=[];a1=[]; sensor_derived_steps=[]
for each_choppedTime_slice in time_slice:
    transion_time_diff, transion_time_diff_with_date = get_time_diff_list(flatted_signle_user_time_motion,each_choppedTime_slice)
    avg_time_diff_for_labels = find_avg_time_diff_for_labels(transion_time_diff)
    daily_time_diff_sum = get_daily_time_diff_sum(transion_time_diff_with_date)
    daily_sensor_derived_steps = get_daily_sensor_derived_steps(daily_time_diff_sum)

    a.append(transion_time_diff); a1.append(transion_time_diff_with_date)
    sensor_derived_steps.append(daily_sensor_derived_steps)

sensor_derived_steps = [item for sublist in sensor_derived_steps for item in sublist]

#############################################################################
# Get (3)average_speed steps from sensor data (set speed = 2 steps/second) 
#############################################################################
# sum steps for Acrigraph
def get_acti_step(acti_data_list):
    temp_acti=[]
    for i in range(len(acti_data_list)):
        acti_data_day1 = acti_data_list[i]
        acti_step = acti_data_day1.sum().Steps
        temp_acti.append(acti_step)
    return temp_acti

wrist_acti_steps=[]
for wrist_acti_list in actitime_slice_total:
    wrist_steps = get_acti_step(wrist_acti_list)
    wrist_acti_steps.append(wrist_steps)
    
pedometer_acti_steps=[]  
for pedometer_acti_list in pedotime_slice_total:
    pedometer_steps = get_acti_step(pedometer_acti_list)
    pedometer_acti_steps.append(pedometer_steps)    
    
wrist_acti_steps = sum(wrist_acti_steps, [])
pedometer_acti_steps = sum(pedometer_acti_steps, [])

'''
# Visualize
import matplotlib.pyplot as plt
#plt.hist(mobility_steps);
#plt.hist(num_of_transitions);
plt.hist(wrist_acti_steps);
plt.hist(pedometer_acti_steps); 
'''


#############################################################################
# Correlation Comparision between acti_steps and num_of_transitions
#############################################################################
y = mobility_steps
x1 = sensor_derived_steps
x2 = num_of_transitions
x3 = wrist_acti_steps
x4 = pedometer_acti_steps
input_x_list = [x1,x2,x3,x4]


# Spearman rank correlation:measure the degree of association between two variables. 
# The Spearman rank correlation test does not carry any assumptions about the distribution of the data
rho_list=[];pval_list=[]
for elt in input_x_list:
    rho,p_val_spear = stats.spearmanr(elt,y)
    rho_list.append(rho);pval_list.append(p_val_spear)

item_list = ['avg speed derived steps','transition numbers','wrist_acti steps','pedometer steps']

spearmanr_result = pd.DataFrame({'item':item_list,'rho':rho_list,'p_val':pval_list})
print(spearmanr_result)  


