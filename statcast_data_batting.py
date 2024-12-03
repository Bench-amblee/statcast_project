import pandas as pd
from pybaseball import statcast
from datetime import datetime

# Define the date range you want to pull data for
start_date = "2023-03-30"  # Adjust for your desired start date
end_date = "2023-10-01"    # Adjust for your desired end date

# Pull the statcast data for the specified date range
df = statcast(start_date, end_date)

# Convert game_date to datetime
df['game_date'] = pd.to_datetime(df['game_date'])

# Define bins for launch_speed (exit velocity) and launch_angle
launch_speed_bins = [0, 80, 90, 100, 110, float('inf')]
launch_angle_bins = [-90, -15, 0, 15, 45, float('inf')]

# Create categories for launch speed and launch angle
df['launch_speed_bucket'] = pd.cut(df['launch_speed'], bins=launch_speed_bins, labels=['<80', '80-90', '90-100', '100-110', '>110'])
df['launch_angle_bucket'] = pd.cut(df['launch_angle'], bins=launch_angle_bins, labels=['Downward', 'Ground Ball', 'Line Drive', 'Fly Ball', 'High Fly'])

# Filter for batting events (e.g., hits, walks, strikeouts)
batting_events = ['single', 'double', 'triple', 'home_run', 'walk', 'strikeout']
df_batting = df[df['events'].isin(batting_events)]

# Group by team and game date
aggregated_data = df_batting.groupby(['home_team', 'game_date']).agg({
    'events': 'count',  # Total plate appearances (events)
    'hit_location': lambda x: x.value_counts().to_dict(),  # Count of each hit location
    'bb_type': lambda x: x.value_counts().to_dict(),  # Count of each batted ball type
    'launch_speed': lambda x: pd.cut(x, launch_speed_bins).value_counts().to_dict(),  # Launch speed buckets
    'launch_angle': lambda x: pd.cut(x, launch_angle_bins).value_counts().to_dict(),  # Launch angle buckets
    'estimated_ba_using_speedangle': 'mean',  # Average estimated BA
    'estimated_woba_using_speedangle': 'mean',  # Average wOBA
    'woba_value': 'sum',  # Total wOBA value for the game
    'babip_value': 'sum',  # Total BABIP value
    'iso_value': 'sum',  # Total ISO value
}).reset_index()

# Save to CSV
aggregated_data.to_csv('batting_aggregated_data.csv', index=False)

print("Aggregated batting data saved successfully!")