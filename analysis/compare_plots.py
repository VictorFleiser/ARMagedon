import json
import math
from collections import defaultdict
import bisect
import statistics
import matplotlib.pyplot as plt
import numpy as np
import os
from statsmodels.nonparametric.smoothers_lowess import lowess
import matplotlib.ticker as ticker
from scipy import stats

# Configuration
DT_SAMPLING = 0.1
BASE_DECAY_RATE_DEFAULT = 0.035
STABILITY_FACTOR_DEFAULT = 0.9

# Log files
adapt_logs = [
    "logs/experimentation/gameplay_logs_Max.jsonl",
    "logs/experimentation/gameplay_logs_H.jsonl",
    "logs/experimentation/gameplay_logs_And.jsonl"
]

noadapt_logs = [
    "logs/experimentation/gameplay_logs_noadapt_30m.jsonl",
    "logs/experimentation/gameplay_logs_noadapt_26m.jsonl"
]

# Helper functions
def effective_decay(letter, success_score, base_decay_rate, stability_factor):
    stability = success_score[letter]
    return base_decay_rate[letter] / (1.0 + stability_factor[letter] * stability)

def decay_value(letter, p0, dt, success_score, base_decay_rate, stability_factor):
    return p0 * math.exp(-effective_decay(letter, success_score, base_decay_rate, stability_factor) * dt)

def record_decay(letter, t0, t1, p_k, times, values, success_score, base_decay_rate, stability_factor):
    if letter not in p_k:
        return
    p0 = p_k[letter]
    t = t0
    while t < t1:
        times[letter].append(t)
        values[letter].append(decay_value(letter, p0, t - t0, success_score, base_decay_rate, stability_factor))
        t += DT_SAMPLING

def process_log(log_file):
    letters_active = set()
    p_k = {}
    success_score = defaultdict(int)
    base_decay_rate = defaultdict(lambda: BASE_DECAY_RATE_DEFAULT)
    stability_factor = defaultdict(lambda: STABILITY_FACTOR_DEFAULT)
    last_update_time = {}
    times = defaultdict(list)
    values = defaultdict(list)
    missiles = {
        "destroyed_no_bomb": [],
        "hit_ground": []
    }

    with open(log_file, "r") as f:
        logs = [json.loads(l) for l in f]

    logs.sort(key=lambda x: x["timestamp"])

    wall_start = logs[0]["timestamp"]
    logical_time = 0.0
    last_wall_time = wall_start
    paused = False

    def advance_time(new_wall_time):
        nonlocal logical_time, last_wall_time
        dt = new_wall_time - last_wall_time
        if not paused:
            logical_time += dt
        last_wall_time = new_wall_time

    for log in logs:
        wall_time = log["timestamp"]
        event = log["event"]
        advance_time(wall_time)

        if event == "game_paused":
            paused = True
            continue
        if event == "game_resumed":
            paused = False
            continue

        if event == "level_transition_started":
            for letter in log.get("new_letters", []):
                letters_active.add(letter)
                p_k[letter] = 0.0
                last_update_time[letter] = logical_time
                times[letter].append(logical_time)
                values[letter].append(0.0)

        if event == "bkt_update":
            letter = log["letter"]
            if letter not in letters_active:
                continue
            record_decay(letter, last_update_time[letter], logical_time, p_k, times, values, success_score, base_decay_rate, stability_factor)
            p_k[letter] = log["p_k"]
            last_update_time[letter] = logical_time
            if "base_decay_rate" in log:
                base_decay_rate[letter] = log["base_decay_rate"]
            if "stability_factor" in log:
                stability_factor[letter] = log["stability_factor"]
            if log.get("outcome") == "correct":
                success_score[letter] += 1
            times[letter].append(logical_time)
            values[letter].append(p_k[letter])

        if event == "missile_destroyed":
            progress = log["progress"]
            if not log.get("bomb_used", False):
                missiles["destroyed_no_bomb"].append((logical_time, progress))

        if event == "missile_hit_ground":
            progress = log["progress"]
            missiles["hit_ground"].append((logical_time, progress))

    for letter in letters_active:
        record_decay(letter, last_update_time[letter], logical_time, p_k, times, values, success_score, base_decay_rate, stability_factor)

    all_letters = sorted(letters_active)
    all_times = sorted(set(t for letter in times for t in times[letter]))

    overall_avg_values = []
    introduced_avg_values = []
    median_values = []
    min_values = []
    std_values = []

    for t in all_times:
        introduced_active_values = []
        overall_active_values = []
        for letter in all_letters:
            if letter in times:
                idx = bisect.bisect_right(times[letter], t) - 1
                if idx >= 0:
                    val = values[letter][idx]
                    introduced_active_values.append(val)
                    overall_active_values.append(val)
                else:
                    overall_active_values.append(0.0)
            else:
                overall_active_values.append(0.0)
        if introduced_active_values:
            introduced_avg_values.append(statistics.mean(introduced_active_values))
            median_values.append(statistics.median(introduced_active_values))
            min_values.append(min(introduced_active_values))
            std_values.append(statistics.stdev(introduced_active_values) if len(introduced_active_values) > 1 else 0)
        else:
            introduced_avg_values.append(0)
            median_values.append(0)
            min_values.append(0)
            std_values.append(0)
        overall_avg_values.append(statistics.mean(overall_active_values))

    return {
        'all_times': all_times,
        'overall_avg': overall_avg_values,
        'introduced_avg': introduced_avg_values,
        'median': median_values,
        'min': min_values,
        'std': std_values,
        'destroyed_no_bomb': missiles['destroyed_no_bomb'],
        'hit_ground': missiles['hit_ground']
    }

