# merge '3 to 4' and '4 to 3'
def merge_3_sensors(ila_lablled):
    label = ila_lablled['label'].values.tolist()
    temp=[]
    for i in range(0,len(label)):
        if label[i] == '0 to 1' or label[i] == '1 to 0':
            temp.append('0 to 1')
        if label[i] == '0 to 2' or label[i] == '2 to 0':
            temp.append('0 to 2')
        if label[i] == '1 to 2' or label[i] == '2 to 1':
            temp.append('1 to 2')

    return temp

def merge_4_sensors(ila_lablled):
    label = ila_lablled['label'].values.tolist()
    temp=[]
    for i in range(0,len(label)):
        if label[i] == '0 to 1' or label[i] == '1 to 0':
            temp.append('0 to 1')
        if label[i] == '0 to 2' or label[i] == '2 to 0':
            temp.append('0 to 2')
        if label[i] == '0 to 3' or label[i] == '3 to 0':
            temp.append('0 to 3')
        if label[i] == '1 to 2' or label[i] == '2 to 1':
            temp.append('1 to 2')
        if label[i] == '1 to 3' or label[i] == '3 to 1':
            temp.append('1 to 3')
        if label[i] == '2 to 3' or label[i] == '3 to 2':
            temp.append('2 to 3')
    return temp


def merge_5_sensors(ila_lablled):
    label = ila_lablled['label'].values.tolist()
    temp=[]
    for i in range(0,len(label)):
        if label[i] == '0 to 1' or label[i] == '1 to 0':
            temp.append('0 to 1')
        if label[i] == '0 to 2' or label[i] == '2 to 0':
            temp.append('0 to 2')
        if label[i] == '0 to 3' or label[i] == '3 to 0':
            temp.append('0 to 3')
        if label[i] == '0 to 4' or label[i] == '4 to 0':
            temp.append('0 to 4')
        if label[i] == '1 to 2' or label[i] == '2 to 1':
            temp.append('1 to 2')
        if label[i] == '1 to 3' or label[i] == '3 to 1':
            temp.append('1 to 3')
        if label[i] == '1 to 4' or label[i] == '4 to 1':
            temp.append('1 to 4')
        if label[i] == '2 to 3' or label[i] == '3 to 2':
            temp.append('2 to 3')
        if label[i] == '2 to 4' or label[i] == '4 to 2':
            temp.append('2 to 4')
        if label[i] == '3 to 4' or label[i] == '4 to 3':
            temp.append('3 to 4')
    return temp


def merge_6_sensors(ila_lablled):
    label = ila_lablled['label'].values.tolist()
    temp=[]
    for i in range(0,len(label)):
        if label[i] == '0 to 1' or label[i] == '1 to 0':
            temp.append('0 to 1')
        if label[i] == '0 to 2' or label[i] == '2 to 0':
            temp.append('0 to 2')
        if label[i] == '0 to 3' or label[i] == '3 to 0':
            temp.append('0 to 3')
        if label[i] == '0 to 4' or label[i] == '4 to 0':
            temp.append('0 to 4')
        if label[i] == '0 to 5' or label[i] == '5 to 0':
            temp.append('0 to 5')
        if label[i] == '1 to 2' or label[i] == '2 to 1':
            temp.append('1 to 2')
        if label[i] == '1 to 3' or label[i] == '3 to 1':
            temp.append('1 to 3')
        if label[i] == '1 to 4' or label[i] == '4 to 1':
            temp.append('1 to 4')
        if label[i] == '1 to 5' or label[i] == '5 to 1':
            temp.append('1 to 5')
        if label[i] == '2 to 3' or label[i] == '3 to 2':
            temp.append('2 to 3')
        if label[i] == '2 to 4' or label[i] == '4 to 2':
            temp.append('2 to 4')
        if label[i] == '2 to 5' or label[i] == '5 to 2':
            temp.append('2 to 5')
        if label[i] == '3 to 4' or label[i] == '4 to 3':
            temp.append('3 to 4')
        if label[i] == '3 to 5' or label[i] == '5 to 3':
            temp.append('3 to 5')
        if label[i] == '4 to 5' or label[i] == '5 to 4':
            temp.append('4 to 5')
    return temp


