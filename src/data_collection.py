import fastf1 as ff1
import pandas as pd
import os
import argparse

def collect_telemetry_data(year, grand_prix, session_type, driver, output_dir='data'):
    """
    Collects telemetry data for a specific driver's fastest lap.
    Returns a pandas DataFrame or an error message string.
    """
    print(f"--- Starting Data Collection for {year} {grand_prix} GP, Session: {session_type}, Driver: {driver} ---")

    # Setup cache
    cache_path = os.path.join(output_dir, 'ff1_cache')
    os.makedirs(cache_path, exist_ok=True)
    ff1.Cache.enable_cache(cache_path)

    try:
        # Load the session data. This time, we load everything needed.
        session = ff1.get_session(year, grand_prix, session_type)
        session.load()  # This is the key change. The default .load() gets what we need.

        # Get the fastest lap for the specified driver from the loaded session
        fastest_lap = session.laps.pick_driver(driver).pick_fastest()

        if fastest_lap is None or pd.isna(fastest_lap.LapTime):
            return None, f"Could not find a valid fastest lap for driver '{driver}'. Please check the abbreviation and ensure they set a time in that session."

        # Get the telemetry data for this lap. This will now work because the session has loaded it.
        telemetry = fastest_lap.get_car_data().add_distance()

        print("--- Data Collection Finished ---")
        return telemetry, None

    except Exception as e:
        print(f"An error occurred during data collection: {e}")
        return None, f"An error occurred: '{e}'. Please check if the Grand Prix name, year, and session type are correct."

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Download and save F1 telemetry data for a driver's fastest lap.")
    parser.add_argument("--year", type=int, default=2023, help="The championship year.")
    parser.add_argument("--gp", type=str, default="Bahrain", help="The Grand Prix name.")
    parser.add_argument("--session", type=str, default="R", help="The session type (e.g., 'R' for Race, 'Q' for Qualifying).")
    parser.add_argument("--driver", type=str, default="PER", help="The driver's three-letter abbreviation (e.g., 'VER', 'PER').")
    args = parser.parse_args()

    # Define the output directory and ensure it exists
    output_directory = 'data'
    os.makedirs(output_directory, exist_ok=True)
    output_path = os.path.join(output_directory, 'telemetry_data.csv')

    # Collect the data
    telemetry_df, error_msg = collect_telemetry_data(args.year, args.gp, args.session, args.driver)

    if error_msg:
        print(f"Error: {error_msg}")
    elif telemetry_df is not None:
        # Save the data to a CSV file
        telemetry_df.to_csv(output_path, index=False)
        print(f"Telemetry data successfully saved to {output_path}")