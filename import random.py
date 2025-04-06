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


import random # Need this for simulation and randomness

# --- Additional Game State Variables ---
game_state = "MENU" # Controls the overall flow: MENU, LOADING, PLACEMENT, PLAYER1_WAR_ROOM, PLAYER1_INTEL_RESOLUTION, PLAYER1_ATTACK_RESOLUTION, PLAYER1_TRAFFIC_LIGHT, PLAYER2_TURN, GAME_OVER
player1_grid = [] # 2D list representing player 1's grid state ('H'idden, 'M'iss, 'X'Hit)
player2_grid = [] # 2D list representing player 2's grid state (from P1's perspective)
player1_ships_state = [] # List of dicts for P1 ships: {'name': str, 'coords': list_of_tuples, 'hits': list_of_tuples, 'sunk': bool}
player2_ships_state = [] # List of dicts for P2 ships (simulated)
consultant_options = [] # Stores the coordinates offered by the consultant
selected_target = None # The coordinate P1 chose in the War Room
war_room_timer_start = 0
WAR_ROOM_DURATION = 10 # seconds
last_attack_result = None # Store if the last P1 attack was 'HIT' or 'MISS'
show_bonus_menu = False
bonus_menu_options = ["Reveal Segment Lv1", "Learn Shape (N/A)", "Attack+ (N/A)"] # MVP: Only first is functional
bonus_menu_rects = []
player1_bonus_streak = 0
player1_corruption_counter = 0
corruption_activated_last_turn = False
player1_traffic_light = 'Y' # G, Y, R
traffic_light_buttons = {} # Rects for traffic light selection
winner = None # Stores 'Player 1' or 'Player 2'

# --- Helper Functions ---

