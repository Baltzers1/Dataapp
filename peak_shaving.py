import pandas as pd
import plotly.graph_objects as go
import numpy as np

def load_data(filepath: str, sheet_name: str = 0) -> pd.DataFrame:
    efficiency = 0.87  # Virkningsgrad fra grid til lader
    df = pd.read_excel(filepath, sheet_name=sheet_name)

    
    df = df.iloc[:, :3]
    df.columns = ['timestamp', 'power_kW', 'active_sessions']

    # Konverter og sorter
    df['power_kW'] = df['power_kW'] / efficiency
    df['timestamp'] = pd.to_datetime(df['timestamp'], format='%d.%m.%Y %H:%M')
    df = df.sort_values('timestamp')

    # Fjern duplikate tidsstempler
    before = len(df)
    df = df.drop_duplicates(subset='timestamp')
    after = len(df)
    

    return df.reset_index(drop=True)


def calculate_peak_shaving(df: pd.DataFrame, peak_limit_kW: float) -> pd.DataFrame:
    df = df.copy()
    df['excess_power_kW'] = df['power_kW'] - peak_limit_kW
    df['excess_power_kW'] = df['excess_power_kW'].apply(lambda x: x if x > 0 else 0)
    df['battery_energy_kWh'] = df['excess_power_kW'] * (5 / 60)
    return df


def simulate_battery_soc(df, peak_limit_kW, battery_capacity_kWh, max_battery_power_kW, max_interval_minutes=10):
    df = df.copy()
    soc = np.full(len(df), battery_capacity_kWh * 0.5)
    soc_min = battery_capacity_kWh * 0.20
    soc_max = battery_capacity_kWh * 0.95

    df['interval_hours'] = df['timestamp'].diff().dt.total_seconds().div(3600).fillna(0)
    max_interval_hours = max_interval_minutes / 60
    df['interval_hours'] = df['interval_hours'].apply(lambda x: min(x, max_interval_hours))

    discharge_power = np.zeros(len(df))
    charge_power = np.zeros(len(df))

    for i in range(1, len(df)):
        power = df["power_kW"].iloc[i]
        interval = df['interval_hours'].iloc[i]

        if power > peak_limit_kW:
            needed_discharge = power - peak_limit_kW
            max_discharge = min(max_battery_power_kW, (soc[i-1] - soc_min) / interval)
            discharge_power[i] = min(needed_discharge, max_discharge)
        else:
            discharge_power[i] = 0

        if power < peak_limit_kW and soc[i-1] < soc_max:
            available_charge_power = min(peak_limit_kW - power, max_battery_power_kW)
            max_charge_power = (soc_max - soc[i-1]) / interval
            charge_power[i] = min(available_charge_power, max_charge_power)
        else:
            charge_power[i] = 0

        soc[i] = soc[i-1] - discharge_power[i] * interval + charge_power[i] * interval
        soc[i] = np.clip(soc[i], soc_min, soc_max)

    df["soc_kWh"] = soc
    df["discharge_power_kW"] = discharge_power
    df["charge_power_kW"] = charge_power

    return df


def evaluate_capacity_and_power_options(df: pd.DataFrame, peak_limit_kW: float,
                                        capacities_kWh: list, power_limits_kW: list) -> pd.DataFrame:
    combinations = []
    for capacity in capacities_kWh:
        for power in power_limits_kW:
            soc_df = simulate_battery_soc(df, peak_limit_kW, capacity, power)

            power_after = soc_df['power_kW'] - soc_df['discharge_power_kW']
            peak_events = soc_df['power_kW'] > peak_limit_kW
            unmet = power_after > peak_limit_kW

            unmet_fraction = (unmet & peak_events).sum() / peak_events.sum() * 100 if peak_events.sum() > 0 else 0

            combinations.append({
                "battery_capacity_kWh": capacity,
                "max_power_kW": power,
                "unmet_peak_fraction": round(unmet_fraction, 1)
            })
    return pd.DataFrame(combinations)





def plot_power_profile(df: pd.DataFrame, peak_limit_kW: float):
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['power_kW'],
        mode='lines',
        name='Original effekt (kW)'
    ))

    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['power_kW'] - df['excess_power_kW'],
        mode='lines',
        name='Etter peak shaving'
    ))

    fig.add_hline(y=peak_limit_kW, line_dash='dash', line_color='red')

    fig.update_layout(
        title="Effektprofil med Peak Shaving",
        xaxis_title="Tid",
        yaxis_title="Effekt (kW)",
        height=450
    )

    return fig


def plot_soc(df: pd.DataFrame, battery_capacity_kWh: float):
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['soc_kWh'],
        mode='lines',
        name='Batteri SoC (kWh)'
    ))

    fig.add_hline(y=battery_capacity_kWh * 0.9, line_dash='dash', line_color='green')
    fig.add_hline(y=battery_capacity_kWh * 0.1, line_dash='dash', line_color='red')

    fig.update_layout(
        title="State of Charge (SoC) over tid",
        xaxis_title="Tid",
        yaxis_title="Energi (kWh)",
        height=400
    )

    return fig



def pivot_evaluation_results(df: pd.DataFrame) -> pd.DataFrame:
    return df.pivot(index="battery_capacity_kWh", columns="max_power_kW", values="unmet_peak_fraction")


def generate_battery_config_space(df: pd.DataFrame, peak_limit_kW: float, step_power=100, step_capacity=100):
    min_power = 100
    max_power = min_power + 900
    power_range = list(range(min_power, max_power + step_power, step_power))
    capacity_range = [int(p * 2) for p in power_range]
    return capacity_range, power_range


import plotly.express as px

def plot_evaluation_heatmap(pivoted_df: pd.DataFrame):
    fig = px.imshow(
        pivoted_df.values,
        x=[str(col) for col in pivoted_df.columns],
        y=[str(row) for row in pivoted_df.index],
        color_continuous_scale="YlGnBu",
        labels={'color': '% Ikke-dekket peak'}
    )

    fig.update_layout(
        title="Heatmap – Andel ikke-dekket peakshaving (%)",
        xaxis_title="Maks batterieffekt (kW)",
        yaxis_title="Batterikapasitet (kWh)",
        height=600
    )

    return fig
