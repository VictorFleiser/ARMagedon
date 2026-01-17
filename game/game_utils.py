import pygame


def save_profile_on_exit(profile_manager, components):
    """Save profile data when exiting the game"""
    print("Saving profile...")
    session_duration = pygame.time.get_ticks() / 1000.0  # seconds
    success_score = components['gameplay_section'].spawner.bkt.success_score
    current_level = components['gameplay_section'].spawner.get_current_level()
    
    profile_manager.save_profile(
        success_score=success_score,
        current_level=current_level,
        session_duration=session_duration
    )
    print(f"Profile saved.")
    print(f"Session duration: {profile_manager.format_playtime(session_duration)}")
