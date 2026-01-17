import json
import time
from pathlib import Path

PRINT_TO_TERMINAL = False

class BaseLogger:
    def __init__(self, filepath):
        self.filepath = Path(filepath)
        self.filepath.parent.mkdir(parents=True, exist_ok=True)

        self.file = open(self.filepath, "a", encoding="utf-8")

    def log(self, event_type, **data):
        entry = {
            "timestamp": time.time(),
            "event": event_type,
            **data
        }
        self.file.write(json.dumps(entry) + "\n")
        self.file.flush()
        if PRINT_TO_TERMINAL:
            print(entry)

    def close(self):
        self.file.close()

    # --- Pause / Resume logging ---
    def pause(self, reason):
        # when the game is paused
        # reason = "player_paused" (when escape is pressed) or "level_transition" (for when the gameplay is paused during level transitions)
        self.log(
            "game_paused",
            reason=reason
        )

    def resume(self, reason):
        # when the game is resumed
        # reason = "player_resumed" (when escape is pressed) or "level_transition_complete" (for when the gameplay is resumed after level transitions)
        self.log(
            "game_resumed",
            reason=reason
        )

class GameplayLogger(BaseLogger):

    # --- Missiles ---
    def missile_spawned(self, missile):
        # when a missile is created
        self.log(
            "missile_spawned",
            missile_id=str(missile.id),
            letter=missile.letter,
            column=missile.column,
            speed=missile.speed_time,
            hint_start=missile.hint_start
        )

    def missile_hint_shown(self, missile):
        # when a missile's hint is shown
        self.log(
            "missile_hint_shown",
            missile_id=str(missile.id)
        )

    def missile_destroyed(self, missile, progress, score, bomb_used):
        # when a missile is destroyed by player
        self.log(
            "missile_destroyed",
            missile_id=str(missile.id),
            progress=progress,
            score=score,
            bomb_used=bomb_used
        )

    def missile_hit_ground(self, missile, progress):
        # when a missile reaches the ground or hits a building
        self.log(
            "missile_hit_ground",
            missile_id=str(missile.id),
            progress=progress
        )

    # --- Semaphores ---
    def semaphore_completed(self, semaphore):
        # when a semaphore input is successfully completed and received by gameplay
        self.log(
            "semaphore_completed",
            semaphore=semaphore
        )

    # --- Player ---
    def lives_updated(self, lives_remaining, life_fragments):
        # when player's lives are modified, including fragments
        self.log(
            "lives_updated",
            lives_remaining=lives_remaining,
            life_fragments=life_fragments
        )

    def bombs_updated(self, bombs_remaining, bomb_fragments):
        # when player's bombs are modified, including fragments
        self.log(
            "bombs_updated",
            bombs_remaining=bombs_remaining,
            bomb_fragments=bomb_fragments
        )

    def score_updated(self, new_score):
        # when player's score is modified
        self.log(
            "score_updated",
            new_score=new_score
        )

    # -- BKT --
    def bkt_update(self, letter, outcome, p_k, base_decay_rate=None, stability_factor=None, verbose=True):
        # outcome: 'correct', 'incorrect', or 'bomb_ignore'
        if verbose: print(f"[BKT] Letter '{letter}' - Outcome: {outcome:12s} - P(K): {p_k:.4f}")
        log_data = {
            "letter": letter,
            "outcome": outcome,
            "p_k": p_k
        }
        if base_decay_rate is not None:
            log_data["base_decay_rate"] = base_decay_rate
        if stability_factor is not None:
            log_data["stability_factor"] = stability_factor
        self.log("bkt_update", **log_data)
    
    def bkt_state_snapshot(self, all_p_k, verbose=False):
        # visual and useful for debugging, i'll leave it here
        if verbose:
            print("\n" + "="*60)
            print("BKT State Snapshot - Knowledge Probabilities")
            print("="*60)
        sorted_letters = sorted(all_p_k.items(), key=lambda x: x[1])
        for letter, p_k in sorted_letters:
            bar_length = int(p_k * 40)
            bar = '█' * bar_length + '░' * (40 - bar_length)
            if verbose: print(f"  {letter}: {p_k:.4f} [{bar}]")
        if verbose: print("="*60 + "\n")
        self.log(
            "bkt_state_snapshot",
            all_p_k=all_p_k
        )

    # --- Bonus Bar ---
    def bonus_bar_filled(self, bonus_kind):
        # when the bonus bar is completely filled
        self.log(
            "bonus_bar_filled",
            bonus_kind=bonus_kind
        )
    
    # --- Level Transitions ---
    def level_transition_started(self, level, new_letters):
        # when a level transition is triggered and screen is shown
        self.log(
            "level_transition_started",
            level=level,
            new_letters=new_letters
        )
    
    def level_transition_completed(self, level):
        # when a level transition completes (user finished all new semaphores and countdown finished)
        self.log(
            "level_transition_completed",
            level=level
        )


class WebcamLogger(BaseLogger):

    def invalid_detection(self, landmarks_positions):
        # when the detected landmarks are invalid for semaphore recognition (hands or body not detected properly)
        self.log(
            "invalid_detection",
            landmarks_positions=landmarks_positions
        )

    def valid_detection(self, landmarks_positions):
        # when the detected landmarks are valid for semaphore recognition (hands and body detected properly)
        self.log(
            "valid_detection",
            landmarks_positions=landmarks_positions
        )

    def semaphore_detected(self, semaphore, landmarks_positions):
        # when a semaphore is detected from the current hand positions that is different from the last detected one
        self.log(
            "semaphore_detected",
            semaphore=semaphore,
            landmarks_positions=landmarks_positions
        )

    # def semaphore_completed(self, semaphore, landmarks_positions):
    #     # when a semaphore is successfully completed (held for required duration)
    #     self.log(
    #         "semaphore_completed",
    #         semaphore=semaphore,
    #         landmarks_positions=landmarks_positions
    #     )

class DummyLogger(BaseLogger):
    # Logger that overrides all methods to do nothing (for when we re-use classes that expect a logger but don't need logging)
    def __init__(self):
        pass
    def log(self, event_type=None, **data):
        pass
    def close(self):
        pass
    def pause(self, reason=None):
        pass
    def resume(self, reason=None):
        pass
    def missile_spawned(self, missile=None):
        pass
    def missile_hint_shown(self, missile=None):
        pass
    def missile_destroyed(self, missile=None, progress=None, score=None, bomb_used=None):
        pass
    def missile_hit_ground(self, missile=None, progress=None):
        pass
    def semaphore_completed(self, semaphore=None):
        pass
    def lives_updated(self, lives_remaining=None, life_fragments=None):
        pass
    def bombs_updated(self, bombs_remaining=None, bomb_fragments=None):
        pass
    def score_updated(self, new_score=None):
        pass
    def bkt_update(self, letter=None, outcome=None, p_k=None, base_decay_rate=None, stability_factor=None, verbose=True):
        pass
    def bkt_state_snapshot(self, all_p_k=None, verbose=False):
        pass
    def bonus_bar_filled(self, bonus_kind=None):
        pass
    def level_transition_started(self, level=None, new_letters=None):
        pass
    def level_transition_completed(self, level=None):
        pass
    def invalid_detection(self, landmarks_positions=None):
        pass
    def valid_detection(self, landmarks_positions=None):
        pass
    def semaphore_detected(self, semaphore=None, landmarks_positions=None):
        pass
    