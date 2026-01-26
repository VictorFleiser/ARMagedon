import json
import math
from collections import defaultdict
import bisect
import statistics
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from statsmodels.nonparametric.smoothers_lowess import lowess

# ============================
# Configuration
# ============================
LOG_FILE = "logs/gameplay_logs_Thomas33min.jsonl"
LOG_FILE = "logs/gameplay_logs_Victor30min.jsonl"
LOG_FILE = "logs/gameplay_logs_Victor25min.jsonl"
LOG_FILE = "logs/gameplay_logs_Vic_random_30min.jsonl"
LOG_FILE = "logs/experimentation/gameplay_logs_Max.jsonl"

# FLAGS for computations : each flag slows down the creation of the plot quite a bit, turn off if not needed
COMPUTE_MIN_KNOWLEDGE = True
COMPUTE_AVERAGE_KNOWLEDGE = True
COMPUTE_MEDIAN_KNOWLEDGE = True

DISPLAY_PAUSED = False        # True = flat during pause, False = cut pause out		# DO NOT SET TO TRUE, IT DOENS'T SEEM TO WORK
DT_SAMPLING = 0.1

BASE_DECAY_RATE_DEFAULT = 0.035
STABILITY_FACTOR_DEFAULT = 0.9

LOWESS_FRAC = 0.1   # smoothing strength for the missile progress curve (smaller = more reactive)

# Trace registries for toggles
TRACE_GROUPS = {
    "knowledge": [],
    "missiles": [],
    "events": {},
    "knowledge_summary": [],
}

EVENTS_TO_MARK = {
    "missile_hit_ground": "red",
    "missile_hint_shown": "orange",
    "level_transition_started": "blue",
    "bonus_bar_filled": "green",
    "semaphore_completed:BOMB": "purple",
}
for evt in EVENTS_TO_MARK:
    TRACE_GROUPS["events"][evt] = []

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
# Missile state containers
# ============================
missiles = {
    "destroyed_no_bomb": {"x": [], "y": []},
    "destroyed_bomb": {"x": [], "y": []},
    "hit_ground": {"x": [], "y": [], "size": []},
}

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
    
    # --- Missile events ---
    if event == "missile_destroyed":
        progress = log["progress"]
        if log.get("bomb_used", False):
            missiles["destroyed_bomb"]["x"].append(logical_time)
            missiles["destroyed_bomb"]["y"].append(progress)
        else:
            missiles["destroyed_no_bomb"]["x"].append(logical_time)
            missiles["destroyed_no_bomb"]["y"].append(progress)

    if event == "missile_hit_ground":
        progress = log["progress"]
        missiles["hit_ground"]["x"].append(logical_time)
        missiles["hit_ground"]["y"].append(progress)
        missiles["hit_ground"]["size"].append(14 if progress >= 1.0 else 8)

# ============================
# Final decay extension
# ============================
for letter in letters_active:
    record_decay(letter, last_update_time[letter], logical_time)

all_letters = sorted(letters_active)

# ============================
# Plotly figure
# ============================
fig = make_subplots(specs=[[{"secondary_y": True}]])

fig.update_layout(
    legend=dict(
        groupclick="togglegroup"
    )
)

def toggle_group(indices, visible):
    # When hiding via buttons, use legendonly so the legend entry stays visible
    target_visibility = True if visible else "legendonly"
    return [
        {
            "visible": target_visibility,
        },
        indices,
    ]

def toggle_group_event(visible):
    # Toggle all event traces together; keep legend entries visible
    target_visibility = True if visible else "legendonly"
    event_indices = []
    for evt in EVENTS_TO_MARK:
        event_indices.extend(TRACE_GROUPS["events"].get(evt, []))
    return [
        {
            "visible": target_visibility,
        },
        event_indices,
    ]


