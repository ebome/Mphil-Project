import numpy as np
from scipy import stats
import pandas as pd
import matplotlib.pyplot as plt
import datetime as dt
import mysql.connector


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

#############################################################################
# Remove repetitive dates of sleep recording 
#############################################################################
def get_masked_dataframe(start_date, end_date, df):
    mask = (df['start_date']>= start_date) & (df['start_date'] < end_date)
    new_df = df.loc[mask]
    return new_df
 
reformed_sleep_list_with_no_repetitive = [];
for each_user_sleep_df in reformed_sleep_list_temp:
    cleaned_this_user = pd.DataFrame({}) 
    sleep_date_list = each_user_sleep_df['start_date'].tolist()
    slice_windows = pd.date_range(sleep_date_list[0], periods=500, freq='1D').tolist()
    for i in range(len(slice_windows)-1):
        start_date = slice_windows[i]
        end_date = slice_windows[i+1]
        only_user_one_day_df = get_masked_dataframe(start_date, end_date, each_user_sleep_df)
        if only_user_one_day_df.empty == False:
            # keep the longest sleep duration in record
            only_user_one_day_df = only_user_one_day_df.fillna(method='ffill')
            only_user_one_day_cleaned = only_user_one_day_df.sort_values('sleep_duration').drop_duplicates(['PID'], keep='last')
            cleaned_this_user = pd.concat([cleaned_this_user,only_user_one_day_cleaned])
    reformed_sleep_list_with_no_repetitive.append(cleaned_this_user)

# There will be reocrds in same day indicate daytime nap, 
# so if start and end day are same, and remove
reformed_sleep_list_no_nap = []
for each_user_sleep in reformed_sleep_list_with_no_repetitive:
    removed_sleep_days = pd.DataFrame({})
    start_dates = [each_day.date() for each_day in each_user_sleep['start_date'].tolist()] 
    end_dates = [each_day.date() for each_day in each_user_sleep['end_date'].tolist()] 
    start_hours = [each_day.time() for each_day in each_user_sleep['start_date'].tolist()] 
    sleep_duration = [each_duration/3600 for each_duration in each_user_sleep['sleep_duration'].tolist()]
    nap_time_ends = dt.time(17,0,0);    nap_time_starts = dt.time(7,0,0)

    index_list = each_user_sleep.index.tolist()
    
    for i in range(len(start_dates)):
        if start_dates[i]==end_dates[i] and sleep_duration[i] < 3 :
            index = index_list[i]
            removed = each_user_sleep.loc[index]
            removed_sleep_days = removed_sleep_days.append(removed)
    
    each_user_sleep = each_user_sleep[~each_user_sleep.isin(removed_sleep_days)].dropna()    
    reformed_sleep_list_no_nap.append(each_user_sleep)     





reformed_sleep_list_no_repetitive=[]    
for each_user_sleep in reformed_sleep_list_no_nap:
    start_dates = [each_day.date() for each_day in each_user_sleep['start_date'].tolist()] 
    for i in range(len(start_dates)-1):
        if start_dates[i] == start_dates[i+1] and\
        (start_dates[i] - timedelta(days=1)) != start_dates[i-1]:
            start_dates[i] = start_dates[i] - timedelta(days=1)
        if start_dates[i] == start_dates[i+1] and\
        (start_dates[i+1] + timedelta(days=1)) != start_dates[i+2]:
            start_dates[i+1] = start_dates[i+2] - timedelta(days=1)
    
    each_user_sleep['date_for_this_sleep'] = start_dates
    reformed_sleep_list_no_repetitive.append(each_user_sleep)   
    
    
###################################################
# Match sleep and motion sensor on the dates
###################################################
# Same, for each unit in reformed_sleep_list_with_no_repetitive and users_transition,remove the 
# dates that in reformed_sleep_list_with_no_repetitive but not in users_transition
reformed_sleep_list = [];reformed_sensor_list = []
for i in range(len(users_transition)):
    # add the day as index of mobility
    each_PID_mobility = users_transition[i]
    each_PID_mobility['start_day_trucated'] = [each_day.date() for each_day in each_PID_mobility['date'].tolist()] 
    # add the day as index of sleep, change the consecutive cells with reptitive day
    each_PID_sleep = reformed_sleep_list_no_nap[i]
    each_PID_sleep['start_day_trucated'] = [each_day.date() for each_day in each_PID_sleep['start_date'].tolist()] 

    # match the days
    each_PID_mobility_reformed = each_PID_mobility[each_PID_mobility['start_day_trucated'].isin(each_PID_sleep['start_day_trucated'])]
    each_PID_sleep_reformed = each_PID_sleep[each_PID_sleep['start_day_trucated'].isin(each_PID_mobility_reformed['start_day_trucated'])]
    
    reformed_sensor_list.append(each_PID_mobility_reformed)
    reformed_sleep_list.append(each_PID_sleep_reformed)

