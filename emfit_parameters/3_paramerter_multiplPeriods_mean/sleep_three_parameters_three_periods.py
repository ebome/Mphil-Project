import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import datetime as dt
import mysql.connector
from datetime import timedelta

###################################################
# Sleep summary data: Fetch from local database
###################################################
mydb = mysql.connector.connect(user ='root', password ='123456')
mycursor = mydb.cursor()
# approximately 3 min to finish loading 5 million lines
dacs_all_sleep = pd.read_sql("SELECT * FROM dacs_all_data.sleep_data_up_to_nov;", con=mydb)
mycursor.close()
mydb.close()

dacs_all_sleep['start_date']=pd.to_datetime(dacs_all_sleep['start_date'])
dacs_all_sleep['end_date']=pd.to_datetime(dacs_all_sleep['end_date'])
# add 'sleep efficiency' column
dacs_all_sleep['sleep_efficiency']=dacs_all_sleep['sleep_duration']/dacs_all_sleep['bed_duration']
# clean some useless columns
dacs_all_sleep = dacs_all_sleep.drop(['sleep_data_id','room_id','sensor_type','sensor_udn',
                                      'sensor_name','sensor_id','device_id','session_id'], axis=1)

# change 'rebaseline' in PID for 3-175, 3-183
dacs_all_sleep['PID'] = [x.replace(' Rebaseline','') for x in dacs_all_sleep['PID']]


# count the number of PID and see how many days of data each PID has
output = dacs_all_sleep.groupby('PID').size()
# Remove the PID with output days less than 40 days from dacs_all_sleep
for PID, days in output.items():
    if days < 21:
        dacs_all_sleep = dacs_all_sleep[(dacs_all_sleep.PID !=PID)]
each_user_sleep_days = dacs_all_sleep.groupby('PID').size()


##################################################
# Keep the "solitary residents", Regardless withdraw or not
###################################################
solitary_list_intervention_group = pd.read_excel(r'D:\Sensor_Data_Processing\DACS_users_live_alone.xlsx')

# make sure they live alone
solitary_list_intervention_group = solitary_list_intervention_group[solitary_list_intervention_group['living_arrangments']==1]
# make sure they have sensor installed in home
solitary_list_intervention_group =  solitary_list_intervention_group[solitary_list_intervention_group['randomised_group']==1]
solitary_users = solitary_list_intervention_group['record_id'].tolist()
# Remove non-solitary users from sensor and mobility data 
solitary_dacs_sleep = dacs_all_sleep[dacs_all_sleep['PID'].isin(solitary_users)]
# Check if PID in sleep is same as motion
sleep_pid = solitary_dacs_sleep['PID'].unique().tolist()

###################################################
# Group sleep sensor: 44 solitary users
###################################################
# NOTE: use solitary_dacs_sleep or non_solitary_dacs_sleep in line 65 changes all result below
sleep_grouped_list = list(solitary_dacs_sleep.groupby(['PID']))
reformed_sleep_list_temp=[]
for each_PID in sleep_grouped_list:
    reformed_sleep_list_temp.append(each_PID[1])
  

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
        if start_dates[i]==end_dates[i] and sleep_duration[i] < 3:
            index = index_list[i]
            removed = each_user_sleep.loc[index]
            removed_sleep_days = removed_sleep_days.append(removed)
    
    each_user_sleep = each_user_sleep[~each_user_sleep.isin(removed_sleep_days)].dropna(how='all')    
    reformed_sleep_list_no_nap.append(each_user_sleep)     

# after removing the 'so-called' nap that less than 3 hours, we can change the dates
reformed_sleep_list_no_repetitive=[]    
for each_user_sleep in reformed_sleep_list_no_nap:
    start_dates = [each_day.date() for each_day in each_user_sleep['start_date'].tolist()] 
    for i in range(len(start_dates)-2):
        if start_dates[i] == start_dates[i+1] and\
        (start_dates[i] - timedelta(days=1)) != start_dates[i-1]:
            start_dates[i] = start_dates[i] - timedelta(days=1)
        if start_dates[i] == start_dates[i+1] and\
        (start_dates[i+1] + timedelta(days=1)) != start_dates[i+2]:
            start_dates[i+1] = start_dates[i+2] - timedelta(days=1)
    
    each_user_sleep['date_for_this_sleep'] = start_dates
    reformed_sleep_list_no_repetitive.append(each_user_sleep)