def merge_7_sensors(ila_lablled):
    label = ila_lablled['label'].values.tolist()
    temp=[]
    for i in range(0,len(label)):
        if label[i] == '0 to 1' or label[i] == '1 to 0':
            temp.append('0 to 1')
        if label[i] == '0 to 2' or label[i] == '2 to 0':
            temp.append('0 to 2')
        if label[i] == '0 to 3' or label[i] == '3 to 0':
            temp.append('0 to 3')
        if label[i] == '0 to 4' or label[i] == '4 to 0':
            temp.append('0 to 4')
        if label[i] == '0 to 5' or label[i] == '5 to 0':
            temp.append('0 to 5')
        if label[i] == '0 to 6' or label[i] == '6 to 0':
            temp.append('0 to 6')
            
        if label[i] == '1 to 2' or label[i] == '2 to 1':
            temp.append('1 to 2')
        if label[i] == '1 to 3' or label[i] == '3 to 1':
            temp.append('1 to 3')
        if label[i] == '1 to 4' or label[i] == '4 to 1':
            temp.append('1 to 4')
        if label[i] == '1 to 5' or label[i] == '5 to 1':
            temp.append('1 to 5')              
        if label[i] == '1 to 6' or label[i] == '6 to 1':
            temp.append('1 to 6')

        if label[i] == '2 to 3' or label[i] == '3 to 2':
            temp.append('2 to 3')
        if label[i] == '2 to 4' or label[i] == '4 to 2':
            temp.append('2 to 4')
        if label[i] == '2 to 5' or label[i] == '5 to 2':
            temp.append('2 to 5')           
        if label[i] == '2 to 6' or label[i] == '6 to 2':
            temp.append('2 to 6')            
           
        if label[i] == '3 to 4' or label[i] == '4 to 3':
            temp.append('3 to 4')
        if label[i] == '3 to 5' or label[i] == '5 to 3':
            temp.append('3 to 5')
        if label[i] == '3 to 6' or label[i] == '6 to 3':
            temp.append('3 to 6')           
            
        if label[i] == '4 to 5' or label[i] == '5 to 4':
            temp.append('4 to 5')
        if label[i] == '4 to 6' or label[i] == '6 to 4':
            temp.append('4 to 6')

        if label[i] == '5 to 6' or label[i] == '6 to 5':
            temp.append('5 to 6')
                
    return temp


def merge_8_sensors(ila_lablled):
    label = ila_lablled['label'].values.tolist()
    temp=[]
    for i in range(0,len(label)):
        if label[i] == '0 to 1' or label[i] == '1 to 0':
            temp.append('0 to 1')
        if label[i] == '0 to 2' or label[i] == '2 to 0':
            temp.append('0 to 2')
        if label[i] == '0 to 3' or label[i] == '3 to 0':
            temp.append('0 to 3')
        if label[i] == '0 to 4' or label[i] == '4 to 0':
            temp.append('0 to 4')
        if label[i] == '0 to 5' or label[i] == '5 to 0':
            temp.append('0 to 5')           
        if label[i] == '0 to 6' or label[i] == '6 to 0':
            temp.append('0 to 6')
        if label[i] == '0 to 7' or label[i] == '7 to 0':
            temp.append('0 to 7')
            
        if label[i] == '1 to 2' or label[i] == '2 to 1':
            temp.append('1 to 2')
        if label[i] == '1 to 3' or label[i] == '3 to 1':
            temp.append('1 to 3')
        if label[i] == '1 to 4' or label[i] == '4 to 1':
            temp.append('1 to 4')
        if label[i] == '1 to 5' or label[i] == '5 to 1':
            temp.append('1 to 5')              
        if label[i] == '1 to 6' or label[i] == '6 to 1':
            temp.append('1 to 6')
        if label[i] == '1 to 7' or label[i] == '7 to 1':
            temp.append('1 to 7')

        if label[i] == '2 to 3' or label[i] == '3 to 2':
            temp.append('2 to 3')
        if label[i] == '2 to 4' or label[i] == '4 to 2':
            temp.append('2 to 4')
        if label[i] == '2 to 5' or label[i] == '5 to 2':
            temp.append('2 to 5')           
        if label[i] == '2 to 6' or label[i] == '6 to 2':
            temp.append('2 to 6')
        if label[i] == '2 to 7' or label[i] == '7 to 2':
            temp.append('2 to 7')
           
        if label[i] == '3 to 4' or label[i] == '4 to 3':
            temp.append('3 to 4')
        if label[i] == '3 to 5' or label[i] == '5 to 3':
            temp.append('3 to 5')
        if label[i] == '3 to 6' or label[i] == '6 to 3':
            temp.append('3 to 6')
        if label[i] == '3 to 7' or label[i] == '7 to 3':
            temp.append('3 to 7')            
            
        if label[i] == '4 to 5' or label[i] == '5 to 4':
            temp.append('4 to 5')
        if label[i] == '4 to 6' or label[i] == '6 to 4':
            temp.append('4 to 6')
        if label[i] == '4 to 7' or label[i] == '7 to 4':
            temp.append('4 to 7')

        if label[i] == '5 to 6' or label[i] == '6 to 5':
            temp.append('5 to 6')
        if label[i] == '5 to 7' or label[i] == '7 to 5':
            temp.append('5 to 7')
            
        if label[i] == '6 to 7' or label[i] == '7 to 6':
            temp.append('6 to 7')
                
    return temp

