import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime as dt
from scipy import stats

dacs_all=pd.read_csv(r"D:\MentalHealth\dacs_91_sleep_data.csv")

dacs_all['start_date']=pd.to_datetime(dacs_all['start_date'])
dacs_all['end_date']=pd.to_datetime(dacs_all['end_date'])

# add 'sleep efficiency' column
dacs_all['sleep_efficiency']=dacs_all['sleep_duration']/dacs_all['bed_duration']

# clean some useless columns
dacs_all = dacs_all.drop(['sleep_data_id','start_time','end_time'], axis=1)

# remove the unappeared users in Apr from dataframe, and re-run the previous lines to check  
dacs_all = dacs_all[(dacs_all.PID !='3-195') & (dacs_all.PID !='3-37') &\
                    (dacs_all.PID !='3-13') & (dacs_all.PID !='3-41') &\
                    (dacs_all.PID !='3-125') & (dacs_all.PID !='3-187') &\
                    (dacs_all.PID !='3-3') & (dacs_all.PID !='3-169') &\
                    (dacs_all.PID !='3-85') & (dacs_all.PID !='3-121') &\
                    (dacs_all.PID !='3-51') ]

# for simplicity, only keep the columns needed
dacs_all = dacs_all.drop(['device_id','min_heart_rate','max_heart_rate',
                          'min_respiration_rate','max_respiration_rate','fm_count',
                          'hrv_score','hrv_lf','hrv_hf','hrv_rmssd_evening',
                          'hrv_rmssd_morning','end_date'], axis=1)


###################################################
# make a boolean mask of window
###################################################

def get_masked_dataframe(start_date, end_date, df):
    mask = (df['start_date']>= start_date) & (df['start_date'] < end_date)
    new_df = df.loc[mask]
    return new_df

start_date = dt.strptime('2019-12-29 00:00:00','%Y-%m-%d %H:%M:%S')
end_date = dt.strptime('2020-05-25 00:00:00','%Y-%m-%d %H:%M:%S')
new_all = get_masked_dataframe(start_date, end_date, dacs_all)


list_each_user=[]
for name,group in new_all.groupby(['PID']):
    list_each_user.append(group)

# remove the users who have less than 100 days
list_each_user_selected = []
for i in range(len(list_each_user)):
    each_user=list_each_user[i]
    if len(each_user)>100:
        list_each_user_selected.append(each_user)
#----------------------------------------
# from the 56 users, split to two lists by Mar 15th
# Jan - Mar 14th as baseline
end_date_b = dt.strptime('2020-03-15 00:00:00','%Y-%m-%d %H:%M:%S')
user_selected_baseline=[]
for each_user in list_each_user_selected:
    baseline_duration = get_masked_dataframe(start_date, end_date_b, each_user)
    user_selected_baseline.append(baseline_duration)

# Mar 14th - May 4th as a whole
end_date_apr = dt.strptime('2020-05-01 00:00:00','%Y-%m-%d %H:%M:%S')
user_selected_covid19=[]
for each_user in list_each_user_selected:
    baseline_duration = get_masked_dataframe(end_date_b, end_date_apr, each_user)
    user_selected_covid19.append(baseline_duration)


###################################################
# Get the mean and std for each sleep parameter
###################################################


def get_parameter_summary(parameter_str):

    mean_list=[];std_list=[]; user_list=[];
    mean_list_covid=[];std_list_covid=[]; 
    ttest_list=[];pval_list=[]
    for i in range(len(user_selected_baseline)):
        each_user_baseline= user_selected_baseline[i]
        each_user_covid= user_selected_covid19[i]
        
        # user ID from each_user
        userID = each_user_baseline['PID'].tolist()[1]
        user_mean = each_user_baseline[parameter_str].mean()
        user_std= each_user_baseline[parameter_str].std()
        user_list.append(userID)
        mean_list.append(user_mean)
        std_list.append(user_std)
    
        user_mean_covid = each_user_covid[parameter_str].mean()
        user_std_covid = each_user_covid[parameter_str].std()
        mean_list_covid.append(user_mean_covid)
        std_list_covid.append(user_std_covid)
        '''
        Calculates the T-test for the means of two independent samples of scores. 
        This is a two-sided test for the null hypothesis that two independent samples have 
        identical average (expected) values. This test assumes that the populations have 
        identical variances by default.
        '''
        # get the two arrays of base group and covid group
        user_covid = each_user_covid[parameter_str].dropna().tolist()
        user_base = each_user_baseline[parameter_str].dropna().tolist()
        ttest,pval = stats.ttest_ind(user_base,user_covid,equal_var = False)
        ttest_list.append(ttest);pval_list.append(pval)


    parameter_summary = pd.DataFrame({'PID':user_list,'baseline_mean':mean_list,'baseline_std':std_list,
                     'covid_mean':mean_list_covid,'std_covid':std_list_covid,
                     't-test between base/covid group':ttest_list,'p-value':pval_list})
    return parameter_summary