# notice that in 'date_for_this_sleep' there are still repetitives (eg. in 3-1 date: 19-10-30, 19-11-06)
# so remove these suplicates days requires 3-by-3 window of checking
reformed_sleep_no_repetitive=[]    
for each_user_sleep in reformed_sleep_list_no_repetitive:
    start_dates = each_user_sleep['date_for_this_sleep'].tolist()
    for i in range(2,len(start_dates)-3):
        
        if start_dates[i] == start_dates[i+1] and\
        (start_dates[i-1] - timedelta(days=1)) != start_dates[i-1]:
            start_dates[i-1] = start_dates[i-2] + timedelta(days=1)
            start_dates[i] = start_dates[i-1] + timedelta(days=1)
        
        if start_dates[i] == start_dates[i+1] and\
        (start_dates[i+2] + timedelta(days=1)) != start_dates[i+3]:
            start_dates[i+2] = start_dates[i+3] - timedelta(days=1)
            start_dates[i+1] = start_dates[i+2] - timedelta(days=1)
    
    each_user_sleep['new_date_for_this_sleep'] = start_dates
    reformed_sleep_no_repetitive.append(each_user_sleep)


# In 'new_date_for_this_sleep' there are still repetitives 
# so remove these suplicates days by keeping the longest sleep duration
reformed_sleep_final=[]    
for each_user_sleep in reformed_sleep_no_repetitive:
    drop_dup_df = each_user_sleep.loc[(each_user_sleep['new_date_for_this_sleep'].shift() != each_user_sleep['new_date_for_this_sleep'])]
    reformed_sleep_final.append(drop_dup_df)


# for the Nan values in sleep data, we choose to remove them 
aaa=[]
for each_user_sleep in reformed_sleep_final:
    each_user_sleep = each_user_sleep.dropna(subset=['sleep_duration'])
    aaa.append(each_user_sleep) 
    
    
#----------------------
# to CSV files
bbb=[]
for each_user_sleep in reformed_sleep_final:
    each_user_sleep = each_user_sleep.dropna(subset=['sleep_duration'])
    each_user_sleep = each_user_sleep.drop(columns=['session_id', 'date_for_this_sleep','new_date_for_this_sleep'])
    bbb.append(each_user_sleep)

path = r'D:/44_single_sleeper'

users_list=[]
for each in bbb:
    users_list.append(each['PID'].tolist()[0])

csv_file_list = []
for each_user_str in users_list:
    each_csv_name = path+'/'+each_user_str+'.csv'
    csv_file_list.append(each_csv_name)

for i in range(len(csv_file_list)):
    bbb[i].to_csv(csv_file_list[i],index=False)
    
    

#############################################################################
# Sleep parameter selection
#############################################################################
# Ground truth mobility, ignore those who have data less than 29 days
def get_sleep_parameter_with_date(reformed_sleep_list,sleep_para,coverting_dividor):
    temp_sleep_duration=[]
    for each_user_sleep in reformed_sleep_list:
        cc = each_user_sleep['PID'].tolist()
        bb = each_user_sleep['new_date_for_this_sleep'].tolist()
        aa = each_user_sleep[sleep_para].tolist()
        aa = [x/coverting_dividor for x in aa] # convert second to hours
        user_sleep = pd.DataFrame({'PID':cc,'date':bb,sleep_para:aa})
        temp_sleep_duration.append(user_sleep) 
    return temp_sleep_duration

