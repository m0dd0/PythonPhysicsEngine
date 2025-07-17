import pygame

# --- Initialization ---
pygame.init()
screen = pygame.display.set_mode((800, 600))
pygame.display.set_caption("Correct Key Press Test")
font = pygame.font.SysFont("Arial", 24)
clock = pygame.time.Clock()

KEYS_TO_CHECK = [
    getattr(pygame, key_name) 
    for key_name in dir(pygame) 
    if key_name.startswith("K_")
]
print(len(KEYS_TO_CHECK), "keys to check")

# --- Main Loop ---
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # --- Get Held Keys (Correct Method) ---
    pressed_keys = pygame.key.get_pressed()
    held_keys_names = set()

    # # Iterate through the keys we care about
    for key_constant in KEYS_TO_CHECK:
        # Check the state of that specific key in the tuple
        if pressed_keys[key_constant]:
            # If pressed, get its name and add it to our set
            held_keys_names.add(pygame.key.name(key_constant))

    # --- Get Mouse Button States ---
    mouse_buttons = pygame.mouse.get_pressed()
    mouse_pos = pygame.mouse.get_pos()
    
    pressed_mouse_buttons = []
    button_names = ["Left", "Middle", "Right"]
    
    for i, is_pressed in enumerate(mouse_buttons):
        if is_pressed and i < len(button_names):
            pressed_mouse_buttons.append(button_names[i])

    # --- Rendering ---
    screen.fill((240, 240, 240))

    # Display keyboard keys
    keys_text = f"Keys Held: {sorted(list(held_keys_names))}"
    keys_surface = font.render(keys_text, True, (0, 0, 0))
    screen.blit(keys_surface, (10, 10))
    
    # Display mouse buttons
    mouse_text = f"Mouse Buttons: {pressed_mouse_buttons}"
    mouse_surface = font.render(mouse_text, True, (0, 0, 0))
    screen.blit(mouse_surface, (10, 40))
    
    # Display mouse position
    pos_text = f"Mouse Position: {mouse_pos}"
    pos_surface = font.render(pos_text, True, (0, 0, 0))
    screen.blit(pos_surface, (10, 70))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
