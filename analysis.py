import os
import glob
import pandas as pd
import peak_shaving as ps
from simulation import run_parallel_simulations
from utils import get_simulation_combinations

def run_analysis(
    folder_path: str,
    output_path: str,
    peak_fraction: float = 0.6,
    profile: str = "Medium",
    progress_callback=None,
    save_figures=False,
    capacities: list[int] = None,
    powers: list[int] = None,
    manual_peak_kW: float = None
):
    # 1. Last inn Excel-filer
    excel_files = glob.glob(os.path.join(folder_path, "*.xlsx"))
    if not excel_files:
        raise FileNotFoundError("Ingen Excel-filer funnet i valgt mappe.")

    dfs = [ps.load_data(file) for file in excel_files]
    df_all = pd.concat(dfs, ignore_index=True)

    # 2. Beregn peak-grense
    max_peak = df_all['power_kW'].max()
    peak_limit_kW = manual_peak_kW if manual_peak_kW is not None else max_peak * peak_fraction

    # 3. Utfør peak shaving
    df_all = ps.calculate_peak_shaving(df_all, peak_limit_kW)
    combinations = get_simulation_combinations(profile, capacities, powers)

    # 4. Simuler kombinasjoner
    evaluation_grid = run_parallel_simulations(df_all, peak_limit_kW, combinations, progress_callback)

    # 5. Valider resultater
    expected_cols = {"battery_capacity_kWh", "max_power_kW", "unmet_peak_fraction"}
    actual_cols = set(evaluation_grid.columns)
    if not expected_cols.issubset(actual_cols):
        raise ValueError(
            f"Feil i resultater fra simulering: forventet kolonner {expected_cols}, men fikk {actual_cols}"
        )

    # 6. Evaluer og finn optimal
    pivoted = ps.pivot_evaluation_results(evaluation_grid)
    acceptable = evaluation_grid[evaluation_grid["unmet_peak_fraction"] <= 2.5]
    optimal = acceptable.sort_values(by=["battery_capacity_kWh", "max_power_kW"]).head(1)

    df_opt = pd.DataFrame()
    fig_soc = None
    fig_heatmap = None

    if not optimal.empty:
        opt_capacity = optimal.iloc[0]['battery_capacity_kWh']
        opt_power = optimal.iloc[0]['max_power_kW']
        df_opt = ps.simulate_battery_soc(df_all, peak_limit_kW, opt_capacity, opt_power)

        if save_figures:
            fig_soc = ps.plot_soc(df_opt, opt_capacity)

    if save_figures:
        fig_heatmap = ps.plot_evaluation_heatmap(pivoted)

    # 7. Lagre Excel-resultater
    with pd.ExcelWriter(output_path) as writer:
        df_all.to_excel(writer, sheet_name="All data", index=False)
        if not df_opt.empty:
            df_opt.to_excel(writer, sheet_name="Optimal SoC", index=False)
        evaluation_grid.to_excel(writer, sheet_name="Evaluering", index=False)
        pivoted.to_excel(writer, sheet_name="Heatmap", index=True)

    # 8. Returnér resultater + figurer
    return {
        "max_peak_kW": round(max_peak, 1),
        "used_peak_limit_kW": round(peak_limit_kW, 1),
        "optimal_config": optimal.to_dict(orient="records")[0] if not optimal.empty else None,
        "soc_fig": fig_soc,
        "heatmap_fig": fig_heatmap
    }
