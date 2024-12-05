import pandas as pd
import streamlit as st
from pybaseball import statcast
from datetime import datetime
import time

# Streamlit UI setup
st.title("Refined Statcast Data")

# Date range selection
start_date = st.date_input("Start Date", datetime(2023, 3, 30))
end_date = st.date_input("End Date", datetime(2023, 11, 1))

# Team selection (multiple teams)
teams = ['ATL','AZ','BAL','BOS',
         'CHC','CIN','CLE','COL','CWS',
         'DET','HOU','KC','LAA','LAD',
         'MIA','MIL','MIN','NYM','NYY',
         'OAK','PHI','PIT','SD','SEA',
         'SF','STL','TB','TEX','TOR','WSH']
home_teams = st.multiselect("Select Home Teams", options=teams)

# Function to load and filter the data based on user input
def load_and_process_data(start_date, end_date, home_teams):
    # Convert dates to strings
    start_date_str = start_date.strftime('%Y-%m-%d')
    end_date_str = end_date.strftime('%Y-%m-%d')

    # Pull the Statcast data
    df = statcast(start_date_str, end_date_str)

    # Add a season column
    df['season'] = pd.to_datetime(df['game_date']).dt.year

    # Rename hit_distance to hit_distance_sc
    df.rename(columns={'hit_distance': 'hit_distance_sc'}, inplace=True)

    # Define bins
    bins = {
        'release_speed': [0, 80, 90, 100, 110, float('inf')],
        'launch_speed': [0, 80, 90, 100, 110, float('inf')],
        'launch_angle': [-90, -15, 0, 15, 45, float('inf')],
        'woba_value': [0, 0.2, 0.4, 0.6, 0.8, 1],
        'babip_value': [0, 0.2, 0.4, 0.6, 0.8, 1],
        'iso_value': [0, 0.2, 0.4, 0.6, 0.8, 1],
        'hit_distance_sc': [0, 150, 250, 350, float('inf')],
    }

    bin_labels = {
        'release_speed': ['<80', '80-90', '90-100', '100-110', '>110'],
        'launch_speed': ['<80', '80-90', '90-100', '100-110', '>110'],
        'launch_angle': ['Downward', 'Ground Ball', 'Line Drive', 'Fly Ball', 'High Fly'],
        'woba_value': ['Low', 'Below Average', 'Average', 'Above Average', 'High'],
        'babip_value': ['Low', 'Below Average', 'Average', 'Above Average', 'High'],
        'iso_value': ['Low', 'Below Average', 'Average', 'Above Average', 'High'],
        'hit_distance_sc': ['<150', '150-250', '250-350', '>350'],
    }

    # Apply binning
    for metric, bin_ranges in bins.items():
        if metric in df.columns:
            df[f'{metric}_bucket'] = pd.cut(df[metric], bins=bin_ranges, labels=bin_labels[metric])

    # Filter by home teams selected
    if home_teams:
        df = df[df['home_team'].isin(home_teams)]

    # Aggregate data at the game level
    agg_functions = {
        'pitch_type': lambda x: x.value_counts().to_dict(),
        'bb_type': lambda x: x.value_counts().to_dict(),
        'hit_location': lambda x: x.value_counts().to_dict(),
        'release_speed_bucket': lambda x: x.value_counts().to_dict(),
        'launch_speed_bucket': lambda x: x.value_counts().to_dict(),
        'launch_angle_bucket': lambda x: x.value_counts().to_dict(),
        'woba_value_bucket': lambda x: x.value_counts().to_dict(),
        'babip_value_bucket': lambda x: x.value_counts().to_dict(),
        'iso_value_bucket': lambda x: x.value_counts().to_dict(),
        'hit_distance_sc_bucket': lambda x: x.value_counts().to_dict(),
        'release_pos_x': 'mean',
        'release_pos_z': 'mean',
        'estimated_ba_using_speedangle': 'mean',
        'estimated_woba_using_speedangle': 'mean',
    }

    grouped = df.groupby(['season', 'game_date', 'home_team', 'away_team']).agg(agg_functions).reset_index()

    # Reshape data into a tall/narrow format
    final_data = grouped.melt(
        id_vars=['season', 'game_date', 'home_team', 'away_team'],
        var_name='metric_name',
        value_name='metric_value'
    )

    # Add metric type
    metric_types = {
        'pitch_type': 'Pitching',
        'release_speed_bucket': 'Pitching',
        'bb_type': 'Batting',
        'launch_speed_bucket': 'Batting',
        'launch_angle_bucket': 'Batting',
        'woba_value_bucket': 'Batting',
        'babip_value_bucket': 'Batting',
        'iso_value_bucket': 'Batting',
        'hit_distance_sc_bucket': 'Batting',
        'hit_location': 'Pitching',
        'release_pos_x': 'Pitching',
        'release_pos_z': 'Pitching',
        'estimated_ba_using_speedangle': 'Batting',
        'estimated_woba_using_speedangle': 'Batting',
    }

    final_data['metric_type'] = final_data['metric_name'].map(metric_types)

    return final_data

# Run when the button is pressed
if st.button("Generate Report"):
    st.write(f"Filtering data from {start_date} to {end_date} for teams: {home_teams}")
    
    # Add spinner to show loading process
    with st.spinner('Loading data...'):
        # Show a progress bar while data is processing
        progress_bar = st.progress(0)
        
        # Simulate long processing time for demonstration purposes
        for i in range(10):
            time.sleep(0.3)  # Simulate some work (replace with actual work)
            progress_bar.progress((i + 1) * 10)  # Update progress bar

        # Actually load and process data
        data = load_and_process_data(start_date, end_date, home_teams)
    
    # Store the processed data in session state
    st.session_state.data = data
    st.session_state.processed = True  # Mark as processed

    st.write("Data loaded successfully!")

# If data has been processed, allow the user to download it
if 'data' in st.session_state and st.session_state.processed:
    # Format the filename to include start and end dates
    filename = f"statcast_data_{start_date.strftime('%Y-%m-%d')}_to_{end_date.strftime('%Y-%m-%d')}.csv"
    
    # Convert data to CSV
    csv_data = st.session_state.data.to_csv(index=False)
    
    # Provide download button with the dynamically generated filename
    st.download_button("Download CSV", csv_data, filename, "text/csv")

    # Option to clear data and re-run the query
    if st.button("Clear Data"):
        # Reset session state to allow re-querying
        del st.session_state.data
        st.session_state.processed = False
        st.write("Data has been cleared. You can now re-run the query.")