from scipy import stats
import pandas as pd
import datetime as dt
import numpy as np
from matplotlib import pyplot as plt


all_dacs_sensor = pd.read_csv(r'D:\DACS\Archive\DACS_All_Data_20191030.csv')
all_dacs_mobility = pd.read_csv(r'D:/DACS/Archive/mobility.csv')

# Replace all Mar with 3, all other month with corresponding number
all_dacs_mobility['unit'] = all_dacs_mobility['unit'].replace(
        ['3-Jan','3-Jul','3-Jun','3-Mar','3-May','3-Nov','3-Oct'], 
        ['3-1','3-7','3-6','3-3','3-5','3-11','3-10'])

all_dacs_mobility['unit'] = all_dacs_mobility['unit'].replace(
  ['Mar-13','Mar-15','Mar-16','Mar-18','Mar-19','Mar-20','Mar-21','Mar-24','Mar-27',
   'Mar-28','Mar-29','Mar-35','Mar-37','Mar-38','Mar-39','Mar-41','Mar-42','Mar-48',
   'Mar-51','Mar-52','Mar-55','Mar-57','Mar-58','Mar-59','Mar-62','Mar-65','Mar-66',
   'Mar-67','Mar-70','Mar-80','Mar-84','Mar-85','Mar-87','Mar-89','Mar-91','Mar-92',
   'Mar-93','Mar-94','Mar-96','Mar-97'], 
  ['3-13','3-15','3-16','3-18','3-19','3-20','3-21','3-24','3-27','3-28','3-29',
   '3-35','3-37','3-38','3-39','3-41','3-42','3-48','3-51','3-52','3-55','3-57',
   '3-58','3-59','3-62','3-65','3-66','3-67','3-70','3-80','3-84','3-85','3-87',
   '3-89','3-91','3-92','3-93','3-94','3-96','3-97'])

# If sensor readings unit is not in mobility unit, just delete
people_list = all_dacs_sensor['PID'].unique().tolist()
people_list_mobility = all_dacs_mobility['unit'].unique().tolist()

# remove 4 houses: 102,112,159,175 from mobility
people_list_mobility.remove('3-102');people_list_mobility.remove('3-112');
people_list_mobility.remove('3-159');people_list_mobility.remove('3-175')
people_list_mobility.remove('3-131');people_list_mobility.remove('3-164')
people_list_mobility.remove('3-157');people_list_mobility.remove('3-42')

# find the units that appear in mobility but not in sensor reading
unit_not_in_mobility = [elem for elem in people_list if elem not in people_list_mobility]
# remove these units from sensor reading dataframe
# The ~ is a not operator 
new_dacs_sensor = all_dacs_sensor[~all_dacs_sensor.PID.isin(unit_not_in_mobility)]
# drop the multi-residential houses from all_dacs_mobility,3-157 has 2 days data, drop too
unit_to_remove_from_mobility = ['3-102','3-112','3-159','3-175','3-131','3-164','3-157','3-42']
new_dacs_mobility = all_dacs_mobility[~all_dacs_mobility.unit.isin(unit_to_remove_from_mobility)]

# split the whole data into different people/unit
mobility_grouped_list = list(new_dacs_mobility.groupby(['unit']))
sensor_grouped_list = list(new_dacs_sensor.groupby(['PID']))

#############################################################################
# Pre-selecting of useful time and data
#############################################################################
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
    
    # up to this step, we have get the dataframw, but don't forget to convert to time object
    datetime_list = []
    time_list = MotionData_ila["local_timestamp"].values.tolist()
    for elt in time_list:
        aa = dt.datetime.strptime(elt, '%Y-%m-%d %H:%M:%S')
        datetime_list.append(aa)
    MotionData_ila['extact_time'] = time_list         
    
    # Sort the datetime 
    aaa = MotionData_ila.sort_values(by="extact_time") 
    return aaa

reformed_sensor_list=[]
for each_PID in sensor_grouped_list:
    PID_motiondata = each_PID[1]
    reformed_each_df = reform_df(PID_motiondata)
    reformed_sensor_list.append(reformed_each_df)

# reform the mobility since cleaned_sensor_list and mobility_list have same PID units
reformed_mobility_list=[]    
for each_unit in mobility_grouped_list:
    unit_motiondata = each_unit[1]
    reformed_mobility_list.append(unit_motiondata)
    
    
#----------------------------------------------------------------------------- 
# For each unit in reformed_mobility_list and reformed_sensor_list, remove the 
# dates that not shown in reformed_mobility_list
cleaned_sensor_list = []