# --- Letter curves ---
for letter in sorted(times.keys()):
    fig.add_trace(
        go.Scatter(
            x=times[letter],
            y=values[letter],
            mode="lines",
            name=f"Letter {letter}",
            # legendgroup="knowledge"
        )
    )
    TRACE_GROUPS["knowledge"].append(len(fig.data) - 1)

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
            # legendgroup="events"
        )
    )
    TRACE_GROUPS["events"][event].append(len(fig.data) - 1)

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
                # legendgroup="events"
            )
        )
    TRACE_GROUPS["events"][event].extend(
        range(len(fig.data) - len(times_for_event) + 1, len(fig.data))
    )
# ============================
# Compute minimum knowledge curve
# ============================

all_times = sorted(
    set(t for letter in times for t in times[letter])
)
if COMPUTE_MIN_KNOWLEDGE :

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
            # legendgroup="knowledge_summary"
        )
    )
    TRACE_GROUPS["knowledge_summary"].append(len(fig.data) - 1)

# Compute average and median knowledge
if COMPUTE_AVERAGE_KNOWLEDGE or COMPUTE_MEDIAN_KNOWLEDGE :

    introduced_avg_values = []
    overall_avg_values = []
    median_values = []
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
                    # not yet introduced
                    overall_active_values.append(0.0)
            else:
                overall_active_values.append(0.0)
        if introduced_active_values:
            if COMPUTE_AVERAGE_KNOWLEDGE:
                introduced_avg_values.append(statistics.mean(introduced_active_values))
            if COMPUTE_MEDIAN_KNOWLEDGE:
                median_values.append(statistics.median(introduced_active_values))
        else:
            if COMPUTE_AVERAGE_KNOWLEDGE:
                introduced_avg_values.append(0)
            if COMPUTE_MEDIAN_KNOWLEDGE:
                median_values.append(0)
        overall_avg_values.append(statistics.mean(overall_active_values))

    if COMPUTE_AVERAGE_KNOWLEDGE :
        # trace for average knowledge (introduced letters)
        fig.add_trace(
            go.Scatter(
                x=all_times,
                y=introduced_avg_values,
                mode="lines",
                name="Average knowledge (introduced letters)",
                line=dict(width=3, color="blue"),
                # legendgroup="knowledge_summary"
            )
        )
        TRACE_GROUPS["knowledge_summary"].append(len(fig.data) - 1)

        # trace for overall average knowledge
        fig.add_trace(
            go.Scatter(
                x=all_times,
                y=overall_avg_values,
                mode="lines",
                name="Overall average knowledge (all letters)",
                line=dict(width=3, color="purple"),
                # legendgroup="knowledge_summary"
            )
        )
        TRACE_GROUPS["knowledge_summary"].append(len(fig.data) - 1)

    if COMPUTE_MEDIAN_KNOWLEDGE :
        # trace for median knowledge
        fig.add_trace(
            go.Scatter(
                x=all_times,
                y=median_values,
                mode="lines",
                name="Median knowledge (introduced letters)",
                line=dict(width=3, color="green"),
                # legendgroup="knowledge_summary"
            )
        )
        TRACE_GROUPS["knowledge_summary"].append(len(fig.data) - 1)

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
    TRACE_GROUPS["knowledge_summary"].append(len(fig.data) - 1)

max_time = max((max(times[letter]) for letter in times if times[letter]), default=0)
tickvals = list(range(0, int(max_time) + 1, 60))
ticktext = [f"{int(v // 60)}:{int(v % 60):02d}" for v in tickvals] # mm:ss format

fig.update_layout(
    # title="Knowledge Evolution per Letter",
    xaxis_title="Game Time (mm:ss)",
    yaxis_title="Knowledge p_k",
    yaxis=dict(range=[0, 1.05]),
    hovermode="x unified",
    xaxis=dict(
        tickvals=tickvals,
        ticktext=ticktext
    )
)

fig.update_yaxes(
    title_text="Knowledge p_k",
    range=[0, 1.05],
    secondary_y=False,
)

fig.update_yaxes(
    title_text="Missile progress",
    range=[0, 1.05],
    autorange="reversed",
    secondary_y=True,
)

