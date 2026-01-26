import pygame
import time
from assets.assets import BLACK
from game.UI.status_section import GAMEOVER_EVENT
from game.UI.semaphore_detected_section import SEMAPHORE_COMPLETE_EVENT
from game.UI.bonus_bar_section import BONUSBAR_FULL_EVENT

# Custom events
RESOLVE_BONUS_MISSILE = pygame.USEREVENT + 10
LEVEL_TRANSITION_EVENT = pygame.USEREVENT + 20


def handle_events(components, debug_mode, profile_mode):
    """Handle all pygame events, returns (running, debug_mode, profile_mode)"""
    running = True
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            break
        
        elif event.type == GAMEOVER_EVENT:
            components['gameplay_section'].gameover()
        
        elif event.type == SEMAPHORE_COMPLETE_EVENT:
            if components['level_transition_screen'].active:
                components['level_transition_screen'].check_semaphore_input(event.semaphore)
            else:
                components['gameplay_section'].semaphore_input(event.semaphore)
        
        elif event.type == BONUSBAR_FULL_EVENT:
            components['gameplay_section'].bonus_bar_filled()
        
        elif event.type == RESOLVE_BONUS_MISSILE:
            components['gameplay_section'].resolve_bonus_event()
        
        elif event.type == LEVEL_TRANSITION_EVENT:
            all_unlocked = components['gameplay_section'].spawner.get_unlocked_letters()
            display_level = event.level + 1
            components['level_transition_screen'].start_transition(display_level, event.new_letters, all_unlocked)
            components['gameplay_logger'].level_transition_started(display_level, event.new_letters)
        
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_d:
                debug_mode = not debug_mode
                print(f"Debug mode: {'ON' if debug_mode else 'OFF'}")
            elif event.key == pygame.K_p:
                profile_mode = not profile_mode
                print(f"Performance profiling: {'ON' if profile_mode else 'OFF'}")
            elif event.key == pygame.K_b:
                components['webcam_section'].toggle_blur()
            elif event.key == pygame.K_t:
                components['webcam_section'].toggle_display_mode()
            elif event.key == pygame.K_ESCAPE:
                game_clock = components['game_clock']
                if game_clock.button_paused:
                    game_clock.resume("player_resumed")
                elif components['level_transition_screen'].active:
                    game_clock.pause("player_paused")
                else:
                    game_clock.pause("player_paused")
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            components['pause_screen'].handle_event(event)
    
    return running, debug_mode, profile_mode


def update_game(components, profile_mode):
    """Update all game components, returns frame_times dict if profiling"""
    frame_times = {}
    
    # Webcam update
    t0 = time.perf_counter()
    frame, detected_semaphore = components['webcam_section'].update()
    if profile_mode:
        frame_times['webcam_update'] = time.perf_counter() - t0
    
    # Update dependent panels
    t0 = time.perf_counter()
    components['semaphore_section'].update_semaphore_detected(detected_semaphore)
    
    dt = components['game_clock'].get_dt()
    
    components['semaphore_section'].update()
    components['status_section'].update(dt)
    components['bonus_section'].update()
    components['gameplay_section'].update(dt)
    
    # Update level transition screen
    if components['level_transition_screen'].active:
        transition_ended = components['level_transition_screen'].update(dt)
        if transition_ended:
            components['gameplay_section'].spawner.advance_to_level(components['level_transition_screen'].current_level - 1)
            components['gameplay_logger'].level_transition_completed(components['level_transition_screen'].current_level)
    
    if profile_mode:
        frame_times['updates'] = time.perf_counter() - t0
    
    return frame, frame_times


def draw_game(screen, components, frame, debug_mode, profile_mode):
    """Draw all game components, returns frame_times dict if profiling"""
    frame_times = {}
    
    t0 = time.perf_counter()
    screen.fill(BLACK)
    components['gameplay_section'].draw(screen, debug_mode=debug_mode)
    components['status_section'].draw(screen)
    components['semaphore_section'].draw(screen)
    components['bonus_section'].draw(screen)
    components['webcam_section'].draw(screen, frame, debug_mode=debug_mode)
    
    # Overlays
    if components['level_transition_screen'].active:
        components['level_transition_screen'].draw(screen)
    if components['game_clock'].button_paused:
        components['pause_screen'].draw(screen)
    
    pygame.display.flip()
    
    if profile_mode:
        frame_times['draw_flip'] = time.perf_counter() - t0
    
    return frame_times


def run_game_loop(screen, components, clock):
    """Main game loop"""
    debug_mode = False
    profile_mode = False
    running = True
    
    while running:
        loop_start = time.perf_counter()
        
        # Handle events
        running, debug_mode, profile_mode = handle_events(components, debug_mode, profile_mode)
        
        if not running:
            break
        
        # Update game state
        frame, update_times = update_game(components, profile_mode)
        
        # Draw everything
        draw_times = draw_game(screen, components, frame, debug_mode, profile_mode)
        
        clock.tick(60)
        
        # Print timing info periodically when profiling
        if profile_mode:
            frame_times = {**update_times, **draw_times}
            frame_times['total_loop'] = time.perf_counter() - loop_start
            if pygame.time.get_ticks() % 1000 < 16:
                print(f"\n--- Frame Timing (ms) ---")
                for key, value in frame_times.items():
                    print(f"{key:20s}: {value*1000:6.2f} ms")
                fps = clock.get_fps()
                print(f"{'FPS':20s}: {fps:6.1f}")
                print("-" * 30)