for i in range(len(reformed_sensor_list)):
    each_PID = reformed_sensor_list[i]
    each_unit = reformed_mobility_list[i]
    # for the two dataframe, check the time
    mobility_date = each_unit.date.tolist()
    sensor_date = each_PID.local_timestamp.tolist()
    #  mobility has time format YY-MM-DD but sensor also has hours
    mobility_date = [dt.datetime.strptime(date, '%d/%m/%Y').date() for date in mobility_date] 
    sensor_date = [dt.datetime.strptime(date, '%Y-%m-%d %H:%M:%S') for date in sensor_date]
    # sensor hours can be removed
    sensor_date_truncated = [each_day.date() for each_day in sensor_date] 
    # now the days that in sensor reading but not in mobilty are found
    date_not_in_mobility = [elem for elem in sensor_date_truncated if elem not in mobility_date]
    # remove repetitive items in date_not_in_mobility
    date_notin_mobility = list(set(date_not_in_mobility))
    date_notin_mobility = sorted(date_notin_mobility)
    # transfer the list back to str format
    aaa = [each_date.__str__() for each_date in date_notin_mobility] 

    # after the for loop, each_PID will have same dates as each_unit in mobility
    for a in aaa:
        # find the sensor readings that should be deleted
        deleted = each_PID[each_PID['extact_time'].str.contains(a)]
        # remove these units from sensor reading dataframe
        each_PID = pd.concat([each_PID, deleted]).drop_duplicates(keep=False)

    cleaned_sensor_list.append(each_PID)

#############################################################################
# Get the lists of transition times
#############################################################################
# Remove 'repetitive sensor'
def remove_dup_df(motion_data):
    # drop the duplicates in sensor_id
    drop_dup_df = motion_data.loc[(motion_data['sensor_id'].shift() != motion_data['sensor_id'])]
    return drop_dup_df
#----------------------------------------------------------------------------- 
sensor_list=[]
for each_PID in cleaned_sensor_list:
    cleaned_each_df = remove_dup_df(each_PID)
    sensor_list.append(cleaned_each_df)

'''
time span for mobility: 2019/04/26 - 2019/10/29(included) (maximal 172 days in mobility_list). 
Just remove the dates that are not in this range for sensor_list
'''    
# Chopped datetime
base = dt.datetime.strptime('2019-04-26 00:00:00', '%Y-%m-%d %H:%M:%S')
datelist = pd.date_range(base, periods=188).tolist()
choppedTime=[]
for elt in datelist:
    strg = f'{elt:%Y-%m-%d %H:%M:%S}'
    choppedTime.append(strg)

# Keep the sensor readings from sensor_list based on the chopped time
start_time = choppedTime[0]
end_time = choppedTime[-1]
final_sensor_list=[]
for each_user_sensor_reading in sensor_list:
    each_user_sensor_reading = each_user_sensor_reading[(each_user_sensor_reading['local_timestamp'] > start_time) & (each_user_sensor_reading['local_timestamp'] < end_time) ]
    final_sensor_list.append(each_user_sensor_reading)

#-----------------------------------------------------------------------------  
# get daily room transition

# find maximal and minimal snesors
max_rooms=0
min_rooms=len(final_sensor_list[0]['new_sensor_id'].unique().tolist())
for each_user in final_sensor_list:
    test_user_room_list = each_user['new_sensor_id'].unique().tolist()
    if len(test_user_room_list) >= max_rooms:
        max_rooms = len(test_user_room_list)
    if len(test_user_room_list) < min_rooms:
        min_rooms = len(test_user_room_list)
# now we know max_room=10, min_room=5

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
for test_user in final_sensor_list:
    user_sensor_reading = change_sensor_name(test_user)
    finally_sensor_list.append(user_sensor_reading)
#-----------------------------------------------------------------------------  
# merge '3 to 4' and '4 to 3'
def merge_5_sensors(ila_lablled):
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
        if label[i] == '1 to 2' or label[i] == '2 to 1':
            temp.append('1 to 2')
        if label[i] == '1 to 3' or label[i] == '3 to 1':
            temp.append('1 to 3')
        if label[i] == '1 to 4' or label[i] == '4 to 1':
            temp.append('1 to 4')
        if label[i] == '2 to 3' or label[i] == '3 to 2':
            temp.append('2 to 3')
        if label[i] == '2 to 4' or label[i] == '4 to 2':
            temp.append('2 to 4')
        if label[i] == '3 to 4' or label[i] == '4 to 3':
            temp.append('3 to 4')
    return temp


def merge_6_sensors(ila_lablled):
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


