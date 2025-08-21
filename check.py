import seaborn as sns
import pandas as pd
import matplotlib.pyplot as plt

# Load dataset
df = pd.read_csv('data/datasets/dataset.csv')

# Clean Protocol column
df['Protocol'] = df['Protocol'].str.strip()
df['Protocol'] = df['Protocol'].astype('category')

# Pairplot
print(df['Protocol'].value_counts())

sns.pairplot(df, hue='Protocol',
             vars=['NumNodes','NodeSpeed','PauseTime','TxRange','TrafficLoad','SimTime'],
             palette="Set1")   # better colors
plt.show()
