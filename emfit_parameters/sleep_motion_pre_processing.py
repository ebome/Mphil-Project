import numpy as np
from scipy import stats
import pandas as pd
import matplotlib.pyplot as plt
import datetime as dt
import mysql.connector
import copy


dacs_all_sleep = pd.read_csv(r"D:\Sensor_Data_Processing\dacs_91_sleep_data.csv")

dacs_all_sleep['start_date']=pd.to_datetime(dacs_all_sleep['start_date'])
dacs_all_sleep['end_date']=pd.to_datetime(dacs_all_sleep['end_date'])
# add 'sleep efficiency' column
dacs_all_sleep['sleep_efficiency']=dacs_all_sleep['sleep_duration']/dacs_all_sleep['bed_duration']
# clean some useless columns
dacs_all_sleep = dacs_all_sleep.drop(['sleep_data_id','end_time'], axis=1)

# count the number of PID and see how many days of data each PID has
output = dacs_all_sleep.groupby('PID').size()
# Remove the PID with output days less than 40 days from dacs_all_sleep
for PID, days in output.items():
    if days < 40:
        dacs_all_sleep = dacs_all_sleep[(dacs_all_sleep.PID !=PID)]
each_user_sleep_days = dacs_all_sleep.groupby('PID').size()


###################################################
# Motion sensor to transition: Fetch from local database
###################################################
mydb = mysql.connector.connect(user ='root', password ='123456')
mycursor = mydb.cursor()
# approximately 3 min to finish loading 5 million lines
data = pd.read_sql("SELECT * FROM dacs_db_up_to_may.all_dacs_paticipants_motion;", con=mydb)
mycursor.close()
mydb.close()

#------------------------------------------------
# remove the features that are not needed
motion_data = data.drop(columns=['sensor_type', 'sensor_udn'])
# remove "chair" since this is for tranfer in ADL
motion_data = motion_data[~motion_data['sensor_name'].str.contains('Chair')]
#data.to_csv(r'D:\Sensor_Data_Processing\all_user_mobility_up_to_Aug.csv')    

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

###################################################
# Match sleep and motion sensor on the dates
###################################################
# For each unit in reformed_sensor_list_temp and reformed_sleep_list_temp, remove the 
# dates that in reformed_sensor_list but not in reformed_sleep_list_temp
reformed_sensor_list = [];deleted_list_for_all_day=[]
for i in range(len(reformed_sensor_list_temp)):
    each_PID_sensor = reformed_sensor_list_temp[i]
    each_PID_sleep = reformed_sleep_list_temp[i]
    # for the two dataframe, check the time
    sleep_date = each_PID_sleep['start_date'].tolist()
    sensor_date = each_PID_sensor['exact_time'].tolist()
    # mobility has time format YY-MM-DD but sensor also has hours
    sensor_date = [dt.datetime.strptime(date[0:19], '%Y-%m-%d %H:%M:%S') for date in sensor_date]
    
    # time with hours can be trimmed
    sensor_date_truncated = [each_day.date() for each_day in sensor_date] 
    sensor_date_truncated_distinct = list(set(sensor_date_truncated)) # distinct dates
    sleep_date_truncated = [each_start_day.date() for each_start_day in sleep_date] 
    sleep_date_truncated_distinct = list(set(sleep_date_truncated)) 
    
    # find the days that in sleep but not in sensor reading
    date_not_in_sleep = [elem for elem in sensor_date_truncated_distinct if elem not in sleep_date_truncated_distinct]
    # remove repetitive items in date_not_in_mobility
    date_not_in_sleep = list(set(date_not_in_sleep))
    date_notin_sleep = sorted(date_not_in_sleep)
    # transfer the list back to str format
    aaa = [each_date.__str__() for each_date in date_notin_sleep] 

    # after the for loop, each_PID_sleep in sleep will have all dates in each_PID_sensor
    # just add a for loop to remove each date in aaa(date in sensor but not in sleep)
    deleted_list=[]
    for a in aaa:
        # find the sensor readings that should be deleted
        deleted = each_PID_sensor[each_PID_sensor['exact_time'].str.contains(a)]
        deleted_list.append(deleted)
        # remove these units from sensor reading dataframe
        each_PID_sensor = pd.concat([each_PID_sensor, deleted]).drop_duplicates(keep=False)

    reformed_sensor_list.append(each_PID_sensor)
    deleted_list_for_all_day.append(deleted_list)
    