def merge_7_sensors(ila_lablled):
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
        if label[i] == '0 to 6' or label[i] == '6 to 0':
            temp.append('0 to 6')
            
        if label[i] == '1 to 2' or label[i] == '2 to 1':
            temp.append('1 to 2')
        if label[i] == '1 to 3' or label[i] == '3 to 1':
            temp.append('1 to 3')
        if label[i] == '1 to 4' or label[i] == '4 to 1':
            temp.append('1 to 4')
        if label[i] == '1 to 5' or label[i] == '5 to 1':
            temp.append('1 to 5')              
        if label[i] == '1 to 6' or label[i] == '6 to 1':
            temp.append('1 to 6')

        if label[i] == '2 to 3' or label[i] == '3 to 2':
            temp.append('2 to 3')
        if label[i] == '2 to 4' or label[i] == '4 to 2':
            temp.append('2 to 4')
        if label[i] == '2 to 5' or label[i] == '5 to 2':
            temp.append('2 to 5')           
        if label[i] == '2 to 6' or label[i] == '6 to 2':
            temp.append('2 to 6')            
           
        if label[i] == '3 to 4' or label[i] == '4 to 3':
            temp.append('3 to 4')
        if label[i] == '3 to 5' or label[i] == '5 to 3':
            temp.append('3 to 5')
        if label[i] == '3 to 6' or label[i] == '6 to 3':
            temp.append('3 to 6')           
            
        if label[i] == '4 to 5' or label[i] == '5 to 4':
            temp.append('4 to 5')
        if label[i] == '4 to 6' or label[i] == '6 to 4':
            temp.append('4 to 6')

        if label[i] == '5 to 6' or label[i] == '6 to 5':
            temp.append('5 to 6')
                
    return temp


def merge_8_sensors(ila_lablled):
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
        if label[i] == '0 to 6' or label[i] == '6 to 0':
            temp.append('0 to 6')
        if label[i] == '0 to 7' or label[i] == '7 to 0':
            temp.append('0 to 7')
            
        if label[i] == '1 to 2' or label[i] == '2 to 1':
            temp.append('1 to 2')
        if label[i] == '1 to 3' or label[i] == '3 to 1':
            temp.append('1 to 3')
        if label[i] == '1 to 4' or label[i] == '4 to 1':
            temp.append('1 to 4')
        if label[i] == '1 to 5' or label[i] == '5 to 1':
            temp.append('1 to 5')              
        if label[i] == '1 to 6' or label[i] == '6 to 1':
            temp.append('1 to 6')
        if label[i] == '1 to 7' or label[i] == '7 to 1':
            temp.append('1 to 7')

        if label[i] == '2 to 3' or label[i] == '3 to 2':
            temp.append('2 to 3')
        if label[i] == '2 to 4' or label[i] == '4 to 2':
            temp.append('2 to 4')
        if label[i] == '2 to 5' or label[i] == '5 to 2':
            temp.append('2 to 5')           
        if label[i] == '2 to 6' or label[i] == '6 to 2':
            temp.append('2 to 6')
        if label[i] == '2 to 7' or label[i] == '7 to 2':
            temp.append('2 to 7')
           
        if label[i] == '3 to 4' or label[i] == '4 to 3':
            temp.append('3 to 4')
        if label[i] == '3 to 5' or label[i] == '5 to 3':
            temp.append('3 to 5')
        if label[i] == '3 to 6' or label[i] == '6 to 3':
            temp.append('3 to 6')
        if label[i] == '3 to 7' or label[i] == '7 to 3':
            temp.append('3 to 7')            
            
        if label[i] == '4 to 5' or label[i] == '5 to 4':
            temp.append('4 to 5')
        if label[i] == '4 to 6' or label[i] == '6 to 4':
            temp.append('4 to 6')
        if label[i] == '4 to 7' or label[i] == '7 to 4':
            temp.append('4 to 7')

        if label[i] == '5 to 6' or label[i] == '6 to 5':
            temp.append('5 to 6')
        if label[i] == '5 to 7' or label[i] == '7 to 5':
            temp.append('5 to 7')
            
        if label[i] == '6 to 7' or label[i] == '7 to 6':
            temp.append('6 to 7')
                
    return temp

