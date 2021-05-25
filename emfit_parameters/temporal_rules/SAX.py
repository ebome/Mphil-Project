import numpy as np
import math
 
class SAX_trans:
    
    def __init__(self, ts, w, alpha):
        self.ts = ts
        self.w = w
        self.alpha = alpha
        self.aOffset = ord('a') # the alphabet starts from a
        self.breakpoints = {'3' : [-0.43, 0.43],
                            '4' : [-0.67, 0, 0.67],
                            '5' : [-0.84, -0.25, 0.25, 0.84],
                            '6' : [-0.97, -0.43, 0, 0.43, 0.97],
                            '7' : [-1.07, -0.57, -0.18, 0.18, 0.57, 1.07],
                            '8' : [-1.15, -0.67, -0.32, 0, 0.32, 0.67, 1.15],
            
        }
        self.beta = self.breakpoints[str(self.alpha)]
        
    def normalize(self):  
        X = np.asanyarray(self.ts)
        return (X - np.nanmean(X)) / np.nanstd(X)
 
    def paa_trans(self):  
        tsn = self.normalize() # you can also use SAX_trans.normalize(self) to call self
        paa_ts = []
        n = len(tsn)
        xk = math.ceil( n / self.w )  # math.ceil() rounds up, int() round down
        for i in range(0,n,xk):
            temp_ts = tsn[i:i+xk]
            paa_ts.append(np.mean(temp_ts))
            i = i + xk
        return paa_ts
    
    def to_sax(self):   # convert to SAX str representation
        tsn = self.paa_trans()
        len_tsn = len(tsn)
        len_beta = len(self.beta)
        strx = ''
        for i in range(len_tsn):
            letter_found = False
            for j in range(len_beta):
                if np.isnan(tsn[i]):
                    strx += '-'
                    letter_found = True
                    break                   
                if tsn[i] < self.beta[j]:
                    strx += chr(self.aOffset +j)
                    letter_found = True
                    break
            if not letter_found:
                strx += chr(self.aOffset + len_beta)
        return strx
    
    
    def compare_Dict(self):   
        num_rep = range(self.alpha) 
        letters = [chr(x + self.aOffset) for x in num_rep]   
        compareDict = {}
        len_letters = len(letters)
        for i in range(len_letters):
            for j in range(len_letters):
                if np.abs(num_rep[i] - num_rep[j])<=1:
                    compareDict[letters[i]+letters[j]]=0
                else:
                    high_num = np.max([num_rep[i], num_rep[j]])-1
                    low_num = np.min([num_rep[i], num_rep[j]])
                    compareDict[letters[i]+letters[j]] = self.beta[high_num] - self.beta[low_num]
        return compareDict
   
    def dist(self, strx1,strx2):
        len_strx1 = len(strx1)
        len_strx2 = len(strx2)
        com_dict = self.compare_Dict()
 
        if len_strx1 != len_strx2:
            print("The length of the two strings does not match")
        else:
            list_letter_strx1 = [x for x in strx1]
            list_letter_strx2 = [x for x in strx2]
            mindist = 0.0
            for i in range(len_strx1):
                if list_letter_strx1[i] != '-' and list_letter_strx2[i] != '-':
                    mindist += (com_dict[list_letter_strx1[i] + list_letter_strx2[i]])**2
            mindist = np.sqrt((len(self.ts)*1.0)/ (self.w*1.0)) * np.sqrt(mindist)
            return mindist
  
                    