# ============================
# Missile scatter plots
# ============================
fig.add_trace(
    go.Scatter(
        x=missiles["destroyed_no_bomb"]["x"],
        y=missiles["destroyed_no_bomb"]["y"],
        mode="markers",
        name="Destroyed (no bomb)",
        marker=dict(color="green", size=8),
        # legendgroup="missiles",
    ),
    secondary_y=True,
)
TRACE_GROUPS["missiles"].append(len(fig.data) - 1)

fig.add_trace(
    go.Scatter(
        x=missiles["destroyed_bomb"]["x"],
        y=missiles["destroyed_bomb"]["y"],
        mode="markers",
        name="Destroyed (bomb)",
        marker=dict(color="blue", size=8),
        # legendgroup="missiles",
    ),
    secondary_y=True,
)
TRACE_GROUPS["missiles"].append(len(fig.data) - 1)

fig.add_trace(
    go.Scatter(
        x=missiles["hit_ground"]["x"],
        y=missiles["hit_ground"]["y"],
        mode="markers",
        name="Hit ground",
        marker=dict(
            color="red",
            size=missiles["hit_ground"]["size"],
        ),
        # legendgroup="missiles",
    ),
    secondary_y=True,
)
TRACE_GROUPS["missiles"].append(len(fig.data) - 1)

# ============================
# LOWESS regression curves for missiles
# ============================
def add_lowess(x, y, name, color):
    if len(x) < 5:
        return
    smoothed = lowess(y, x, frac=LOWESS_FRAC, return_sorted=True)
    fig.add_trace(
        go.Scatter(
            x=smoothed[:, 0],
            y=smoothed[:, 1],
            mode="lines",
            name=name,
            line=dict(color=color, width=3),
            # legendgroup="missiles",
        ),
        secondary_y=True,
    )
    TRACE_GROUPS["missiles"].append(len(fig.data) - 1)

add_lowess(
    missiles["destroyed_no_bomb"]["x"],
    missiles["destroyed_no_bomb"]["y"],
    "Trend: destroyed (no bomb)",
    "darkgreen",
)

# add_lowess(
#     missiles["destroyed_bomb"]["x"],
#     missiles["destroyed_bomb"]["y"],
#     "Trend: destroyed (bomb)",
#     "darkblue",
# )

# add_lowess(
#     missiles["hit_ground"]["x"],
#     missiles["hit_ground"]["y"],
#     "Trend: hit ground",
#     "darkred",
# )


# ============================
# Buttons to toggle visibility
# ============================

fig.update_layout(
    updatemenus=[
        dict(
            type="buttons",
            direction="right",
            x=0.5,
            y=1.18,
            showactive=True,
            buttons=[
                dict(
                    label="Toggle Knowledge",
                    method="restyle",
                    args=toggle_group(TRACE_GROUPS["knowledge"], False),
                    args2=toggle_group(TRACE_GROUPS["knowledge"], True),
                ),
                dict(
                    label="Toggle Missiles",
                    method="restyle",
                    args=toggle_group(TRACE_GROUPS["missiles"], False),
                    args2=toggle_group(TRACE_GROUPS["missiles"], True),
                ),
                dict(
                    label="Toggle Events",
                    method="restyle",
                    args=toggle_group_event(False),
                    args2=toggle_group_event(True),
                ),
                dict(
                    label="Toggle Summary",
                    method="restyle",
                    args=toggle_group(TRACE_GROUPS["knowledge_summary"], False),
                    args2=toggle_group(TRACE_GROUPS["knowledge_summary"], True),
                ),
                dict(
                    label="Show All",
                    method="restyle",
                    args=[
                        {
                            "visible": True,
                        },
                        list(range(len(fig.data))),
                    ],
                ),
                dict(
                    label="Hide All",
                    method="restyle",
                    args=[
                        {
                            "visible": "legendonly",
                        },
                        list(range(len(fig.data))),
                    ],
                ),
            ],
        )
    ]
)

fig.show()