# Process logs
data_adapt = [process_log(f) for f in adapt_logs]
data_noadapt = [process_log(f) for f in noadapt_logs]

# Time formatter
def format_time(x, pos):
    minutes = int(x // 60)
    seconds = int(x % 60)
    return f"{minutes:02d}:{seconds:02d}"

# Statistical analyses
print("Analyses statistiques des différences entre les groupes (Adaptation vs Sans Adaptation):")
print("=" * 80)

# Helper function to get value at a specific time
def get_value_at_time(d, time, key):
    times = d['all_times']
    vals = d[key]
    i = bisect.bisect_right(times, time) - 1
    if i >= 0:
        return vals[i]
    else:
        return float('nan')  # If no data, but assume all have

# Find common last timestamp (min of max times)
all_max_times = [max(d['all_times']) for d in data_adapt + data_noadapt]
min_last_time = min(all_max_times)
print(f"Timestamp commun maximal (où toutes les sessions ont des données) : {min_last_time:.1f} secondes ({int(min_last_time // 60):02d}:{int(min_last_time % 60):02d})")
print("-" * 80)

# Existing time-averaged analyses
adapt_overall = [np.mean(d['overall_avg']) for d in data_adapt]
noadapt_overall = [np.mean(d['overall_avg']) for d in data_noadapt]
t_stat, p_val = stats.ttest_ind(adapt_overall, noadapt_overall)
print(f"Moyenne Globale P(K) (moyenne temporelle): Adapt moy = {np.mean(adapt_overall):.3f} ± {np.std(adapt_overall):.3f}, Sans Adapt moy = {np.mean(noadapt_overall):.3f} ± {np.std(noadapt_overall):.3f}, t-stat = {t_stat:.3f}, p-value = {p_val:.3f}")

adapt_avg = [np.mean(d['introduced_avg']) for d in data_adapt]
noadapt_avg = [np.mean(d['introduced_avg']) for d in data_noadapt]
t_stat, p_val = stats.ttest_ind(adapt_avg, noadapt_avg)
print(f"Moyenne P(K) (moyenne temporelle): Adapt moy = {np.mean(adapt_avg):.3f} ± {np.std(adapt_avg):.3f}, Sans Adapt moy = {np.mean(noadapt_avg):.3f} ± {np.std(noadapt_avg):.3f}, t-stat = {t_stat:.3f}, p-value = {p_val:.3f}")

adapt_std = [np.mean(d['std']) for d in data_adapt]
noadapt_std = [np.mean(d['std']) for d in data_noadapt]
t_stat, p_val = stats.ttest_ind(adapt_std, noadapt_std)
print(f"Écart-Type P(K) (moyenne temporelle): Adapt moy = {np.mean(adapt_std):.3f} ± {np.std(adapt_std):.3f}, Sans Adapt moy = {np.mean(noadapt_std):.3f} ± {np.std(noadapt_std):.3f}, t-stat = {t_stat:.3f}, p-value = {p_val:.3f}")

adapt_median = [np.mean(d['median']) for d in data_adapt]
noadapt_median = [np.mean(d['median']) for d in data_noadapt]
t_stat, p_val = stats.ttest_ind(adapt_median, noadapt_median)
print(f"Médiane P(K) (moyenne temporelle): Adapt moy = {np.mean(adapt_median):.3f} ± {np.std(adapt_median):.3f}, Sans Adapt moy = {np.mean(noadapt_median):.3f} ± {np.std(noadapt_median):.3f}, t-stat = {t_stat:.3f}, p-value = {p_val:.3f}")

adapt_min = [np.mean(d['min']) for d in data_adapt]
noadapt_min = [np.mean(d['min']) for d in data_noadapt]
t_stat, p_val = stats.ttest_ind(adapt_min, noadapt_min)
print(f"Minimum P(K) (moyenne temporelle): Adapt moy = {np.mean(adapt_min):.3f} ± {np.std(adapt_min):.3f}, Sans Adapt moy = {np.mean(noadapt_min):.3f} ± {np.std(noadapt_min):.3f}, t-stat = {t_stat:.3f}, p-value = {p_val:.3f}")

adapt_destroyed_count = [len(d['destroyed_no_bomb']) for d in data_adapt]
noadapt_destroyed_count = [len(d['destroyed_no_bomb']) for d in data_noadapt]
t_stat, p_val = stats.ttest_ind(adapt_destroyed_count, noadapt_destroyed_count)
print(f"Nombre de missiles détruits (sans bombe, moyenne temporelle): Adapt moy = {np.mean(adapt_destroyed_count):.1f} ± {np.std(adapt_destroyed_count):.1f}, Sans Adapt moy = {np.mean(noadapt_destroyed_count):.1f} ± {np.std(noadapt_destroyed_count):.1f}, t-stat = {t_stat:.3f}, p-value = {p_val:.3f}")

adapt_destroyed_progress = [np.mean([p for t,p in d['destroyed_no_bomb']]) if d['destroyed_no_bomb'] else 0 for d in data_adapt]
noadapt_destroyed_progress = [np.mean([p for t,p in d['destroyed_no_bomb']]) if d['destroyed_no_bomb'] else 0 for d in data_noadapt]
t_stat, p_val = stats.ttest_ind(adapt_destroyed_progress, noadapt_destroyed_progress)
print(f"Progression moyenne des missiles détruits (sans bombe, moyenne temporelle): Adapt moy = {np.mean(adapt_destroyed_progress):.3f} ± {np.std(adapt_destroyed_progress):.3f}, Sans Adapt moy = {np.mean(noadapt_destroyed_progress):.3f} ± {np.std(noadapt_destroyed_progress):.3f}, t-stat = {t_stat:.3f}, p-value = {p_val:.3f}")

adapt_hit_count = [len(d['hit_ground']) for d in data_adapt]
noadapt_hit_count = [len(d['hit_ground']) for d in data_noadapt]
t_stat, p_val = stats.ttest_ind(adapt_hit_count, noadapt_hit_count)
print(f"Nombre de missiles touchant le sol (moyenne temporelle): Adapt moy = {np.mean(adapt_hit_count):.1f} ± {np.std(adapt_hit_count):.1f}, Sans Adapt moy = {np.mean(noadapt_hit_count):.1f} ± {np.std(noadapt_hit_count):.1f}, t-stat = {t_stat:.3f}, p-value = {p_val:.3f}")

adapt_hit_progress = [np.mean([p for t,p in d['hit_ground']]) if d['hit_ground'] else 0 for d in data_adapt]
noadapt_hit_progress = [np.mean([p for t,p in d['hit_ground']]) if d['hit_ground'] else 0 for d in data_noadapt]
t_stat, p_val = stats.ttest_ind(adapt_hit_progress, noadapt_hit_progress)
print(f"Progression moyenne des missiles touchant le sol (moyenne temporelle): Adapt moy = {np.mean(adapt_hit_progress):.3f} ± {np.std(adapt_hit_progress):.3f}, Sans Adapt moy = {np.mean(noadapt_hit_progress):.3f} ± {np.std(noadapt_hit_progress):.3f}, t-stat = {t_stat:.3f}, p-value = {p_val:.3f}")

print("-" * 80)
print("Analyses au timestamp commun maximal:")

# At common last timestamp
adapt_overall_last = [get_value_at_time(d, min_last_time, 'overall_avg') for d in data_adapt]
noadapt_overall_last = [get_value_at_time(d, min_last_time, 'overall_avg') for d in data_noadapt]
t_stat, p_val = stats.ttest_ind(adapt_overall_last, noadapt_overall_last)
print(f"Moyenne Globale P(K) à t={min_last_time:.1f}s: Adapt = {adapt_overall_last}, Sans Adapt = {noadapt_overall_last}, moy Adapt = {np.mean(adapt_overall_last):.3f} ± {np.std(adapt_overall_last):.3f}, moy Sans Adapt = {np.mean(noadapt_overall_last):.3f} ± {np.std(noadapt_overall_last):.3f}, t-stat = {t_stat:.3f}, p-value = {p_val:.3f}")

adapt_avg_last = [get_value_at_time(d, min_last_time, 'introduced_avg') for d in data_adapt]
noadapt_avg_last = [get_value_at_time(d, min_last_time, 'introduced_avg') for d in data_noadapt]
t_stat, p_val = stats.ttest_ind(adapt_avg_last, noadapt_avg_last)
print(f"Moyenne P(K) à t={min_last_time:.1f}s: Adapt = {adapt_avg_last}, Sans Adapt = {noadapt_avg_last}, moy Adapt = {np.mean(adapt_avg_last):.3f} ± {np.std(adapt_avg_last):.3f}, moy Sans Adapt = {np.mean(noadapt_avg_last):.3f} ± {np.std(noadapt_avg_last):.3f}, t-stat = {t_stat:.3f}, p-value = {p_val:.3f}")

adapt_std_last = [get_value_at_time(d, min_last_time, 'std') for d in data_adapt]
noadapt_std_last = [get_value_at_time(d, min_last_time, 'std') for d in data_noadapt]
t_stat, p_val = stats.ttest_ind(adapt_std_last, noadapt_std_last)
print(f"Écart-Type P(K) à t={min_last_time:.1f}s: Adapt = {adapt_std_last}, Sans Adapt = {noadapt_std_last}, moy Adapt = {np.mean(adapt_std_last):.3f} ± {np.std(adapt_std_last):.3f}, moy Sans Adapt = {np.mean(noadapt_std_last):.3f} ± {np.std(noadapt_std_last):.3f}, t-stat = {t_stat:.3f}, p-value = {p_val:.3f}")

adapt_median_last = [get_value_at_time(d, min_last_time, 'median') for d in data_adapt]
noadapt_median_last = [get_value_at_time(d, min_last_time, 'median') for d in data_noadapt]
t_stat, p_val = stats.ttest_ind(adapt_median_last, noadapt_median_last)
print(f"Médiane P(K) à t={min_last_time:.1f}s: Adapt = {adapt_median_last}, Sans Adapt = {noadapt_median_last}, moy Adapt = {np.mean(adapt_median_last):.3f} ± {np.std(adapt_median_last):.3f}, moy Sans Adapt = {np.mean(noadapt_median_last):.3f} ± {np.std(noadapt_median_last):.3f}, t-stat = {t_stat:.3f}, p-value = {p_val:.3f}")

adapt_min_last = [get_value_at_time(d, min_last_time, 'min') for d in data_adapt]
noadapt_min_last = [get_value_at_time(d, min_last_time, 'min') for d in data_noadapt]
t_stat, p_val = stats.ttest_ind(adapt_min_last, noadapt_min_last)
print(f"Minimum P(K) à t={min_last_time:.1f}s: Adapt = {adapt_min_last}, Sans Adapt = {noadapt_min_last}, moy Adapt = {np.mean(adapt_min_last):.3f} ± {np.std(adapt_min_last):.3f}, moy Sans Adapt = {np.mean(noadapt_min_last):.3f} ± {np.std(noadapt_min_last):.3f}, t-stat = {t_stat:.3f}, p-value = {p_val:.3f}")

print("=" * 80)

# Create plots folder
os.makedirs('plots/comparison', exist_ok=True)

# Colors
adapt_color = '#1f77b4'  # Blue
noadapt_color = '#ff7f0e'  # Orange

# Plot 1: Overall Avg P(K)
fig, ax = plt.subplots(figsize=(10, 6))
for d in data_adapt:
    ax.plot(d['all_times'], d['overall_avg'], color=adapt_color, alpha=0.7, label='Avec Adaptation')
for d in data_noadapt:
    ax.plot(d['all_times'], d['overall_avg'], color=noadapt_color, alpha=0.7, label='Sans Adaptation')
ax.set_xlabel('Temps')
ax.set_ylabel('Moyenne Globale P(K)')
ax.set_title('Moyenne Globale P(K) au Cours du Temps')
ax.xaxis.set_major_formatter(ticker.FuncFormatter(format_time))
ax.legend()
plt.savefig('plots/comparison/overall_avg_pk.png', dpi=300, bbox_inches='tight')
plt.close()

# Plot 2: Avg P(K)
fig, ax = plt.subplots(figsize=(10, 6))
for d in data_adapt:
    ax.plot(d['all_times'], d['introduced_avg'], color=adapt_color, alpha=0.7, label='Avec Adaptation')
for d in data_noadapt:
    ax.plot(d['all_times'], d['introduced_avg'], color=noadapt_color, alpha=0.7, label='Sans Adaptation')
ax.set_xlabel('Temps')
ax.set_ylabel('Moyenne P(K)')
ax.set_title('Moyenne P(K) au Cours du Temps')
ax.xaxis.set_major_formatter(ticker.FuncFormatter(format_time))
ax.legend()
plt.savefig('plots/comparison/avg_pk.png', dpi=300, bbox_inches='tight')
plt.close()

# Plot 3: Std P(K)
fig, ax = plt.subplots(figsize=(10, 6))
for d in data_adapt:
    ax.plot(d['all_times'], d['std'], color=adapt_color, alpha=0.7, label='Avec Adaptation')
for d in data_noadapt:
    ax.plot(d['all_times'], d['std'], color=noadapt_color, alpha=0.7, label='Sans Adaptation')
ax.set_xlabel('Temps')
ax.set_ylabel('Écart-Type P(K)')
ax.set_title('Écart-Type de P(K) au Cours du Temps')
ax.xaxis.set_major_formatter(ticker.FuncFormatter(format_time))
ax.legend()
plt.savefig('plots/comparison/std_pk.png', dpi=300, bbox_inches='tight')
plt.close()

# Plot 4: Median P(K)
fig, ax = plt.subplots(figsize=(10, 6))
for d in data_adapt:
    ax.plot(d['all_times'], d['median'], color=adapt_color, alpha=0.7, label='Avec Adaptation')
for d in data_noadapt:
    ax.plot(d['all_times'], d['median'], color=noadapt_color, alpha=0.7, label='Sans Adaptation')
ax.set_xlabel('Temps')
ax.set_ylabel('Médiane P(K)')
ax.set_title('Médiane P(K) au Cours du Temps')
ax.xaxis.set_major_formatter(ticker.FuncFormatter(format_time))
ax.legend()
plt.savefig('plots/comparison/median_pk.png', dpi=300, bbox_inches='tight')
plt.close()

# Plot 5: Minimum P(K)
fig, ax = plt.subplots(figsize=(10, 6))
for d in data_adapt:
    ax.plot(d['all_times'], d['min'], color=adapt_color, alpha=0.7, label='Avec Adaptation')
for d in data_noadapt:
    ax.plot(d['all_times'], d['min'], color=noadapt_color, alpha=0.7, label='Sans Adaptation')
ax.set_xlabel('Temps')
ax.set_ylabel('Minimum P(K)')
ax.set_title('Minimum P(K) au Cours du Temps')
ax.xaxis.set_major_formatter(ticker.FuncFormatter(format_time))
ax.legend()
plt.savefig('plots/comparison/min_pk.png', dpi=300, bbox_inches='tight')
plt.close()

# Plot 6: Destroyed (no bomb) trend
fig, ax = plt.subplots(figsize=(10, 6))
for d in data_adapt:
    if d['destroyed_no_bomb']:
        times, progresses = zip(*d['destroyed_no_bomb'])
        sorted_idx = np.argsort(times)
        t_sorted = np.array(times)[sorted_idx]
        p_sorted = np.array(progresses)[sorted_idx]
        smoothed = lowess(p_sorted, t_sorted, frac=0.1)
        ax.plot(smoothed[:, 0], smoothed[:, 1], color=adapt_color, alpha=0.7, label='Avec Adaptation')
for d in data_noadapt:
    if d['destroyed_no_bomb']:
        times, progresses = zip(*d['destroyed_no_bomb'])
        sorted_idx = np.argsort(times)
        t_sorted = np.array(times)[sorted_idx]
        p_sorted = np.array(progresses)[sorted_idx]
        smoothed = lowess(p_sorted, t_sorted, frac=0.1)
        ax.plot(smoothed[:, 0], smoothed[:, 1], color=noadapt_color, alpha=0.7, label='Sans Adaptation')
# Add individual points
for d in data_adapt:
    if d['destroyed_no_bomb']:
        times, progresses = zip(*d['destroyed_no_bomb'])
        ax.scatter(times, progresses, color=adapt_color, alpha=0.5, s=5)
for d in data_noadapt:
    if d['destroyed_no_bomb']:
        times, progresses = zip(*d['destroyed_no_bomb'])
        ax.scatter(times, progresses, color=noadapt_color, alpha=0.5, s=5)
ax.set_xlabel('Temps')
ax.set_ylabel('Progression')
ax.set_title('Tendance de la Progression des Missiles Détruits (Sans Bombe)')
ax.xaxis.set_major_formatter(ticker.FuncFormatter(format_time))
ax.invert_yaxis()
ax.legend()
plt.savefig('plots/comparison/destroyed_no_bomb.png', dpi=300, bbox_inches='tight')
plt.close()

# Plot 7: Hit ground
fig, ax = plt.subplots(figsize=(10, 6))
ax.scatter([], [], color=adapt_color, label='Avec Adaptation', alpha=0.7, s=10)
ax.scatter([], [], color=noadapt_color, label='Sans Adaptation', alpha=0.7, s=10)
for d in data_adapt:
    if d['hit_ground']:
        times, progresses = zip(*d['hit_ground'])
        ax.scatter(times, progresses, color=adapt_color, alpha=0.7, s=10)
for d in data_noadapt:
    if d['hit_ground']:
        times, progresses = zip(*d['hit_ground'])
        ax.scatter(times, progresses, color=noadapt_color, alpha=0.7, s=10)
ax.set_xlabel('Temps')
ax.set_ylabel('Progression')
ax.set_title('Progression des Missiles Touchant le Sol')
ax.xaxis.set_major_formatter(ticker.FuncFormatter(format_time))
ax.legend()
plt.savefig('plots/comparison/hit_ground.png', dpi=300, bbox_inches='tight')
plt.close()

print("Plots saved in plots/comparison/")