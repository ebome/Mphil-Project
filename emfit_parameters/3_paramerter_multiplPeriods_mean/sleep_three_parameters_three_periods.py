import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import datetime as dt
import mysql.connector

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
# follow Mahnoosh's suggestion in one user
# split day-by-day, but not from 0am. Instead, split each day from 7pm 
base = dt.datetime.strptime('2019-05-02 19:00:00', '%Y-%m-%d %H:%M:%S')
datelist = pd.date_range(base, periods=580).tolist()
choppedTime=[]
for elt in datelist:
    strg = f'{elt:%Y-%m-%d %H:%M:%S}'
    choppedTime.append(strg)
    
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
    start_timestamp = final_big_df['start_time'].tolist()[0]
    end_timestamp = final_big_df['end_time'].tolist()[0]
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
    TST = TST/3600; WASO=WASO/60
    
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
                         'start_timestamp':start_timestamp,
                         'end_timestamp':end_timestamp,
                         'TST(hour)':TST, 'WASO(min)':WASO,'SOL(min)':SOL,
                         'SE':sleep_efficiency,'toss_turn_count':toss_turn_count,
                         'avg_hr':avg_hr,'avg_rr':avg_rr,'awake_count':awake_count,
                         'bed_exit_count':bed_exit_count,
                         'bed_exit_duration(min)':bed_exit_duration}, index=[0])

    
# NOTE: we should use start_date ALL THE TIME, since end_date is not necessary
def get_one_user_sleep_data(test_user,choppedTime):

    first_date_in_this_user = test_user['start_date'].tolist()[0]
    last_date_in_this_user = test_user['start_date'].tolist()[-1]

    sleep_summary_one_person = pd.DataFrame({})
    for i in range(len(choppedTime)-1):
        one_day_sleep  = test_user[test_user['start_date'] > choppedTime[i]]
        one_day_sleep  = one_day_sleep[one_day_sleep['start_date'] < choppedTime[i+1]]
               
        # e.g. choppedTime start  4-26, hence the choppedila_day is length 0 before the start date
        if first_date_in_this_user > datelist[i+1] or last_date_in_this_user < datelist[i]:
            continue    
        if len(one_day_sleep)==0:
            continue

        # one_day_sleep is the records for this day, now 
        # 1. remove the start_date that not within 7pm-6am
        # 2. for the rest episodes, check if they have same start time
        start_time = dt.datetime.strptime(choppedTime[i],'%Y-%m-%d %H:%M:%S')
        one_day_sleep_with_episodes = keep_record_in_interval(one_day_sleep, start_time)
        if len(one_day_sleep_with_episodes)==0:
            continue
    
        sleep_episodes_list = keep_longest_tst_in_episode(one_day_sleep_with_episodes)

        # now for each episode in sleep_episodes_list, process each parameter
        daily_summary = obtain_summary(sleep_episodes_list)    
        sleep_summary_one_person = pd.concat([sleep_summary_one_person,daily_summary])
        abab = sleep_summary_one_person.reset_index().drop(columns=['index'])

    return abab

#------------------
#test_user = reformed_sleep_list_temp[18]
#test_user = test_user.dropna(subset=['sleep_duration'])
#sleep_summary_one_person = get_one_user_sleep_data(test_user,choppedTime)

#------------------
reformed_sleep_list_no_nap = []
for test_user in reformed_sleep_list_temp:
    # drop rows with nan sleep_duration
    test_user = test_user.dropna(subset=['sleep_duration'])
    sleep_summary_one_person = get_one_user_sleep_data(test_user,choppedTime)
    reformed_sleep_list_no_nap.append(sleep_summary_one_person)
    

#############################################################################
# To CSV files
#############################################################################
path = r'D:/44_single_sleeper'

users_list=[]
for each in reformed_sleep_list_no_nap:
    users_list.append(each['PID'].tolist()[0])

csv_file_list = []
for each_user_str in users_list:
    each_csv_name = path+'/'+each_user_str+'.csv'
    csv_file_list.append(each_csv_name)

for i in range(len(csv_file_list)):
    reformed_sleep_list_no_nap[i].to_csv(csv_file_list[i],index=False)
    
    
#############################################################################
# Sleep parameter selection
#############################################################################
def get_sleep_parameter_with_date(reformed_sleep_list,sleep_para):
    temp_sleep_duration=[]
    for each_user_sleep in reformed_sleep_list:
        cc = each_user_sleep['PID'].tolist()
        bb = each_user_sleep['start_sleep_time'].tolist()
        aa = each_user_sleep[sleep_para].tolist()
        user_sleep = pd.DataFrame({'PID':cc,'date':bb,sleep_para:aa})
        temp_sleep_duration.append(user_sleep) 
    return temp_sleep_duration