def merge_9_sensors(ila_lablled):
    label = ila_lablled['label'].values.tolist()
    temp=[]
    for i in range(0,len(label)):
        if label[i] == '0 to 1' or label[i] == '1 to 0':
            temp.append('0 to 1')
        if label[i] == '0 to 2' or label[i] == '2 to 0':
            temp.append('0 to 2')
        if label[i] == '0 to 3' or label[i] == '3 to 0':
            temp.append('0 to 3')
        if label[i] == '0 to 4' or label[i] == '4 to 0':
            temp.append('0 to 4')
        if label[i] == '0 to 5' or label[i] == '5 to 0':
            temp.append('0 to 5')           
        if label[i] == '0 to 6' or label[i] == '6 to 0':
            temp.append('0 to 6')
        if label[i] == '0 to 7' or label[i] == '7 to 0':
            temp.append('0 to 7')
        if label[i] == '0 to 8' or label[i] == '8 to 0':
            temp.append('0 to 8')
            
        if label[i] == '1 to 2' or label[i] == '2 to 1':
            temp.append('1 to 2')
        if label[i] == '1 to 3' or label[i] == '3 to 1':
            temp.append('1 to 3')
        if label[i] == '1 to 4' or label[i] == '4 to 1':
            temp.append('1 to 4')
        if label[i] == '1 to 5' or label[i] == '5 to 1':
            temp.append('1 to 5')              
        if label[i] == '1 to 6' or label[i] == '6 to 1':
            temp.append('1 to 6')
        if label[i] == '1 to 7' or label[i] == '7 to 1':
            temp.append('1 to 7')
        if label[i] == '1 to 8' or label[i] == '8 to 1':
            temp.append('1 to 8')

        if label[i] == '2 to 3' or label[i] == '3 to 2':
            temp.append('2 to 3')
        if label[i] == '2 to 4' or label[i] == '4 to 2':
            temp.append('2 to 4')
        if label[i] == '2 to 5' or label[i] == '5 to 2':
            temp.append('2 to 5')           
        if label[i] == '2 to 6' or label[i] == '6 to 2':
            temp.append('2 to 6')
        if label[i] == '2 to 7' or label[i] == '7 to 2':
            temp.append('2 to 7')
        if label[i] == '2 to 8' or label[i] == '8 to 2':
            temp.append('2 to 8')
            
           
        if label[i] == '3 to 4' or label[i] == '4 to 3':
            temp.append('3 to 4')
        if label[i] == '3 to 5' or label[i] == '5 to 3':
            temp.append('3 to 5')
        if label[i] == '3 to 6' or label[i] == '6 to 3':
            temp.append('3 to 6')
        if label[i] == '3 to 7' or label[i] == '7 to 3':
            temp.append('3 to 7')
        if label[i] == '3 to 8' or label[i] == '8 to 3':
            temp.append('3 to 8')
            
            
        if label[i] == '4 to 5' or label[i] == '5 to 4':
            temp.append('4 to 5')
        if label[i] == '4 to 6' or label[i] == '6 to 4':
            temp.append('4 to 6')
        if label[i] == '4 to 7' or label[i] == '7 to 4':
            temp.append('4 to 7')
        if label[i] == '4 to 8' or label[i] == '8 to 4':
            temp.append('4 to 8')

        if label[i] == '5 to 6' or label[i] == '6 to 5':
            temp.append('5 to 6')
        if label[i] == '5 to 7' or label[i] == '7 to 5':
            temp.append('5 to 7')
        if label[i] == '5 to 8' or label[i] == '8 to 5':
            temp.append('5 to 8')
            
        if label[i] == '6 to 7' or label[i] == '7 to 6':
            temp.append('6 to 7')
        if label[i] == '6 to 8' or label[i] == '8 to 6':
            temp.append('6 to 8')
            
        if label[i] == '7 to 8' or label[i] == '8 to 7':
            temp.append('8 to 7')
                
    return temp