#----------------------------------------------------------------------------- 
# Same, for each unit in reformed_sleep_list_temp and reformed_sensor_list_temp,remove the 
# dates that in reformed_sleep_list_temp but not in reformed_sensor_list_temp
reformed_sleep_list = [];
for i in range(len(reformed_sensor_list)):
    each_PID_sensor = reformed_sensor_list[i]
    each_PID_sleep = reformed_sleep_list_temp[i]
    # for the two dataframe, check the time
    sleep_date = each_PID_sleep['start_date'].tolist()
    sensor_date = each_PID_sensor['exact_time'].tolist()
    #  mobility has time format YY-MM-DD but sensor also has hours
    sensor_date = [dt.datetime.strptime(date[0:19], '%Y-%m-%d %H:%M:%S') for date in sensor_date]
    
    # sensor hours can be removed
    sensor_date_truncated = [each_day.date() for each_day in sensor_date] 
    sensor_date_truncated_distinct = list(set(sensor_date_truncated)) # distinct dates
    sleep_date_truncated = [each_start_day.date() for each_start_day in sleep_date] 
    sleep_date_truncated_distinct = list(set(sleep_date_truncated)) 

    # find the days that in sensor reading but not in mobility
    date_not_in_sensor = [elem for elem in sleep_date_truncated_distinct if elem not in sensor_date_truncated_distinct]
    # remove repetitive items in date_not_in_mobility
    date_notin_sensor = list(set(date_not_in_sensor))
    date_notin_sensor = sorted(date_notin_sensor) # date_notin_sensor is a list with date elements
    
    # remove the mobility dates that should be deleted
    keeped_sleep_PID_unit = each_PID_sleep[~each_PID_sleep['start_date'].isin(date_notin_sensor)]
    reformed_sleep_list.append(keeped_sleep_PID_unit)

#----------------------------------------------------------------------------- 
# Remove repetitive dates of sleep recording 
def get_masked_dataframe(start_date, end_date, df):
    mask = (df['start_date']>= start_date) & (df['start_date'] < end_date)
    new_df = df.loc[mask]
    return new_df
 
reformed_sleep_list_with_no_repetitive = [];

for each_user_sleep_df in reformed_sleep_list:
    cleaned_this_user = pd.DataFrame({}) 
    sleep_date_list = each_user_sleep_df['start_date'].tolist()
    slice_windows = pd.date_range(sleep_date_list[0], periods=300, freq='1D').tolist()

    for i in range(len(slice_windows)-1):
        start_date = slice_windows[i]
        end_date = slice_windows[i+1]
        only_user_one_day_df = get_masked_dataframe(start_date, end_date, each_user_sleep_df)
        # keep the longest sleep duration in record
        only_user_one_day_df = only_user_one_day_df.fillna(method='ffill')
        only_user_one_day_cleaned = only_user_one_day_df.sort_values('sleep_duration').drop_duplicates(['PID'], keep='last')
        cleaned_this_user = pd.concat([cleaned_this_user,only_user_one_day_cleaned])
    
    reformed_sleep_list_with_no_repetitive.append(cleaned_this_user)

#############################################################################
# Use random sleep parameter as the length dates
#############################################################################
# Ground truth mobility, ignore those who have data less than 29 days
def get_temp_sleep_parameter(reformed_sleep_list_with_no_repetitive,sleep_para,coverting_dividor):
    temp_sleep_duration=[]
    for each_user_mobility in reformed_sleep_list_with_no_repetitive:
        aa = each_user_mobility[sleep_para].tolist()
        aa = [x/coverting_dividor for x in aa] # convert second to hours
        temp_sleep_duration.append(aa) 
    return temp_sleep_duration

