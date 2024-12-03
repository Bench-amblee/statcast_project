import pandas as pd
from pybaseball import statcast

# Define the range of dates for the desired seasons
start_date = "2023-03-30"  # Adjust for your desired start date
end_date = "2023-10-01"    # Adjust for your desired end date

# Fetch Statcast data for the date range
print("Fetching data from Statcast. This might take a while...")
data = statcast(start_dt=start_date, end_dt=end_date)
print("Data fetch complete.")

# Add a "season" column
data["season"] = pd.to_datetime(data["game_date"]).dt.year

# Define pitch speed buckets
def bucket_pitch_speed(speed):
    if pd.isna(speed):
        return "Unknown"
    elif speed < 80:
        return "<80"
    elif 80 <= speed < 90:
        return "80-90"
    elif 90 <= speed < 100:
        return "90-100"
    else:
        return "100+"

# Apply pitch speed buckets
data["speed_bucket"] = data["release_speed"].apply(bucket_pitch_speed)

# Group data by game and team for aggregations
aggregated_data = data.groupby(
    ["season", "game_date", "home_team", "away_team"]
).agg(
    pitch_type_counts=pd.NamedAgg(column="pitch_type", aggfunc=lambda x: x.value_counts().to_dict()),
    speed_bucket_counts=pd.NamedAgg(column="speed_bucket", aggfunc=lambda x: x.value_counts().to_dict()),
    avg_release_speed=pd.NamedAgg(column="release_speed", aggfunc="mean"),
    max_release_speed=pd.NamedAgg(column="release_speed", aggfunc="max"),
    total_pitches=pd.NamedAgg(column="pitch_type", aggfunc="count"),
).reset_index()

# Save to CSV
output_file = "aggregated_statcast_data.csv"
aggregated_data.to_csv(output_file, index=False)
print(f"Aggregated data successfully exported to {output_file}")