import pandas as pd

df = pd.read_csv('1.csv', usecols=[11,12])
d1 = df.iloc[:,0:1]
d2 = df.iloc[:,1:2]
print(d1.values.tolist())
print(d2.values)
