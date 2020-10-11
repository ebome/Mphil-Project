import pandas as pd
import datetime as dt
import numpy as np
from matplotlib import pyplot as plt
import merge_sensors as ms # make sure they are in same dir, run ms first




# Chopped datetime       
base = dt.datetime.strptime('2019-04-26 00:00:00', '%Y-%m-%d %H:%M:%S')
datelist = pd.date_range(base, periods=400).tolist()
choppedTime=[]
for elt in datelist:
    strg = f'{elt:%Y-%m-%d %H:%M:%S}'
    choppedTime.append(strg)



def labelled_room_and_time_diff(cleaned_ila):
    tempDF = pd.DataFrame({})
    temp1=[];temp2=[]
    for i in range(0, len(cleaned_ila)-1):
        room_previous_sensor = cleaned_ila.iloc[i]['changed_sensor_id'] 
        room_next_sensor =  cleaned_ila.iloc[i+1]['changed_sensor_id']
        if room_previous_sensor == room_next_sensor: 
            continue
        
        # only if room_previous_sensor != room_next_sensor indicate room transition
        elif room_previous_sensor != room_next_sensor:
            label = str(int(room_previous_sensor))+' to '+str(int(room_next_sensor)) 
            temp1.append(label)
            room_previous_time = cleaned_ila.iloc[i]['exact_time'][0:19] 
            room_previous_time = dt.datetime.strptime(room_previous_time, '%Y-%m-%d %H:%M:%S')
            room_next_time =  cleaned_ila.iloc[i+1]['exact_time'][0:19]
            room_next_time = dt.datetime.strptime(room_next_time, '%Y-%m-%d %H:%M:%S')
            time_diff =  (room_next_time - room_previous_time).seconds
            temp2.append(time_diff)

    tempDF['label'] = temp1
    tempDF['time difference'] = temp2
    return tempDF


def get_time_diff_for_one_room_part_A(cleaned_ila,choppedTime):
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

        if room_num == 3:
            merge_labelled_ilaList = ms.merge_3_sensors(ila_lablled)
        if room_num == 4:
            merge_labelled_ilaList = ms.merge_4_sensors(ila_lablled)
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
    
        # temp has the same length as time_diff_list, they are all for one day
        time_diff_list_all_days.append(time_diff_list)
        transition.append(merge_labelled_ilaList)
    
    return time_diff_list_all_days,transition,day

def get_time_diff_for_one_room_part_B(time_diff_list_all_days,transition,day,room_str):
    # now get the index for the room_label
    one_room_time_diff_by_days=[]
    for j in range(len(transition)):
        each_day_s_transition_label = transition[j]
        indices = []
        for i in range(len(each_day_s_transition_label)):
            if each_day_s_transition_label[i] == room_str:
                indices.append(i)
        
        store_list = []
        each_day_s_time_diff_one_room = time_diff_list_all_days[j]
        for each_index in indices:
           store_list.append(each_day_s_time_diff_one_room[each_index])
           
        one_room_time_diff_by_days.append(store_list)
    
    # make them as dataframe
    one_room_time_diff_with_date=pd.DataFrame({'Day':day,
                                             'one_room_time_diff':one_room_time_diff_by_days})

    return one_room_time_diff_with_date
#--------------------------------  
test_user = remove_consecutive_rooms_data[44]
single_user_transion_time_diff, single_user_transion_time_diff_with_date = get_time_diff_list(test_user,choppedTime)
aaa = single_user_transion_time_diff_with_date['transition label'].tolist()[0]
aaab = [x for xs in aaa for x in xs.split(',')]


def get_28day_allday_time_diff(one_user,choppedTime):
    time_diff_list_all_days,transition,day = get_time_diff_for_one_room_part_A(one_user,choppedTime)
    # get all room_str from 'transition'
    flat_transition = [item for sublist in transition for item in sublist]
    all_room_strs = list(set(flat_transition))
    # loop all_room_strs
    time_diff_for_all_room_pair=[]
    for room_str in all_room_strs:
        one_room_time_diff_with_date = get_time_diff_for_one_room_part_B(time_diff_list_all_days,transition,day,room_str)
        flat_one_room_time_diff_28day = [item for sublist in one_room_time_diff_with_date[0:29]['one_room_time_diff'].tolist() for item in sublist]
        median_28day = np.median(np.asarray(flat_one_room_time_diff_28day))
        flat_one_room_time_diff_Allday = [item for sublist in one_room_time_diff_with_date['one_room_time_diff'].tolist() for item in sublist]
        median_Allday = np.median(np.asarray(flat_one_room_time_diff_Allday))
        time_diff_for_all_room_pair.append(median_Allday-median_28day)
    return time_diff_for_all_room_pair

all_user_time_diff =[]
for each_user in remove_consecutive_rooms_data:
    time_diff_for_all_room_pair = get_28day_allday_time_diff(each_user,choppedTime)
    all_user_time_diff.append(time_diff_for_all_room_pair)

falt_all_user_time_diff= [item for sublist in all_user_time_diff for item in sublist]
cleanedList1 = [x for x in falt_all_user_time_diff if str(x) != 'nan']
plt.hist(cleanedList1,bins=50,color='r')
cleanedList2 = [x for x in cleanedList1 if abs(x) < 240]

# mean and std
np.std(cleanedList1)


plt.figure(figsize=(8,5))
x = list(range(len(cleanedList1)))
plt.scatter(x,cleanedList1,c='r',s=10)
plt.xlabel('room pairs')
plt.ylabel('transition time difference = median(all days) - median(28 days) (seconds)')


#---------------------------------------
def get_accumulate_avg_time(ploting_data_with_14_lists):
    indices = list(range(1,len(ploting_data_with_14_lists)+1))
    print(indices)
    avg_time_accumulation =[]
    for x in indices:
        flat_ploting_data_with_14_lists = [item for sublist in ploting_data_with_14_lists[0:x] for item in sublist]
        accumulate_avg = np.asarray(flat_ploting_data_with_14_lists).mean()
        avg_time_accumulation.append(accumulate_avg)
    return avg_time_accumulation

time_diff_list_all_days,transition,day = get_time_diff_for_one_room_part_A(test_user,choppedTime)
room_str = '1 to 2'
one_room_time_diff_with_date = get_time_diff_for_one_room_part_B(time_diff_list_all_days,transition,day,room_str)
day_length = 14
ploting_dates= one_room_time_diff_with_date.iloc[0:day_length+1]['Day'].tolist()
ploting_data= one_room_time_diff_with_date.iloc[0:day_length+1]['one_room_time_diff'].tolist()
avg_time_accumulation = get_accumulate_avg_time(ploting_data)
plt.plot(avg_time_accumulation);plt.xlabel('Days');plt.ylabel('Accumulative mean transiton time for two rooms')
plt.title(room_str+' transition time accumulative mean plot')

plt.figure(figsize=(10,5))
for xe, ye in zip(ploting_dates, ploting_data):
    plt.scatter([xe] * len(ye), ye, s=9, c='r')
plt.yscale('log')    
plt.title('user 3-175 '+room_str+' transition time')
plt.xlabel('First 14 days')
plt.ylabel('Log(Transition duration (seconds))')
plt.xticks(list(range(len(ploting_dates))))
plt.axes().set_xticklabels(ploting_dates,rotation='vertical')
