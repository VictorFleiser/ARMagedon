import json
from collections import defaultdict
import numpy as np
import matplotlib.pyplot as plt

log_files = [
'logs/gameplay_logs_Victor30min.jsonl',
"logs/gameplay_logs_Thomas33min.jsonl",
]
# log_files = ["logs/experimentation/gameplay_logs_Max.jsonl"]
# log_files = ["logs/experimentation/gameplay_logs_L.jsonl"]
data = []
for log_file in log_files:
    with open(log_file, 'r') as f:
        for line in f:
            data.append(json.loads(line))

# Extract log name for titles
# log_name = "Aggregated"  # or customize based on files
log_names = [f.split('/')[-1].replace("gameplay_logs_", "").replace(".jsonl", "") for f in log_files]
log_name = "_".join(log_names) if len(log_names) <= 3 else f"{len(log_names)}_files"

# Filter for BKT update events
bkt_updates = [d for d in data if d['event'] == 'bkt_update']

print(f"Aggregating data from {len(log_files)} log file(s): {', '.join(log_names)}")
print(f"Total BKT updates: {len(bkt_updates)}")
print()

# Group BKT updates by letter
letter_data = defaultdict(list)
for update in bkt_updates:
    letter_data[update['letter']].append(update)

print('BKT Parameter Estimation (with success_score)')
print('=' * 50)
print('Method: Direct estimation from observed patterns')
print()

print(f"P(L0) estimated from initial response correctness (1-P(G) if correct, 0.0 if incorrect), P(G) fixed at 0.25")

# Initialize storage for results
results = {} # {letter: [p_l0, p_t, p_s, p_g]}
n_totals = {}
accuracies = {}
table_rows = []

# Process each letter
for letter in sorted(letter_data.keys()):
    updates = letter_data[letter]
    if len(updates) < 3: 
        continue # not enough data to estimate

    outcomes = [1 if u['outcome'] == 'correct' else 0 for u in updates]
    p_k_values = [u['p_k'] for u in updates]
    success_scores = [u['success_score'] for u in updates]

    n_correct = sum(outcomes)
    n_total = len(outcomes)
    n_totals[letter] = n_total
    accuracy = n_correct / n_total
    accuracies[letter] = accuracy

    # Estimate P(T) (learning rate)
    correct_indices = [i for i, o in enumerate(outcomes) if o == 1]
    if len(correct_indices) > 1:
        p_k_changes = []
        for i in range(1, len(correct_indices)):
            idx1, idx2 = correct_indices[i-1], correct_indices[i]
            change = p_k_values[idx2] - p_k_values[idx1]
            # Adjust for continuous decay between correct responses
            avg_success_score = np.mean(success_scores[idx1:idx2])
            effective_decay = 0.045 / (1.0 + 0.9 * avg_success_score)
            time_diff = updates[idx2]['timestamp'] - updates[idx1]['timestamp']
            if time_diff > 0:
                decay_factor = np.exp(-effective_decay * time_diff)
                change = change / decay_factor if decay_factor > 0 else change
            p_k_changes.append(change)

        avg_learning_rate = np.mean(p_k_changes) if p_k_changes else 0
        # P(T) estimation: delta ≈ P(T) * (1 - P(K)_avg)
        avg_p_k = np.mean(p_k_values[:-1])
        estimated_p_t = avg_learning_rate / (1 - avg_p_k) if (1 - avg_p_k) > 0.1 else 0.1
        estimated_p_t = np.clip(estimated_p_t, 0.01, 0.5)
    else:
        estimated_p_t = 0.1 # Default if not enough correct responses

    # Estimate P(S) - Slip probability from incorrect responses
    incorrect_indices = [i for i, o in enumerate(outcomes) if o == 0]
    if incorrect_indices:
        estimated_p_s = 1 - accuracy
        estimated_p_s = np.clip(estimated_p_s, 0.01, 0.3)
    else:
        estimated_p_s = 0.05  # Default if no incorrect responses

    # P(G) - Guess probability (fixed)
    estimated_p_g = 0.25

    # P(L0) - Initial knowledge probability (1 - P(G) if first response correct, else 0)
    # This is a reasonable heuristic for initial knowledge
    initial_correct = outcomes[0] if outcomes else 0
    estimated_p_l0 = (1 - estimated_p_g) if initial_correct == 1 else 0.0

    results[letter] = [estimated_p_l0, estimated_p_t, estimated_p_s, estimated_p_g]

    table_rows.append((letter, f"{n_correct}/{n_total}", f"{accuracy:.1%}", f"{estimated_p_l0:.3f}", f"{estimated_p_t:.3f}", f"{estimated_p_s:.3f}", f"{avg_learning_rate:.3f}"))