temp_sleep_duration = get_sleep_parameter_with_date(reformed_sleep_list_no_nap,'TST(hour)')
temp_sleep_efficiency = get_sleep_parameter_with_date(reformed_sleep_list_no_nap,'SE')
temp_waso = get_sleep_parameter_with_date(reformed_sleep_list_no_nap,'WASO(min)')

#===========================================================
temp_sleep_start_time=[];temp_sleep_end_time=[]
for each_user_sleep in reformed_sleep_list_no_nap:
    cc = each_user_sleep['PID'].tolist()
    bb = each_user_sleep['start_sleep_time'].tolist()
    aa = each_user_sleep['finish_sleep_time'].tolist()
    
    bbb = each_user_sleep['start_timestamp'].tolist()
    aaa = each_user_sleep['end_timestamp'].tolist()
    
    user_sleep_start = pd.DataFrame({'PID':cc,'start_sleep_time':bb,'start_timestamp':bbb})
    user_sleep_end = pd.DataFrame({'PID':cc,'finish_sleep_time':aa,'end_timestamp':aaa})
    temp_sleep_start_time.append(user_sleep_start)     
    temp_sleep_end_time.append(user_sleep_end) 

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

df_concat_TST = one_sleep_para_all_users(period1_start,period2_start,period3_start,period1_end,period2_end,period3_end,temp_sleep_duration, 'TST(hour)')
df_concat_WASO = one_sleep_para_all_users(period1_start,period2_start,period3_start,period1_end,period2_end,period3_end,temp_waso, 'WASO(min)')
df_concat_SE = one_sleep_para_all_users(period1_start,period2_start,period3_start,period1_end,period2_end,period3_end,temp_sleep_efficiency, 'SE')

#############################################################################
# Sleep start and end time by different periods
#############################################################################
# get mean of time list
from cmath import rect, phase
from math import radians, degrees

def meanAngle(deg):
    complexDegree = sum(rect(1, radians(d)) for d in deg) / len(deg)
    argument = phase(complexDegree)
    meanAngle = degrees(argument)
    return meanAngle

def meanTime(times):
    t = (time.split(':') for time in times)
    seconds = ((float(s) + int(m) * 60 + int(h) * 3600) 
               for h, m, s in t)
    day = 24 * 60 * 60
    toAngles = [s * 360. / day for s in seconds]
    meanAsAngle = meanAngle(toAngles)
    meanSeconds = meanAsAngle * day / 360.
    if meanSeconds < 0:
        meanSeconds += day
    h, m = divmod(meanSeconds, 3600)
    m, s = divmod(m, 60)
    return('%02i:%02i:%02i' % (h, m, s))

print( meanTime(['03:07:00','23:09:08']) )

#---------------------------
def one_period_time_mean_median(period_start,period_end,temp_sleep_start_time, start_end_str):
    all_users_this_period=pd.DataFrame({})
    for each_user in temp_sleep_start_time:
        test = each_user.loc[(each_user[start_end_str] > period_start) & (each_user[start_end_str] <= period_end)]
        if len(test)==0:
            mean=np.nan; median = np.nan; earliest_time=np.nan; latest_time=np.nan
        if len(test)==1:
            test[start_end_str] = pd.to_datetime(test[start_end_str], unit='s')
            test['start_sleep_time_hour'] = [a.time() for a in test[start_end_str].tolist()]
            test['start_sleep_time_hour'] = [a.strftime("%H:%M:%S") for a in test['start_sleep_time_hour'].tolist()]
            mean = str(test['start_sleep_time_hour'].tolist()[0])+' #'
            median = mean
            earliest_time = mean
            latest_time = mean
        if len(test) > 1:  
            test[start_end_str] = pd.to_datetime(test[start_end_str], unit='s')
            test['start_sleep_time_hour'] = [a.time() for a in test[start_end_str].tolist()]
            # convert to str
            test['start_sleep_time_hour'] = [a.strftime("%H:%M:%S") for a in test['start_sleep_time_hour'].tolist()]
            # input the list of str to function
            mean = meanTime(test['start_sleep_time_hour'].tolist())
            #---------------------------
            # get median of time list
            # sort the time, and count length, if odd, take median;
            # if even, take mean of two middle values
            test = test.sort_values(by=['start_sleep_time_hour'])
            start_sleep_time_hour_df = test['start_sleep_time_hour'].reset_index()
            if len(test)%2 == 1: # length is odd number
                median = start_sleep_time_hour_df['start_sleep_time_hour'].iloc[int((len(test)+1)/2)]
            if len(test)%2 == 0: # length is even number
                first = start_sleep_time_hour_df['start_sleep_time_hour'].iloc[int(len(test)/2)]
                second = start_sleep_time_hour_df['start_sleep_time_hour'].iloc[int((len(test)+2)/2)]
                median = meanTime([first,second])
            #---------------------------
            # get eralier and latest time list, case by case
            fixed_time_day_divisor = dt.time(0,0,0).strftime("%H:%M:%S")
            today_start_sleep_time_df = start_sleep_time_hour_df[start_sleep_time_hour_df['start_sleep_time_hour']<fixed_time_day_divisor]
            tmr_start_sleep_time_df = start_sleep_time_hour_df[start_sleep_time_hour_df['start_sleep_time_hour']>=fixed_time_day_divisor]
        
            if len(today_start_sleep_time_df)>0:
                earliest_time = today_start_sleep_time_df['start_sleep_time_hour'].tolist()[0]
            if len(today_start_sleep_time_df)==0:
                earliest_time = tmr_start_sleep_time_df['start_sleep_time_hour'].tolist()[0]
            if len(tmr_start_sleep_time_df)>0:
                latest_time = tmr_start_sleep_time_df['start_sleep_time_hour'].tolist()[-1]
            if len(tmr_start_sleep_time_df)==0:
                latest_time = today_start_sleep_time_df['start_sleep_time_hour'].tolist()[-1]
                
        # store values
        this_user_this_period = pd.DataFrame({'mean_start_time':mean,'median_start_time':median,
                                              'earliest_start_time':earliest_time,
                                              'latest_start_time':latest_time}, index=[0])
        all_users_this_period = pd.concat([all_users_this_period,this_user_this_period], ignore_index=True)
    return all_users_this_period


