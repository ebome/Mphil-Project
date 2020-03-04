import os
import pandas as pd


dir_dacs = r'D:\Class2_SleepPeriods_2020_02_17\Class2_SleepPeriods_2020_02_17\Class2_DACS_2020_02_17'
dacs=[]
for nextdir in os.listdir(dir_dacs):
    temp = dir_dacs + str('\\') + nextdir
    dacs.append(temp)
dacs = dacs[0:-2] # remove two csv files
   
dir_pisa = r'D:\Class2_SleepPeriods_2020_02_17\Class2_SleepPeriods_2020_02_17\Class2_PISA_2020_02_17'
pisa=[]
for nextdir in os.listdir(dir_pisa):
    temp = dir_pisa + str('\\') + nextdir
    pisa.append(temp)
pisa = pisa[0:-2] # remove two csv files



list_sleep_sum = []
list_sleep_class = []    

for each_dacs_dir in dacs:
    dacs_sleep_id = each_dacs_dir[-6:] # sleep ID has 6 digits
    
    dacs_sleep_this_id = []
    for nextdir in os.listdir(each_dacs_dir):
        temp = dir_dacs + str('\\') + dacs_sleep_id + str('\\') + nextdir
        dacs_sleep_this_id.append(temp)

    # now we can access 2 csv files via each dir in dacs_sleep_this_id
    for each_dir in dacs_sleep_this_id: 
    # eg. each_dir = D:\Class2_SleepPeriods_2020_02_17\Class2_SleepPeriods_2020_02_17\Class2_DACS_2020_02_17\001f4a\001f4a-pp-2019-06-18--09.53-12.53-2582558
    # get the 2 files names in each_dir
        all_file = os.listdir(each_dir)
        path0 = each_dir + str('\\') + all_file[0]
        path1 = each_dir + str('\\') + all_file[1]
        sleep_sumData = pd.read_csv(path0,index_col=None, header=0)
        sleep_classData = pd.read_csv(path1,index_col=None, header=0)
        
        # get the filename columns
        sleep_sum_col_name = all_file[0][:-4] # [:-4] removes '.csv' appendix
        sleep_class_col_name = all_file[1][:-4]

        # add the filename column into the dataframe
        # Creates a column and sets all rows to the same value
        sleep_sumData['filename'] = sleep_sum_col_name
        sleep_classData['filename'] = sleep_class_col_name
        
        list_sleep_sum.append(sleep_sumData)
        list_sleep_class.append(sleep_classData)

# --------------------------------------------
pisa_sleep_sum = []
pisa_sleep_class = []    

for each_pisa_dir in pisa:
    pisa_sleep_id = each_pisa_dir[-6:] # sleep ID has 6 digits
    
    pisa_sleep_this_id = []
    for nextdir in os.listdir(each_pisa_dir):
        temp = dir_pisa + str('\\') + pisa_sleep_id + str('\\') + nextdir
        pisa_sleep_this_id.append(temp)

    # now we can access 2 csv files via each dir in dacs_sleep_this_id
    for each_dir in pisa_sleep_this_id: 
    # eg. each_dir = D:\Class2_SleepPeriods_2020_02_17\Class2_SleepPeriods_2020_02_17\Class2_DACS_2020_02_17\001f4a\001f4a-pp-2019-06-18--09.53-12.53-2582558
    # get the 2 files names in each_dir
        all_file = os.listdir(each_dir)
        path0 = each_dir + str('\\') + all_file[0]
        path1 = each_dir + str('\\') + all_file[1]
        sleep_sum_pisa = pd.read_csv(path0,index_col=None, header=0)
        sleep_class_pisa = pd.read_csv(path1,index_col=None, header=0)
        
        # get the filename columns
        sleep_sum_col_name = all_file[0][:-4] # [:-4] removes '.csv' appendix
        sleep_class_col_name = all_file[1][:-4]

        # add the filename column into the dataframe
        # Creates a column and sets all rows to the same value
        sleep_sum_pisa['filename'] = sleep_sum_col_name
        sleep_class_pisa['filename'] = sleep_class_col_name
        
        pisa_sleep_sum.append(sleep_sum_pisa)
        pisa_sleep_class.append(sleep_class_pisa)

####################################################################
# combine DACS sleep summary and sleep class into big csv files
####################################################################
dacs_data1 = pd.concat(list_sleep_sum, ignore_index=True, sort =False)
filepath1 = dir_dacs + str('\\') + 'DACS_sleep_class.csv'
dacs_data1.to_csv(filepath1)

dacs_data2 = pd.concat(list_sleep_class, ignore_index=True, sort =False)
filepath2 = dir_dacs + str('\\') + 'DACS_sleep_summary.csv'
dacs_data2.to_csv(filepath2)


pisa_data1 = pd.concat(pisa_sleep_sum, ignore_index=True, sort =False)
filepath1 = dir_pisa + str('\\') + 'PISA_sleep_class.csv'
pisa_data1.to_csv(filepath1)

pisa_data2 = pd.concat(pisa_sleep_class, ignore_index=True, sort =False)
filepath2 = dir_pisa + str('\\') + 'PISA_sleep_summary.csv'
pisa_data2.to_csv(filepath2)

