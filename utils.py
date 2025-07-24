def get_simulation_combinations(profile: str, capacities=None, powers=None):
    if capacities and powers:
        return [(c, p) for c in capacities for p in powers]

    if profile == "Small":
        capacities = [300, 600, 900]
        powers = [600, 1200, 1800]
    elif profile == "Medium":
        capacities = [200, 400, 600, 800, 1000]
        powers = [400, 800, 1200, 1600, 2000]
    else:  # Large
        step_power = 100
        powers = list(range(100, 1100, step_power))
        capacities = [int(p * 2) for p in powers]

    return [(c, p) for c in capacities for p in powers]



def estimate_runtime(combinations: list[tuple[int, int]], est_time_per_combo=0.15) -> float:
    return len(combinations) * est_time_per_combo