#############################################################################
# Sleep parameter selection
#############################################################################
# Ground truth mobility, ignore those who have data less than 29 days
def get_temp_sleep_parameter(reformed_sleep_list_with_no_repetitive,sleep_para,coverting_dividor):
    temp_sleep_duration=[]
    for each_user_mobility in reformed_sleep_list_with_no_repetitive:
        aa = each_user_mobility[sleep_para].tolist()
        aa = [x/coverting_dividor for x in aa] # convert second to hours
        temp_sleep_duration.append(aa) 
    return temp_sleep_duration

temp_sleep_duration= get_temp_sleep_parameter(reformed_sleep_list,'sleep_duration',3600)
temp_sleep_onset_duration= get_temp_sleep_parameter(reformed_sleep_list,'sleep_onset_duration',60)
temp_sleep_efficiency= get_temp_sleep_parameter(reformed_sleep_list,'sleep_efficiency',1)
temp_waso= get_temp_sleep_parameter(reformed_sleep_list,'awake_duration',60)
 
    
flat_sleep_duration = [item for sublist in temp_sleep_duration for item in sublist]
print('flat_sleep_duration = ', len(flat_sleep_duration))
    
avg_of_sleep_days = np.nanmean(np.asarray(flat_sleep_duration))



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
# Anova and t test
#############################################################################
# from users get their ages
user_gender = pd.read_csv(r'D:\Sensor_Data_Processing\gender_label\survey_labels.csv')
user_gender = user_gender[user_gender['record_id'].isin(user_list_sleep)]
time_list = user_gender["date_of_birth"].values.tolist()
datetime_list = [dt.datetime.strptime(x, '%Y-%m-%d') for x in time_list]
age_list = [(dt.datetime.today() - birth_date) // dt.timedelta(days=365.2425) for birth_date in datetime_list]
user_gender['age'] = age_list 
user_gender = user_gender.sort_values(by=['record_id']).reset_index()
# add mental score to user_gender
user_mental_score = pd.read_csv(r'D:\Sensor_Data_Processing\gender_label\eq5d_and_mood_and_mental_scores.csv')
user_mental_score = user_mental_score[user_mental_score['PID'].isin(user_gender['record_id'].tolist())]
user_gender['mental_score'] = [int(x) for x in user_mental_score['ATSM'].tolist()]

# removed users that has mental score < 5
user_gender = user_gender[user_gender['mental_score']>=7]


# For paper
user_paper= pd.read_csv(r'D:\Sensor_Data_Processing\dasc individual correlation coefficients data up to 2020 May.csv')
user_gender_paper = user_gender[user_gender['record_id'].isin(user_paper['User'])]
user_gender_paper = user_gender_paper.merge(user_paper, left_on='record_id', right_on='User', how = 'inner')
time_list = user_gender_paper["date_of_birth"].values.tolist()
datetime_list = [dt.datetime.strptime(x, '%Y-%m-%d') for x in time_list]
age_list = [(dt.datetime.today() - birth_date) // dt.timedelta(days=365.2425) for birth_date in datetime_list]
user_gender_paper['age'] = age_list 
user_gender_paper = user_gender_paper.sort_values(by=['record_id']).reset_index()
user_mental_score = pd.read_csv(r'D:\Sensor_Data_Processing\gender_label\eq5d_and_mood_and_mental_scores.csv')
user_mental_score_paper = user_mental_score[user_mental_score['PID'].isin(user_gender_paper['record_id'].tolist())]
user_gender_paper['mental_score'] = [int(x) for x in user_mental_score_paper['ATSM'].tolist()]

user_female_paper = user_gender_paper[user_gender_paper['home_care_package_level']==6]
user_female_paper['home_care_package_level'].describe()

# mean for male and female age
selected_df_male = user_gender[user_gender['gender']==1]
selected_df_female = user_gender[user_gender['gender']==2]
selected_df_70s = user_gender.loc[(user_gender['age']>=70) & (user_gender['age']<80)]
selected_df_80s = user_gender.loc[(user_gender['age']>=80) & (user_gender['age']<90)]
selected_df_90s = user_gender.loc[(user_gender['age']>=90) & (user_gender['age']<100)]

selected_df_male['age'].describe()

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

mobility_data_male = merge_data_mobility(selected_df_male,reformed_sensor_list)
sleep_tst_male = merge_data_sleep_para(selected_df_male,temp_sleep_duration)
sleep_sol_male = merge_data_sleep_para(selected_df_male,temp_sleep_onset_duration)
sleep_effi_male = merge_data_sleep_para(selected_df_male,temp_sleep_efficiency)
sleep_waso_male = merge_data_sleep_para(selected_df_male,temp_waso)
mobility_data_female = merge_data_mobility(selected_df_female,reformed_sensor_list)
sleep_tst_female = merge_data_sleep_para(selected_df_female,temp_sleep_duration)
sleep_sol_female = merge_data_sleep_para(selected_df_female,temp_sleep_onset_duration)
sleep_effi_female = merge_data_sleep_para(selected_df_female,temp_sleep_efficiency)
sleep_waso_female = merge_data_sleep_para(selected_df_female,temp_waso)

mobility_data_70s = merge_data_mobility(selected_df_70s,reformed_sensor_list)
sleep_tst_70s = merge_data_sleep_para(selected_df_70s,temp_sleep_duration)
sleep_sol_70s = merge_data_sleep_para(selected_df_70s,temp_sleep_onset_duration)
sleep_effi_70s = merge_data_sleep_para(selected_df_70s,temp_sleep_efficiency)
sleep_waso_70s = merge_data_sleep_para(selected_df_70s,temp_waso)
                 
mobility_data_80s = merge_data_mobility(selected_df_80s,reformed_sensor_list)
sleep_tst_80s = merge_data_sleep_para(selected_df_80s,temp_sleep_duration)
sleep_sol_80s = merge_data_sleep_para(selected_df_80s,temp_sleep_onset_duration)
sleep_effi_80s = merge_data_sleep_para(selected_df_80s,temp_sleep_efficiency)
sleep_waso_80s = merge_data_sleep_para(selected_df_80s,temp_waso)

mobility_data_90s = merge_data_mobility(selected_df_90s,reformed_sensor_list)
sleep_tst_90s = merge_data_sleep_para(selected_df_90s,temp_sleep_duration)
sleep_sol_90s = merge_data_sleep_para(selected_df_90s,temp_sleep_onset_duration)
sleep_effi_90s = merge_data_sleep_para(selected_df_90s,temp_sleep_efficiency)
sleep_waso_90s = merge_data_sleep_para(selected_df_90s,temp_waso)

#############################################################################
# get hist plots and independent t test
#############################################################################
# male and female distributions
kwargs = dict(alpha=0.5, bins=100)
plt.hist([item for sublist in sleep_effi_male for item in sublist],**kwargs, color='y', label='male SE')
plt.hist([item for sublist in sleep_effi_female for item in sublist],**kwargs, color='b', label='female SE')
plt.legend()

def two_group_ttest(group_a, group_b):
    a = [item for sublist in group_a for item in sublist]
    b = [item for sublist in group_b for item in sublist]
    ttest,pval = stats.ttest_ind(a,b)
    return ttest,pval
    
ttest,pval = two_group_ttest(sleep_effi_male, sleep_effi_female)
print(ttest,pval)

def get_mean_and_std(group_a):
    a = np.asarray([item for sublist in group_a for item in sublist])
    avg = a.mean()
    std = a.std()
    return avg,std

avg,std = get_mean_and_std(mobility_data_female)
avg,std = get_mean_and_std(sleep_tst_female)
avg,std = get_mean_and_std(sleep_sol_female)
avg,std = get_mean_and_std(sleep_waso_female)
avg,std = get_mean_and_std(sleep_effi_female)
print(avg,std)

avg0,std0 = get_mean_and_std(mobility_data_70s)
print(avg0,std0)
avg1,std1 = get_mean_and_std(sleep_tst_70s)
print(avg1,std1)
avg2,std2 = get_mean_and_std(sleep_sol_70s)
print(avg2,std2)
avg3,std3 = get_mean_and_std(sleep_waso_70s)
print(avg3,std3)
avg4,std4 = get_mean_and_std(sleep_effi_70s)
print(avg4,std4)

#############################################################################
# get hist plots and one way ANOVA
#############################################################################
plt.hist([item for sublist in sleep_effi_70s for item in sublist],**kwargs, color='r', label='70s')
plt.hist([item for sublist in sleep_effi_80s for item in sublist],**kwargs, color='b', label='80s')
plt.hist([item for sublist in sleep_effi_90s for item in sublist],**kwargs, color='g', label='90s')
plt.legend()
plt.title('SE in age groups')

import statsmodels.api as sm
from statsmodels.formula.api import ols
from statsmodels.stats.anova import anova_lm

def get_df_for_three_group(group_a,group_b,group_c):
    a = [item for sublist in group_a for item in sublist]
    b = [item for sublist in group_b for item in sublist]
    c = [item for sublist in group_c for item in sublist]
    data_a = pd.DataFrame({'age_group':'70s','para_value':a})
    data_b = pd.DataFrame({'age_group':'80s','para_value':b})
    data_c = pd.DataFrame({'age_group':'90s','para_value':c})
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

# another way to do one way ANOVA
f, p = stats.f_oneway(data[data['age_group'] == '70s'].para_value,
                      data[data['age_group'] == '80s'].para_value,
                      data[data['age_group'] == '90s'].para_value)
 
print ('One-way ANOVA')
print ('=============')
 
print ('F value:', f)
print ('P value:', p, '\n')


