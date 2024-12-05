import pandas as pd
import streamlit as st
from pybaseball import statcast
from datetime import datetime
import time

# Streamlit UI setup
st.title("Refined Statcast Data")

# Define season start and end dates in a dictionary
season_dates = {
    '2024': {'start': '2024-03-28', 'end': '2024-10-30'},
    '2023': {'start': '2023-03-30', 'end': '2023-11-01'},
    '2022': {'start': '2022-04-07', 'end': '2022-11-05'},
    '2021': {'start': '2021-04-01', 'end': '2021-11-02'},
    '2020': {'start': '2020-07-23', 'end': '2020-10-27'},
    '2019': {'start': '2019-03-28', 'end': '2019-10-30'},
    '2018': {'start': '2018-03-29', 'end': '2018-10-28'},
    '2017': {'start': '2017-04-02', 'end': '2017-11-01'},
    '2016': {'start': '2016-04-03', 'end': '2016-11-02'},
    '2015': {'start': '2015-04-05', 'end': '2015-11-01'},
    '2014': {'start': '2014-03-22', 'end': '2014-10-29'},
    '2013': {'start': '2013-04-01', 'end': '2013-10-30'},
    '2012': {'start': '2012-04-05', 'end': '2012-10-28'},
    '2011': {'start': '2011-03-31', 'end': '2011-10-28'},
    '2010': {'start': '2010-04-04', 'end': '2010-11-01'},
    '2009': {'start': '2009-04-05', 'end': '2009-11-04'},
    '2008': {'start': '2008-03-25', 'end': '2008-10-29'},
    '2007': {'start': '2007-04-01', 'end': '2007-10-28'},
}

# Season selection (multiple seasons)
seasons = list(season_dates.keys())
selected_seasons = st.multiselect("Select Seasons", options=seasons)

# Team selection (multiple teams)
# Team selection (multiple teams)
teams = ['ATL','AZ','BAL','BOS',
         'CHC','CIN','CLE','COL','CWS',
         'DET','HOU','KC','LAA','LAD',
         'MIA','MIL','MIN','NYM','NYY',
         'OAK','PHI','PIT','SD','SEA',
         'SF','STL','TB','TEX','TOR','WSH']

# Checkbox to select all teams
select_all = st.checkbox("Select All Teams")

# If select all is checked, automatically select all teams
if select_all:
    home_teams = teams
else:
    home_teams = st.multiselect("Select Home Teams", options=teams, default=[])

st.write(f"Selected teams: {home_teams}")

# Function to load and filter the data based on user input
def load_and_process_data(seasons, home_teams):
    # Initialize an empty dataframe to collect all data
    all_data = pd.DataFrame()

    # Loop through each selected season and load the data
    for season in seasons:
        start_date_str = season_dates[season]['start']
        end_date_str = season_dates[season]['end']

        # Pull the Statcast data for the selected season
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

        # Append the data from this season to the final dataset
        all_data = pd.concat([all_data, final_data])

    return all_data

# Run when the button is pressed
if st.button("Generate Report"):
    if selected_seasons:
        st.write(f"Filtering data for seasons: {selected_seasons} and teams: {home_teams}")
    
        # Add spinner to show loading process
        with st.spinner('Loading data...'):
            # Actually load and process data
            data = load_and_process_data(selected_seasons, home_teams)
        
        # Store the processed data in session state
        st.session_state.data = data
        st.session_state.processed = True  # Mark as processed

        st.write("Data loaded successfully!")
    else:
        st.error("Please select at least one season.")

# If data has been processed, allow the user to download it
if 'data' in st.session_state and st.session_state.processed:
    # Format the filename to include the seasons
    seasons_str = "_".join(selected_seasons)
    filename = f"statcast_data_seasons_{seasons_str}.csv"
    
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

