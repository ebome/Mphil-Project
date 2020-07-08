import numpy as np
import statsmodels.api as sm
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime as dt
from scipy import stats

dacs_all = pd.read_csv(r"D:\MentalHealth\dacs_91_sleep_data.csv")

dacs_all['start_date']=pd.to_datetime(dacs_all['start_date'])
dacs_all['end_date']=pd.to_datetime(dacs_all['end_date'])

# add 'sleep efficiency' column
dacs_all['sleep_efficiency']=dacs_all['sleep_duration']/dacs_all['bed_duration']

# add the mental scores for each user into dacs_all
mental_score = pd.read_excel(r"D:\MentalHealth\all_user_mental_score.xlsx")
dacs_all = pd.merge(dacs_all, mental_score, on='PID')

# clean some useless columns
dacs_all = dacs_all.drop(['sleep_data_id','end_time'], axis=1)

# remove the unappeared users in Apr from dataframe, and re-run the previous lines to check  
dacs_all = dacs_all[(dacs_all.PID !='3-195') &\
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


# count the number of PID in data
output = dacs_all.groupby('PID').size()
print('user count:',len(output))

'''
if the docuement eq5d_and_mood_and_mental_scores.csv PID have format 'Mar-xx', change them into
'3-xx  in csv and drag down to make all changed
'''
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
end_date_apr = dt.strptime('2020-05-10 00:00:00','%Y-%m-%d %H:%M:%S')
user_selected_covid19=[]
for each_user in list_each_user_selected:
    baseline_duration = get_masked_dataframe(end_date_b, end_date_apr, each_user)
    user_selected_covid19.append(baseline_duration)

###################################################
# remove the repetitive data from each user 
# --> keep the shortest duration as record
###################################################
# just select one user
only_user = dacs_all[dacs_all['PID']=='3-146']
start_date = dt.strptime('2019-12-29 00:00:00','%Y-%m-%d %H:%M:%S')
end_date = dt.strptime('2020-05-25 00:00:00','%Y-%m-%d %H:%M:%S')
this_year_only_user = get_masked_dataframe(start_date, end_date, only_user)
this_year_only_user.plot(x='start_date', y = 'sleep_duration',figsize=(14,5))

# slicing the dates into pieces
slice_windows = pd.date_range('2019-12-29 00:00:00', periods=130, freq='1D').tolist()

cleaned_this_user = pd.DataFrame({}) 
for i in range(len(slice_windows)-1):
    start_date = slice_windows[i]
    end_date = slice_windows[i+1]
    only_user_one_day_df = get_masked_dataframe(start_date, end_date, this_year_only_user)
    # in only_user_one_day_df, we remove the duplicates
    # keep the longest sleep duration in record
    only_user_one_day_df = only_user_one_day_df.fillna(method='ffill')
    only_user_one_day_cleaned = only_user_one_day_df.sort_values('sleep_duration').drop_duplicates(['PID'], keep='last')
    cleaned_this_user = pd.concat([cleaned_this_user,only_user_one_day_cleaned])

cleaned_this_user.plot(x='start_date', y = 'sleep_duration',figsize=(14,5))

# add the X, T, XT; but first, drop the rows containing nan
cleaned_this_user = cleaned_this_user.dropna(how='any')
covid_time = dt.strptime('2020-03-15 00:00:00','%Y-%m-%d %H:%M:%S')
cleaned_this_user['time'] = list(range(1,len(cleaned_this_user)+1))
cleaned_this_user['intervention'] = 0
cleaned_this_user.loc[cleaned_this_user['start_date'] > covid_time, 'intervention'] = 1
cleaned_this_user['time_after_intervention'] = 0
cleaned_this_user.loc[cleaned_this_user['start_date'] > covid_time, 'time_after_intervention'] = 1
length_of_intervention_days = len(cleaned_this_user[cleaned_this_user['time_after_intervention'] ==1])
cleaned_this_user.loc[cleaned_this_user['start_date'] > covid_time, 'time_after_intervention'] = list(range(1,length_of_intervention_days+1))

# trucate the data from a certain date
trucate_date = dt.strptime('2020-01-01 00:00:00','%Y-%m-%d %H:%M:%S')
cleaned_truncate_dates = cleaned_this_user[cleaned_this_user['start_date'] > trucate_date ]
cleaned_truncate_dates.plot(x='start_date', y = 'sleep_duration',figsize=(14,5))

'''
# write to csv for latter use
xls_path = r"D:\MentalHealth\cleaned_truncate_dates.csv"
cleaned_truncate_dates.to_csv(xls_path)
'''
###################################################
# ITS analysis
###################################################
# read the modifies file
whole_user = cleaned_truncate_dates.copy(deep=True)
parameter_list = ['sleep_duration','sleep_efficiency','rem_sleep_duration','light_sleep_duration',
                  'deep_sleep_duration','sleep_onset_duration','sleep_score','awakenings',
                  'awake_duration','bed_exit_count','bed_exit_duration']

the_parameter =parameter_list[1] 
X = whole_user[['time','intervention','time_after_intervention']] # time after interruption
X = sm.add_constant(X)
Y = whole_user[the_parameter] # DEPENDENT VARIABLE

model_time = sm.OLS(Y,X)
results_time = model_time.fit()
results_time.summary()
#---------------------------------------
# test the data for autocorrelation
pd.plotting.autocorrelation_plot(cleaned_this_user[the_parameter])

###################################################
# ITS analysis visualization
###################################################
cleaned_truncate_dates = cleaned_this_user[cleaned_this_user['start_date'] >= trucate_date ]
# use cleaned_truncate_dates dataframe to have two lines parameters
cleaned_truncate_dates_baseline = cleaned_truncate_dates[cleaned_truncate_dates['start_date'] < covid_time]
cleaned_truncate_dates_covid = cleaned_truncate_dates[cleaned_truncate_dates['start_date'] >= covid_time]
# m = slope, b=intercept
x_axis_baseline = list(range(len(cleaned_truncate_dates_baseline[the_parameter])))
m_baseline, b_baseline = np.polyfit(x_axis_baseline, cleaned_truncate_dates_baseline[the_parameter], 1)
x_axis_covid = list(range(len(cleaned_truncate_dates_covid[the_parameter])))
m_covid, b_covid = np.polyfit(x_axis_covid, cleaned_truncate_dates_covid[the_parameter], 1)

#---------------------------------------
# after getting m and b for baseline and covid, we need to change the cleaned_truncate_dates to a series
dates_in_time_format = cleaned_truncate_dates['start_date'].dt.strftime('%Y-%m-%d') # in datetime format
dates_in_time_format = dates_in_time_format.values.tolist()
cleaned_truncate_dates['start_date_in_str']=dates_in_time_format
cleaned_truncate_dates = cleaned_truncate_dates.set_index('start_date_in_str')
cleaned_truncate_dates.index = pd.DatetimeIndex(cleaned_truncate_dates.index)
starting_of_date = cleaned_truncate_dates_baseline['start_date'].iloc[0].strftime('%Y-%m-%d')
ending_of_date = cleaned_truncate_dates_covid['start_date'].iloc[-1].strftime('%Y-%m-%d')
idx = pd.date_range(starting_of_date, ending_of_date)
cleaned_truncate_dates = cleaned_truncate_dates.reindex(idx, fill_value='nan')
#---------------------------------------
# now recut baseline and covid that containing the missing days
cleaned_truncate_dates_baseline_with_nan = cleaned_truncate_dates[cleaned_truncate_dates.index < covid_time]
cleaned_truncate_dates_covid_with_nan = cleaned_truncate_dates[cleaned_truncate_dates.index >= covid_time]

x_axis_baseline = list(range(len(cleaned_truncate_dates_baseline_with_nan)))
# to get x_axis_covid, just re-change the ['time'] in cleaned_truncate_dates
cleaned_truncate_dates['time'] = list(range(1,len(cleaned_truncate_dates)+1))
cleaned_truncate_dates['intervention'] = 0
cleaned_truncate_dates.loc[cleaned_truncate_dates.index >= covid_time, 'intervention'] = 1
cleaned_truncate_dates['time_after_intervention'] = 0
cleaned_truncate_dates.loc[cleaned_truncate_dates.index >= covid_time, 'time_after_intervention'] = 1
length_of_intervention_days = len(cleaned_truncate_dates[cleaned_truncate_dates['time_after_intervention'] ==1])
cleaned_truncate_dates.loc[cleaned_truncate_dates.index >= covid_time, 'time_after_intervention'] = list(range(1,length_of_intervention_days+1))
# now use ['time'] in cleaned_truncate_dates as x_axis_covid
x_axis_covid = cleaned_truncate_dates[cleaned_truncate_dates.index>= covid_time]['time'].values.tolist()

#---------------------------------------
# from series cleaned_truncate_dates_one_parameter, get the dates 
y = cleaned_truncate_dates[the_parameter]
dates = list(range(len(y)))
x_labels = [date.strftime('%Y-%m-%d') for date in cleaned_truncate_dates.index]

# plot the whole
plt.figure(figsize =(25,5))
plt.plot(dates, y, c = 'blue')
plt.grid(True,alpha=0.5)
plt.ylabel('sleep efficiency (%)')
plt.xticks(dates, x_labels, rotation='vertical')
plt.plot(x_axis_baseline, m_baseline*np.asarray(x_axis_baseline) + b_baseline,'--',
         color="r",label='y1={:.4f}x+{:.4f}'.format(m_baseline,b_baseline))
plt.plot(x_axis_covid, m_covid*np.asarray(x_axis_covid) + b_covid,'--',
         color="g",label='y2={:.4f}x+{:.4f}'.format(m_covid,b_covid))
plt.xlabel('Sleep start recording date')

###################################################
# Merge the selected 10 users data
###################################################
'''
3-37, 3-175, 3-87, 3-188,3-6, 3-7, 3-96, 3-122,3-146, 3-167 

in parameter_summary_sleep_duration: 
    index at 35,26,50,28,43,47,57,9,14,24
'''

index_list = [35,26,50,28,43,47,57,9,14,24]

def dataframe_of_users(index_list,user_selected_baseline):
    baseline_dataframe = pd.DataFrame({})
    for i in index_list:
        the_user = user_selected_baseline[i]
        baseline_dataframe = pd.concat([baseline_dataframe,the_user])
    return baseline_dataframe

baseline_dataframe = dataframe_of_users(index_list,user_selected_baseline)
covid_dataframe = dataframe_of_users(index_list,user_selected_covid19)

# use box plot to show their distribution
baseline_dataframe['label']='baseline'
covid_dataframe['label']='covid'
merged_df=pd.concat([baseline_dataframe,covid_dataframe])

import seaborn as sns
sns.set(rc={'figure.figsize':(12,6)})
sns.boxplot(x='PID', y='sleep_duration', hue='label', data=merged_df)
sns.boxplot(x='PID', y='sleep_efficiency', hue='label', data=merged_df)
sns.boxplot(x='PID', y='rem_sleep_duration', hue='label', data=merged_df)
sns.boxplot(x='PID', y='light_sleep_duration', hue='label', data=merged_df)
sns.boxplot(x='PID', y='deep_sleep_duration', hue='label', data=merged_df)
sns.boxplot(x='PID', y='sleep_onset_duration', hue='label', data=merged_df)
sns.boxplot(x='PID', y='sleep_score', hue='label', data=merged_df)
sns.boxplot(x='PID', y='awakenings', hue='label', data=merged_df)
sns.boxplot(x='PID', y='awake_duration', hue='label', data=merged_df)
sns.boxplot(x='PID', y='bed_exit_count', hue='label', data=merged_df)
sns.boxplot(x='PID', y='bed_exit_duration', hue='label', data=merged_df)

###################################################
# Get the mean and std for each sleep parameter
###################################################
# make sure baseline and covid have same length   
def get_base_covid_same_length(parameter_str,user_selected_baseline,user_selected_covid19):

    trimmed_base_list=[];trimmed_covid_list =[]

    for i in range(len(user_selected_baseline)):
        each_user_baseline= user_selected_baseline[i]
        each_user_covid= user_selected_covid19[i]
        user_covid = each_user_covid[parameter_str].dropna().tolist()
        user_base = each_user_baseline[parameter_str].dropna().tolist()
    
        if len(user_covid)>len(user_base):
            user_covid_trimed = user_covid[:len(user_base)]
            trimmed_covid_list.append(user_covid_trimed)
            trimmed_base_list.append(user_base)
            continue
        elif len(user_covid) == len(user_base):
            trimmed_covid_list.append(user_covid)
            trimmed_base_list.append(user_base)
            continue
        elif len(user_covid)<len(user_base):
            inverselist_base = user_base[::-1]
            user_base_inverted = inverselist_base[:len(user_covid)]
            user_base_trimed = user_base_inverted[::-1]
            trimmed_covid_list.append(user_covid)
            trimmed_base_list.append(user_base_trimed)

    return trimmed_base_list, trimmed_covid_list

user_base_trimed, user_covid_trimed = get_base_covid_same_length('sleep_duration',user_selected_baseline,user_selected_covid19)
#----------------------------------------
def get_parameter_summary(parameter_str):

    mean_list=[];std_list=[]; user_list=[];
    mean_list_covid=[];std_list_covid=[]; 
    ttest_list=[];pval_list=[]
    
    # get the two arrays of base group and covid group
    user_base_trimed, user_covid_trimed = get_base_covid_same_length(parameter_str,user_selected_baseline,user_selected_covid19)
    for i in range(len(user_base_trimed)):
        each_user_base = user_base_trimed[i]
        each_user_covid = user_covid_trimed[i]
        ttest,pval = stats.ttest_rel(each_user_base,each_user_covid)
        ttest_list.append(ttest);pval_list.append(pval)
    
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


    parameter_summary = pd.DataFrame({'PID':user_list,'baseline_mean':mean_list,'baseline_std':std_list,
                     'covid_mean':mean_list_covid,'std_covid':std_list_covid,'t_test':ttest_list,
                     'p_value':pval_list})
    return parameter_summary


#----------------------------------------
parameter_summary_sleep_duration = get_parameter_summary('sleep_duration')
parameter_summary_bed_duration = get_parameter_summary('bed_duration')
parameter_summary_sleep_score = get_parameter_summary('sleep_score')
parameter_summary_awake_duration = get_parameter_summary('awake_duration')
parameter_summary_rem_sleep_duration = get_parameter_summary('rem_sleep_duration')
parameter_summary_light_sleep_duration = get_parameter_summary('light_sleep_duration')
parameter_summary_bed_exit_count = get_parameter_summary('bed_exit_count')
parameter_summary_bed_exit_duration = get_parameter_summary('bed_exit_duration')

parameter_summary_deep_sleep_duration = get_parameter_summary('deep_sleep_duration')
parameter_summary_sleep_onset_duration = get_parameter_summary('sleep_onset_duration')
parameter_summary_toss_turn_count = get_parameter_summary('toss_turn_count')
parameter_summary_average_heart_rate = get_parameter_summary('average_heart_rate')
parameter_summary_average_respiration_rate = get_parameter_summary('average_respiration_rate')
parameter_summary_average_physical_activity = get_parameter_summary('average_physical_activity')
parameter_summary_awakenings = get_parameter_summary('awakenings')
parameter_summary_sleep_efficiency = get_parameter_summary('sleep_efficiency')

###################################################
# make the 10 user to excel
###################################################

sheet_names = ['sleep_duration','bed_duration','sleep_score','awake_duration',
               'rem_sleep_duration','light_sleep_duration','bed_exit_count',
               'bed_exit_duration','deep_sleep_duration',
               'sleep_onset_duration','toss_turn_count','average_heart_rate',
               'average_respiration_rate','average_physical_activity','awakenings',
               'sleep_efficiency']

              
from pandas import ExcelWriter

def save_xls(list_dfs, xls_path):
    with ExcelWriter(xls_path) as writer:
        for n, df in enumerate(list_dfs):
            df.to_excel(writer,sheet_name = sheet_names[n])
        writer.save()

xls_path = r"D:\MentalHealth\baseline and covid group stats new.xls"


list_dfs = [parameter_summary_sleep_duration.iloc[index_list],parameter_summary_bed_duration.iloc[index_list],
parameter_summary_sleep_score.iloc[index_list],parameter_summary_awake_duration.iloc[index_list],parameter_summary_rem_sleep_duration.iloc[index_list],
parameter_summary_light_sleep_duration.iloc[index_list],parameter_summary_bed_exit_count.iloc[index_list],
parameter_summary_bed_exit_duration.iloc[index_list],parameter_summary_deep_sleep_duration.iloc[index_list],
parameter_summary_sleep_onset_duration.iloc[index_list],parameter_summary_toss_turn_count.iloc[index_list],
parameter_summary_average_heart_rate.iloc[index_list],parameter_summary_average_respiration_rate.iloc[index_list],
parameter_summary_average_physical_activity.iloc[index_list],parameter_summary_awakenings.iloc[index_list],
parameter_summary_sleep_efficiency.iloc[index_list]]

save_xls(list_dfs, xls_path)


###################################################
# paired t test on all the selected user
###################################################
# ignore ATSM score

# test the base and covid have same length
def test_length_base_covid(user_base_trimed,user_covid_trimed):
    for i in range(len(user_base_trimed)):
        if len(user_base_trimed[i])== len(user_covid_trimed[i]):
            continue
        else:
            return False
    return True   
print(test_length_base_covid(user_base_trimed,user_covid_trimed))

# merge base and covid to two groups, and see t test 
def ttest_among_base_covid(user_base_trimed, user_covid_trimed):
    flatten_list_base = [item for sublist in user_base_trimed for item in sublist]
    flatten_list_covid = [item for sublist in user_covid_trimed for item in sublist]
    ttest,pval = stats.ttest_rel(flatten_list_base,flatten_list_covid)
    return ttest,pval

test_list=[];pval_list=[]
parameter_list = ['sleep_duration','sleep_efficiency','rem_sleep_duration','light_sleep_duration',
                  'deep_sleep_duration','sleep_onset_duration','sleep_score','awakenings',
                  'awake_duration','bed_exit_count','bed_exit_duration']
for parameter_str in parameter_list:
    user_base_trimed_parameter, user_covid_trimed_parameter = get_base_covid_same_length(parameter_str,user_selected_baseline,user_selected_covid19)
    ttest, pval = ttest_among_base_covid(user_base_trimed_parameter, user_covid_trimed_parameter)
    test_list.append(ttest);pval_list.append(pval)

all_user_ttest = pd.DataFrame({'parameter':parameter_list, 'paired_t_test':test_list,'p_value':pval_list })


#------------------------------------
# remove those who have ATSM < 7

dacs_no_ci = dacs_all[dacs_all.ATSM >= 7 ]
new_all_no_ci = get_masked_dataframe(start_date, end_date, dacs_no_ci)

list_each_user=[]
for name,group in new_all_no_ci.groupby(['PID']):
    list_each_user.append(group)
# remove the users who have less than 100 days
list_each_user_selected = []
for i in range(len(list_each_user)):
    each_user=list_each_user[i]
    if len(each_user)>100:
        list_each_user_selected.append(each_user)
# from the 56 users, split to two lists by Mar 15th
# Jan - Mar 14th as baseline
end_date_b = dt.strptime('2020-03-15 00:00:00','%Y-%m-%d %H:%M:%S')
user_no_ci_baseline=[]
for each_user in list_each_user_selected:
    baseline_duration = get_masked_dataframe(start_date, end_date_b, each_user)
    user_no_ci_baseline.append(baseline_duration)
# Mar 14th - May 4th as a whole
end_date_apr = dt.strptime('2020-05-10 00:00:00','%Y-%m-%d %H:%M:%S')
user_no_ci_covid19=[]
for each_user in list_each_user_selected:
    baseline_duration = get_masked_dataframe(end_date_b, end_date_apr, each_user)
    user_no_ci_covid19.append(baseline_duration)

test_list=[];pval_list=[]
for parameter_str in parameter_list:
    user_base_trimed_parameter, user_covid_trimed_parameter = get_base_covid_same_length(parameter_str,user_no_ci_baseline,user_no_ci_covid19)
    ttest, pval = ttest_among_base_covid(user_base_trimed_parameter, user_covid_trimed_parameter)
    test_list.append(ttest);pval_list.append(pval)

no_ci_user_ttest = pd.DataFrame({'parameter':parameter_list, 'paired_t_test':test_list,'p_value':pval_list })


###################################################
# plot the distribution of users: histogram
###################################################
# flatten the lists containing dataframe
def trim_and_flatted_data(parameter_str,user_selected_baseline,user_selected_covid19):
    user_base_trimed_sleep_para,user_covid_trimed_sleep_para = get_base_covid_same_length(parameter_str,user_selected_baseline,user_selected_covid19)
    flatten_list_base = [item for sublist in user_base_trimed_sleep_para for item in sublist]
    flatten_list_covid = [item for sublist in user_covid_trimed_sleep_para for item in sublist]
    return flatten_list_base,flatten_list_covid
#------------------------------------------------------------------------
# now 4 dataframe can be flattened:user_no_ci_covid19, user_no_ci_baseline,user_selected_baseline,user_selected_covid19 
parameter_str=parameter_list[10]
all_user_base,all_user_covid = trim_and_flatted_data(parameter_str,user_selected_baseline,user_selected_covid19)
no_ci_user_base,no_ci_user_covid = trim_and_flatted_data(parameter_str,user_no_ci_baseline,user_no_ci_covid19)

fig = plt.figure(figsize=(8,8))
ax1 = fig.add_subplot(2, 1, 1)
ax2 = fig.add_subplot(2,1, 2)

ax1.hist(all_user_base,alpha=0.5,bins = 100,histtype='barstacked',color = 'red',label = 'base')
ax1.hist(all_user_covid,alpha=0.5,bins = 100,histtype='barstacked',color = 'green',label = 'covid')
ax1.set_xlabel('Bin of Values: all users')
ax1.set_ylabel('Frequency')
ax1.legend(loc='upper right')

ax2.hist(no_ci_user_base,alpha=0.5,bins = 100,histtype='barstacked',color = 'red',label = 'base')
ax2.hist(no_ci_user_covid,alpha=0.5,bins = 100,histtype='barstacked',color = 'green',label = 'covid')
ax2.set_xlabel('Bin of Values:users without CI')
ax2.set_ylabel('Frequency')
ax2.legend(loc='upper right')
ax1.set_title(parameter_str)


###################################################
# plot the distribution of users
###################################################

# flatten the lists containing dataframe
no_ci_covid=pd.DataFrame({})
for each_elt in user_no_ci_covid19:
    no_ci_covid = pd.concat([no_ci_covid, each_elt], ignore_index=True, sort=False)
no_ci_covid['group']='user without CI'
no_ci_covid['label']='covid'

no_ci_base=pd.DataFrame({})
for each_elt in user_no_ci_baseline:
    no_ci_base = pd.concat([no_ci_base, each_elt], ignore_index=True, sort=False)
no_ci_base['group']='user without CI'
no_ci_base['label']='baseline'

all_covid=pd.DataFrame({})
for each_elt in user_selected_covid19:
    all_covid = pd.concat([all_covid, each_elt], ignore_index=True, sort=False)
all_covid['group']='all users'
all_covid['label']='covid'

all_base=pd.DataFrame({})
for each_elt in user_selected_baseline:
    all_base = pd.concat([all_base, each_elt], ignore_index=True, sort=False)
all_base['group']='all users'
all_base['label']='baseline'

merged_df=pd.concat([all_covid,all_base,no_ci_covid,no_ci_base])

sns.set(rc={'figure.figsize':(8,8)})
sns.boxplot(x='group', y='sleep_duration', hue='label', data=merged_df)
sns.boxplot(x='group', y='sleep_efficiency', hue='label', data=merged_df)
sns.boxplot(x='group', y='rem_sleep_duration', hue='label', data=merged_df)
sns.boxplot(x='group', y='light_sleep_duration', hue='label', data=merged_df)
sns.boxplot(x='group', y='deep_sleep_duration', hue='label', data=merged_df)
sns.boxplot(x='group', y='sleep_onset_duration', hue='label', data=merged_df)
sns.boxplot(x='group', y='sleep_score', hue='label', data=merged_df)
sns.boxplot(x='group', y='awakenings', hue='label', data=merged_df)
sns.boxplot(x='group', y='awake_duration', hue='label', data=merged_df)
sns.boxplot(x='group', y='bed_exit_count', hue='label', data=merged_df)
sns.boxplot(x='group', y='bed_exit_duration', hue='label', data=merged_df)