print("\nEstimated BKT Parameters per Letter:")
print("-" * 75)
print(f"{'Letter':<6} {'Correct':<10} {'Accuracy':<10} {'P(L0)':<8} {'P(T)':<8} {'P(S)':<8} {'Avg ΔP(K)':<12}")
print("-" * 75)
for row in table_rows:
    print(f"{row[0]:<6} {row[1]:<10} {row[2]:<10} {row[3]:<8} {row[4]:<8} {row[5]:<8} {row[6]:<12}")

if results:
    p_l0_vals = [r[0] for r in results.values()]
    p_t_vals = [r[1] for r in results.values()]
    p_s_vals = [r[2] for r in results.values()]
    p_g_vals = [r[3] for r in results.values()]

    print('\nSummary Statistics:')
    print("-" * 50)
    print(f"{'Parameter':<10} {'Mean':<8} {'Std':<8} {'Median':<8}")
    print("-" * 50)
    print(f"{'P(L0)':<10} {np.mean(p_l0_vals):<8.3f} {np.std(p_l0_vals):<8.3f} {np.median(p_l0_vals):<8.3f}")
    print(f"{'P(T)':<10} {np.mean(p_t_vals):<8.3f} {np.std(p_t_vals):<8.3f} {np.median(p_t_vals):<8.3f}")
    print(f"{'P(S)':<10} {np.mean(p_s_vals):<8.3f} {np.std(p_s_vals):<8.3f} {np.median(p_s_vals):<8.3f}")
    print(f"{'P(G)':<10} {np.mean(p_g_vals):<8.3f} {np.std(p_g_vals):<8.3f} {np.median(p_g_vals):<8.3f}")

# heatmap
if results:
    letters = sorted(results.keys())
    
    fig, axes = plt.subplots(1, 3, figsize=(12, len(letters) * 0.4), sharey=False, gridspec_kw={'width_ratios': [4, 1, 1]})
    
    # BKT Parameters
    params = ['P(L0)', 'P(T)', 'P(S)', 'P(G)']
    param_data = np.array([[results[l][i] for i in range(4)] for l in letters])
    im1 = axes[0].imshow(param_data, cmap='viridis', aspect='auto', vmin=0, vmax=0.75)
    axes[0].set_xticks(range(4))
    axes[0].set_xticklabels(params)
    axes[0].set_yticks(range(len(letters)))
    axes[0].set_yticklabels(letters)
    for i in range(len(letters)):
        for j in range(4):
            val = param_data[i, j]
            text_color = 'black' if val > 0.25 else 'white'
            axes[0].text(j, i, f'{val:.3f}', ha='center', va='center', color=text_color, fontsize=8)
    axes[0].set_title('BKT Parameters')
    fig.colorbar(im1, ax=axes[0], label='Value', shrink=0.8)
    
    # Accuracy
    acc_data = np.array([[accuracies[l]] for l in letters])
    im2 = axes[1].imshow(acc_data, cmap='viridis', aspect='auto', vmin=0, vmax=1)
    axes[1].set_xticks([0])
    axes[1].set_xticklabels(['Accuracy'])
    axes[1].set_yticks(range(len(letters)))
    axes[1].set_yticklabels(letters)
    for i in range(len(letters)):
        val = acc_data[i, 0]
        text_color = 'black' if val > 0.25 else 'white'
        axes[1].text(0, i, f'{val:.1%}', ha='center', va='center', color=text_color, fontsize=8)
    axes[1].set_title('Accuracy')
    fig.colorbar(im2, ax=axes[1], label='Percentage', shrink=0.8)
    
    # Trials
    trials_data = np.array([[n_totals[l]] for l in letters])
    max_trials = max(n_totals.values())
    im3 = axes[2].imshow(trials_data, cmap='plasma', aspect='auto', vmin=0, vmax=max_trials)
    axes[2].set_xticks([0])
    axes[2].set_xticklabels(['Trials'])
    axes[2].set_yticks(range(len(letters)))
    axes[2].set_yticklabels(letters)
    for i in range(len(letters)):
        val = trials_data[i, 0]
        text_color = 'black' if val > max_trials * 0.5 else 'white'
        axes[2].text(0, i, str(val), ha='center', va='center', color=text_color, fontsize=8)
    axes[2].set_title('Number of Trials')
    fig.colorbar(im3, ax=axes[2], label='Count', shrink=0.8)
    
    plt.suptitle(f'BKT Estimation Summary Heatmaps - {log_name}', fontsize=14)
    plt.tight_layout()
    plt.savefig('bkt_combined_heatmaps.png', dpi=150, bbox_inches='tight')
    plt.close()
    print("\nCombined heatmap saved as 'bkt_combined_heatmaps.png'")