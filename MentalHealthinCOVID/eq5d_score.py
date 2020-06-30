import numpy as np
import pandas as pd


baseline=pd.read_csv(r"D:\MentalHealth\dacs_baseline.csv")
mid=pd.read_csv(r"D:\MentalHealth\dacs_mid.csv")
end=pd.read_csv(r"D:\MentalHealth\dacs_end.csv")

'''
MOOD: Question 1/5/7/11/13 answer 'no'--> add 1
rest questions answer 'yes' --> add 1

index 3/7/9/13/15 "no"--> add 1
'''
def get_mood_score(a_df):
    score_list=[]
    for each_user in a_df.iterrows():
        score=0
        if each_user[1][3] == 'No':
            score=score+1
        if each_user[1][4] == 'Yes':
            score=score+1
        if each_user[1][5] == 'Yes':
            score=score+1
        if each_user[1][6] == 'Yes':
            score=score+1
        if each_user[1][7] == 'No':
            score=score+1
        if each_user[1][8] == 'Yes':
            score=score+1
        if each_user[1][9] == 'No':
            score=score+1
        if each_user[1][10] == 'Yes':
            score=score+1
        if each_user[1][11] == 'Yes':
            score=score+1
        if each_user[1][12] == 'Yes':
            score=score+1
        if each_user[1][13] == 'No':
            score=score+1
        if each_user[1][14] == 'Yes':
            score=score+1
        if each_user[1][15] == 'No':
            score=score+1
        if each_user[1][16] == 'Yes':
            score=score+1
        if each_user[1][17] == 'Yes':
            score=score+1

        score_list.append(score)
    return score_list


baseline_mood_list = get_mood_score(baseline)
mid_mood_list = get_mood_score(mid)
end_mood_list = get_mood_score(end)

baseline['mood score']=baseline_mood_list
mid['mood score']=mid_mood_list
end['mood score']=end_mood_list

baseline.drop(baseline.columns[3:18],axis=1,inplace=True)
mid.drop(mid.columns[3:18],axis=1,inplace=True)
end.drop(end.columns[3:18],axis=1,inplace=True)

final_score = pd.merge(baseline,mid, left_on='Participant ID',right_on='Participant ID', how='left')
final_score = pd.merge(final_score,end, left_on='Participant ID',right_on='Participant ID', how='left')


final_score.to_csv(r"D:\MentalHealth\eq5d_and_mood_scores.csv")