temp_sleep_duration= get_temp_sleep_parameter(reformed_sleep_list_with_no_repetitive,'sleep_duration',3600)
temp_sleep_onset_duration= get_temp_sleep_parameter(reformed_sleep_list_with_no_repetitive,'sleep_onset_duration',60)
temp_sleep_efficiency= get_temp_sleep_parameter(reformed_sleep_list_with_no_repetitive,'sleep_efficiency',1)
temp_waso= get_temp_sleep_parameter(reformed_sleep_list_with_no_repetitive,'awake_duration',60)
 
    
flat_sleep_duration = [item for sublist in temp_sleep_duration for item in sublist]
print('flat_sleep_duration = ', len(flat_sleep_duration))
    
avg_of_sleep_days = np.nanmean(np.asarray(flat_sleep_duration))
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
for each_PID in reformed_sensor_list:
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
time span for motion: 2018/04/26 - 2020/05/26(included) (maximal 376 days in cleaned_mobility_list). 
Just remove the dates that are not in this range for sensor_list
'''    
# Chopped datetime       
base = dt.datetime.strptime('2019-01-01 00:00:00', '%Y-%m-%d %H:%M:%S')
datelist = pd.date_range(base, periods=600).tolist()
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
users_transition=[]
for each_user in finally_sensor_list:
    transition = get_transition_arrays(each_user,choppedTime)
    users_transition.append(transition) 

flat_transition = [item for sublist in users_transition for item in sublist]
print('flat_transition = ',  len(flat_transition))

#############################################################################
# Visualization of motion/sleep
#############################################################################
user_index=27

plt.figure(figsize=(15,15))
plt.subplot(5,1,1)
plt.plot(users_transition[user_index][0:60],label = 'mobility',color = 'r')
plt.legend()
plt.ylabel("mobility level")

plt.subplot(5,1,2)
plt.plot(temp_sleep_duration[user_index][0:60],label = 'sleep duration')
plt.legend()
plt.ylabel("hours")

plt.subplot(5,1,3)
plt.plot(temp_sleep_efficiency[user_index][0:60],label = 'sleep efficiency')
plt.legend()
plt.ylabel("sleep efficiency")

plt.subplot(5,1,4)
plt.plot(temp_sleep_onset_duration[user_index][0:60],label = 'sleep onset duration')
plt.legend()
plt.ylabel("minutes")

plt.subplot(5,1,5)
plt.plot(temp_waso[user_index][0:60],label = 'wake after sleep onset')
plt.legend()
plt.xlabel("day")
plt.ylabel("minutes")

#############################################################################
# Anova
#############################################################################
# from users get their ages
user_gender = pd.read_csv(r'D:\Sensor_Data_Processing\gender_label\survey_labels.csv')
user_gender = user_gender[user_gender['record_id'].isin(user_list_sleep)]
time_list = user_gender["date_of_birth"].values.tolist()
datetime_list = [dt.datetime.strptime(x, '%Y-%m-%d') for x in time_list]
age_list = [(dt.datetime.today() - birth_date) // dt.timedelta(days=365.2425) for birth_date in datetime_list]
user_gender['age'] = age_list 

# mean for male and female age
selected_df = user_gender[user_gender['gender']==1]
selected_df['age'].describe()

# select users: male(3-1,3-175,3-85,3-96); female(3-48,3-58,3-159,3-27)
import statsmodels.api as sm
from statsmodels.formula.api import ols

transition_data_male = [users_transition[0][0:60],users_transition[42][0:60],users_transition[39][0:60]]
flat_transition_data_male = [item for sublist in transition_data_male for item in sublist]
transition_data_female = [users_transition[0][0:60],users_transition[42][0:60],users_transition[39][0:60]]
flat_transition_data_female = [item for sublist in transition_data_female for item in sublist]
transition_data_male = pd.DataFrame({'label':'male','data':flat_transition_data_male})
transition_data_female = pd.DataFrame({'label':'female','data':flat_transition_data_female})
transition_data = transition_data_male.append(transition_data_female)

linea_model = ols('label ~ data', data = transition_data).fit()
tabel = sm.stats.anova_lm(linea_model)
print(tabel)







#############################################################################
# Anova
#############################################################################













