import peak_shaving as ps
from concurrent.futures import ProcessPoolExecutor, as_completed
import pandas as pd

def simulate_combo(df, peak_limit_kW, combo):
    capacity, power = combo
    soc_df = ps.simulate_battery_soc(df, peak_limit_kW, capacity, power)

    # Beregn faktisk effekt etter batteriets bidrag
    power_after = soc_df['power_kW'] - soc_df['discharge_power_kW']

    # Identifiser alle topp-punkter over grensen
    peak_events = soc_df['power_kW'] > peak_limit_kW

    # Udekkede topper er de der batteriet ikke klarer å redusere under grensen
    unmet = power_after > peak_limit_kW

    # Beregn andelen udekkede topper
    unmet_fraction = (unmet & peak_events).sum() / peak_events.sum() * 100 if peak_events.sum() > 0 else 0

    return {
        "battery_capacity_kWh": capacity,
        "max_power_kW": power,
        "unmet_peak_fraction": round(unmet_fraction, 1)
    }



def run_parallel_simulations(df: pd.DataFrame, peak_limit_kW: float, combinations: list[tuple[int, int]], progress_callback=None):
    results = []
    with ProcessPoolExecutor() as executor:
        futures = [executor.submit(simulate_combo, df, peak_limit_kW, combo) for combo in combinations]
        for i, future in enumerate(as_completed(futures)):
            try:
                result = future.result()
                if isinstance(result, dict) and all(k in result for k in ["battery_capacity_kWh", "max_power_kW", "unmet_peak_fraction"]):
                    results.append(result)
                else:
                    print(f"Advarsel: Ugyldig resultat for kombinasjon {combinations[i]}: {result}")
            except Exception as e:
                print(f"Feil i simulering for kombinasjon {combinations[i]}: {e}")
            if progress_callback:
                progress_callback(i + 1, len(combinations))

    if not results:
        raise ValueError("Ingen gyldige resultater fra simuleringene.")

    return pd.DataFrame(results)
