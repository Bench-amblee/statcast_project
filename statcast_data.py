# statcast_data v1 - working

import pandas as pd
from pybaseball import batting_stats, pitching_stats

def get_batting_stats(season):
    """Retrieve and prepare offensive metrics for all teams in a given season."""
    batting = batting_stats(season)
    # Aggregate offensive metrics
    team_batting = batting.groupby('Team').agg({
        'R': 'sum',    # Runs
        'H': 'sum',    # Hits
        'HR': 'sum',   # Home runs
        'BB': 'sum',   # Walks
        'SO': 'sum',   # Strikeouts
        'AVG': 'mean', # Batting average
        'OBP': 'mean', # On-base percentage
        'SLG': 'mean', # Slugging percentage
    }).reset_index()

    # Transform into long format
    long_batting = pd.melt(
        team_batting,
        id_vars=['Team'],
        var_name='Metric Name',
        value_name='Value'
    )
    long_batting['Metric Type'] = 'Offensive'
    long_batting['Season'] = season
    return long_batting

def get_pitching_stats(season):
    """Retrieve and prepare defensive metrics for all teams in a given season."""
    pitching = pitching_stats(season)
    # Aggregate defensive metrics
    team_pitching = pitching.groupby('Team').agg({
        'ERA': 'mean',   # Earned Run Average
        'WHIP': 'mean',  # Walks and Hits per Inning Pitched
        'SO': 'sum',     # Strikeouts by pitchers
        'BB': 'sum',     # Walks allowed
        'HR': 'sum',     # Home runs allowed
    }).reset_index()

    # Transform into long format
    long_pitching = pd.melt(
        team_pitching,
        id_vars=['Team'],
        var_name='Metric Name',
        value_name='Value'
    )
    long_pitching['Metric Type'] = 'Defensive'
    long_pitching['Season'] = season
    return long_pitching

def get_player_stats(season):
    """Retrieve and prepare player-level offensive and defensive metrics."""
    batting = batting_stats(season)
    pitching = pitching_stats(season)

    # Offensive player stats
    player_batting = batting.groupby(['Name']).agg({
        'R': 'sum',
        'H': 'sum',
        'HR': 'sum',
        'BB': 'sum',
        'SO': 'sum',
        'AVG': 'mean',
        'OBP': 'mean',
        'SLG': 'mean',
    }).reset_index()

    long_player_batting = pd.melt(
        player_batting,
        id_vars=['Name'],
        var_name='Metric Name',
        value_name='Value'
    )
    long_player_batting['Metric Type'] = 'Offensive'
    long_player_batting['Season'] = season

    # Defensive player stats
    player_pitching = pitching.groupby(['Name']).agg({
        'ERA': 'mean',
        'WHIP': 'mean',
        'SO': 'sum',
        'BB': 'sum',
        'HR': 'sum',
    }).reset_index()

    long_player_pitching = pd.melt(
        player_pitching,
        id_vars=['Name'],
        var_name='Metric Name',
        value_name='Value'
    )
    long_player_pitching['Metric Type'] = 'Defensive'
    long_player_pitching['Season'] = season

    # Combine batting and pitching data
    player_stats = pd.concat([long_player_batting, long_player_pitching], ignore_index=True)
    return player_stats

def combine_and_export(season):
    """Combine offensive and defensive stats for both teams and players, then export as Excel."""
    # Get data for teams
    batting = get_batting_stats(season)
    pitching = get_pitching_stats(season)
    
    # Combine data for teams
    combined_teams = pd.concat([batting, pitching], ignore_index=True)
    combined_teams = combined_teams[['Season', 'Team', 'Metric Type', 'Metric Name', 'Value']]  # Ensure 'Season' is first

    # Get data for players
    player_stats = get_player_stats(season)
    player_stats = player_stats[['Season', 'Name', 'Metric Type', 'Metric Name', 'Value']]  # Ensure 'Season' is first

    # Write data to an Excel file with multiple sheets
    with pd.ExcelWriter(f'statcast_summary_{season}.xlsx', engine='openpyxl') as writer:
        # Export teams data to the first sheet
        combined_teams.to_excel(writer, sheet_name='Teams', index=False)

        # Export players data to the second sheet
        player_stats.to_excel(writer, sheet_name='Players', index=False)

    print(f"Data exported to statcast_summary_{season}.xlsx")

if __name__ == "__main__":
    # Example usage: Export data for the 2023 season
    combine_and_export(2023)