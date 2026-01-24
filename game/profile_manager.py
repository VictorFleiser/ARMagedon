import json
import os
import math
from datetime import datetime
from pathlib import Path

class ProfileManager:
    def __init__(self, profiles_dir="profiles"):
        self.profiles_dir = Path(profiles_dir)
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        self.current_profile = None
    
    def create_profile(self, profile_number, player_name="Player", hard_mode=False):
        """ Create a new profile with given number (1-5) """
        if profile_number < 1 or profile_number > 5:
            raise ValueError("Profile number must be between 1 and 5")
        
        timestamp = datetime.now()
        profile_data = {
            "profile_number": profile_number,
            "player_name": player_name, # We don't use it for now
            "created_date": timestamp.isoformat(),
            "last_played": timestamp.isoformat(),
            "total_playtime_seconds": 0.0,
            "current_level": 0,
            "tutorial_completed": False,
            "hard_mode": hard_mode,  # New flag for hard mode
            "success_score": {}, # Success count for each letter (used for short-term decay and persistence)
            "long_term_score": {}, # Long-term mastery score (increases when success_score >= 10 at session end)
            "long_term_decay_params": {
                "initial_stability_days": 1.0,
                "multiplier_factor": 2.5
            }
        }
        
        # Save to file with "hard" suffix if hard mode
        suffix = "_hard" if hard_mode else ""
        filepath = self.profiles_dir / f"profile_{profile_number}{suffix}_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        with open(filepath, 'w') as f:
            json.dump(profile_data, f, indent=2)
        
        self.current_profile = profile_data
        self.current_profile['filepath'] = str(filepath)
        
        return profile_data
    
    def save_profile(self, success_score=None, current_level=None, session_duration=0.0, success_score_threshold=5):
        """ Save current profile with updated data """
        if self.current_profile is None:
            raise ValueError("No profile loaded")
        
        # Update
        self.current_profile['last_played'] = datetime.now().isoformat()
        self.current_profile['total_playtime_seconds'] += session_duration
        
        if success_score is not None:
            self.current_profile['success_score'] = success_score
            
            if 'long_term_score' not in self.current_profile:
                self.current_profile['long_term_score'] = {}
            
            print("\n" + "=" * 60)
            print("LONG-TERM SCORE UPDATE (Session End)")
            print("=" * 60)
            print(f"Threshold: success_score >= {success_score_threshold}")
            print("-" * 60)

            # increase by 1 for letters with success_score >= threshold
            for letter, s_score in success_score.items():
                if s_score >= success_score_threshold:
                    old_score = self.current_profile['long_term_score'].get(letter, 0)
                    new_score = old_score + 1
                    self.current_profile['long_term_score'][letter] = new_score
                    print(f"Letter {letter}: success_score={s_score} >= {success_score_threshold} -> Long-term score: {old_score} -> {new_score}")
                else:
                    current_score = self.current_profile['long_term_score'].get(letter, 0)
                    self.current_profile['long_term_score'][letter] = current_score
                    print(f"Letter {letter}: success_score={s_score} < {success_score_threshold} -> Long-term score unchanged: {current_score}")
            
            print("=" * 60 + "\n")
        
        if current_level is not None:
            self.current_profile['current_level'] = current_level
        
        # Write to file
        filepath = self.current_profile.get('filepath')
        if filepath:
            with open(filepath, 'w') as f:
                save_data = {k: v for k, v in self.current_profile.items() if k != 'filepath'}
                json.dump(save_data, f, indent=2)
    
    def load_profile(self, filepath):
        """ Load a profile from file """
        with open(filepath, 'r') as f:
            profile_data = json.load(f)
        
        profile_data['filepath'] = str(filepath)
        self.current_profile = profile_data
        
        return profile_data
    
    def list_profiles(self):
        """ List all available profiles """
        profiles = []
        for filepath in self.profiles_dir.glob("profile_*.json"):
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    data['filepath'] = str(filepath)
                    profiles.append(data)
            except Exception as e:
                print(f"Error loading profile {filepath}: {e}")
        profiles.sort(key=lambda p: (p.get('profile_number', 0), p.get('created_date', '')))
        return profiles
    
    def delete_profile(self, filepath):
        """ Delete a profile file """
        try:
            os.remove(filepath)
            if self.current_profile and self.current_profile.get('filepath') == filepath:
                self.current_profile = None
            return True
        except Exception as e:
            print(f"Error deleting profile {filepath}: {e}")
            return False
    
    def get_current_profile(self):
        """ Get the currently loaded profile """
        return self.current_profile
    
    def _get_profile_filename(self, profile_number, timestamp):
        """ Generate filename for a profile """
        date_str = timestamp.strftime("%Y-%m-%d_%H-%M-%S")
        return f"profile_{profile_number}_{date_str}.json"
    
    def format_playtime(self, seconds):
        """ Format playtime seconds to human readable string """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"  
      
    def apply_long_term_decay(self):
        """ Apply long-term (inter-session) decay based on time since last session """
        if self.current_profile is None:
            raise ValueError("No profile loaded")
        
        # Get parameters
        params = self.current_profile.get('long_term_decay_params', {})
        initial_stability = params.get('initial_stability_days', 1.0)
        multiplier_factor = params.get('multiplier_factor', 2.5)
        
        # Calculate time elapsed since last session
        last_played_str = self.current_profile.get('last_played')
        if not last_played_str:
            print("No last_played timestamp, skipping long-term decay")
            return
        
        last_played = datetime.fromisoformat(last_played_str)
        now = datetime.now()
        time_elapsed = now - last_played
        days_elapsed = time_elapsed.total_seconds() / 86400.0
        
        print("\n" + "=" * 60)
        print("LONG-TERM DECAY (Inter-session Forgetting)")
        print("=" * 60)
        print(f"Last played: {last_played.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Time elapsed: {days_elapsed:.4f} days ({time_elapsed.total_seconds() / 3600:.2f} hours)")
        print(f"Initial stability: {initial_stability} days")
        print(f"Multiplier factor: {multiplier_factor}")
        print()
        
        # We skip decay if less than 1 hour elapsed
        if days_elapsed < (1.0 / 24.0):
            print("Less than 1 hour elapsed - treating as same session, no decay applied")
            print("=" * 60 + "\n")
            return
        
        success_score = self.current_profile.get('success_score', {})
        long_term_score = self.current_profile.get('long_term_score', {})
        
        if not success_score:
            print("No success_score found, skipping decay")
            print("=" * 60 + "\n")
            return
        
        print(f"Applying decay to {len(success_score)} letters:")
        print("-" * 60)
        
        # Apply decay to each letter's success_score
        for letter, s_score_old in success_score.items():
            # stability from long_term_score: S = initial_stability * multiplier^(long_term_score)
            score = long_term_score.get(letter, 0)
            S = initial_stability * (multiplier_factor ** score)
            
            # success_score_new = success_score_old * e^(-deltaT/S)
            decay_factor = math.exp(-days_elapsed / S)
            s_score_new = s_score_old * decay_factor
            s_score_new = max(0, int(round(s_score_new)))  # Keep as int
            
            # Update success_score
            success_score[letter] = s_score_new
            
            percent_retained = (s_score_new / s_score_old * 100) if s_score_old > 0 else 0
            
            print(f"Letter {letter}:")
            print(f"  Long-term score: {score}")
            print(f"  Stability (S): {S:.2f} days  ({initial_stability} × {multiplier_factor}^{score})")
            print(f"  Success score before:   {s_score_old}")
            print(f"  Decay factor:  {decay_factor:.4f}  (e^(-{days_elapsed:.4f}/{S:.2f}))")
            print(f"  Success score after:    {s_score_new}  ({percent_retained:.1f}% retained)")
            print()
        
        # Update profile
        self.current_profile['success_score'] = success_score
        
        print("=" * 60)
        print("Long-term decay applied successfully\n")
