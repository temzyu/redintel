import pygame
import sys
import time

# Initialize Pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Red Room")

# Colors
BLACK = (0, 0, 0)
RED = (255, 0, 0)
WHITE = (255, 255, 255)
GRID_COLOR = (160, 160, 160)  # Faded grey for grid lines
SHIP_COLOR = (90, 121, 200)  # Blue for ships
PREVIEW_COLOR = pygame.Color(255, 0, 0, 128) # Transparent red for invalid preview using Color object for alpha

# Fonts
title_font = pygame.font.Font(None, 100)  # Futuristic font for the title
button_font = pygame.font.Font(None, 50)  # Font for the button
label_font = pygame.font.Font(None, 18)  # Smaller font for grid labels

# Button dimensions for the menu screen
button_width, button_height = 200, 60  # Original size for "New Game" button
button_x = (SCREEN_WIDTH - button_width) // 2  # Centered horizontally
button_y = SCREEN_HEIGHT // 2 + 50  # Positioned below the title

# Grid dimensions
GRID_SIZE = 12  # 12x12 grid
TILE_SIZE = 30  # Reduced tile size (smaller grid)
BORDER_SIZE = 60  # Reduced space for labels and padding around the grid

# Center the grid
GRID_X = (SCREEN_WIDTH - (GRID_SIZE * TILE_SIZE)) // 2
GRID_Y = (SCREEN_HEIGHT - (GRID_SIZE * TILE_SIZE)) // 2 - 50  # Adjusted for gap above ship options

# Ship options (smaller versions of the ships)
ship_options = {
    "T-shape": [(0, 0), (1, 0), (2, 0), (1, -1), (1, 1)],  # T-shape
    "L-shape": [(0, 0), (1, 0), (2, 0), (2, 1)],           # L-shape
    "Box": [(0, 0), (0, 1), (1, 0), (1, 1)],               # 2x2 square
    "Linear 4": [(0, 0), (1, 0), (2, 0), (3, 0)],          # 4x1 line
    "Linear 2": [(0, 0), (1, 0)],                          # 2x1 line
    "Unit": [(0, 0)]                                       # Single tile
}

# Ship option dimensions
OPTION_BOX_SIZE = 50  # Reduced size for ship option boxes
OPTION_BOX_PADDING = 10  # Reduced padding between boxes
SHIP_OPTIONS_Y = GRID_Y + GRID_SIZE * TILE_SIZE + 10  # Positioned directly under the grid

# Submit button dimensions for the grid view
submit_button_width_grid, submit_button_height_grid = 100, 40  # Smaller size for the grid view
submit_button_x_grid = SCREEN_WIDTH - submit_button_width_grid - 3  # Padding of 3 pixels from the right edge
submit_button_y_grid = SCREEN_HEIGHT - submit_button_height_grid - 3  # Padding of 3 pixels from the bottom edge

# Variables to track dragging state
dragging_ship = None
dragging_offset_x = 0
dragging_offset_y = 0
placed_ships = []  # List to store placed ships

# List to track names of placed ships
placed_ship_names = []

# Variables for submit button validation
show_validation_message = False
validation_message_time = 0

# Variables for flashing preview
preview_visible = True
flash_counter = 0
FLASH_INTERVAL = 30  # Number of frames between flashes

# --- Core Functions ---

# Function to check if a ship placement violates the 3x3 adjacent rule
def is_adjacent_to_placed_ships(grid_x, grid_y, shape):
    for ship in placed_ships:
        for dx, dy in ship["shape"]:
            placed_x = ship["grid_x"] + dx
            placed_y = ship["grid_y"] + dy

            # Check the 3x3 area around the placed ship's tile
            for sx, sy in shape:
                tile_x = grid_x + sx
                tile_y = grid_y + sy
                if abs(tile_x - placed_x) <= 1 and abs(tile_y - placed_y) <= 1:
                    return True  # Adjacent ship found
    return False