def one_period_time_all_users(period1_start,period2_start,period3_start,period1_end,
                              period2_end,period3_end,temp_sleep_start_time,start_end_str):
    first_period = one_period_time_mean_median(period1_start,period1_end,
                                               temp_sleep_start_time,start_end_str)
    second_period = one_period_time_mean_median(period2_start,period2_end,
                                                temp_sleep_start_time,start_end_str)
    third_period = one_period_time_mean_median(period3_start,period3_end,
                                               temp_sleep_start_time,start_end_str)
    ID_list=[]
    for each in temp_sleep_start_time:
        ID_list.append(each['PID'].tolist()[0])
    # concate the dataframe
    df_concat = pd.concat([first_period,second_period,third_period], axis=1)
    df_concat.index = ID_list
    return df_concat

df_concat_start_time = one_period_time_all_users(period1_start,period2_start,
                                                 period3_start,period1_end,period2_end,period3_end,
                                                 temp_sleep_start_time,'start_sleep_time')

#-----------------------------------------------------------
def one_period_time_end(period_start,period_end,temp_sleep_end_time, start_end_str):
    all_users_this_period=pd.DataFrame({})
    for each_user in temp_sleep_end_time:
        test = each_user.loc[(each_user[start_end_str] > period_start) & (each_user[start_end_str] <= period_end)]
        if len(test)==0:
            mean=np.nan; median = np.nan; earliest_time=np.nan; latest_time=np.nan
        if len(test)==1:
            test[start_end_str] = pd.to_datetime(test[start_end_str], unit='s')
            test['end_sleep_time_hour'] = [a.time() for a in test[start_end_str].tolist()]
            test['end_sleep_time_hour'] = [a.strftime("%H:%M:%S") for a in test['end_sleep_time_hour'].tolist()]
            mean = str(test['end_sleep_time_hour'].tolist()[0])+' #'
            median = mean
            earliest_time = mean
            latest_time = mean
        if len(test)==2:
            test[start_end_str] = pd.to_datetime(test[start_end_str], unit='s')
            test['end_sleep_time_hour'] = [a.time() for a in test[start_end_str].tolist()]
            test['end_sleep_time_hour'] = [a.strftime("%H:%M:%S") for a in test['end_sleep_time_hour'].tolist()]
            mean = str(meanTime(test['end_sleep_time_hour'].tolist()))+' #'
            median = mean
            test = test.sort_values(by=['end_sleep_time_hour'])
            end_sleep_time_hour_df = test['end_sleep_time_hour'].reset_index()
            fixed_time_day_divisor = dt.time(0,0,0).strftime("%H:%M:%S")
            today_start_sleep_time_df = end_sleep_time_hour_df[end_sleep_time_hour_df['end_sleep_time_hour']<fixed_time_day_divisor]
            tmr_start_sleep_time_df = end_sleep_time_hour_df[end_sleep_time_hour_df['end_sleep_time_hour']>=fixed_time_day_divisor]
            if len(today_start_sleep_time_df)>0:
                earliest_time = today_start_sleep_time_df['end_sleep_time_hour'].tolist()[0]
            if len(today_start_sleep_time_df)==0:
                earliest_time = tmr_start_sleep_time_df['end_sleep_time_hour'].tolist()[0]
            if len(tmr_start_sleep_time_df)>0:
                latest_time = tmr_start_sleep_time_df['end_sleep_time_hour'].tolist()[-1]
            if len(tmr_start_sleep_time_df)==0:
                latest_time = today_start_sleep_time_df['end_sleep_time_hour'].tolist()[-1]
            earliest_time = str(earliest_time)+' #'
            latest_time = str(latest_time)+' #'
        if len(test) > 2:  
            test[start_end_str] = pd.to_datetime(test[start_end_str], unit='s')
            test['end_sleep_time_hour'] = [a.time() for a in test[start_end_str].tolist()]
            # convert to str
            test['end_sleep_time_hour'] = [a.strftime("%H:%M:%S") for a in test['end_sleep_time_hour'].tolist()]
            # input the list of str to function
            mean = meanTime(test['end_sleep_time_hour'].tolist())
            #---------------------------
            # get median of time list
            # sort the time, and count length, if odd, take median;
            # if even, take mean of two middle values
            test = test.sort_values(by=['end_sleep_time_hour'])
            start_sleep_time_hour_df = test['end_sleep_time_hour'].reset_index()
            if len(test)%2 == 1: # length is odd number
                median = start_sleep_time_hour_df['end_sleep_time_hour'].iloc[int((len(test)+1)/2)]
            if len(test)%2 == 0: # length is even number
                first = start_sleep_time_hour_df['end_sleep_time_hour'].iloc[int(len(test)/2)]
                second = start_sleep_time_hour_df['end_sleep_time_hour'].iloc[int((len(test)+2)/2)]
                median = meanTime([first,second])
            #---------------------------
            # get eralier and latest time list, case by case
            fixed_time_day_divisor = dt.time(0,0,0).strftime("%H:%M:%S")
            today_start_sleep_time_df = start_sleep_time_hour_df[start_sleep_time_hour_df['end_sleep_time_hour']<fixed_time_day_divisor]
            tmr_start_sleep_time_df = start_sleep_time_hour_df[start_sleep_time_hour_df['end_sleep_time_hour']>=fixed_time_day_divisor]
        
            if len(today_start_sleep_time_df)>0:
                earliest_time = today_start_sleep_time_df['end_sleep_time_hour'].tolist()[0]
            if len(today_start_sleep_time_df)==0:
                earliest_time = tmr_start_sleep_time_df['end_sleep_time_hour'].tolist()[0]
            if len(tmr_start_sleep_time_df)>0:
                latest_time = tmr_start_sleep_time_df['end_sleep_time_hour'].tolist()[-1]
            if len(tmr_start_sleep_time_df)==0:
                latest_time = today_start_sleep_time_df['end_sleep_time_hour'].tolist()[-1]
                
        # store values
        this_user_this_period = pd.DataFrame({'mean_end_time':mean,'median_end_time':median,
                                              'earliest_end_time':earliest_time,
                                              'latest_end_time':latest_time}, index=[0])
        all_users_this_period = pd.concat([all_users_this_period,this_user_this_period], ignore_index=True)
    return all_users_this_period

