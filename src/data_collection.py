import fastf1 as ff1
import pandas as pd
import os
import argparse

def collect_telemetry_data(year, grand_prix, session_type, driver, output_dir='data'):
    print(f"--- [v2.0] Starting Data Collection for {year} {grand_prix} GP, Session: {session_type}, Driver: {driver} ---")

    # Setup cache
    cache_path = os.path.join(output_dir, 'ff1_cache')
    os.makedirs(cache_path, exist_ok=True)
    ff1.Cache.enable_cache(cache_path)

    try:
        # 1. Load Session
        session = ff1.get_session(year, grand_prix, session_type)
        session.load()

        # 2. Get Fastest Lap
        try:
            fastest_lap = session.laps.pick_driver(driver).pick_fastest()
        except KeyError:
            return None, f"Driver '{driver}' not found in this session."

        if fastest_lap is None or pd.isna(fastest_lap.LapTime):
            return None, f"No valid lap time found for driver '{driver}'."

        # 3. Get Telemetry (Speed, RPM, etc.)
        telemetry = fastest_lap.get_car_data().add_distance()

        # 4. Get Positioning Data (GPS Coordinates X, Y, Z)
        pos_data = fastest_lap.get_pos_data()

        # 5. Synchronize Data Streams
        merged_data = pd.merge_asof(
            telemetry,
            pos_data[['Time', 'X', 'Y', 'Z']],
            on='Time',
            direction='nearest'
        )

        # 6. Clean Up
        required_columns = ['Time', 'Distance', 'Speed', 'RPM', 'Throttle', 'Brake', 'nGear', 'DRS', 'X', 'Y', 'Z']

        final_df = merged_data[required_columns].copy()

        print(f"--- Data Collection Finished. Rows: {len(final_df)} ---")
        return final_df, None

    except Exception as e:
        print(f"An error occurred during data collection: {e}")
        return None, f"An error occurred: '{e}'"

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Download synchronized F1 telemetry & GPS data.")
    parser.add_argument("--year", type=int, default=2023, help="The championship year.")
    parser.add_argument("--gp", type=str, default="Bahrain", help="The Grand Prix name.")
    parser.add_argument("--session", type=str, default="R", help="Session type (R, Q, etc).")
    parser.add_argument("--driver", type=str, default="PER", help="Driver abbreviation.")
    args = parser.parse_args()

    output_directory = 'data'
    os.makedirs(output_directory, exist_ok=True)
    output_path = os.path.join(output_directory, 'telemetry_data.csv')

    df, error_msg = collect_telemetry_data(args.year, args.gp, args.session, args.driver)

    if error_msg:
        print(f"Error: {error_msg}")
    elif df is not None:
        df.to_csv(output_path, index=False)
        print(f"Synchronized Telemetry + GPS data saved to {output_path}")