# Function to draw ship options
def draw_ship_options():
    # Predefined positions for ship option boxes
    option_positions = [
        (GRID_X, SHIP_OPTIONS_Y),
        (GRID_X + OPTION_BOX_SIZE + OPTION_BOX_PADDING, SHIP_OPTIONS_Y),
        (GRID_X + 2 * (OPTION_BOX_SIZE + OPTION_BOX_PADDING), SHIP_OPTIONS_Y),
        (GRID_X + 3 * (OPTION_BOX_SIZE + OPTION_BOX_PADDING), SHIP_OPTIONS_Y),
        (GRID_X + 4 * (OPTION_BOX_SIZE + OPTION_BOX_PADDING), SHIP_OPTIONS_Y),
        (GRID_X + 5 * (OPTION_BOX_SIZE + OPTION_BOX_PADDING), SHIP_OPTIONS_Y),
    ]

    # Calculate the starting X position to center the options block
    total_options_width = len(ship_options) * OPTION_BOX_SIZE + (len(ship_options) - 1) * OPTION_BOX_PADDING
    start_options_x = GRID_X + (GRID_SIZE * TILE_SIZE - total_options_width) // 2


    current_option_x = start_options_x
    for index, (ship_name, ship_shape) in enumerate(ship_options.items()):
        # Use the calculated position for this option box
        option_x = current_option_x
        option_y = SHIP_OPTIONS_Y

        # Skip ships that have already been placed
        if ship_name in placed_ship_names:
            # Draw a visually distinct empty/used box
            pygame.draw.rect(screen, (50, 50, 50), (option_x, option_y, OPTION_BOX_SIZE, OPTION_BOX_SIZE)) # Dark grey for used
            pygame.draw.rect(screen, GRID_COLOR, (option_x, option_y, OPTION_BOX_SIZE, OPTION_BOX_SIZE), 1) # Keep outline
        else:
            # Draw the available option box
            pygame.draw.rect(screen, (30, 30, 30), (option_x, option_y, OPTION_BOX_SIZE, OPTION_BOX_SIZE)) # Dark background for options
            pygame.draw.rect(screen, GRID_COLOR, (option_x, option_y, OPTION_BOX_SIZE, OPTION_BOX_SIZE), 1) # Outline

            # --- Calculate ship bounds to center it ---
            min_dx = min(p[0] for p in ship_shape)
            max_dx = max(p[0] for p in ship_shape)
            min_dy = min(p[1] for p in ship_shape)
            max_dy = max(p[1] for p in ship_shape)
            ship_width_tiles = max_dx - min_dx + 1
            ship_height_tiles = max_dy - min_dy + 1
            
            tile_render_size = 8 # Smaller tile size for the ship sprites
            ship_render_width = ship_width_tiles * tile_render_size
            ship_render_height = ship_height_tiles * tile_render_size

            # Calculate top-left corner for rendering the ship centered
            render_start_x = option_x + (OPTION_BOX_SIZE - ship_render_width) // 2
            render_start_y = option_y + (OPTION_BOX_SIZE - ship_render_height) // 2

            # Adjust dx, dy based on min_dx, min_dy to render relative to top-left
            for dx, dy in ship_shape:
                ship_part_rect = pygame.Rect(
                    render_start_x + (dx - min_dx) * tile_render_size,
                    render_start_y + (dy - min_dy) * tile_render_size,
                    tile_render_size -1, tile_render_size -1 # Small gap between tiles
                )
                pygame.draw.rect(screen, SHIP_COLOR, ship_part_rect)

        # Move to the next option position
        current_option_x += OPTION_BOX_SIZE + OPTION_BOX_PADDING


