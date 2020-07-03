# Apr 5 to Apr 14
import os
import pandas as pd
import datetime as dt

filepath= os.path.abspath(r'D:/FloorMap/Qing Room/Single Home Motion Sensors.xls')

MotionData = pd.read_excel(filepath)
MotionData = MotionData[MotionData['sensor_value'] == 1]


#############################################################################
# Pre-selecting of useful time and data
#############################################################################
# get sensors names for each room
room_list = MotionData['room_name'].unique().tolist()
room_list.remove('BathroomTest')

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

# Use 10s sensor data
MotionData_10s = MotionData[ (MotionData['sensor_id'] == 1945) | (MotionData['sensor_id'] ==1955)|(MotionData['sensor_id'] ==1965)| (MotionData['sensor_id'] ==1898)| (MotionData['sensor_id'] ==1933)|(MotionData['sensor_id'] ==5145) ]

# Use 120s sensor data
MotionData_120s = MotionData[ (MotionData['sensor_id'] == 1938) | (MotionData['sensor_id'] ==1950)|(MotionData['sensor_id'] ==1876)| (MotionData['sensor_id'] ==1891)| (MotionData['sensor_id'] ==1928)|(MotionData['sensor_id'] ==2019) ]

# Use 240s sensor data
MotionData_240s = MotionData[ (MotionData['sensor_id'] == 1896) | (MotionData['sensor_id'] ==1881)|(MotionData['sensor_id'] ==1960)| (MotionData['sensor_id'] ==1910)| (MotionData['sensor_id'] ==1866)|(MotionData['sensor_id'] ==2009) ]

# Use continuos sensor data
MotionData_c = MotionData[ (MotionData['sensor_id'] == 2001) | (MotionData['sensor_id'] ==5135)|(MotionData['sensor_id'] ==5140)| (MotionData['sensor_id'] ==5130)| (MotionData['sensor_id'] ==5150)|(MotionData['sensor_id'] ==5145) ]


#############################################################################
# Get (1)ADL steps and (2)number of room transitions
#############################################################################
# Remove 'repetitive sensor'
def remove_dup_df(motion_data):
    # drop the duplicates in sensor_id
    drop_dup_df = motion_data.loc[(motion_data['sensor_id'].shift() != motion_data['sensor_id'])]
    return drop_dup_df


#-----------------------------------------------------------------------------  
# change all the sensor id into 0-6
def reunit_sensor_id(motion_data):
    cleanedData = remove_dup_df(motion_data)
    same_sensor_id = 0
    new_sensors_df = pd.DataFrame({}) 
    for each_room in room_list:
        temp = cleanedData[cleanedData['room_name'] == each_room]
        temp['sensor_id'] = same_sensor_id
        new_sensors_df = new_sensors_df.append(temp)
        same_sensor_id = same_sensor_id + 1
    # sort the data frame by exact_time
    new_sensors_df = new_sensors_df.sort_values(by=['TIMESTAMP'])
    return new_sensors_df

# 0:BathroomA   1:Toilet  2:Kitchen  3:BedroomA  4:Dining Room   5:Lounge
cleanedData_c = reunit_sensor_id(MotionData_c)
cleanedData_10s = reunit_sensor_id(MotionData_10s)
cleanedData_120s = reunit_sensor_id(MotionData_120s)
cleanedData_240s = reunit_sensor_id(MotionData_240s)
#-----------------------------------------------------------------------------  
# Add Ground Truth of all rooms
groundTruth_qing =  {'0 to 1':15,'0 to 2':23,'0 to 3':6,'0 to 4':18,
                     '0 to 5':27,'1 to 2':12,'1 to 3':16,'1 to 4':8,
                     '1 to 5':14,'2 to 3':24,'2 to 4':5,'2 to 5':11,
                     '3 to 4':19,'3 to 5':26,'4 to 5':10} 

