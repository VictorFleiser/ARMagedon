import sys
import pygame
import cv2

# Screen setup
SCREEN_WIDTH, SCREEN_HEIGHT = 1280, 720
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("ARMagedon")
clock = pygame.time.Clock()
pygame.font.init()

# ========================= MAIN MENU =========================
from game.menus.main_menu import MainMenu

main_menu_flag = True
quit_game = False

def start_game_callback():
    global main_menu_flag
    main_menu_flag = False

main_menu = MainMenu(screen, start_game_callback=lambda: start_game_callback())

while main_menu_flag and not quit_game:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            quit_game = True
            main_menu_flag = False
            break
        else:
            main_menu.handle_event(event)
    
    if quit_game:
        break
    
    screen.fill((0, 0, 0))
    main_menu.draw()
    pygame.display.flip()
    clock.tick(60)

# Cleanup main menu webcam
if hasattr(main_menu, 'close'):
    main_menu.close()

# If user quit during main menu, exit cleanly
if quit_game:
    from game.UI.webcam_section import cap
    print("Initiating shutdown...")
    cap.release()
    cv2.destroyAllWindows()
    pygame.quit()
    print("Shutdown complete.")
    sys.exit(0)

# ========================= MAIN GAME =========================
from game.UI.webcam_section import cap
from game.game_setup import setup_game
from game.game_loop import run_game_loop
from game.game_utils import save_profile_on_exit

# Get the selected profile
profile_manager = main_menu.profile_manager
current_profile = profile_manager.get_current_profile()

if current_profile is None:
    print("No profile selected, exiting.")
    cap.release()
    cv2.destroyAllWindows()
    pygame.quit()
    sys.exit(0)

print(f"Starting game with profile: {current_profile.get('player_name', 'Player')}")

# Initialize game components
components = setup_game(screen, current_profile, profile_manager)

# Run main game loop
run_game_loop(screen, components, clock)

# Save profile and cleanup
save_profile_on_exit(profile_manager, components)

print("Initiating shutdown...")
components['audio_manager'].stop_music()
components['webcam_section'].close()
cap.release()
cv2.destroyAllWindows()
pygame.quit()
print("Shutdown complete.")
sys.exit(0)