def one_period_end_time_all_users(period1_start,period2_start,period3_start,period1_end,
                              period2_end,period3_end,temp_sleep_end_time,start_end_str):
    first_period = one_period_time_end(period1_start,period1_end,
                                               temp_sleep_end_time,start_end_str)
    second_period = one_period_time_end(period2_start,period2_end,
                                                temp_sleep_end_time,start_end_str)
    third_period = one_period_time_end(period3_start,period3_end,
                                               temp_sleep_end_time,start_end_str)
    ID_list=[]
    for each in temp_sleep_start_time:
        ID_list.append(each['PID'].tolist()[0])
    # concate the dataframe
    df_concat = pd.concat([first_period,second_period,third_period], axis=1)
    df_concat.index = ID_list
    return df_concat

df_concat_end_time = one_period_end_time_all_users(period1_start,period2_start,
                                               period3_start,period1_end,period2_end,period3_end,
                                               temp_sleep_end_time,'finish_sleep_time')

############################################################################
# from users get their ages
#############################################################################
user_gender = pd.read_csv(r'D:\Sensor_Data_Processing\gender_label\survey_labels.csv')
user_list_sleep=[]
for i in range(len(reformed_sleep_list_no_nap)):
    user_list_sleep.append(reformed_sleep_list_no_nap[i]['PID'].tolist()[0])
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
#df_concat_end_time
#df_concat_start_time
# add mental score
df=df_concat_start_time

df = df[df.index.isin(user_gender['record_id'].tolist())]

# add ATSM score
user_gender_atsm_score = user_gender[['record_id','ATSM','age','gender']]
joined_table = df.merge(user_gender_atsm_score,left_on=df.index,right_on='record_id', 
     how = 'inner')
joined_table = joined_table.rename({'ATSM': 'mental_score'}, axis=1)  

# write table to excel
joined_table.to_excel(r'D:\solitray_44_sleepers\start.xlsx',index=False)


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