#----------------------------------------
parameter_summary_sleep_duration = get_parameter_summary('sleep_duration')
parameter_summary_bed_duration = get_parameter_summary('bed_duration')
parameter_summary_sleep_score = get_parameter_summary('sleep_score')
parameter_summary_awake_duration = get_parameter_summary('awake_duration')
parameter_summary_rem_sleep_duration = get_parameter_summary('rem_sleep_duration')
parameter_summary_light_sleep_duration = get_parameter_summary('light_sleep_duration')

parameter_summary_deep_sleep_duration = get_parameter_summary('deep_sleep_duration')
parameter_summary_sleep_onset_duration = get_parameter_summary('sleep_onset_duration')
parameter_summary_toss_turn_count = get_parameter_summary('toss_turn_count')
parameter_summary_average_heart_rate = get_parameter_summary('average_heart_rate')
parameter_summary_average_respiration_rate = get_parameter_summary('average_respiration_rate')
parameter_summary_average_physical_activity = get_parameter_summary('average_physical_activity')
parameter_summary_awakenings = get_parameter_summary('awakenings')
parameter_summary_sleep_efficiency = get_parameter_summary('sleep_efficiency')

###################################################
# 5 users with 4 parameters in base and covid group to be plotted
###################################################
'''
3-175, 3-6,3-7,3-87,3-91: index at 25/41/45/48/51
'''
index_list = [25,41,45,48,51]
def get_base_covid_mean(df,index_list):
    s = df[['PID','baseline_mean','covid_mean']].ix[index_list]
    return s

plot_awake = get_base_covid_mean(parameter_summary_awake_duration,index_list)
plot_sleep_duration = get_base_covid_mean(parameter_summary_sleep_duration,index_list)
plot_sleep_latency = get_base_covid_mean(parameter_summary_sleep_onset_duration,index_list)
plot_sleep_efficiency = get_base_covid_mean(parameter_summary_sleep_efficiency,index_list)

def get_plot(plot_df,title):
    df = pd.DataFrame({'baseline_mean': plot_df['baseline_mean'].tolist(),
                   'covid_mean': plot_df['covid_mean'].tolist()}, 
    index=plot_df['PID'].tolist())
    ax = df.plot.bar(rot=0,title =title, figsize=(10,5))
    ax.set_xlabel('participant')
    

get_plot(plot_awake,'awake')
get_plot(plot_sleep_duration,'sleep duration')
get_plot(plot_sleep_latency,'sleep latency')
get_plot(plot_sleep_efficiency,'sleep efficiency')


###################################################
# to excel
###################################################

sheet_names = ['sleep_duration','bed_duration','sleep_score','awake_duration',
               'rem_sleep_duration','light_sleep_duration','deep_sleep_duration',
               'sleep_onset_duration','toss_turn_count','average_heart_rate',
               'average_respiration_rate','average_physical_activity','awakenings',
               'sleep_efficiency']
               
from pandas import ExcelWriter

def save_xls(list_dfs, xls_path):
    with ExcelWriter(xls_path) as writer:
        for n, df in enumerate(list_dfs):
            df.to_excel(writer,sheet_name = sheet_names[n])
        writer.save()

xls_path = r"D:\MentalHealth\baseline and covid group stats.xls"


list_dfs = [parameter_summary_sleep_duration,parameter_summary_bed_duration,
parameter_summary_sleep_score,parameter_summary_awake_duration,parameter_summary_rem_sleep_duration,
parameter_summary_light_sleep_duration,parameter_summary_deep_sleep_duration,
parameter_summary_sleep_onset_duration,parameter_summary_toss_turn_count,
parameter_summary_average_heart_rate,parameter_summary_average_respiration_rate,
parameter_summary_average_physical_activity,parameter_summary_awakenings,
parameter_summary_sleep_efficiency]

save_xls(list_dfs, xls_path)