def merge_9_sensors(ila_lablled):
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
        if label[i] == '0 to 6' or label[i] == '6 to 0':
            temp.append('0 to 6')
        if label[i] == '0 to 7' or label[i] == '7 to 0':
            temp.append('0 to 7')
        if label[i] == '0 to 8' or label[i] == '8 to 0':
            temp.append('0 to 8')
            
        if label[i] == '1 to 2' or label[i] == '2 to 1':
            temp.append('1 to 2')
        if label[i] == '1 to 3' or label[i] == '3 to 1':
            temp.append('1 to 3')
        if label[i] == '1 to 4' or label[i] == '4 to 1':
            temp.append('1 to 4')
        if label[i] == '1 to 5' or label[i] == '5 to 1':
            temp.append('1 to 5')              
        if label[i] == '1 to 6' or label[i] == '6 to 1':
            temp.append('1 to 6')
        if label[i] == '1 to 7' or label[i] == '7 to 1':
            temp.append('1 to 7')
        if label[i] == '1 to 8' or label[i] == '8 to 1':
            temp.append('1 to 8')

        if label[i] == '2 to 3' or label[i] == '3 to 2':
            temp.append('2 to 3')
        if label[i] == '2 to 4' or label[i] == '4 to 2':
            temp.append('2 to 4')
        if label[i] == '2 to 5' or label[i] == '5 to 2':
            temp.append('2 to 5')           
        if label[i] == '2 to 6' or label[i] == '6 to 2':
            temp.append('2 to 6')
        if label[i] == '2 to 7' or label[i] == '7 to 2':
            temp.append('2 to 7')
        if label[i] == '2 to 8' or label[i] == '8 to 2':
            temp.append('2 to 8')
            
           
        if label[i] == '3 to 4' or label[i] == '4 to 3':
            temp.append('3 to 4')
        if label[i] == '3 to 5' or label[i] == '5 to 3':
            temp.append('3 to 5')
        if label[i] == '3 to 6' or label[i] == '6 to 3':
            temp.append('3 to 6')
        if label[i] == '3 to 7' or label[i] == '7 to 3':
            temp.append('3 to 7')
        if label[i] == '3 to 8' or label[i] == '8 to 3':
            temp.append('3 to 8')
            
            
        if label[i] == '4 to 5' or label[i] == '5 to 4':
            temp.append('4 to 5')
        if label[i] == '4 to 6' or label[i] == '6 to 4':
            temp.append('4 to 6')
        if label[i] == '4 to 7' or label[i] == '7 to 4':
            temp.append('4 to 7')
        if label[i] == '4 to 8' or label[i] == '8 to 4':
            temp.append('4 to 8')

        if label[i] == '5 to 6' or label[i] == '6 to 5':
            temp.append('5 to 6')
        if label[i] == '5 to 7' or label[i] == '7 to 5':
            temp.append('5 to 7')
        if label[i] == '5 to 8' or label[i] == '8 to 5':
            temp.append('5 to 8')
            
        if label[i] == '6 to 7' or label[i] == '7 to 6':
            temp.append('6 to 7')
        if label[i] == '6 to 8' or label[i] == '8 to 6':
            temp.append('6 to 8')
            
        if label[i] == '7 to 8' or label[i] == '8 to 7':
            temp.append('8 to 7')
                
    return temp