#-----------------------------------------------------------------------------  
#-----------------------------------------------------------------------------  
# Chopped datetime
base = dt.datetime.strptime('2019-04-05 00:00:00', '%Y-%m-%d %H:%M:%S')
datelist = pd.date_range(base, periods=11).tolist()
choppedTime=[]
for elt in datelist:
    strg = f'{elt:%Y-%m-%d %H:%M:%S}'
    choppedTime.append(strg)


def labels_between_room(cleaned_ila):
    tempDF = pd.DataFrame({})
    temp1=[]
    for i in range(0, len(cleaned_ila)-1):
        room_previous_sensor = cleaned_ila.iloc[i]['sensor_id'] 
        room_next_sensor =  cleaned_ila.iloc[i+1]['sensor_id']
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
        if label[i] == '0 to 4' or label[i] == '4 to 0':
            temp.append('0 to 4')
        if label[i] == '0 to 5' or label[i] == '5 to 0':
            temp.append('0 to 5')
        if label[i] == '1 to 2' or label[i] == '2 to 1':
            temp.append('1 to 2')
        if label[i] == '1 to 3' or label[i] == '3 to 1':
            temp.append('1 to 3')
        if label[i] == '1 to 4' or label[i] == '4 to 1':
            temp.append('1 to 4')
        if label[i] == '1 to 5' or label[i] == '5 to 1':
            temp.append('1 to 5')
        if label[i] == '2 to 3' or label[i] == '3 to 2':
            temp.append('2 to 3')
        if label[i] == '2 to 4' or label[i] == '4 to 2':
            temp.append('2 to 4')
        if label[i] == '2 to 5' or label[i] == '5 to 2':
            temp.append('2 to 5')
        if label[i] == '3 to 4' or label[i] == '4 to 3':
            temp.append('3 to 4')
        if label[i] == '3 to 5' or label[i] == '5 to 3':
            temp.append('3 to 5')
        if label[i] == '4 to 5' or label[i] == '5 to 4':
            temp.append('4 to 5')
    return temp


def get_two_arrays(cleaned_ila,groundTruth_ila):
    temp_adl_arr1=[];temp_arr2=[]
    for i in range(len(choppedTime)-1):
        choppedila_day  = cleaned_ila[cleaned_ila['local_timestamp'] > choppedTime[i]]
        choppedila_day  = choppedila_day[choppedila_day['local_timestamp'] < choppedTime[i+1]]
        ila_lablled = labels_between_room(choppedila_day)
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

# Get the 2 arrays from each households
adl_c,arr2_c = get_two_arrays(cleanedData_c,groundTruth_qing)
adl_10s,arr2_10s = get_two_arrays(cleanedData_10s,groundTruth_qing)
adl_120s,arr2_120s = get_two_arrays(cleanedData_120s,groundTruth_qing)
adl_240s,arr2_240s = get_two_arrays(cleanedData_240s,groundTruth_qing)

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

transion_time_diff, transion_time_diff_with_date = get_time_diff_list(cleanedData_c,choppedTime)

#--------------------------------  
def labelled_room_and_time_diff(cleaned_ila):
    tempDF = pd.DataFrame({})
    temp1=[];temp2=[]
    for i in range(0, len(cleaned_ila)-1):
        room_previous_sensor = cleaned_ila.iloc[i]['sensor_id'] 
        room_next_sensor =  cleaned_ila.iloc[i+1]['sensor_id']
        label = str(int(room_previous_sensor))+' to '+str(int(room_next_sensor)) 
        temp1.append(label)
        
        room_previous_time = cleaned_ila.iloc[i]['local_timestamp']
        room_previous_time = dt.datetime.strptime(room_previous_time, '%b %d %Y %I:%M%p')
        room_next_time =  cleaned_ila.iloc[i+1]['local_timestamp']
        room_next_time = dt.datetime.strptime(room_next_time, '%Y-%mm-%D %H:%M:%S')
        time_diff =  (room_next_time - room_previous_time).seconds
        temp2.append(time_diff)

    tempDF['label'] = temp1
    tempDF['time difference'] = temp2
    return tempDF

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
        that_day = that_day_list[0][0:10:] # trim datetime hours
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
transion_time_diff, transion_time_diff_with_date = get_time_diff_list(cleanedData_c,choppedTime)
avg_time_diff_for_labels = find_avg_time_diff_for_labels(transion_time_diff)
daily_time_diff_sum = get_daily_time_diff_sum(transion_time_diff_with_date)
daily_sensor_derived_steps = get_daily_sensor_derived_steps(daily_time_diff_sum)