temp_sleep_duration = get_sleep_parameter_with_date(aaa,'sleep_duration',3600)
temp_sleep_onset_duration = get_sleep_parameter_with_date(aaa,'sleep_onset_duration',60)
temp_sleep_efficiency = get_sleep_parameter_with_date(aaa,'sleep_efficiency',1)
temp_waso = get_sleep_parameter_with_date(aaa,'awake_duration',60)
temp_sleep_bedexit = get_sleep_parameter_with_date(aaa,'bed_exit_duration',60)


#############################################################################
# Sleep parameter by different periods
#############################################################################
period1_start = dt.datetime.strptime('2019-11-01 00:00:00', '%Y-%m-%d %H:%M:%S').date()
period1_end = dt.datetime.strptime('2020-02-29 23:59:59', '%Y-%m-%d %H:%M:%S').date()
period2_start = dt.datetime.strptime('2020-03-01 00:00:00', '%Y-%m-%d %H:%M:%S').date()
period2_end = dt.datetime.strptime('2020-05-31 23:59:59', '%Y-%m-%d %H:%M:%S').date()
period3_start = dt.datetime.strptime('2020-06-01 00:00:00', '%Y-%m-%d %H:%M:%S').date()
period3_end = dt.datetime.strptime('2020-11-29 23:59:59', '%Y-%m-%d %H:%M:%S').date()


def one_sleep_para_mean_median(period_start,period_end,temp_sleep_duration, sleep_para):
    all_users_this_period=pd.DataFrame({})
    for test in temp_sleep_duration:
        test = test.loc[(test['date'] > period_start) & (test['date'] <= period_end)]
        if len(test)>20:
            mean_no_std = np.around( np.mean(test[sleep_para]) , decimals=4)
            std = np.around( np.std(test[sleep_para]) , decimals=4)
            mean = str(mean_no_std)+'±'+str(std)
            median = np.around( np.median(test[sleep_para]) , decimals=4) 
            minimal = np.around( np.min(test[sleep_para]) , decimals=4)
            maximal = np.around( np.max(test[sleep_para]) , decimals=4)
            CI_95_low = np.around(np.percentile(test[sleep_para],2.5), decimals=4) 
            CI_95_high = np.around(np.percentile(test[sleep_para],97.5), decimals=4) 
        elif len(test)<=20 and len(test) > 0:
            mean_no_std = np.around( np.mean(test[sleep_para]) , decimals=4)
            std = np.around( np.std(test[sleep_para]) , decimals=4)
            mean = str(mean_no_std)+'±'+str(std)+' *'
            median = str( np.around( np.median(test[sleep_para]) , decimals=4)  )+' *'
            minimal = str( np.around( np.min(test[sleep_para]) , decimals=4)  )+' *'
            maximal = str( np.around( np.max(test[sleep_para]) , decimals=4)  )+' *'
            CI_95_low = str( np.around( np.percentile(test[sleep_para],2.5), decimals=4)  )+' *'
            CI_95_high = str( np.around(np.percentile(test[sleep_para],97.5) , decimals=4) )+' *'
        elif len(test)== 0:
            mean = np.nan
            median = np.nan
            minimal = np.nan
            maximal = np.nan
            CI_95_low = np.nan
            CI_95_high = np.nan            
        this_user_this_period = pd.DataFrame({'mean':mean,'median':median,'min':minimal,'max':maximal,
                                              '95%_CI_lower':CI_95_low,'95%_CI_upper':CI_95_high}, index=[0])
        all_users_this_period = pd.concat([all_users_this_period,this_user_this_period], ignore_index=True)
    return all_users_this_period

first_period = one_sleep_para_mean_median(period1_start,period1_end,temp_sleep_duration, 'sleep_duration')
second_period = one_sleep_para_mean_median(period2_start,period2_end,temp_sleep_duration, 'sleep_duration')
third_period = one_sleep_para_mean_median(period3_start,period3_end,temp_sleep_duration, 'sleep_duration')