def merge_10_sensors(ila_lablled):
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
        if label[i] == '0 to 6' or label[i] == '6 to 0':
            temp.append('0 to 6')
        if label[i] == '0 to 7' or label[i] == '7 to 0':
            temp.append('0 to 7')
        if label[i] == '0 to 8' or label[i] == '8 to 0':
            temp.append('0 to 8')
        if label[i] == '0 to 9' or label[i] == '9 to 0':
            temp.append('0 to 9')

        if label[i] == '1 to 2' or label[i] == '2 to 1':
            temp.append('1 to 2')
        if label[i] == '1 to 3' or label[i] == '3 to 1':
            temp.append('1 to 3')
        if label[i] == '1 to 4' or label[i] == '4 to 1':
            temp.append('1 to 4')
        if label[i] == '1 to 5' or label[i] == '5 to 1':
            temp.append('1 to 5')              
        if label[i] == '1 to 6' or label[i] == '6 to 1':
            temp.append('1 to 6')
        if label[i] == '1 to 7' or label[i] == '7 to 1':
            temp.append('1 to 7')
        if label[i] == '1 to 8' or label[i] == '8 to 1':
            temp.append('1 to 8')
        if label[i] == '1 to 9' or label[i] == '9 to 1':
            temp.append('1 to 9')

        if label[i] == '2 to 3' or label[i] == '3 to 2':
            temp.append('2 to 3')
        if label[i] == '2 to 4' or label[i] == '4 to 2':
            temp.append('2 to 4')
        if label[i] == '2 to 5' or label[i] == '5 to 2':
            temp.append('2 to 5')           
        if label[i] == '2 to 6' or label[i] == '6 to 2':
            temp.append('2 to 6')
        if label[i] == '2 to 7' or label[i] == '7 to 2':
            temp.append('2 to 7')
        if label[i] == '2 to 8' or label[i] == '8 to 2':
            temp.append('2 to 8')
        if label[i] == '2 to 9' or label[i] == '9 to 2':
            temp.append('2 to 9')           
           
        if label[i] == '3 to 4' or label[i] == '4 to 3':
            temp.append('3 to 4')
        if label[i] == '3 to 5' or label[i] == '5 to 3':
            temp.append('3 to 5')
        if label[i] == '3 to 6' or label[i] == '6 to 3':
            temp.append('3 to 6')
        if label[i] == '3 to 7' or label[i] == '7 to 3':
            temp.append('3 to 7')
        if label[i] == '3 to 8' or label[i] == '8 to 3':
            temp.append('3 to 8')
        if label[i] == '3 to 9' or label[i] == '9 to 3':
            temp.append('3 to 9')
            
        if label[i] == '4 to 5' or label[i] == '5 to 4':
            temp.append('4 to 5')
        if label[i] == '4 to 6' or label[i] == '6 to 4':
            temp.append('4 to 6')
        if label[i] == '4 to 7' or label[i] == '7 to 4':
            temp.append('4 to 7')
        if label[i] == '4 to 8' or label[i] == '8 to 4':
            temp.append('4 to 8')
        if label[i] == '4 to 9' or label[i] == '9 to 4':
            temp.append('4 to 9')

        if label[i] == '5 to 6' or label[i] == '6 to 5':
            temp.append('5 to 6')
        if label[i] == '5 to 7' or label[i] == '7 to 5':
            temp.append('5 to 7')
        if label[i] == '5 to 8' or label[i] == '8 to 5':
            temp.append('5 to 8')
        if label[i] == '5 to 9' or label[i] == '9 to 5':
            temp.append('5 to 9')
            
        if label[i] == '6 to 7' or label[i] == '7 to 6':
            temp.append('6 to 7')
        if label[i] == '6 to 8' or label[i] == '8 to 6':
            temp.append('6 to 8')
        if label[i] == '6 to 9' or label[i] == '9 to 6':
            temp.append('6 to 9')
            
        if label[i] == '7 to 8' or label[i] == '8 to 7':
            temp.append('8 to 7')
        if label[i] == '7 to 9' or label[i] == '9 to 7':
            temp.append('7 to 9')

        if label[i] == '8 to 9' or label[i] == '9 to 8':
            temp.append('8 to 9')
                
    return temp

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

# get_transition_arrays will give daily transition numbers
def get_transition_arrays(cleaned_ila,choppedTime):
    # count how many rooms in this user's house
    room_num = len(cleaned_ila['changed_sensor_id'].unique().tolist())
    # print(room_num)
    transition=[]
    for i in range(len(choppedTime)-1):
        # get daily motion data
        choppedila_day  = cleaned_ila[cleaned_ila['local_timestamp'] > choppedTime[i]]
        choppedila_day  = choppedila_day[choppedila_day['local_timestamp'] < choppedTime[i+1]]
        # choppedTime start  4-26, hence sometime the choppedila_day could be length 0
        if len(choppedila_day)==0:
            continue
        # label the transitions and change them to merged transition labels
        ila_lablled = labels_between_room(choppedila_day)

        if room_num == 5:
            merge_labelled_ilaList = merge_5_sensors(ila_lablled)
        if room_num == 6:
            merge_labelled_ilaList = merge_6_sensors(ila_lablled)
        if room_num == 7:
            merge_labelled_ilaList = merge_7_sensors(ila_lablled)
        if room_num == 8:
            merge_labelled_ilaList = merge_8_sensors(ila_lablled)
        if room_num == 9:
            merge_labelled_ilaList = merge_9_sensors(ila_lablled)
        if room_num == 10:
            merge_labelled_ilaList = merge_10_sensors(ila_lablled)

        transition.append(len(merge_labelled_ilaList))
    
    return transition

'''
 User 3-70 has mobility from 07.30 - 8.28 but sensor reading from 6.12, 7.19,7.29-8.28. 
 So previously we ensure the date of sensor matches the mobility,
 now make sure the date of mobility can match sensor
'''
# Chopped datetime
base2 = dt.datetime.strptime('2019-07-30 00:00:00', '%Y-%m-%d %H:%M:%S')
datelist2 = pd.date_range(base2, periods=31).tolist()
choppedTime2=[]
for elt in datelist2:
    strg = f'{elt:%Y-%m-%d %H:%M:%S}'
    choppedTime2.append(strg)

# Keep the sensor readings from sensor_list based on the chopped time
start_time2 = choppedTime2[0]
end_time2 = choppedTime2[-1]
the_XXX_user = reformed_mobility_list[61]
# change the date format in 'date'
the_XXX_user['new_date'] = pd.to_datetime(the_XXX_user["date"], format = '%d/%m/%Y')
# chop the user's mobility and put back to reformed_mobility_list
the_XXXAAA_user = the_XXX_user[(the_XXX_user['new_date'] >= start_time2)& (the_XXX_user['new_date'] < end_time2)]
reformed_mobility_list[61] = the_XXXAAA_user

