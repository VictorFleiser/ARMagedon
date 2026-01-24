import json
import math
from collections import defaultdict
import bisect
import statistics
import plotly.graph_objects as go

# ============================
# Configuration
# ============================
LOG_FILE = "logs/gameplay_logs_Thomas33min.jsonl"
LOG_FILE = "logs/gameplay_logs_Victor30min.jsonl"
LOG_FILE = "logs/gameplay_logs_Victor25min.jsonl"
LOG_FILE = "logs/gameplay_logs_Vic_random_30min.jsonl"

# FLAGS for computations : each flag slows down the creation of the plot quite a bit, turn off if not needed
COMPUTE_MIN_KNOWLEDGE = True
COMPUTE_AVERAGE_KNOWLEDGE = True
COMPUTE_MEDIAN_KNOWLEDGE = True

DISPLAY_PAUSED = False        # True = flat during pause, False = cut pause out		# DO NOT SET TO TRUE, IT DOENS'T SEEM TO WORK
DT_SAMPLING = 0.1

BASE_DECAY_RATE_DEFAULT = 0.035
STABILITY_FACTOR_DEFAULT = 0.9

EVENTS_TO_MARK = {
    "missile_hit_ground": "red",
    "missile_hint_shown": "orange",
    "level_transition_started": "blue",
    "bonus_bar_filled": "green",
    "semaphore_completed:BOMB": "purple",
}

# ============================
# State containers
# ============================
letters_active = set()

p_k = {}
success_score = defaultdict(int)
base_decay_rate = defaultdict(lambda: BASE_DECAY_RATE_DEFAULT)
stability_factor = defaultdict(lambda: STABILITY_FACTOR_DEFAULT)
last_update_time = {}

times = defaultdict(list)
values = defaultdict(list)

event_times = defaultdict(list)

# ============================
# Helper functions
# ============================
def effective_decay(letter):
    stability = success_score[letter]
    return base_decay_rate[letter] / (1.0 + stability_factor[letter] * stability)

def decay_value(letter, p0, dt):
    return p0 * math.exp(-effective_decay(letter) * dt)

def record_decay(letter, t0, t1):
    if letter not in p_k:
        return
    p0 = p_k[letter]
    t = t0
    while t < t1:
        times[letter].append(t)
        values[letter].append(decay_value(letter, p0, t - t0))
        t += DT_SAMPLING

# ============================
# Load logs
# ============================
with open(LOG_FILE, "r") as f:
    logs = [json.loads(l) for l in f]

logs.sort(key=lambda x: x["timestamp"])

# ============================
# Time handling
# ============================
wall_start = logs[0]["timestamp"]
logical_time = 0.0
last_wall_time = wall_start
paused = False

def advance_time(new_wall_time):
    global logical_time, last_wall_time
    dt = new_wall_time - last_wall_time
    if not paused or DISPLAY_PAUSED:
        logical_time += dt
    last_wall_time = new_wall_time

# ============================
# Main processing loop
# ============================
for log in logs:
    wall_time = log["timestamp"]
    event = log["event"]

    advance_time(wall_time)

    # --- Pause handling ---
    if event == "game_paused":
        paused = True
        continue

    if event == "game_resumed":
        paused = False
        continue

    # --- Event markers ---
    if event in EVENTS_TO_MARK:
        event_times[event].append(logical_time)

    if event == "semaphore_completed" and log.get("semaphore") == "BOMB":
        event_times["semaphore_completed:BOMB"].append(logical_time)

    # --- New letters ---
    if event == "level_transition_started":
        for letter in log.get("new_letters", []):
            letters_active.add(letter)
            p_k[letter] = 0.0
            last_update_time[letter] = logical_time
            times[letter].append(logical_time)
            values[letter].append(0.0)

    # --- Knowledge update ---
    if event == "bkt_update":
        letter = log["letter"]
        if letter not in letters_active:
            continue

        record_decay(letter, last_update_time[letter], logical_time)

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

# ============================
# Final decay extension
# ============================
for letter in letters_active:
    record_decay(letter, last_update_time[letter], logical_time)

