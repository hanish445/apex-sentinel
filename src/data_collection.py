import fastf1 as ff1
import pandas as pd
import os
import argparse
from datetime import timedelta

def collect_telemetry_data(year, grand_prix, session_type, driver, output_dir='data'):
    print(f"--- [v2.5] Loading {year} {grand_prix} ({session_type}) for {driver} ---")

    # Setup cache
    cache_path = os.path.join(output_dir, 'ff1_cache')
    os.makedirs(cache_path, exist_ok=True)
    ff1.Cache.enable_cache(cache_path)

    try:
        # 1. Load Session
        session = ff1.get_session(year, grand_prix, session_type)
        session.load()

        # 2. Get All Laps (for benchmarks)
        all_laps = session.laps
        driver_laps = all_laps.pick_driver(driver)

        # 3. Get The Specific Lap to Replay (Fastest Lap)
        try:
            target_lap = driver_laps.pick_fastest()
        except KeyError:
            return None, f"Driver '{driver}' not found.", None

        if target_lap is None or pd.isna(target_lap.LapTime):
            return None, f"No valid lap time found for driver '{driver}'.", None

        # --- SECTOR PERFORMANCE ANALYSIS ---
        # Benchmarks (purple/green)
        pb_s1 = all_laps['Sector1Time'].min()
        pb_s2 = all_laps['Sector2Time'].min()
        pb_s3 = all_laps['Sector3Time'].min()

        db_s1 = driver_laps['Sector1Time'].min()
        db_s2 = driver_laps['Sector2Time'].min()
        db_s3 = driver_laps['Sector3Time'].min()

        cur_s1 = target_lap['Sector1Time']
        cur_s2 = target_lap['Sector2Time']
        cur_s3 = target_lap['Sector3Time']

        # [FIXED] Robust Color Logic
        def get_sector_color(current, session_best, personal_best):
            # Check ALL inputs for NaT (Not a Time) or None
            if pd.isna(current) or pd.isna(session_best) or pd.isna(personal_best):
                return '#fff200' # Default to Yellow if any data is missing

            try:
                # Convert to Seconds (Float) for Safe Comparison
                def to_sec(val):
                    if isinstance(val, pd.Timedelta): return val.total_seconds()
                    return float(val)

                cur_sec = to_sec(current)
                sb_sec = to_sec(session_best)
                pb_sec = to_sec(personal_best)

                tol = 0.001 # Tolerance

                if cur_sec <= (sb_sec + tol):
                    return '#b124e8' # PURPLE (Session Best)
                elif cur_sec <= (pb_sec + tol):
                    return '#00ff00' # GREEN (Personal Best)
                else:
                    return '#fff200' # YELLOW (No Improvement)
            except:
                return '#fff200' # Fallback to Yellow on any math error

        colors = {
            "s1": get_sector_color(cur_s1, pb_s1, db_s1),
            "s2": get_sector_color(cur_s2, pb_s2, db_s2),
            "s3": get_sector_color(cur_s3, pb_s3, db_s3)
        }

        print(f"Sector Analysis: {colors}")

        # 4. Get Telemetry & GPS
        telemetry = target_lap.get_car_data().add_distance()
        pos_data = target_lap.get_pos_data()

        merged_data = pd.merge_asof(
            telemetry,
            pos_data[['Time', 'X', 'Y', 'Z']],
            on='Time',
            direction='nearest'
        )

        # 5. Extract Real Boundaries
        t_s1 = target_lap['Sector1Time']
        t_s2 = target_lap['Sector2Time']

        # Calculate Distances for Sector Lines
        # Use simple fallback if t_s1 is NaT
        if pd.isna(t_s1): t_s1 = pd.Timedelta(seconds=30)
        if pd.isna(t_s2): t_s2 = pd.Timedelta(seconds=30)

        s1_row = merged_data.iloc[(merged_data['Time'] - t_s1).abs().argsort()[:1]]
        s1_dist = s1_row['Distance'].values[0] if not s1_row.empty else 0

        s2_row = merged_data.iloc[(merged_data['Time'] - (t_s1 + t_s2)).abs().argsort()[:1]]
        s2_dist = s2_row['Distance'].values[0] if not s2_row.empty else 0

        total_dist = merged_data['Distance'].max()

        sector_info = {
            "s1_end": float(s1_dist),
            "s2_end": float(s2_dist),
            "track_length": float(total_dist),
            "colors": colors
        }

        # 6. Clean Up
        required_columns = ['Time', 'Distance', 'Speed', 'RPM', 'Throttle', 'Brake', 'nGear', 'DRS', 'X', 'Y', 'Z']
        final_df = merged_data[required_columns].copy()

        return final_df, None, sector_info

    except Exception as e:
        print(f"An error occurred: {e}")
        return None, str(e), None

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, default=2023)
    parser.add_argument("--gp", type=str, default="Bahrain")
    parser.add_argument("--session", type=str, default="R")
    parser.add_argument("--driver", type=str, default="PER")
    args = parser.parse_args()

    df, err, sec = collect_telemetry_data(args.year, args.gp, args.session, args.driver)
    if df is not None:
        print("Data Loaded Successfully")
        print(sec)