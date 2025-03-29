import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Please Load the CSV file for a specific player, e.g., "player_1_behavior_log.csv" or "3_behavior_log.csv"
df=pd.read_csv('3_behavior_log.csv')

# Filter data so it is clearly visualized in the heatmap
df_filtered=df[df['player_y'] >= 669]

heatmap,xedges,yedges=np.histogram2d(df_filtered['player_x'],df_filtered['player_y'],bins=50)
extent=[xedges[0],xedges[-1],yedges[0],yedges[-1]]

plt.figure()
plt.imshow(heatmap.T,extent=extent,origin='lower',aspect='auto',cmap='hot')
plt.colorbar(label='Frequency')
plt.xlabel('Player X Position')
plt.ylabel('Player Y Position')
plt.title('Heatmap of Player Positions (Y >= 400)')
plt.show()

action_to_key={
    '1': "Move (A/D)",
    '2': "Jump (W)",
    '3': "Attack1 (R)",
    '4': "Attack2 (T)"}

df['key']=df['action'].astype(str).map(action_to_key)

df_keys=df.dropna(subset=['key']) #filter out rows that are not mapped like idle (0), hit (5), death (6)

key_counts=df_keys['key'].value_counts()

plt.figure()
key_counts.plot(kind='bar')
plt.xlabel('Key Press')
plt.ylabel('Frequency')
plt.title('Preferred Moves by Frequency')
plt.show()