#############################################################################
# Correlation Comparision
#############################################################################
import matplotlib.pyplot as plt
plt.hist(adl_c);plt.hist(arr2_c) # blue: ADL; orange: arr2
'''
plt.hist(adl_10s);plt.hist(arr2_10s) 

plt.hist(adl_120s);plt.hist(arr2_120s) 

plt.hist(adl_240s);plt.hist(arr2_240s) 

'''
#-----------------------------------------------------------------------------  
# Pearson: assume normally distributed. Linearity assumes a straight line 
# relationship between each of the two variables and 
# homoscedasticity assumes that data is equally distributed about the regression line. 
from scipy import stats
two_tailed_p_value_c = stats.pearsonr(adl_c,arr2_c)
print('Pearson 2 tail, continous(cts) ferrying:',two_tailed_p_value_c)
two_tailed_p_value_10s = stats.pearsonr(adl_10s,arr2_10s)
print('Pearson 2 tail, 10s ferrying:',two_tailed_p_value_10s)
two_tailed_p_value_120s = stats.pearsonr(adl_120s,arr2_120s)
print('Pearson 2 tail, 120s ferrying:',two_tailed_p_value_120s)
two_tailed_p_value_240s = stats.pearsonr(adl_240s,arr2_240s)
print('Pearson 2 tail, continous ferrying:',two_tailed_p_value_240s)

#-----------------------------------------------------------------------------  
# Kendall rank correlation: measures the strength of dependence between two variables
tau_c, p_val_ken_c = stats.kendalltau(adl_c,arr2_c)
print('Kendall tau,cts ferrying:',tau_c,' Kendall p_value,cts ferrying:',p_val_ken_c)
tau_10s, p_val_ken_10s = stats.kendalltau(adl_10s,arr2_10s)
print('Kendall tau,10s ferrying:',tau_10s,' Kendall p_value,10s ferrying:',p_val_ken_10s)
tau_120s, p_val_ken_120s = stats.kendalltau(adl_120s,arr2_120s)
print('Kendall tau,120s ferrying:',tau_120s,' Kendall p_value,120s ferrying:',p_val_ken_120s)
tau_240s, p_val_ken_240s = stats.kendalltau(adl_240s,arr2_240s)
print('Kendall tau,240s ferrying:',tau_240s,' Kendall p_value,240s ferrying:',p_val_ken_240s)

#-----------------------------------------------------------------------------  
# Spearman rank correlation:measure the degree of association between two variables. 
# The Spearman rank correlation test does not carry any assumptions about the distribution of the data
rho_c,p_val_c = stats.spearmanr(adl_c,arr2_c)
print('Spearman rho,cts ferrying:',rho_c,' Spearman p_value,cts ferrying:',p_val_c)
rho_10s,p_val_10s = stats.spearmanr(adl_10s,arr2_10s)
print('Spearman rho,10s ferrying:',rho_10s,' Spearman p_value,10s ferrying:',p_val_10s)
rho_120s,p_val_120s = stats.spearmanr(adl_120s,arr2_120s)
print('Spearman rho,120s ferrying:',rho_120s,' Spearman p_value,120s ferrying:',p_val_120s)
rho_240s,p_val_240s = stats.spearmanr(adl_240s,arr2_240s)
print('Spearman rho,240s ferrying:',rho_240s,' Spearman p_value,240s ferrying:',p_val_240s)