'''
 User 3-65 has mobility from 07.29-10.27 but sensor reading from 10.2-10.30. 
 So previously we ensure the date of sensor matches the mobility,
 now make sure the date of mobility can match sensor
'''
# Chopped datetime
base3 = dt.datetime.strptime('2019-10-02 00:00:00', '%Y-%m-%d %H:%M:%S')
datelist3 = pd.date_range(base3, periods=27).tolist()
choppedTime3=[]
for elt in datelist3:
    strg = f'{elt:%Y-%m-%d %H:%M:%S}'
    choppedTime3.append(strg)

# Keep the sensor readings from sensor_list based on the chopped time
start_time3 = choppedTime3[0]
end_time3 = choppedTime3[-1]
the_XXX_user = reformed_mobility_list[57]
# change the date format in 'date'
the_XXX_user['new_date'] = pd.to_datetime(the_XXX_user["date"], format = '%d/%m/%Y')
# chop the user's mobility and put back to reformed_mobility_list
the_XXXAAA_user = the_XXX_user[(the_XXX_user['new_date'] >= start_time3) & (the_XXX_user['new_date'] < end_time3) ]
reformed_mobility_list[57] = the_XXXAAA_user


'''
LONG COMPUTING TIME
'''
temp_transition=[]
for each_user in finally_sensor_list:
    transition = get_transition_arrays(each_user,choppedTime)
    # remove all the 0 from transition list
    final_transition = list(filter(lambda a: a != 0, transition))    
    temp_transition.append(final_transition)

# Ground truth mobility
temp_mobility=[]
for each_user_mobility in reformed_mobility_list:
    aa = each_user_mobility['VALUE'].tolist()
    final_mobility = list(filter(lambda a: a != 0, aa))
    temp_mobility.append(final_mobility)
    
    
## get 3-121 and 3-42 dataframe
#Mar121Date = reformed_mobility_list[9]['date'].tolist()     
#Mar121 = pd.DataFrame({'date':Mar121Date,'transition':temp_transition[9],'step':temp_mobility[9]})   
#Mar42Date = reformed_mobility_list[47]['date'].tolist() 
##  Mar42Date has 95, while temp_transition[47] and temp_mobility[47] have 93 elements, so error   
#Mar42 = pd.DataFrame({'date':Mar42Date,'transition':temp_transition[47],'step':temp_mobility[47]})   
    
    
#-----------------------------------------------------------------------------  
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
        label = str(int(room_previous_sensor))+' to '+str(int(room_next_sensor)) 
        temp1.append(label)
        
        room_previous_time = cleaned_ila.iloc[i]['local_timestamp'] 
        room_previous_time = dt.datetime.strptime(room_previous_time, '%Y-%m-%d %H:%M:%S')
        room_next_time =  cleaned_ila.iloc[i+1]['local_timestamp']
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
            merge_labelled_ilaList = merge_5_sensors(ila_lablled)
        if room_num == 6:
            merge_labelled_ilaList = merge_6_sensors(ila_lablled)
        if room_num == 7:
            merge_labelled_ilaList = merge_7_sensors(ila_lablled)
        if room_num == 8:
            merge_labelled_ilaList = merge_8_sensors(ila_lablled)
        if room_num == 9:
            merge_labelled_ilaList = merge_9_sensors(ila_lablled)
        if room_num == 10:
            merge_labelled_ilaList = merge_10_sensors(ila_lablled)
    
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
#test_user = finally_sensor_list[10]
#single_user_transion_time_diff, single_user_transion_time_diff_with_date = get_time_diff_list(test_user,choppedTime)

#--------------------------------  
def find_avg_time_diff_for_labels(single_user_transion_time_diff):
    # find the avg time diff of each label
    time_diff_grouped_list = list(single_user_transion_time_diff.groupby(['transition label']))

    avg=[];labels=[]
    for each_label in time_diff_grouped_list:
        each_label_avg = each_label[1]['time diff'].mean()
        avg.append(each_label_avg)
        labels.append(each_label[0])
    reciprocal = [1/i for i in avg]
    avg_time_diff_for_labels = pd.DataFrame({'label':labels,'avg time(s)':avg,
                                             'reciprocal(unit/s)':reciprocal})
    return avg_time_diff_for_labels