# Function to draw the flashing preview of the ship while dragging
def draw_flashing_preview():
    global preview_visible, flash_counter

    if dragging_ship:
        # Increment the flash counter
        flash_counter += 1
        if flash_counter >= FLASH_INTERVAL:
            preview_visible = not preview_visible  # Toggle visibility
            flash_counter = 0

        # Calculate the potential grid position of the ship's origin (top-left)
        mouse_x, mouse_y = pygame.mouse.get_pos() # Use current mouse pos for preview
        
        # Adjust mouse position based on dragging offset relative to the ship's (0,0) tile
        origin_mouse_x = mouse_x - dragging_offset_x 
        origin_mouse_y = mouse_y - dragging_offset_y

        grid_x = (origin_mouse_x - GRID_X + TILE_SIZE // 2) // TILE_SIZE # Add half tile for better snapping
        grid_y = (origin_mouse_y - GRID_Y + TILE_SIZE // 2) // TILE_SIZE

        # Check if the placement is valid (within grid and not adjacent)
        valid_placement = True
        collision = False
        adjacent = False

        temp_preview_rects = []
        for dx, dy in dragging_ship["shape"]:
            tile_x = grid_x + dx
            tile_y = grid_y + dy
            if not (0 <= tile_x < GRID_SIZE and 0 <= tile_y < GRID_SIZE):
                valid_placement = False
                break
            # Check for direct collision with already placed ships
            for ship in placed_ships:
                for pdx, pdy in ship["shape"]:
                    if tile_x == ship["grid_x"] + pdx and tile_y == ship["grid_y"] + pdy:
                        collision = True
                        break
                if collision: break
            if collision: break

            rect = pygame.Rect(
                GRID_X + tile_x * TILE_SIZE,
                GRID_Y + tile_y * TILE_SIZE,
                TILE_SIZE,
                TILE_SIZE
            )
            temp_preview_rects.append(rect)

        if valid_placement and not collision:
            adjacent = is_adjacent_to_placed_ships(grid_x, grid_y, dragging_ship["shape"])
            if adjacent:
                valid_placement = False

        # Draw the preview if it's supposed to be visible
        if preview_visible:
            preview_surface = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            if valid_placement:
                preview_surface.fill((0, 255, 0, 100)) # Greenish tint for valid
            else:
                preview_surface.fill((255, 0, 0, 100)) # Reddish tint for invalid

            for rect in temp_preview_rects:
                 screen.blit(preview_surface, rect.topleft)


# Function to draw the menu screen
def draw_menu():
    screen.fill(BLACK)  # Black background

    # Draw the title
    title_text = title_font.render("RED ROOM", True, RED)
    title_x = (SCREEN_WIDTH - title_text.get_width()) // 2
    title_y = SCREEN_HEIGHT // 4
    screen.blit(title_text, (title_x, title_y))

    # Draw the "New Game" button
    button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
    pygame.draw.rect(screen, WHITE, button_rect)
    button_text = button_font.render("New Game", True, BLACK)
    button_text_rect = button_text.get_rect(center=button_rect.center)
    screen.blit(button_text, button_text_rect)

# Main menu loop
def menu_loop():
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = event.pos
                # Check if the "New Game" button is clicked
                if button_x <= mouse_x <= button_x + button_width and button_y <= mouse_y <= button_y + button_height:
                    return  # Exit the menu loop and start the game

        draw_menu()
        pygame.display.flip()

# Function to display the loading screen
def loading_screen(duration=5): # Allow duration override
    start_time = time.time()  # Record the start time
    frames = [".", "..", "...", "..", "."]  # Animation frames
    frame_index = 0
    clock = pygame.time.Clock()

    while time.time() - start_time < duration:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        # Draw the loading screen
        screen.fill(BLACK)  # Black background
        loading_text = button_font.render(f"Loading{frames[frame_index]}", True, WHITE)
        loading_x = (SCREEN_WIDTH - loading_text.get_width()) // 2
        loading_y = SCREEN_HEIGHT // 2
        screen.blit(loading_text, (loading_x, loading_y))

        # Update the display
        pygame.display.flip()

        # Update the animation frame
        frame_index = (frame_index + 1) % len(frames)
        clock.tick(3) # Control animation speed (approx 3 fps for this)


# Function to draw the grid
def draw_grid():
    for x in range(GRID_SIZE):
        for y in range(GRID_SIZE):
            rect = pygame.Rect(GRID_X + x * TILE_SIZE, GRID_Y + y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            pygame.draw.rect(screen, GRID_COLOR, rect, 1)  # Draw grid lines (faded grey)

# Function to draw grid labels
def draw_labels():
    # Draw column labels (A–L)
    for col in range(GRID_SIZE):
        label = label_font.render(chr(65 + col), True, WHITE)  # Convert column index to letter
        label_x = GRID_X + col * TILE_SIZE + TILE_SIZE // 2 - label.get_width() // 2
        label_y = GRID_Y - 20 # Increased gap above the grid slightly
        screen.blit(label, (label_x, label_y))

    # Draw row labels (1–12)
    for row in range(GRID_SIZE):
        label = label_font.render(str(row + 1), True, WHITE)  # Convert row index to number
        label_x = GRID_X - 20 - label.get_width() # Increased gap to the left slightly
        label_y = GRID_Y + row * TILE_SIZE + TILE_SIZE // 2 - label.get_height() // 2
        screen.blit(label, (label_x, label_y))

# Function to draw the "Submit" button in the grid view
def draw_submit_button_grid():
    button_rect = pygame.Rect(submit_button_x_grid, submit_button_y_grid, submit_button_width_grid, submit_button_height_grid)
    pygame.draw.rect(screen, WHITE, button_rect)
    submit_text = pygame.font.Font(None, 30).render("Submit", True, BLACK)  # Smaller text for "Submit"
    submit_text_rect = submit_text.get_rect(center=button_rect.center)
    screen.blit(submit_text, submit_text_rect)

# Function to draw the validation message
def draw_validation_message():
    global show_validation_message # Need to modify global state potentially
    # Check if the message should disappear after 2 seconds
    current_time = pygame.time.get_ticks()
    # print(f"Current time: {current_time}, Validation message time: {validation_message_time}") # Debug
    if current_time - validation_message_time > 2000:
        # print("Validation message timeout") # Debug
        show_validation_message = False # Hide the message after timeout
        return

    # print("Drawing validation message") # Debug

    # Define the message text
    message_text = "Place all your ships"
    small_font = pygame.font.Font(None, 24)  # Smaller font for the message
    message_surface = small_font.render(message_text, True, BLACK)  # Black text
    text_width, text_height = message_surface.get_size()

    # Calculate the message box dimensions with padding
    padding = 5 # Increased padding slightly
    message_box_width = text_width + 2 * padding
    message_box_height = text_height + 2 * padding

    # Position the box above the Submit button
        # Position the box so its right edge aligns with the submit button's right edge (screen edge - padding)
    message_box_x = SCREEN_WIDTH - message_box_width - 3
    message_box_y = submit_button_y_grid - message_box_height - 5 # 5 pixels above submit button

    # Draw the white message box
    pygame.draw.rect(screen, WHITE, (message_box_x, message_box_y, message_box_width, message_box_height))

    # Draw the black outline around the box
    pygame.draw.rect(screen, BLACK, (message_box_x, message_box_y, message_box_width, message_box_height), 1)

    # Draw the message text centered inside the box
    text_x = message_box_x + padding
    text_y = message_box_y + padding
    screen.blit(message_surface, (text_x, text_y))

# Function to handle dragging and dropping ships
def handle_drag_and_drop(event):
    global dragging_ship, dragging_offset_x, dragging_offset_y, placed_ships, placed_ship_names

    if event.type == pygame.MOUSEBUTTONDOWN:
        mouse_x, mouse_y = event.pos

        # Check click on ship options first
        current_option_x = GRID_X + (GRID_SIZE * TILE_SIZE - (len(ship_options) * OPTION_BOX_SIZE + (len(ship_options) - 1) * OPTION_BOX_PADDING)) // 2
        option_y = SHIP_OPTIONS_Y
        ship_clicked = False
        for index, (ship_name, ship_shape) in enumerate(ship_options.items()):
             # Only allow clicking if ship hasn't been placed yet
            if ship_name not in placed_ship_names:
                option_rect = pygame.Rect(current_option_x, option_y, OPTION_BOX_SIZE, OPTION_BOX_SIZE)
                if option_rect.collidepoint(mouse_x, mouse_y):
                    dragging_ship = {
                        "name": ship_name,
                        "shape": ship_shape,
                        "x": mouse_x, # Store initial mouse pos for offset calculation
                        "y": mouse_y
                    }
                    # Calculate offset from the ship's (0,0) tile *within the option box*
                    # Find ship center within the box
                    min_dx = min(p[0] for p in ship_shape)
                    max_dx = max(p[0] for p in ship_shape)
                    min_dy = min(p[1] for p in ship_shape)
                    max_dy = max(p[1] for p in ship_shape)
                    ship_width_tiles = max_dx - min_dx + 1
                    ship_height_tiles = max_dy - min_dy + 1
                    tile_render_size = 8
                    ship_render_width = ship_width_tiles * tile_render_size
                    ship_render_height = ship_height_tiles * tile_render_size
                    render_start_x = current_option_x + (OPTION_BOX_SIZE - ship_render_width) // 2
                    render_start_y = option_y + (OPTION_BOX_SIZE - ship_render_height) // 2
                    # Offset from the top-left of the (0,0) tile representation
                    zero_tile_render_x = render_start_x + (0 - min_dx) * tile_render_size
                    zero_tile_render_y = render_start_y + (0 - min_dy) * tile_render_size

                    dragging_offset_x = mouse_x - zero_tile_render_x
                    dragging_offset_y = mouse_y - zero_tile_render_y

                    ship_clicked = True
                    break # Stop checking options once found
            current_option_x += OPTION_BOX_SIZE + OPTION_BOX_PADDING

        # If no ship option was clicked, check if a placed ship was clicked (for potential moving later)
        # (Add logic here if you want to allow moving placed ships)

    elif event.type == pygame.MOUSEBUTTONUP:
        if dragging_ship:
            mouse_x, mouse_y = event.pos

             # Adjust mouse position based on dragging offset relative to the ship's (0,0) tile
            origin_mouse_x = mouse_x - dragging_offset_x
            origin_mouse_y = mouse_y - dragging_offset_y

            # Snap the ship's origin (0,0) to the grid
            grid_x = (origin_mouse_x - GRID_X + TILE_SIZE // 2) // TILE_SIZE
            grid_y = (origin_mouse_y - GRID_Y + TILE_SIZE // 2) // TILE_SIZE


            # Check if the placement is valid (within grid, no collision, not adjacent)
            valid_placement = True
            collision = False
            for dx, dy in dragging_ship["shape"]:
                tile_x = grid_x + dx
                tile_y = grid_y + dy
                if not (0 <= tile_x < GRID_SIZE and 0 <= tile_y < GRID_SIZE):
                    valid_placement = False
                    break
                # Check collision with existing ships
                for ship in placed_ships:
                    for pdx, pdy in ship["shape"]:
                         if tile_x == ship["grid_x"] + pdx and tile_y == ship["grid_y"] + pdy:
                            collision = True
                            break
                    if collision: break
                if collision: break

            if valid_placement and not collision:
                 # Check adjacency rule
                if is_adjacent_to_placed_ships(grid_x, grid_y, dragging_ship["shape"]):
                    valid_placement = False

            if valid_placement:
                # Add the ship to the placed ships list
                placed_ships.append({
                    "name": dragging_ship["name"],
                    "shape": dragging_ship["shape"],
                    "grid_x": grid_x,
                    "grid_y": grid_y
                })
                # Add the ship name to the placed_ship_names list
                placed_ship_names.append(dragging_ship["name"])

            # Reset dragging state regardless of placement validity
            dragging_ship = None

    elif event.type == pygame.MOUSEMOTION:
        if dragging_ship:
            # Position is updated implicitly by using pygame.mouse.get_pos() in draw funcs
            pass # No need to update dragging_ship["x"], ["y"] here if preview uses get_pos

# Function to draw the dragging ship (actual ship following mouse)
def draw_dragging_ship():
    if dragging_ship:
        mouse_x, mouse_y = pygame.mouse.get_pos() # Use current mouse position

        # Draw each tile relative to the mouse, adjusted by the initial offset
        for dx, dy in dragging_ship["shape"]:
            rect = pygame.Rect(
                mouse_x - dragging_offset_x + dx * TILE_SIZE,
                mouse_y - dragging_offset_y + dy * TILE_SIZE,
                TILE_SIZE-1, # Slightly smaller to show grid lines
                TILE_SIZE-1
            )
            pygame.draw.rect(screen, SHIP_COLOR, rect)


# Function to draw placed ships on the grid
def draw_placed_ships():
    for ship in placed_ships:
        for dx, dy in ship["shape"]:
            rect = pygame.Rect(
                GRID_X + (ship["grid_x"] + dx) * TILE_SIZE,
                GRID_Y + (ship["grid_y"] + dy) * TILE_SIZE,
                TILE_SIZE-1, # Slightly smaller to show grid lines
                TILE_SIZE-1
            )
            pygame.draw.rect(screen, SHIP_COLOR, rect)


# --- New Functions for Phase 6 and 7 ---

# Helper to draw the background state (grid, ships, etc.)
def draw_current_grid_state(darken_alpha=0):
    # Fill the screen with the background color
    screen.fill((60, 51, 154))  # Background color: #3c339a
    # Draw the grid
    draw_grid()
    # Draw the grid labels
    draw_labels()
    # Draw the ship options (might be empty if all placed)
    draw_ship_options()
    # Draw the placed ships
    draw_placed_ships()
    # Draw the submit button (though it won't be interactive here)
    # draw_submit_button_grid() # Optional: Might not want submit button visible here

    # Apply darkening overlay if needed
    if darken_alpha > 0:
        dark_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        dark_surface.fill((0, 0, 0, darken_alpha)) # Black with transparency
        screen.blit(dark_surface, (0, 0))

# Phase 6: "Are You Ready" Animation
def are_you_ready_animation():
    clock = pygame.time.Clock()
    strip_height = 80
    strip_y = (SCREEN_HEIGHT - strip_height) // 2
    strip_color = (0, 0, 0, 180) # Translucent black
    strip_x = SCREEN_WIDTH # Start off-screen right
    strip_target_x = 0 # Move all the way across
    strip_speed = 15 # Pixels per frame

    text_content = "Are you ready"
    text_font = button_font
    text_color = WHITE
    displayed_text = ""
    char_index = 0
    typing_delay = 100 # Milliseconds per character
    last_char_time = 0 # Will be initialized properly when state changes

    # Button properties
    button_w, button_h = 100, 50
    button_padding = 40
    yes_button_x = (SCREEN_WIDTH // 2) - button_w - (button_padding // 2)
    no_button_x = (SCREEN_WIDTH // 2) + (button_padding // 2)
    buttons_y = strip_y + strip_height + 30
    yes_button_rect = pygame.Rect(yes_button_x, buttons_y, button_w, button_h)
    no_button_rect = pygame.Rect(no_button_x, buttons_y, button_w, button_h)
    button_text_color = BLACK
    button_bg_color = WHITE

    state = "darkening" # States: darkening, strip_moving, typing, waiting_input
    darken_alpha = 0
    max_darken = 150
    darken_speed = 5

    running = True
    while running:
        current_time = pygame.time.get_ticks()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and state == "waiting_input":
                mouse_pos = event.pos
                if yes_button_rect.collidepoint(mouse_pos):
                    return True # Player chose Yes
                elif no_button_rect.collidepoint(mouse_pos):
                    return False # Player chose No

        # --- Update state ---
        if state == "darkening":
            darken_alpha += darken_speed
            if darken_alpha >= max_darken:
                darken_alpha = max_darken
                state = "strip_moving"
                last_char_time = current_time # Reset timer for typing start (when strip starts moving)

        elif state == "strip_moving":
            strip_x -= strip_speed
            if strip_x <= strip_target_x:
                strip_x = strip_target_x
                state = "typing"
                last_char_time = current_time # Reset timer right before typing begins

        elif state == "typing":
            if char_index < len(text_content) and current_time - last_char_time > typing_delay:
                displayed_text += text_content[char_index]
                char_index += 1
                last_char_time = current_time
            elif char_index >= len(text_content):
                 state = "waiting_input"

        # --- Drawing ---
        # Draw the persistent background state (grid, ships) with darkening
        draw_current_grid_state(darken_alpha)

        # Draw the moving/static strip
        if state != "darkening": # Draw strip once darkening is complete
            # Use a surface for transparency
            strip_surface = pygame.Surface((SCREEN_WIDTH, strip_height), pygame.SRCALPHA)
            strip_surface.fill(strip_color)
            screen.blit(strip_surface, (strip_x, strip_y))


        # Draw the typing text inside the strip
        if state == "typing" or state == "waiting_input":
            text_surface = text_font.render(displayed_text, True, text_color)
            text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, strip_y + strip_height // 2))
            screen.blit(text_surface, text_rect)

        # Draw buttons when waiting for input
        if state == "waiting_input":
            # Yes button
            pygame.draw.rect(screen, button_bg_color, yes_button_rect)
            yes_text = button_font.render("Yes", True, button_text_color)
            yes_text_rect = yes_text.get_rect(center=yes_button_rect.center)
            screen.blit(yes_text, yes_text_rect)
            # No button
            pygame.draw.rect(screen, button_bg_color, no_button_rect)
            no_text = button_font.render("No", True, button_text_color)
            no_text_rect = no_text.get_rect(center=no_button_rect.center)
            screen.blit(no_text, no_text_rect)

        pygame.display.flip()
        clock.tick(60) # Limit frame rate

# Phase 7: "Ready for War" Animation
def ready_for_war_animation():
    # Short loading screen before the final message
    loading_screen(duration=2)

    clock = pygame.time.Clock()
    text_content = "Ready for war"
    text_font = title_font # Use a larger font
    text_color = WHITE
    displayed_text = ""
    char_index = 0
    typing_delay = 150 # Milliseconds per character
    last_char_time = pygame.time.get_ticks()
    end_delay = 2000 # Milliseconds to wait after text is finished
    typing_finished_time = None

    running = True
    while running:
        current_time = pygame.time.get_ticks()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        # --- Update state (typing) ---
        if typing_finished_time is None: # If still typing
            if char_index < len(text_content) and current_time - last_char_time > typing_delay:
                displayed_text += text_content[char_index]
                char_index += 1
                last_char_time = current_time
            elif char_index >= len(text_content):
                 typing_finished_time = current_time # Record when typing finished

        elif current_time - typing_finished_time > end_delay: # If typing finished and delay passed
            running = False # End the animation loop

        # --- Drawing ---
        screen.fill(BLACK) # Black background

        # Draw the typing text
        text_surface = text_font.render(displayed_text, True, text_color)
        text_rect = text_surface.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        screen.blit(text_surface, text_rect)

        pygame.display.flip()
        clock.tick(60)

    # End of animation - exit the game
    print("Game simulation ended.")
    pygame.quit()
    sys.exit()

# --- End of New Functions ---


# --- Grid View Function ---
def grid_view():
    global show_validation_message, validation_message_time, dragging_ship # Declare globals used/modified

    clock = pygame.time.Clock() # Clock for framerate control

    while True: # This is the loop for the grid screen itself
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            # Handle drag-and-drop events FIRST
            handle_drag_and_drop(event)

            # Check for "Submit" button click only if NOT currently dragging a ship
            if event.type == pygame.MOUSEBUTTONDOWN and not dragging_ship:
                mouse_x, mouse_y = event.pos
                # print(f"Mouse clicked at: {mouse_x}, {mouse_y}") # Optional debug
                submit_rect = pygame.Rect(submit_button_x_grid, submit_button_y_grid, submit_button_width_grid, submit_button_height_grid)
                if submit_rect.collidepoint(mouse_x, mouse_y):
                    # print("Submit button clicked") # Optional debug
                    # Check if all ships are placed
                    if len(placed_ship_names) < len(ship_options):
                        # print("Not all ships placed") # Optional debug
                        show_validation_message = True
                        validation_message_time = pygame.time.get_ticks()
                        # print(f"Validation message time set to: {validation_message_time}") # Optional debug
                    else:
                        # print("All ships placed, exiting grid_view") # Optional debug
                        return  # <-- Exit grid_view function when ready

        # --- Drawing for grid_view screen ---
        screen.fill((60, 51, 154))  # Background color: #3c339a
        draw_grid()
        draw_labels()
        draw_submit_button_grid()
        draw_ship_options()
        draw_placed_ships() # Draw placed ships first

        # Draw flashing preview only when dragging
        if dragging_ship:
            draw_flashing_preview()
            draw_dragging_ship() # Draw the actual ship being dragged over the preview


        # Draw the validation message if needed (inside the loop)
        if show_validation_message:
            # print("Displaying validation message") # Optional debug
            draw_validation_message() # This function handles its own timeout check

        # Update the display *at the end* of the grid_view loop
        pygame.display.flip()
        clock.tick(60) # Limit framerate to 60 FPS


# --- Main Game Execution ---

# Run the menu loop ONCE at the start
menu_loop()

# Show the initial loading screen ONCE
loading_screen()

# Loop for ship placement and confirmation
while True:
    # Display the grid view for ship placement
    # grid_view() returns when the player clicks "Submit" with all ships placed
    grid_view() # Call the function

    # Start Phase 6: "Are You Ready" animation
    player_choice = are_you_ready_animation() # Call the function, returns True/False

    if player_choice:
        # Player clicked "Yes" - Proceed to Phase 7
        print("Player chose YES.")
        ready_for_war_animation() # Call the function, handles final animation and exits
        # The program should exit within ready_for_war_animation()
        # break # This break might not even be reached, but is safe to keep
    else:
        # Player clicked "No" - Loop back to grid_view
        print("Player chose NO. Returning to ship placement.")
        # Reset validation message in case it was showing
        show_validation_message = False
        # The loop will naturally restart and call grid_view() again

# This part will likely not be reached if ready_for_war_animation() exits correctly
print("Exiting game.")
pygame.quit()
sys.exit()