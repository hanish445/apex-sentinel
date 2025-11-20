import fastf1 as ff1
import pandas as pd
import os


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