def initialize_game_grids():
    """Sets up empty grids for both players."""
    global player1_grid, player2_grid
    player1_grid = [['H' for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
    player2_grid = [['H' for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

def setup_player1_ship_states():
    """Converts placed_ships into the state tracking format."""
    global player1_ships_state
    player1_ships_state = []
    for ship in placed_ships:
        coords = []
        for dx, dy in ship["shape"]:
            coords.append((ship["grid_x"] + dx, ship["grid_y"] + dy))
        player1_ships_state.append({
            'name': ship['name'],
            'coords': coords,
            'hits': [],
            'sunk': False
        })
        # Mark initial ship locations on P1's grid (for internal use/debug)
        # In a real PvP, this grid wouldn't be directly drawn this way
        # for x, y in coords:
        #    if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
        #       player1_grid[y][x] = 'S' # Mark ship presence

def place_ships_randomly(player_ships_state_list, player_grid):
    """Places ships randomly for the simulated opponent."""
    temp_placed_names = []
    attempts = 0
    max_attempts = 500 # Prevent infinite loops

    ship_definitions = list(ship_options.items()) # Get ships to place
    random.shuffle(ship_definitions) # Place in random order

    for ship_name, shape in ship_definitions:
        placed = False
        ship_attempts = 0
        while not placed and ship_attempts < max_attempts:
            ship_attempts += 1
            grid_x = random.randint(0, GRID_SIZE - 1)
            grid_y = random.randint(0, GRID_SIZE - 1)

            valid_placement = True
            collision = False
            adjacent = False
            temp_coords = []

            # Check bounds and collisions with already placed temp ships
            for dx, dy in shape:
                tile_x = grid_x + dx
                tile_y = grid_y + dy
                if not (0 <= tile_x < GRID_SIZE and 0 <= tile_y < GRID_SIZE):
                    valid_placement = False
                    break
                # Check collision with existing ships for this player
                for existing_ship in player_ships_state_list:
                     if (tile_x, tile_y) in existing_ship['coords']:
                         collision = True
                         break
                if collision: break
                temp_coords.append((tile_x, tile_y))

            if not valid_placement or collision:
                continue # Try new random coords

            # Check adjacency (simplified for random placement)
            # Create a temporary ship dict to check against existing ones
            temp_ship_for_adjacency = {"grid_x": grid_x, "grid_y": grid_y, "shape": shape}
            # Convert existing state list to format needed by is_adjacent_to_placed_ships
            temp_existing_ships_for_check = [
                {"grid_x": s['coords'][0][0] - min(p[0] for p in ship_options[s['name']]), # Approx grid_x/y
                 "grid_y": s['coords'][0][1] - min(p[1] for p in ship_options[s['name']]),
                 "shape": ship_options[s['name']]}
                 for s in player_ships_state_list
            ]

            # Need to adapt is_adjacent_to_placed_ships or use simpler logic here
            # Simplified Adjacency Check for random placement:
            for tx, ty in temp_coords:
                for check_x in range(tx - 1, tx + 2):
                    for check_y in range(ty - 1, ty + 2):
                        if (check_x, check_y) == (tx, ty): continue # Skip self
                        for existing_ship in player_ships_state_list:
                            if (check_x, check_y) in existing_ship['coords']:
                                adjacent = True
                                break
                        if adjacent: break
                    if adjacent: break
                if adjacent: break


            if not adjacent:
                # Add the ship
                player_ships_state_list.append({
                    'name': ship_name,
                    'coords': temp_coords,
                    'hits': [],
                    'sunk': False
                })
                placed = True
                temp_placed_names.append(ship_name)

    print(f"Simulated Player 2 placed {len(player_ships_state_list)} ships.")
    if len(player_ships_state_list) < len(ship_options):
        print("Warning: Could not place all simulated ships randomly.")


def get_all_hidden_ship_coords(player_ship_state):
    """Returns a list of coordinates for all ship segments that haven't been hit yet."""
    hidden_coords = []
    for ship in player_ship_state:
        if not ship['sunk']:
            for coord in ship['coords']:
                if coord not in ship['hits']:
                    hidden_coords.append(coord)
    return hidden_coords

def generate_consultant_options():
    """Generates 3 target options, 1 guaranteed hit."""
    global consultant_options
    consultant_options = []

    # 1. Find a guaranteed hit location
    hidden_enemy_coords = get_all_hidden_ship_coords(player2_ships_state)
    if not hidden_enemy_coords:
        print("No hidden enemy coords left!")
         # Handle game end or logic error - for MVP, pick random hidden grid spots
        guaranteed_hit = None
    else:
        guaranteed_hit = random.choice(hidden_enemy_coords)
        consultant_options.append(guaranteed_hit)

    # 2. Find empty sea tiles (not hit before, not the guaranteed hit)
    possible_misses = []
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            if player2_grid[r][c] == 'H' and (c, r) != guaranteed_hit:
                 # Also ensure it's not an unhit part of an *existing* ship
                 is_ship = False
                 for ship in player2_ships_state:
                     if (c, r) in ship['coords']:
                         is_ship = True
                         break
                 if not is_ship:
                     possible_misses.append((c, r))


    # 3. Add 2 misses (ensure they are distinct and not the hit)
    random.shuffle(possible_misses)
    miss_count = 0
    for miss_coord in possible_misses:
        if miss_count < 2:
            consultant_options.append(miss_coord)
            miss_count += 1
        else:
            break

    # Ensure we always have 3 options, even if few spots left (add duplicates if needed)
    while len(consultant_options) < 3:
        rand_x = random.randint(0, GRID_SIZE - 1)
        rand_y = random.randint(0, GRID_SIZE - 1)
        # Avoid adding known hits/misses if possible
        if player2_grid[rand_y][rand_x] == 'H':
             consultant_options.append((rand_x, rand_y))
        else: # fallback if grid full
             consultant_options.append((rand_x, rand_y))


    random.shuffle(consultant_options) # Shuffle the final list

def check_hit(target_coord, opponent_ships_state):
    """Checks if the target coordinate hits any ship."""
    for ship in opponent_ships_state:
        if target_coord in ship['coords']:
            return True, ship # Return True and the ship hit
    return False, None # Return False, no ship hit

def update_ship_states(player_ships_state):
    """Checks and updates the 'sunk' status of ships."""
    all_sunk = True
    for ship in player_ships_state:
        if not ship['sunk']:
            if len(ship['hits']) == len(ship['coords']):
                ship['sunk'] = True
                print(f"Player's {ship['name']} Sunk!")
            else:
                all_sunk = False # At least one ship is not sunk
    return all_sunk # Returns True if all ships for this player are sunk

def check_win_condition():
    """Checks if all ships of either player are sunk."""
    global winner, game_state
    player1_all_sunk = update_ship_states(player1_ships_state)
    player2_all_sunk = update_ship_states(player2_ships_state)

    if player2_all_sunk:
        winner = "Player 1"
        game_state = "GAME_OVER"
        print("GAME OVER - Player 1 Wins!")
    elif player1_all_sunk:
        winner = "Player 2"
        game_state = "GAME_OVER"
        print("GAME OVER - Player 2 Wins!")


def simulate_player2_turn():
    """Simulated Player 2 takes a turn."""
    global player1_grid, player1_ships_state, game_state

    print("Simulated Player 2's Turn...")
    # Simple AI: Choose a random hidden tile on Player 1's grid
    possible_targets = []
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            if player1_grid[r][c] == 'H':
                possible_targets.append((c, r))

    if not possible_targets:
        print("P2: No targets left?")
        check_win_condition() # Check win before switching back
        game_state = "PLAYER1_WAR_ROOM"
        return

    p2_target = random.choice(possible_targets)
    target_x, target_y = p2_target

    hit, ship_hit = check_hit(p2_target, player1_ships_state)

    if hit:
        print(f"P2 Hit Player 1 at {p2_target}!")
        player1_grid[target_y][target_x] = 'X'
        # Find which ship was hit and add to its hits
        for ship in player1_ships_state:
             if p2_target in ship['coords']:
                 if p2_target not in ship['hits']: # Avoid duplicate hits
                      ship['hits'].append(p2_target)
                 break # Ship found
    else:
        print(f"P2 Missed at {p2_target}.")
        player1_grid[target_y][target_x] = 'M'

    time.sleep(1) # Pause briefly to simulate thinking/action

    check_win_condition()
    # If game not over, return to Player 1's turn
    if game_state != "GAME_OVER":
        game_state = "PLAYER1_WAR_ROOM"


# --- Drawing Functions ---

def draw_player_grid(grid_data, x_offset, y_offset, show_ships=False):
    """Draws a player's grid."""
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            tile_state = grid_data[r][c]
            rect = pygame.Rect(x_offset + c * TILE_SIZE, y_offset + r * TILE_SIZE, TILE_SIZE, TILE_SIZE)
            color = GRID_COLOR
            fill = 0 # 0 means fill, 1 means border

            if tile_state == 'M':
                pygame.draw.circle(screen, (100, 100, 255), rect.center, TILE_SIZE // 4) # Blue circle for miss
                fill = 1
            elif tile_state == 'X':
                pygame.draw.line(screen, RED, rect.topleft, rect.bottomright, 3) # Red X for hit
                pygame.draw.line(screen, RED, rect.topright, rect.bottomleft, 3)
                fill = 1
            elif tile_state == 'S' and show_ships: # Show own ship placement debug
                 color = SHIP_COLOR
                 fill = 0 # fill the square
            elif tile_state == 'H':
                 color = GRID_COLOR
                 fill = 1 # Just border for hidden
            # Add more states if needed (like Ghost 'G')

            pygame.draw.rect(screen, color, rect, fill if fill != 0 else 1) # Always draw border
            if fill == 0: # If filled, fill with color
                 pygame.draw.rect(screen, color, rect.inflate(-2, -2), 0)


def draw_game_ui():
    """Draws the main game interface based on game_state."""
    global bonus_menu_rects, traffic_light_buttons # To store clickable areas

    screen.fill((30, 30, 60)) # Dark blue background

    # Grid Positions
    p1_grid_x = 50
    p1_grid_y = 100
    p2_grid_x = SCREEN_WIDTH - (GRID_SIZE * TILE_SIZE) - 50
    p2_grid_y = 100

    # Titles
    p1_title = button_font.render("Your Fleet", True, WHITE)
    screen.blit(p1_title, (p1_grid_x, p1_grid_y - 40))
    p2_title = button_font.render("Enemy Waters", True, WHITE)
    screen.blit(p2_title, (p2_grid_x, p2_grid_y - 40))

    # Draw Grids
    draw_player_grid(player1_grid, p1_grid_x, p1_grid_y, show_ships=True) # Show P1's ships
    draw_player_grid(player2_grid, p2_grid_x, p2_grid_y, show_ships=False) # Hide P2's ships

    # Status Text Area
    status_y = p1_grid_y + GRID_SIZE * TILE_SIZE + 20
    status_font = pygame.font.Font(None, 24)

    # Player 1 Status
    p1_ships_left = sum(1 for s in player1_ships_state if not s['sunk'])
    p1_status_text = status_font.render(f"P1 Ships Left: {p1_ships_left}", True, WHITE)
    screen.blit(p1_status_text, (p1_grid_x, status_y))
    streak_text = status_font.render(f"Bonus Streak: {player1_bonus_streak}", True, (255, 255, 0)) # Yellow
    screen.blit(streak_text, (p1_grid_x, status_y + 25))
    corruption_text = status_font.render(f"Corruption: {player1_corruption_counter}/3", True, (255, 100, 100)) # Light Red
    screen.blit(corruption_text, (p1_grid_x, status_y + 50))
    traffic_light_color = {'G': (0, 255, 0), 'Y': (255, 255, 0), 'R': (255, 0, 0)}
    pygame.draw.circle(screen, traffic_light_color[player1_traffic_light], (p1_grid_x + 200, status_y + 15), 10) # P1 light indicator

     # Player 2 Status (Simulated)
    p2_ships_left = sum(1 for s in player2_ships_state if not s['sunk'])
    p2_status_text = status_font.render(f"P2 Ships Left: {p2_ships_left}", True, WHITE)
    screen.blit(p2_status_text, (p2_grid_x, status_y))


    # --- State Specific UI ---
    ui_area_x = p1_grid_x + GRID_SIZE * TILE_SIZE + 20
    ui_area_y = p1_grid_y
    ui_area_width = p2_grid_x - ui_area_x - 20
    ui_area_height = GRID_SIZE * TILE_SIZE

    if game_state == "PLAYER1_WAR_ROOM":
        # Consultant Box
        consultant_rect = pygame.Rect(ui_area_x, ui_area_y, ui_area_width, 150)
        pygame.draw.rect(screen, (50, 50, 50), consultant_rect)
        pygame.draw.rect(screen, GRID_COLOR, consultant_rect, 1)
        consultant_title = status_font.render("AI Consultant:", True, WHITE)
        screen.blit(consultant_title, (consultant_rect.x + 10, consultant_rect.y + 10))
        # Simple Advice
        advice = random.choice(["Scanning indicates activity.", "Consider these coordinates.", "High probability targets detected."])
        advice_text = status_font.render(advice, True, WHITE)
        screen.blit(advice_text, (consultant_rect.x + 10, consultant_rect.y + 40))

        # Options
        option_y_start = consultant_rect.bottom + 20
        option_font = pygame.font.Font(None, 30)
        for i, coord in enumerate(consultant_options):
            option_text = f"Option {i+1}: {chr(65 + coord[0])}{coord[1] + 1}"
            text_surf = option_font.render(option_text, True, BLACK)
            button_rect = pygame.Rect(ui_area_x + 10, option_y_start + i * 40, ui_area_width - 20, 35)
            # Highlight on hover (example)
            mouse_pos = pygame.mouse.get_pos()
            button_color = WHITE
            if button_rect.collidepoint(mouse_pos):
                 button_color = (200, 200, 200) # Lighter grey on hover
            pygame.draw.rect(screen, button_color, button_rect)
            text_rect = text_surf.get_rect(center=button_rect.center)
            screen.blit(text_surf, text_rect)

        # Timer
        elapsed_time = time.time() - war_room_timer_start
        time_left = max(0, WAR_ROOM_DURATION - elapsed_time)
        timer_text = title_font.render(f"{time_left:.1f}", True, RED if time_left < 5 else WHITE)
        timer_rect = timer_text.get_rect(center=(ui_area_x + ui_area_width / 2, option_y_start + len(consultant_options) * 40 + 50))
        screen.blit(timer_text, timer_rect)

    elif game_state == "PLAYER1_INTEL_RESOLUTION":
         # Potentially show bonus menu here
         if show_bonus_menu:
             bonus_menu_rect = pygame.Rect(ui_area_x, ui_area_y, ui_area_width, 200)
             pygame.draw.rect(screen, (60, 80, 60), bonus_menu_rect) # Greenish BG
             pygame.draw.rect(screen, GRID_COLOR, bonus_menu_rect, 1)
             bonus_title = status_font.render("Bonus Action Available!", True, WHITE)
             screen.blit(bonus_title, (bonus_menu_rect.x + 10, bonus_menu_rect.y + 10))

             bonus_font = pygame.font.Font(None, 28)
             bonus_menu_rects = [] # Clear previous rects
             for i, bonus_name in enumerate(bonus_menu_options):
                 text_surf = bonus_font.render(bonus_name, True, BLACK)
                 button_rect = pygame.Rect(bonus_menu_rect.x + 10, bonus_menu_rect.y + 50 + i * 40, bonus_menu_rect.width - 20, 35)
                 bonus_menu_rects.append(button_rect) # Store for click detection

                 mouse_pos = pygame.mouse.get_pos()
                 button_color = WHITE if i == 0 else (150, 150, 150) # Grey out non-functional
                 if button_rect.collidepoint(mouse_pos) and i == 0: # Only highlight functional
                      button_color = (200, 200, 200)
                 pygame.draw.rect(screen, button_color, button_rect)
                 text_rect = text_surf.get_rect(center=button_rect.center)
                 screen.blit(text_surf, text_rect)

         else:
             # Indicate processing...
             processing_text = button_font.render("Resolving Intel...", True, WHITE)
             processing_rect = processing_text.get_rect(center=(ui_area_x + ui_area_width / 2, ui_area_y + ui_area_height / 2))
             screen.blit(processing_text, processing_rect)


    elif game_state == "PLAYER1_ATTACK_RESOLUTION":
         # Show result briefly
         result_text = button_font.render(last_attack_result if last_attack_result else "", True, RED if last_attack_result=="HIT" else WHITE)
         result_rect = result_text.get_rect(center=(ui_area_x + ui_area_width / 2, ui_area_y + ui_area_height / 2))
         screen.blit(result_text, result_rect)
         if corruption_activated_last_turn:
              corruption_notice = status_font.render("Corruption Reset Bonus Streak!", True, RED)
              notice_rect = corruption_notice.get_rect(center=(result_rect.centerx, result_rect.bottom + 30))
              screen.blit(corruption_notice, notice_rect)


    elif game_state == "PLAYER1_TRAFFIC_LIGHT":
        # Draw Traffic Light Buttons
        light_area_rect = pygame.Rect(ui_area_x, ui_area_y, ui_area_width, 150)
        pygame.draw.rect(screen, (50, 50, 50), light_area_rect)
        pygame.draw.rect(screen, GRID_COLOR, light_area_rect, 1)
        prompt_text = status_font.render("Select Confidence Level:", True, WHITE)
        screen.blit(prompt_text, (light_area_rect.x + 10, light_area_rect.y + 10))

        button_size = 50
        button_y = light_area_rect.centery + 10
        spacing = 20
        total_width = 3 * button_size + 2 * spacing
        start_x = light_area_rect.centerx - total_width // 2

        traffic_light_buttons = {} # Clear previous
        colors = {'G': (0, 200, 0), 'Y': (200, 200, 0), 'R': (200, 0, 0)}
        keys = ['G', 'Y', 'R']
        for i, key in enumerate(keys):
            rect = pygame.Rect(start_x + i * (button_size + spacing), button_y - button_size // 2, button_size, button_size)
            traffic_light_buttons[key] = rect
            pygame.draw.rect(screen, colors[key], rect, border_radius=5)
            # Highlight if selected
            if player1_traffic_light == key:
                 pygame.draw.rect(screen, WHITE, rect, 3, border_radius=5)


    elif game_state == "PLAYER2_TURN":
        turn_text = button_font.render("Opponent's Turn...", True, WHITE)
        turn_rect = turn_text.get_rect(center=(ui_area_x + ui_area_width / 2, ui_area_y + ui_area_height / 2))
        screen.blit(turn_text, turn_rect)

    elif game_state == "GAME_OVER":
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        result_msg = f"{winner} Wins!"
        result_text = title_font.render(result_msg, True, GREEN if winner == "Player 1" else RED)
        result_rect = result_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))
        screen.blit(result_text, result_rect)

        rematch_font = pygame.font.Font(None, 40)
        rematch_text = rematch_font.render("Press R for Rematch or Q to Quit", True, WHITE)
        rematch_rect = rematch_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50))
        screen.blit(rematch_text, rematch_rect)


# --- Game Loop ---
running = True
clock = pygame.time.Clock()
transition_timer = 0 # Used for short pauses between states

while running:
    current_time = time.time()
    pygame_ticks = pygame.time.get_ticks()

    # --- Event Handling ---
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.QUIT:
            running = False

        # State-specific input handling
        if game_state == "MENU":
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = event.pos
                if button_x <= mouse_x <= button_x + button_width and button_y <= mouse_y <= button_y + button_height:
                    game_state = "LOADING"
                    transition_timer = pygame_ticks + 5000 # Set loading duration

        elif game_state == "PLACEMENT":
            handle_drag_and_drop(event) # Use your existing function
            if event.type == pygame.MOUSEBUTTONDOWN:
                 mouse_x, mouse_y = event.pos
                 submit_rect = pygame.Rect(submit_button_x_grid, submit_button_y_grid, submit_button_width_grid, submit_button_height_grid)
                 if submit_rect.collidepoint(mouse_x, mouse_y) and not dragging_ship:
                      if len(placed_ship_names) < len(ship_options):
                          show_validation_message = True
                          validation_message_time = pygame_ticks
                      else:
                          # --- Initialize Main Game ---
                          initialize_game_grids()
                          setup_player1_ship_states()
                          player2_ships_state = [] # Clear previous P2 ships
                          place_ships_randomly(player2_ships_state, player2_grid) # Place P2 ships
                          # Reset counters/state
                          player1_bonus_streak = 0
                          player1_corruption_counter = 0
                          corruption_activated_last_turn = False
                          player1_traffic_light = 'Y'
                          winner = None
                          # Start first turn
                          game_state = "PLAYER1_WAR_ROOM"
                          # Don't start timer yet, done in state logic

        elif game_state == "PLAYER1_WAR_ROOM":
             if event.type == pygame.MOUSEBUTTONDOWN:
                 mouse_pos = event.pos
                 # --- Re-calculate necessary positions for collision detection ---
                 p1_grid_x = 50
                 p1_grid_y = 100
                 p2_grid_x = SCREEN_WIDTH - (GRID_SIZE * TILE_SIZE) - 50
                 ui_area_x = p1_grid_x + GRID_SIZE * TILE_SIZE + 20
                 ui_area_y = p1_grid_y # Need this too
                 ui_area_width = p2_grid_x - ui_area_x - 20
                 # Calculate where the consultant box ends to find button start y
                 consultant_rect_height = 150 # Height used in drawing
                 option_y_start = ui_area_y + consultant_rect_height + 20 # Start Y below consultant box

                 # --- Now check collisions using the same logic as drawing ---
                 for i, coord in enumerate(consultant_options):
                     # Calculate the specific button rect for *this* option
                     button_rect = pygame.Rect(ui_area_x + 10, option_y_start + i * 40, ui_area_width - 20, 35)
                     if button_rect.collidepoint(mouse_pos):
                         selected_target = coord
                         print(f"Player selected target: {selected_target}")
                         game_state = "PLAYER1_INTEL_RESOLUTION"
                         show_bonus_menu = False # Reset bonus menu flag
                         break # Exit loop after selection

        elif game_state == "PLAYER1_INTEL_RESOLUTION":
             if show_bonus_menu and event.type == pygame.MOUSEBUTTONDOWN:
                 mouse_pos = event.pos
                 for i, rect in enumerate(bonus_menu_rects):
                      if rect.collidepoint(mouse_pos):
                          chosen_bonus = bonus_menu_options[i]
                          print(f"Player chose bonus: {chosen_bonus}")
                          # --- Apply Bonus (MVP: Only Reveal Segment) ---
                          if chosen_bonus == "Reveal Segment Lv1":
                              # Reveal 1 adjacent unknown tile next to the hit (selected_target)
                              hit_x, hit_y = selected_target
                              possible_reveals = []
                              for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]: # Orthogonal adjacent
                                   check_x, check_y = hit_x + dx, hit_y + dy
                                   if 0 <= check_x < GRID_SIZE and 0 <= check_y < GRID_SIZE and player2_grid[check_y][check_x] == 'H':
                                       possible_reveals.append((check_x, check_y))
                              if possible_reveals:
                                   reveal_coord = random.choice(possible_reveals)
                                   rx, ry = reveal_coord
                                   # Check what's actually there
                                   is_ship_segment, _ = check_hit(reveal_coord, player2_ships_state)
                                   player2_grid[ry][rx] = 'X' if is_ship_segment else 'M' # Mark revealed tile appropriately
                                   print(f"Bonus Revealed: {reveal_coord} as {'Hit' if is_ship_segment else 'Miss'}")

                          # No matter the choice, move on after selection
                          show_bonus_menu = False # Hide menu
                          game_state = "PLAYER1_ATTACK_RESOLUTION"
                          transition_timer = pygame_ticks + 1000 # Short pause to see result
                          break

        elif game_state == "PLAYER1_TRAFFIC_LIGHT":
             if event.type == pygame.MOUSEBUTTONDOWN:
                 mouse_pos = event.pos
                 for light, rect in traffic_light_buttons.items():
                      if rect.collidepoint(mouse_pos):
                          player1_traffic_light = light
                          print(f"Player set light to: {light}")
                          # Transition after selection
                          game_state = "PLAYER2_TURN"
                          transition_timer = pygame_ticks + 500 # Short delay before P2 acts
                          break

        elif game_state == "GAME_OVER":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    running = False
                elif event.key == pygame.K_r:
                    # Reset for rematch - Go back to placement? Or Menu? Let's go Menu.
                    # Reset all game variables
                    placed_ships = []
                    placed_ship_names = []
                    # Other state vars will be reset when placement finishes
                    game_state = "MENU"


    # --- Game Logic / State Transitions ---
    if game_state == "LOADING":
        if pygame_ticks >= transition_timer:
             game_state = "PLACEMENT"
             # Reset placement specific things if needed
             placed_ships = []
             placed_ship_names = []
             dragging_ship = None
             show_validation_message = False


    elif game_state == "PLAYER1_WAR_ROOM":
        # Start timer if not already started for this state instance
        if war_room_timer_start == 0:
             war_room_timer_start = current_time
             generate_consultant_options() # Generate options when entering state
             print(f"Consultant options: {consultant_options}")


        # Check timer expiry
        elapsed_time = current_time - war_room_timer_start
        if elapsed_time > WAR_ROOM_DURATION:
            print("War Room Timer Expired!")
            selected_target = None # Indicate no selection / miss
            game_state = "PLAYER1_INTEL_RESOLUTION"
            show_bonus_menu = False

    elif game_state == "PLAYER1_INTEL_RESOLUTION":
        war_room_timer_start = 0 # Reset timer for next time
        # This state logic runs once upon entering
        if selected_target is not None: # Only process if a target was chosen
            hit, ship_hit = check_hit(selected_target, player2_ships_state)
            corruption_check_needed = False

            if hit:
                last_attack_result = "HIT"
                player1_bonus_streak += 1
                player1_corruption_counter += 1
                show_bonus_menu = True # Allow bonus selection UI to show
                print(f"P1 Hit! Streak: {player1_bonus_streak}, Corruption: {player1_corruption_counter}")
                if player1_corruption_counter >= 3:
                     corruption_check_needed = True
            else:
                last_attack_result = "MISS"
                player1_bonus_streak = 0
                player1_corruption_counter = 0
                show_bonus_menu = False # No bonus on miss
                print("P1 Miss! Streak & Corruption Reset.")
                # Transition directly if no bonus menu
                game_state = "PLAYER1_ATTACK_RESOLUTION"
                transition_timer = pygame_ticks + 1000 # Short pause

            # Corruption Trigger Check (only if needed)
            if corruption_check_needed:
                if random.random() < 0.90: # 90% chance
                    print("CORRUPTION ACTIVATED!")
                    corruption_activated_last_turn = True
                    # Note: Streak reset happens *after* attack resolution phase
                    player1_corruption_counter = 0 # Reset counter now
                else:
                    print("Corruption check passed (no trigger).")
                    corruption_activated_last_turn = False
            else:
                 corruption_activated_last_turn = False # Ensure it's false if not triggered

            # If bonus menu isn't shown, we need to move state forward after processing
            if not show_bonus_menu and game_state == "PLAYER1_INTEL_RESOLUTION":
                 game_state = "PLAYER1_ATTACK_RESOLUTION"
                 transition_timer = pygame_ticks + 1000 # Short pause

        else: # Handle case where timer expired (selected_target is None)
             last_attack_result = "MISS (Timeout)"
             player1_bonus_streak = 0
             player1_corruption_counter = 0
             show_bonus_menu = False
             corruption_activated_last_turn = False
             print("P1 Miss (Timeout)! Streak & Corruption Reset.")
             game_state = "PLAYER1_ATTACK_RESOLUTION"
             transition_timer = pygame_ticks + 1000


    elif game_state == "PLAYER1_ATTACK_RESOLUTION":
         # This state mainly waits for the transition timer or displays results
         if pygame_ticks >= transition_timer:
             # Apply attack result to grid AFTER showing it
             if selected_target:
                 tx, ty = selected_target
                 if last_attack_result == "HIT":
                     player2_grid[ty][tx] = 'X'
                     # Update ship state
                     for ship in player2_ships_state:
                         if selected_target in ship['coords']:
                             if selected_target not in ship['hits']:
                                 ship['hits'].append(selected_target)
                             break
                 elif "MISS" in last_attack_result: # Catches normal miss and timeout miss
                     # Ensure we don't mark over an already revealed tile from bonus
                     if player2_grid[ty][tx] == 'H':
                          player2_grid[ty][tx] = 'M'

             # Reset streak if corruption happened
             if corruption_activated_last_turn:
                 player1_bonus_streak = 0
                 print("Bonus streak reset due to corruption.")
                 # corruption_activated_last_turn = False # Reset flag after use? Let's reset after P2 turn for clarity

             check_win_condition()
             if game_state != "GAME_OVER":
                 game_state = "PLAYER1_TRAFFIC_LIGHT"


    elif game_state == "PLAYER1_TRAFFIC_LIGHT":
         # Logic is handled by button clicks, then transitions
         pass # Waiting for input or automatic transition

    elif game_state == "PLAYER2_TURN":
         # Logic is handled by button clicks, then transitions
         if pygame_ticks >= transition_timer:
             simulate_player2_turn()
             corruption_activated_last_turn = False # Reset corruption flag after P2 turn finishes

    # --- Drawing ---
    screen.fill(BLACK) # Clear screen

    if game_state == "MENU":
        draw_menu()
    elif game_state == "LOADING":
        # Basic loading text until proper screen is back
        loading_text = button_font.render("Loading...", True, WHITE)
        loading_rect = loading_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        screen.blit(loading_text, loading_rect)
    elif game_state == "PLACEMENT":
        # Use your existing placement drawing logic
        screen.fill((60, 51, 154))
        draw_grid()
        draw_labels()
        draw_submit_button_grid()
        draw_ship_options()
        draw_placed_ships()
        if dragging_ship:
             draw_flashing_preview()
             draw_dragging_ship()
        if show_validation_message:
             draw_validation_message() # Handles its own timeout
    elif game_state in ["PLAYER1_WAR_ROOM", "PLAYER1_INTEL_RESOLUTION", "PLAYER1_ATTACK_RESOLUTION", "PLAYER1_TRAFFIC_LIGHT", "PLAYER2_TURN", "GAME_OVER"]:
         draw_game_ui() # Central drawing function for the main game

    pygame.display.flip()
    clock.tick(60) # Limit FPS

# --- End of Game ---
pygame.quit()
sys.exit()