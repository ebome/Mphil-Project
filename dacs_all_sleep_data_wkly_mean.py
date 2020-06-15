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
list_each_user_selected = []; selected_user_list =[]
for i in range(len(list_each_user)):
    each_user=list_each_user[i]
    if len(each_user)>100:
        list_each_user_selected.append(each_user)
        selected_user_list.append(each_user['PID'].tolist()[0])
#----------------------------------------
# create week-interval for slicing
slice_windows = pd.date_range('2019-12-29 00:00:00', periods=20, freq='7D').tolist()

# in list_each_user_selected, slice each_user into week and get the mean, std
# ONLY SEEP EFFICIENCY!!!

all_user_for_all_week_mean=[];all_user_for_all_week_std=[]
for each_user in list_each_user_selected:
    
    the_same_user_mean=[]; the_same_user_std=[]
    for i in range(len(slice_windows)-1):
        start_date = slice_windows[i]
        end_date = slice_windows[i+1]
        each_week_for_this_user = get_masked_dataframe(start_date, end_date, each_user)
        mean_for_this_week = each_week_for_this_user['awake_duration'].mean()
        std_for_this_week = each_week_for_this_user['awake_duration'].std()
        the_same_user_mean.append(mean_for_this_week);the_same_user_std.append(std_for_this_week)
    
    all_user_for_all_week_mean.append(the_same_user_mean)
    all_user_for_all_week_std.append(the_same_user_std)

###################################################
# combine the result of sleep efficiency
###################################################
wk_list =  ['mean at week %s' % s for s in range(20)] # it has week 0
wk_list = wk_list[1:]
wk_list2 = ['std at week %s' % s for s in range(20)][1:] 

df_all_week_mean = pd.DataFrame(all_user_for_all_week_mean, columns = wk_list)    
df_all_week_std = pd.DataFrame(all_user_for_all_week_std, columns = wk_list2)      
mean_for_weeks = pd.DataFrame({'PID':selected_user_list})
std_for_weeks = pd.DataFrame({'PID':selected_user_list})

mean_for_weeks = pd.concat([mean_for_weeks,df_all_week_mean],axis=1)
std_for_weeks = pd.concat([std_for_weeks,df_all_week_std],axis=1)


# plot the 5 users mean chart: 3-175, 3-6, 3-7, 3-87, 3-91, 3-37, 3-96
# 3-114, 3-146, 3-167
user1 = mean_for_weeks.iloc[26].fillna(0).values.tolist()[1:]
user2 = mean_for_weeks.iloc[43].fillna(0).values.tolist()[1:]
user3 = mean_for_weeks.iloc[47].fillna(0).values.tolist()[1:]
user4 = mean_for_weeks.iloc[50].fillna(0).values.tolist()[1:]
user5 = mean_for_weeks.iloc[53].fillna(0).values.tolist()[1:]
user6 = mean_for_weeks.iloc[35].fillna(0).values.tolist()[1:]
user7 = mean_for_weeks.iloc[57].fillna(0).values.tolist()[1:]
user8 = mean_for_weeks.iloc[7].fillna(0).values.tolist()[1:]
user9 = mean_for_weeks.iloc[14].fillna(0).values.tolist()[1:]
user10 = mean_for_weeks.iloc[24].fillna(0).values.tolist()[1:]


x=list(range(len(user1)))
labels = ['3-175', '3-6', '3-7', '3-87', '3-91','3-37','3-96','3-114', '3-146', '3-167']
y=[tuple(user1),tuple(user2),tuple(user3),tuple(user4),tuple(user5),tuple(user6),
   tuple(user7),tuple(user8),tuple(user9),tuple(user10),]

plt.figure(figsize=(10,5))
plt.plot(x,user1)
plt.plot(x,user2)
plt.plot(x,user3)
plt.plot(x,user4)
plt.plot(x,user5)
plt.plot(x,user6)
plt.plot(x,user7)
plt.plot(x,user8)
plt.plot(x,user9)
plt.plot(x,user10)
plt.legend(labels)
plt.xlabel('weeks');plt.ylabel('awake_duration')
plt.title('weekly mean for participants')
plt.axvline(x=12)


###################################################
# save the file
###################################################
sheet_names = ['mean for each week','std for each week']
               
from pandas import ExcelWriter

def save_xls(list_dfs, xls_path):
    with ExcelWriter(xls_path) as writer:
        for n, df in enumerate(list_dfs):
            df.to_excel(writer,sheet_name = sheet_names[n])
        writer.save()

xls_path = r"D:\MentalHealth\each week stats.xls"

list_dfs = [mean_for_weeks,std_for_weeks]

save_xls(list_dfs, xls_path)


