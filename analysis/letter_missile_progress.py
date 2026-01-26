import json
from collections import defaultdict
import plotly.graph_objects as go
import numpy as np

# ============================
# Configuration
# ============================
# Can be a single file or a list of files

LOG_FILES = [
    "logs/gameplay_logs_Victor30min.jsonl",
]

# LOG_FILES = [
#     "logs/experimentation/gameplay_logs_And.jsonl",
#     "logs/experimentation/gameplay_logs_H.jsonl",
#     "logs/experimentation/gameplay_logs_Max.jsonl",
# ]

# Sort letters by average (highest to lowest) or median
SORT_BY_AVERAGE = False
SORT_BY_MEDIAN = False

# ============================
# Missile containers per letter
# ============================
missile_events_per_letter = defaultdict(lambda: {
    "destroyed_no_bomb": {"y": []},
    "destroyed_bomb": {"y": []},
    "hit_ground": {"y": [], "size": []},
})

current_letter = None

# ============================
# Load logs
# ============================
logs = []
for log_file in LOG_FILES:
    with open(log_file, "r") as f:
        logs.extend([json.loads(l) for l in f])

logs.sort(key=lambda x: x["timestamp"])

# ============================
# Parse logs
# ============================
for log in logs:
    event = log.get("event")

    # Track which letter is currently active
    if event == "bkt_update":
        current_letter = log.get("letter")

    if not current_letter:
        continue

    # Missile destroyed
    if event == "missile_destroyed":
        progress = log["progress"]
        if log.get("bomb_used", False):
            missile_events_per_letter[current_letter]["destroyed_bomb"]["y"].append(progress)
        else:
            missile_events_per_letter[current_letter]["destroyed_no_bomb"]["y"].append(progress)

    # Missile hit ground
    if event == "missile_hit_ground":
        progress = log["progress"]
        missile_events_per_letter[current_letter]["hit_ground"]["y"].append(progress)
        missile_events_per_letter[current_letter]["hit_ground"]["size"].append(
            14 if progress >= 1.0 else 8
        )

# ============================
# Sort letters by average or median if enabled
# ============================
if SORT_BY_AVERAGE:
    # Calculate averages for each letter
    letter_averages = {}
    for letter, data in missile_events_per_letter.items():
        all_progress = (
            data["destroyed_no_bomb"]["y"] + 
            data["destroyed_bomb"]["y"] + 
            data["hit_ground"]["y"]
        )
        if all_progress:
            letter_averages[letter] = np.mean(all_progress)
    
    # Sort letters by average (highest to lowest)
    sorted_letters = sorted(letter_averages.keys(), key=lambda x: letter_averages[x], reverse=True)
else:
    sorted_letters = sorted(missile_events_per_letter.keys())

if SORT_BY_MEDIAN:
	# Calculate medians for each letter
	letter_medians = {}
	for letter, data in missile_events_per_letter.items():
		all_progress = (
			data["destroyed_no_bomb"]["y"] + 
			data["destroyed_bomb"]["y"] + 
			data["hit_ground"]["y"]
		)
		if all_progress:
			letter_medians[letter] = np.median(all_progress)
	
	# Sort letters by median (highest to lowest)
	sorted_letters = sorted(letter_medians.keys(), key=lambda x: letter_medians[x], reverse=True)

# ============================
# Build figure
# ============================
fig_letters = go.Figure()

# --- Destroyed (no bomb) ---
fig_letters.add_trace(
    go.Scatter(
        x=[
            letter
            for letter in sorted_letters
            for _ in missile_events_per_letter[letter]["destroyed_no_bomb"]["y"]
        ],
        y=[
            y
            for letter in sorted_letters
            for y in missile_events_per_letter[letter]["destroyed_no_bomb"]["y"]
        ],
        mode="markers",
        name="Destroyed (no bomb)",
        marker=dict(color="green", size=8),
    )
)

# --- Destroyed (bomb) ---
fig_letters.add_trace(
    go.Scatter(
        x=[
            letter
            for letter in sorted_letters
            for _ in missile_events_per_letter[letter]["destroyed_bomb"]["y"]
        ],
        y=[
            y
            for letter in sorted_letters
            for y in missile_events_per_letter[letter]["destroyed_bomb"]["y"]
        ],
        mode="markers",
        name="Destroyed (bomb)",
        marker=dict(color="blue", size=8),
    )
)

# --- Hit ground ---
fig_letters.add_trace(
    go.Scatter(
        x=[
            letter
            for letter in sorted_letters
            for _ in missile_events_per_letter[letter]["hit_ground"]["y"]
        ],
        y=[
            y
            for letter in sorted_letters
            for y in missile_events_per_letter[letter]["hit_ground"]["y"]
        ],
        mode="markers",
        name="Hit ground",
        marker=dict(
            color="red",
            size=[
                size
                for letter in sorted_letters
                for size in missile_events_per_letter[letter]["hit_ground"]["size"]
            ],
        ),
    )
)

# ============================
# Calculate and add average/median markers
# ============================
for letter in sorted_letters:
    data = missile_events_per_letter[letter]
    # Combine all progress values for this letter
    all_progress = (
        data["destroyed_no_bomb"]["y"] + 
        data["destroyed_bomb"]["y"] + 
        data["hit_ground"]["y"]
    )
    
    if all_progress:  # Only calculate if there's data
        avg_progress = np.mean(all_progress)
        median_progress = np.median(all_progress)
        q1_progress = np.percentile(all_progress, 25)
        q3_progress = np.percentile(all_progress, 75)
        
        # Add average marker
        fig_letters.add_trace(
            go.Scatter(
                x=[letter],
                y=[avg_progress],
                mode="markers",
                name=f"Average",
                marker=dict(color="purple", size=16, symbol="diamond"),
                showlegend=(letter == list(missile_events_per_letter.keys())[0]),  # Only show legend once
                legendgroup="average",
            )
        )
        
        # Add median marker
        fig_letters.add_trace(
            go.Scatter(
                x=[letter],
                y=[median_progress],
                mode="markers",
                name=f"Median",
                marker=dict(color="orange", size=16, symbol="square"),
                showlegend=(letter == list(missile_events_per_letter.keys())[0]),  # Only show legend once
                legendgroup="median",
            )
        )
        
        # Add Q1 marker
        fig_letters.add_trace(
            go.Scatter(
                x=[letter],
                y=[q1_progress],
                mode="markers",
                name=f"Q1 (25th percentile)",
                marker=dict(color="cyan", size=14, symbol="triangle-up"),
                showlegend=(letter == list(missile_events_per_letter.keys())[0]),
                legendgroup="q1",
            )
        )
        
        # Add Q3 marker
        fig_letters.add_trace(
            go.Scatter(
                x=[letter],
                y=[q3_progress],
                mode="markers",
                name=f"Q3 (75th percentile)",
                marker=dict(color="magenta", size=14, symbol="triangle-down"),
                showlegend=(letter == list(missile_events_per_letter.keys())[0]),
                legendgroup="q3",
            )
        )

# ============================
# Layout
# ============================
fig_letters.update_layout(
    title="Missile Progress per Letter",
    xaxis_title="Letter",
    yaxis_title="Missile progress",
    yaxis=dict(
        range=[0, 1.05],
        autorange="reversed",  # missiles go top → bottom
    ),
    hovermode="closest",
)

fig_letters.show()