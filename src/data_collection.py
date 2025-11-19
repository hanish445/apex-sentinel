import fastf1 as ff1
import pandas as pd
import os

def collect_telemetry_data(year, grand_prix, session_type, driver, output_dir='data'):
    """
    Collects and saves telemetry data for a specific driver's fastest lap
    during a given F1 session.

    Args:
        year (int): The year of the race.
        grand_prix (str): The name of the Grand Prix (e.g., 'Bahrain').
        session_type (str): The session to analyze (e.g., 'R' for Race, 'Q' for Qualifying).
        driver (str): The three-letter abbreviation for the driver (e.g., 'VER').
        output_dir (str): The directory to save the output CSV file.
    """
    print(f"--- Starting Data Collection for {year} {grand_prix} Grand Prix ---")

    # Setup cache to avoid re-downloading data
    cache_path = os.path.join(output_dir, 'ff1_cache')
    if not os.path.exists(cache_path):
        os.makedirs(cache_path)
    ff1.Cache.enable_cache(cache_path)
    print(f"FastF1 cache enabled at: {cache_path}")

    # Load the session data
    print(f"Loading session: {year} {grand_prix} {session_type}...")
    session = ff1.get_session(year, grand_prix, session_type)
    session.load()
    print("Session loaded successfully.")

    # Get the fastest lap for the specified driver
    print(f"Fetching fastest lap for driver {driver}...")
    fastest_lap = session.laps.pick_driver(driver).pick_fastest()

    if fastest_lap is None or pd.isna(fastest_lap.LapTime):
        print(f"Could not find a valid fastest lap for driver {driver}. Exiting.")
        return

    print(f"Fastest lap found: {fastest_lap.LapTime}")

    # Get telemetry data for the lap
    print("Fetching telemetry data for the lap...")
    telemetry = fastest_lap.get_car_data().add_distance()
    print("Telemetry data fetched.")

    # Define output file path
    output_filename = os.path.join(output_dir, 'telemetry_data.csv')

    # Save the data to a CSV file
    print(f"Saving telemetry data to {output_filename}...")
    telemetry.to_csv(output_filename, index=False)

    print("--- Data Collection Finished ---")
    print(f"Telemetry for {driver}'s fastest lap at the {year} {grand_prix} GP saved successfully.")


if __name__ == "__main__":
    # --- Configuration ---
    RACE_YEAR = 2023
    GRAND_PRIX = 'Bahrain'
    SESSION_TYPE = 'R'  # 'R' for Race
    DRIVER_ABBR = 'VER' # Max Verstappen

    collect_telemetry_data(
        year=RACE_YEAR,
        grand_prix=GRAND_PRIX,
        session_type=SESSION_TYPE,
        driver=DRIVER_ABBR
    )