# ============================
# Plotly figure
# ============================
fig = go.Figure()

# --- Letter curves ---
for letter in sorted(times.keys()):
    fig.add_trace(
        go.Scatter(
            x=times[letter],
            y=values[letter],
            mode="lines",
            name=f"Letter {letter}"
        )
    )

# --- Event markers ---
for event, color in EVENTS_TO_MARK.items():
    times_for_event = event_times.get(event, [])
    if not times_for_event:
        continue

    # First trace: appears in legend
    fig.add_trace(
        go.Scatter(
            x=[times_for_event[0], times_for_event[0]],
            y=[0, 1],
            mode="lines",
            line=dict(color=color, dash="dot"),
            name=event,
            legendgroup=event,
            showlegend=True,
        )
    )

    # Remaining traces: same legend group, hidden from legend
    for t in times_for_event[1:]:
        fig.add_trace(
            go.Scatter(
                x=[t, t],
                y=[0, 1],
                mode="lines",
                line=dict(color=color, dash="dot"),
                legendgroup=event,
                showlegend=False,
            )
        )

# ============================
# Compute minimum knowledge curve
# ============================

if COMPUTE_MIN_KNOWLEDGE :
    all_times = sorted(
    set(t for letter in times for t in times[letter])
    )

    min_values = []
    for t in all_times:
        active_values = []
        for letter in times:
            # Use binary search to find latest value at or before time t
            idx = bisect.bisect_right(times[letter], t) - 1
            if idx >= 0:
                active_values.append(values[letter][idx])
        min_values.append(min(active_values) if active_values else 0)
    
    # trace for minimum knowledge
    fig.add_trace(
        go.Scatter(
            x=all_times,
            y=min_values,
            mode="lines",
            name="Minimum knowledge (all letters)",
            line=dict(width=4, color="black"),
        )
    )


# Compute average and median knowledge
if COMPUTE_AVERAGE_KNOWLEDGE or COMPUTE_MEDIAN_KNOWLEDGE :

    avg_values = []
    median_values = []
    for t in all_times:
        active_values = []
        for letter in times:
            # Use binary search to find latest value at or before time t
            idx = bisect.bisect_right(times[letter], t) - 1
            if idx >= 0:
                active_values.append(values[letter][idx])
        if active_values:
            if COMPUTE_AVERAGE_KNOWLEDGE:
                avg_values.append(statistics.mean(active_values))
            if COMPUTE_MEDIAN_KNOWLEDGE:
                median_values.append(statistics.median(active_values))
        else:
            avg_values.append(0)
            median_values.append(0)

    if COMPUTE_AVERAGE_KNOWLEDGE :
        # trace for average knowledge
        fig.add_trace(
            go.Scatter(
                x=all_times,
                y=avg_values,
                mode="lines",
                name="Average knowledge (all letters)",
                line=dict(width=3, color="blue"),
            )
        )

    if COMPUTE_MEDIAN_KNOWLEDGE :
        # trace for median knowledge
        fig.add_trace(
            go.Scatter(
                x=all_times,
                y=median_values,
                mode="lines",
                name="Median knowledge (all letters)",
                line=dict(width=3, color="green"),
            )
        )

# --- Knowledge threshold line ---
if all_times:
    fig.add_trace(
        go.Scatter(
            x=[0, max(all_times)],
            y=[0.5, 0.5],
            mode="lines",
            name="Knowledge threshold (0.5)",
            line=dict(width=2, dash="dot", color="black"),
        )
    )

max_time = max((max(times[letter]) for letter in times if times[letter]), default=0)
tickvals = list(range(0, int(max_time) + 1, 60))
ticktext = [f"{int(v // 60)}:{int(v % 60):02d}" for v in tickvals] # mm:ss format

fig.update_layout(
    title="Knowledge Evolution per Letter",
    xaxis_title="Game Time (mm:ss)",
    yaxis_title="Knowledge p_k",
    yaxis=dict(range=[0, 1.05]),
    hovermode="x unified",
    xaxis=dict(
        tickvals=tickvals,
        ticktext=ticktext
    )
)

fig.show()