def merge_10_sensors(ila_lablled):
    label = ila_lablled['label'].values.tolist()
    temp=[]
    for i in range(0,len(label)):
        if label[i] == '0 to 1' or label[i] == '1 to 0':
            temp.append('0 to 1')
        if label[i] == '0 to 2' or label[i] == '2 to 0':
            temp.append('0 to 2')
        if label[i] == '0 to 3' or label[i] == '3 to 0':
            temp.append('0 to 3')
        if label[i] == '0 to 4' or label[i] == '4 to 0':
            temp.append('0 to 4')
        if label[i] == '0 to 5' or label[i] == '5 to 0':
            temp.append('0 to 5')           
        if label[i] == '0 to 6' or label[i] == '6 to 0':
            temp.append('0 to 6')
        if label[i] == '0 to 7' or label[i] == '7 to 0':
            temp.append('0 to 7')
        if label[i] == '0 to 8' or label[i] == '8 to 0':
            temp.append('0 to 8')
        if label[i] == '0 to 9' or label[i] == '9 to 0':
            temp.append('0 to 9')

        if label[i] == '1 to 2' or label[i] == '2 to 1':
            temp.append('1 to 2')
        if label[i] == '1 to 3' or label[i] == '3 to 1':
            temp.append('1 to 3')
        if label[i] == '1 to 4' or label[i] == '4 to 1':
            temp.append('1 to 4')
        if label[i] == '1 to 5' or label[i] == '5 to 1':
            temp.append('1 to 5')              
        if label[i] == '1 to 6' or label[i] == '6 to 1':
            temp.append('1 to 6')
        if label[i] == '1 to 7' or label[i] == '7 to 1':
            temp.append('1 to 7')
        if label[i] == '1 to 8' or label[i] == '8 to 1':
            temp.append('1 to 8')
        if label[i] == '1 to 9' or label[i] == '9 to 1':
            temp.append('1 to 9')

        if label[i] == '2 to 3' or label[i] == '3 to 2':
            temp.append('2 to 3')
        if label[i] == '2 to 4' or label[i] == '4 to 2':
            temp.append('2 to 4')
        if label[i] == '2 to 5' or label[i] == '5 to 2':
            temp.append('2 to 5')           
        if label[i] == '2 to 6' or label[i] == '6 to 2':
            temp.append('2 to 6')
        if label[i] == '2 to 7' or label[i] == '7 to 2':
            temp.append('2 to 7')
        if label[i] == '2 to 8' or label[i] == '8 to 2':
            temp.append('2 to 8')
        if label[i] == '2 to 9' or label[i] == '9 to 2':
            temp.append('2 to 9')           
           
        if label[i] == '3 to 4' or label[i] == '4 to 3':
            temp.append('3 to 4')
        if label[i] == '3 to 5' or label[i] == '5 to 3':
            temp.append('3 to 5')
        if label[i] == '3 to 6' or label[i] == '6 to 3':
            temp.append('3 to 6')
        if label[i] == '3 to 7' or label[i] == '7 to 3':
            temp.append('3 to 7')
        if label[i] == '3 to 8' or label[i] == '8 to 3':
            temp.append('3 to 8')
        if label[i] == '3 to 9' or label[i] == '9 to 3':
            temp.append('3 to 9')
            
        if label[i] == '4 to 5' or label[i] == '5 to 4':
            temp.append('4 to 5')
        if label[i] == '4 to 6' or label[i] == '6 to 4':
            temp.append('4 to 6')
        if label[i] == '4 to 7' or label[i] == '7 to 4':
            temp.append('4 to 7')
        if label[i] == '4 to 8' or label[i] == '8 to 4':
            temp.append('4 to 8')
        if label[i] == '4 to 9' or label[i] == '9 to 4':
            temp.append('4 to 9')

        if label[i] == '5 to 6' or label[i] == '6 to 5':
            temp.append('5 to 6')
        if label[i] == '5 to 7' or label[i] == '7 to 5':
            temp.append('5 to 7')
        if label[i] == '5 to 8' or label[i] == '8 to 5':
            temp.append('5 to 8')
        if label[i] == '5 to 9' or label[i] == '9 to 5':
            temp.append('5 to 9')
            
        if label[i] == '6 to 7' or label[i] == '7 to 6':
            temp.append('6 to 7')
        if label[i] == '6 to 8' or label[i] == '8 to 6':
            temp.append('6 to 8')
        if label[i] == '6 to 9' or label[i] == '9 to 6':
            temp.append('6 to 9')
            
        if label[i] == '7 to 8' or label[i] == '8 to 7':
            temp.append('8 to 7')
        if label[i] == '7 to 9' or label[i] == '9 to 7':
            temp.append('7 to 9')

        if label[i] == '8 to 9' or label[i] == '9 to 8':
            temp.append('8 to 9')
                
    return temp
