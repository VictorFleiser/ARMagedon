import pygame


def save_profile_on_exit(profile_manager, components):
    """Save profile data when exiting the game"""
    print("Saving profile...")
    session_duration = pygame.time.get_ticks() / 1000.0  # seconds
    bkt_state = components['gameplay_section'].spawner.get_bkt_state()
    success_score = components['gameplay_section'].spawner.bkt.success_score
    current_level = components['gameplay_section'].spawner.get_current_level()
    status_section = components['status_section']
    
    # Get the starting score from the profile to calculate session score
    starting_score = profile_manager.get_current_profile().get('stats', {}).get('total_score', 0)
    session_score = status_section.score - starting_score
    
    stats = {
        "total_score": status_section.score,
        "lives_remaining": status_section.lives + (status_section.life_fragments / 4.0),
        "bombs_remaining": status_section.bombs + (status_section.bomb_fragments / 4.0)
    }
    
    profile_manager.save_profile(
        bkt_state=bkt_state,
        success_score=success_score,
        current_level=current_level,
        stats=stats,
        session_duration=session_duration
    )
    print(f"Profile saved. Session score: {session_score}, Total score: {stats['total_score']}")
    print(f"Session duration: {profile_manager.format_playtime(session_duration)}")