def one_sleep_para_all_users(period1_start,period2_start,period3_start,period1_end,period2_end,period3_end,temp_sleep_duration, sleep_para):
    first_period = one_sleep_para_mean_median(period1_start,period1_end,temp_sleep_duration, sleep_para)
    second_period = one_sleep_para_mean_median(period2_start,period2_end,temp_sleep_duration, sleep_para)
    third_period = one_sleep_para_mean_median(period3_start,period3_end,temp_sleep_duration, sleep_para)
    ID_list=[]
    for each in temp_sleep_duration:
        ID_list.append(each['PID'].tolist()[0])
    # concate the dataframe
    df_concat = pd.concat([first_period,second_period,third_period], axis=1)
    df_concat.index = ID_list
    return df_concat

df_concat_TST = one_sleep_para_all_users(period1_start,period2_start,period3_start,period1_end,period2_end,period3_end,temp_sleep_duration, 'sleep_duration')
df_concat_WASO = one_sleep_para_all_users(period1_start,period2_start,period3_start,period1_end,period2_end,period3_end,temp_waso, 'awake_duration')
df_concat_SE = one_sleep_para_all_users(period1_start,period2_start,period3_start,period1_end,period2_end,period3_end,temp_sleep_efficiency, 'sleep_efficiency')

############################################################################
# Visualization of sleep
#############################################################################
# from users get their ages
user_gender = pd.read_csv(r'D:\Sensor_Data_Processing\gender_label\survey_labels.csv')
user_list_sleep=[]
for i in range(len(reformed_sleep_no_repetitive)):
    user_list_sleep.append(reformed_sleep_no_repetitive[i]['PID'].tolist()[0])