#--------------------------------  
#avg_time_diff_for_labels = find_avg_time_diff_for_labels(single_user_transion_time_diff)

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
    step_speed = 1.57
    this_user_all_the_days=[]
    for daily_time_diff_sum in all_the_days:
        # Combine daily time diff sums with the avg_time_diff_for_labels
        merged_time_diff_df = pd.merge(avg_time_diff_for_labels, daily_time_diff_sum, on="label")
        merged_time_diff_df['daily units walked'] = merged_time_diff_df['reciprocal(unit/s)'] * merged_time_diff_df['daily time diff sum(s)']
        merged_time_diff_df['total steps'] = merged_time_diff_df['daily units walked'] * step_speed
        daily_sensor_derived_steps = merged_time_diff_df['total steps'].sum()
        this_user_all_the_days.append(daily_sensor_derived_steps)
    return this_user_all_the_days

#--------------------------------
# for debug
test_user = finally_sensor_list[58]
single_user_transion_time_diff, single_user_transion_time_diff_with_date = get_time_diff_list(test_user,choppedTime)
avg_time_diff_for_labels = find_avg_time_diff_for_labels(single_user_transion_time_diff)
daily_time_diff_sum = get_daily_time_diff_sum(single_user_transion_time_diff_with_date)
daily_sensor_derived_steps = get_daily_sensor_derived_steps(daily_time_diff_sum)

import time
start_time = time.time()

temp_sensor_derived_steps=[]
for each_user in finally_sensor_list:
    single_user_transion_time_diff, single_user_transion_time_diff_with_date = get_time_diff_list(each_user,choppedTime)
    # get the avg time diff for this user 
    avg_time_diff_for_labels = find_avg_time_diff_for_labels(single_user_transion_time_diff)
    # now for this user, every day there is a mobility. In total there are X days mobility
    all_the_days = get_daily_time_diff_sum(single_user_transion_time_diff_with_date)
    this_user_all_the_days = get_daily_sensor_derived_steps(all_the_days)
    # remove all the 0 from transition list
    final_this_user_all_the_days = list(filter(lambda a: a != 0, this_user_all_the_days))    
    temp_sensor_derived_steps.append(final_this_user_all_the_days)

print("--- %s seconds ---" % (time.time() - start_time)) # 278.122 seconds 

# for debug
a1=[]
for mob in temp_sensor_derived_steps:
    t = len(mob)
    a1.append(t)
a2=[]
for trans in temp_mobility:
    t = len(trans)
    a2.append(t)  
aaa1 = [elem for elem in a2 if elem not in a1]

print('if aaa1_indices has list index out of range, then bug free')
aaa1_indices = [i for i, x in enumerate(a2) if x == aaa1[1]]
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

flat_sensor_derived_step = [item for sublist in temp_sensor_derived_steps for item in sublist]
result3 = bootstrap(flat_sensor_derived_step, 2000, 0.95, average)

 
#############################################################################
# Case Study: 3-1
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
            merge_labelled_ilaList = merge_5_sensors(ila_lablled)
        if room_num == 6:
            merge_labelled_ilaList = merge_6_sensors(ila_lablled)
        if room_num == 7:
            merge_labelled_ilaList = merge_7_sensors(ila_lablled)
        if room_num == 8:
            merge_labelled_ilaList = merge_8_sensors(ila_lablled)
        if room_num == 9:
            merge_labelled_ilaList = merge_9_sensors(ila_lablled)
        if room_num == 10:
            merge_labelled_ilaList = merge_10_sensors(ila_lablled)

        transition.append(len(merge_labelled_ilaList))

    merged_df = pd.DataFrame({'Day':day,'Transition daily':transition})
    return merged_df

case = finally_sensor_list[0]
case_df = get_transition_in_dates(case,choppedTime)
case_mobility = temp_sensor_derived_steps[0]
case_df['Steps'] = case_mobility
#case_df.to_csv(r'D:\DACS\Archive\case_df.csv')
# now get Y axis and X axis
dates = [pd.to_datetime(date) for date in case_df['Day']]
# set the plot
plt.figure(figsize =(11,9))

plt.subplot(2, 1, 1)
plt.scatter(dates, case_df['Transition daily'],label='Room Transitions',s =20, c = 'blue')
plt.grid(True,alpha=0.5)
plt.legend(loc='upper left')
plt.ylabel('Transition Counts')

plt.subplot(2, 1, 2)
plt.scatter(dates, case_df['Steps'],label='Fixed-distance Mobility',s =20, c = 'red')
plt.grid(True,alpha=0.5)
plt.legend(loc='upper left')
plt.ylabel('Mobility in Steps')

#plt.xlim(dates[0],dates[-1])


#############################################################################
# Linear Regression on each of the individual
#############################################################################
user_list=[]
for each_PID in sensor_grouped_list:
    PID_name = each_PID[0]
    user_list.append(PID_name)


