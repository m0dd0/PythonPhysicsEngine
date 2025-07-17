import pygame

# --- Initialization ---
pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Correct Key Press Test")
font = pygame.font.SysFont("Arial", 24)
clock = pygame.time.Clock()

# Create a list of the key constants we want to check
# This example just checks the letters a-z
KEYS_TO_CHECK = [getattr(pygame, f"K_{chr(c)}") for c in range(ord("a"), ord("z") + 1)]

# --- Main Loop ---
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # --- Get Held Keys (Correct Method) ---
    pressed_keys = pygame.key.get_pressed()
    held_keys_names = set()

    # Iterate through the keys we care about
    for key_constant in KEYS_TO_CHECK:
        # Check the state of that specific key in the tuple
        if pressed_keys[key_constant]:
            # If pressed, get its name and add it to our set
            held_keys_names.add(pygame.key.name(key_constant))

    # --- Rendering ---
    screen.fill((240, 240, 240))

    text_to_display = f"Keys Held: {sorted(list(held_keys_names))}"
    text_surface = font.render(text_to_display, True, (0, 0, 0))
    screen.blit(text_surface, (10, 10))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