user_gender = user_gender[user_gender['record_id'].isin(user_list_sleep)]
time_list = user_gender["date_of_birth"].values.tolist()
datetime_list = [dt.datetime.strptime(x, '%Y-%m-%d') for x in time_list]
age_list = [(dt.datetime.today() - birth_date) // dt.timedelta(days=365.2425) for birth_date in datetime_list]
user_gender['age'] = age_list 
user_gender = user_gender.sort_values(by=['record_id']).reset_index()
user_gender['home_care_package_level'].loc[(user_gender['home_care_package_level']==6)] = 1
# add mental score to user_gender
user_mental_score = pd.read_csv(r'D:\Sensor_Data_Processing\gender_label\eq5d_and_mood_and_mental_scores.csv')
user_mental_score = user_mental_score[user_mental_score['PID'].isin(user_gender['record_id'].tolist())]
user_gender = user_gender.merge(user_mental_score,left_on='record_id',right_on='PID', 
     how = 'inner')[['record_id', 'living_area', 'home_care_package_level', 'gender',
                     'age','ATSM']]
user_gender['ATSM'] = [int(x) for x in user_gender['ATSM'].tolist()]

#############################################################################
# map sleep median and mean with user_gender
#############################################################################
#df = df_concat_TST.merge(df_concat_WASO, how="inner", left_index=True, right_index=True)
#df = df.merge(df_concat_SE, how="inner", left_index=True, right_index=True)
# add mental score
df=df_concat_SE

df = df[df.index.isin(user_gender['record_id'].tolist())]

# add ATSM score
user_gender_atsm_score = user_gender[['record_id','ATSM','age','gender']]
joined_table = df.merge(user_gender_atsm_score,left_on=df.index,right_on='record_id', 
     how = 'inner')
joined_table = joined_table.rename({'ATSM': 'mental_score'}, axis=1)  

# write table to excel
joined_table.to_excel(r'D:\solitray_44_sleepers\se.xlsx',index=False)


#############################################################################
# Plotting
#############################################################################
# split joined_table 
# STEP1: remove all nan rows
joined_table_no_three_periods = joined_table.dropna(thresh=12)
# STEP2: divide by age
joined_table_70s = joined_table_no_three_periods[joined_table_no_three_periods['age']<80]
joined_table_80s = joined_table_no_three_periods[(joined_table_no_three_periods['age']>79) & (joined_table_no_three_periods['age']<90)]
joined_table_90s = joined_table_no_three_periods[joined_table_no_three_periods['age']>89]

joined_table_70s_half_A = joined_table_70s[joined_table_70s['age']<75]
joined_table_70s_half_B = joined_table_70s[joined_table_70s['age']>74]
joined_table_80s_half_A = joined_table_80s[joined_table_80s['age']<86]
joined_table_80s_half_B = joined_table_80s[joined_table_80s['age']>85]

# PLOT
def plot_TST_for_one_age_group(joined_table_x0s_df,title_str):
    plt.figure(figsize=(8,8))
    plt.title(title_str)
    for each_user_row in joined_table_x0s_df.iterrows():
        label = str(each_user_row[1].iloc[-4])+', ATSM is '+str(each_user_row[1].iloc[-3])+\
        ', gender is '+str(each_user_row[1].iloc[-1])
        plt.plot([0,1,2],each_user_row[1].iloc[[0,2,4]],label = label,marker = 'o')
        plt.legend(bbox_to_anchor=(1, 1.05))
    plt.tick_params(axis='x',which='both',bottom=False, top=False, labelbottom=False) 

plot_TST_for_one_age_group(joined_table_70s_half_A,'Sleepers in their 70s')
plot_TST_for_one_age_group(joined_table_70s_half_B,'Sleepers in their 70s')
plot_TST_for_one_age_group(joined_table_80s_half_A,'Sleepers in their 80s')
plot_TST_for_one_age_group(joined_table_80s_half_B,'Sleepers in their 80s')
plot_TST_for_one_age_group(joined_table_90s,'Sleepers in their 90s')

def plot_WASO_for_one_age_group(joined_table_x0s_df,title_str):
    plt.figure(figsize=(8,8))
    plt.title(title_str)
    for each_user_row in joined_table_x0s_df.iterrows():
        label = str(each_user_row[1].iloc[-4])+', ATSM is '+str(each_user_row[1].iloc[-3])+\
        ', gender is '+str(each_user_row[1].iloc[-1])
        plt.plot([0,1,2],each_user_row[1].iloc[[6,8,10]],label = label,marker = 'o')
        plt.legend(bbox_to_anchor=(1, 1.05))
    plt.tick_params(axis='x',which='both',bottom=False, top=False, labelbottom=False) 

plot_WASO_for_one_age_group(joined_table_70s_half_A,'Sleepers in their 70s')
plot_WASO_for_one_age_group(joined_table_70s_half_B,'Sleepers in their 70s')
plot_WASO_for_one_age_group(joined_table_80s_half_A,'Sleepers in their 80s')
plot_WASO_for_one_age_group(joined_table_80s_half_B,'Sleepers in their 80s')
plot_WASO_for_one_age_group(joined_table_90s,'Sleepers in their 90s')


def plot_SE_for_one_age_group(joined_table_x0s_df,title_str):
    plt.figure(figsize=(8,8))
    plt.title(title_str)
    for each_user_row in joined_table_x0s_df.iterrows():
        label = str(each_user_row[1].iloc[-4])+', ATSM is '+str(each_user_row[1].iloc[-3])+\
        ', gender is '+str(each_user_row[1].iloc[-1])
        plt.plot([0,1,2],each_user_row[1].iloc[[12,14,16]],label = label,marker = 'o')
        plt.legend(bbox_to_anchor=(1, 1.05))
    plt.tick_params(axis='x',which='both',bottom=False, top=False, labelbottom=False) 

plot_SE_for_one_age_group(joined_table_70s_half_A,'Sleepers in their 70s')
plot_SE_for_one_age_group(joined_table_70s_half_B,'Sleepers in their 70s')
plot_SE_for_one_age_group(joined_table_80s_half_A,'Sleepers in their 80s')
plot_SE_for_one_age_group(joined_table_80s_half_B,'Sleepers in their 80s')
plot_SE_for_one_age_group(joined_table_90s,'Sleepers in their 90s')