from sklearn.linear_model import LinearRegression
# get the logistic regression for every user
# Y = a0 + a1*X, and we are trying to minimize residual r
# Z = b0 + b1*T, and we are trying to minimize residual r

r_sq_list1=[];intercept_list1=[];coef_list1=[]
r_sq_list2=[];intercept_list2=[];coef_list2=[]
for i in range(len(temp_sensor_derived_steps)):
    each_drived_step = temp_sensor_derived_steps[i]
    each_mobility = temp_mobility[i]
    each_transition = temp_transition[i]
    
    x = np.array(each_mobility).reshape((-1, 1))
    y = np.array(each_drived_step)
    t = np.array(each_mobility).reshape((-1, 1))
    z = np.array(each_transition)

    model1 = LinearRegression()
    model1.fit(x, y)
    r_sq1 = model1.score(x, y)
    model2 = LinearRegression()
    model2.fit(t, z)
    r_sq2 = model2.score(t, z)

    r_sq_list1.append(r_sq1)
    intercept_list1.append(model1.intercept_)
    coef_list1.append(model1.coef_)
    r_sq_list2.append(r_sq2)
    intercept_list2.append(model2.intercept_)
    coef_list2.append(model2.coef_)

least_square_result = pd.DataFrame({'User':user_list,'a0':intercept_list1,
                               'a1':coef_list1,'R^2 1':r_sq_list1,
                               'b0':intercept_list2,
                               'b1':coef_list2,'R^2 2':r_sq_list2})
    
least_square_result.to_csv(r'D:\DACS\Individual Participant-linear regression.csv')    
# count number of R^2 
count_small_R_1 = sum(map(lambda x : x<0.5, r_sq_list1))
count_large_R_2 = sum(map(lambda x : x>0.8, r_sq_list2))    

    
#-----------------------------------------------------------------------------  
# Get spearman correlation
rho_list1=[];rho_list2=[];rho_list3=[];p_val1=[];p_val2=[];p_val3=[]
for i in range(len(temp_sensor_derived_steps)):
    each_sensor_derived_steps = temp_sensor_derived_steps[i]
    each_mobility = temp_mobility[i]
    each_transition = temp_transition[i]

    each_user_rho1,each_user_p_val1 = stats.spearmanr(each_transition,each_mobility)
    #each_user_rho2,each_user_p_val2 = stats.spearmanr(each_sensor_derived_steps,each_transition)
    each_user_rho3,each_user_p_val3 = stats.spearmanr(each_sensor_derived_steps,each_mobility)
    
    rho_list1.append(each_user_rho1);p_val1.append(each_user_p_val1)
    #rho_list2.append(each_user_rho2);p_val2.append(each_user_p_val2)
    rho_list3.append(each_user_rho3);p_val3.append(each_user_p_val3)

spearman_result = pd.DataFrame({'User':user_list,'Rho1 transition and fixed-distance':rho_list1,'p-val 1':p_val1,
                                'Rho2 fixed-speed and fixed-distance':rho_list3,'p-val 2':p_val3})

spearman_result.to_csv(r'D:\DACS\Individual Participant-correlation coefficient.csv')     
# count rho2 and rho3 moderate corr (0.6<rho<0.8)
count_moderate3 = sum(map(lambda x : 0.6<x<0.8, rho_list3))
count_weak3 = sum(map(lambda x : x<0.6, rho_list3))
   
#############################################################################
# Correlation Comparision
#############################################################################
# For all users
flat_mobility = [item for sublist in temp_mobility for item in sublist]
flat_sensor_derived_steps = [item for sublist in temp_sensor_derived_steps for item in sublist]
flat_transition = [item for sublist in temp_transition for item in sublist]

each_user_rho1,each_user_p_val1 = stats.spearmanr(flat_sensor_derived_steps,flat_mobility)
print('spearmanr flat_sensor_derived_steps VS flat_mobility rho:',each_user_rho1)
print('spearmanr flat_sensor_derived_steps VS flat_mobility p-val',each_user_p_val1)

each_user_rho2,each_user_p_val2 = stats.spearmanr(flat_sensor_derived_steps,flat_transition)
print('spearmanr flat_sensor_derived_steps VS flat_transition rho:',each_user_rho2)
print('spearmanr flat_sensor_derived_steps VS flat_transition p-val',each_user_p_val2)

each_user_rho3,each_user_p_val3 = stats.spearmanr(flat_transition,flat_mobility)
print('spearmanr flat_transition VS flat_mobility rho:',each_user_rho3)
print('spearmanr flat_transition VS flat_mobility p-val',each_user_p_val3)
