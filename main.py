import pygame
import random
import math
import os # Import the os module

# Initialize Pygame
pygame.init()  # Keep this at the VERY top

# Check if the display module is initialized
if not pygame.display.get_init():
    print("Error: Pygame display module was not initialized.")
    exit()

# Screen dimensions (Shorter and wider)
screen_width = 1280
screen_height = 720
try:
    screen = pygame.display.set_mode((screen_width, screen_height))
except pygame.error as e:
    print(f"Error creating the display: {e}")
    print("Ensure a display is properly connected and configured.")
    print("SDL_VIDEODRIVER:", os.environ.get('SDL_VIDEODRIVER')) #helpful
    exit()

pygame.display.set_caption("Survivor Game")

# Game world dimensions (Significantly larger than the screen)
world_width = 2000
world_height = 2000

# Player properties
player_size = 50
# Player starts at the center of the world
player_x = world_width // 2 - player_size // 2
player_y = world_height // 2 - player_size // 2
player_speed = 1
player_color = (255, 255, 0)  # Yellow
player_health = 20  # Player health.  Game over at 0.
base_player_speed = 1

# Camera properties
camera_x = player_x - screen_width // 2
camera_y = player_y - screen_height // 2

# Arrow properties
arrow_color = (255, 255, 0)  # Yellow
arrow_width = 10
arrow_height = 20
arrow_speed = 10
arrows = []  # List to store active arrows
double_arrows = False

# Game state variables
game_over = False  # Add game over state
font = pygame.font.Font(None, 36)  # For text rendering
game_wave = 0 #starting wave
wave_duration = 10 #seconds
enemy_count = 0
time_since_last_wave = 0 #track time
wave_in_progress = False # Add this line
enemies_spawned = False #keep track if enemies are spawned
wave_end_time = 0

# Ability Timers and Cooldowns
e_ability_active = False
e_ability_start_time = 0
e_ability_duration = 5  # seconds
e_ability_cooldown = 10  # seconds
e_cooldown_start_time = 0

q_ability_active = False
q_ability_start_time = 0
q_ability_duration = 5
q_ability_cooldown = 15
q_cooldown_start_time = 0

# New enemy types
class Enemy:
    def __init__(self, x, y, size, color, speed, health, shape="square", damage=1): #added damage
        self.x = x
        self.y = y
        self.size = size
        self.color = color
        self.speed = speed
        self.health = health
        self.max_health = health #store max health
        self.shape = shape  # "square", "triangle", or "circle"
        self.damage = damage #store the damage
        self.last_hit_time = 0 #store the last time the enemy hit the player.

    def draw(self):
        #use pygame to draw
        if self.shape == "triangle":
            # Calculate the points of the triangle
            point1 = (int(self.x + self.size // 2 - camera_x), int(self.y - camera_y))
            point2 = (int(self.x - camera_x), int(self.y + self.size - camera_y))
            point3 = (int(self.x + self.size - camera_x), int(self.y + self.size - camera_y))
            pygame.draw.polygon(screen, self.color, [point1, point2, point3])
        elif self.shape == "circle":
            pygame.draw.circle(screen, self.color, (int(self.x + self.size / 2 - camera_x), int(self.y + self.size / 2 - camera_y)), self.size // 2)
        else:
            pygame.draw.rect(screen, self.color, (int(self.x - camera_x), int(self.y - camera_y), self.size, self.size))

    def move(self, player_x, player_y):
        enemy_dx = player_x + player_size // 2 - (self.x + self.size // 2)
        enemy_dy = player_y + player_size // 2 - (self.y + self.size // 2)
        angle = math.atan2(enemy_dy, enemy_dx)
        self.x += self.speed * math.cos(angle)
        self.y += self.speed * math.sin(angle)
    def is_collision(self, other_x, other_y, other_size):
        return (
            self.x < other_x + other_size
            and self.x + self.size > other_x
            and self.y < other_y + other_size
            and self.y + self.size > other_y
        )
class HealthPickup:
    def __init__(self, x, y, size=30):
        self.x = x
        self.y = y
        self.size = size
        self.color = (0, 255, 0)  # Green

def spawn_health_pickup():
    global health_pickups, health_spawn_message, health_spawn_time
    while True:
        x = random.randint(0, world_width - 30)
        y = random.randint(0, world_height - 30)
        if math.sqrt((x - player_x) ** 2 + (y - player_y) ** 2) > 100:
            break
    health_pickups.append(HealthPickup(x, y))
    health_spawn_message = "Health pickup spawned!"
    health_spawn_time = pygame.time.get_ticks() / 1000

def update_camera():
    global camera_x, camera_y
    camera_x = player_x - screen_width // 2
    camera_y = player_y - screen_height // 2

    # Keep camera within world bounds
    if camera_x < 0:
        camera_x = 0
    elif camera_x > world_width - screen_width:
        camera_x = world_width - screen_width
    if camera_y < 0:
        camera_y = 0
    elif camera_y > world_height - screen_height:
        camera_y = world_height - screen_height

# Define tile_size for the checkered background
tile_size = 100

def draw_checkered_background():
    num_tiles_x = math.ceil(world_width / tile_size)
    num_tiles_y = math.ceil(world_height / tile_size)
    # Loop through the tiles and draw them
    for x in range(num_tiles_x):
        for y in range(num_tiles_y):
            # Calculate the position of the tile, adjusted for the camera
            tile_x = x * tile_size - camera_x
            tile_y = y * tile_size - camera_y

            # Determine the color of the tile (black or white)
            if (x + y) % 2 == 0:
                color = (255, 255, 255)  # White
            else:
                color = (0, 0, 0)  # Black

            # Draw the tile if it's within the visible area
            if tile_x < screen_width and tile_x + tile_size > 0 and \
               tile_y < screen_height and tile_y + tile_size > 0:
                pygame.draw.rect(screen, color, (int(tile_x), int(tile_y), tile_size, tile_size))

# Function to draw the game over screen
def draw_game_over_screen():
    screen.fill((0, 0, 0))  # Black background
    game_over_text = font.render("Game Over", True, (255, 255, 255))
    restart_text = font.render("Restart", True, (255, 255, 255))
    close_text = font.render("Close", True, (255, 255, 255))
    wave_text = font.render(f"Wave: {game_wave}", True, (128,128,128)) #changed to grey

    # Get the rects for the text
    game_over_rect = game_over_text.get_rect(center=(screen_width // 2, screen_height // 3))
    restart_rect = restart_text.get_rect(center=(screen_width // 2, screen_height // 2))
    close_rect = close_text.get_rect(center=(screen_width // 2, screen_height // 2 + 50))  # Position below restart
    wave_rect = wave_text.get_rect(topleft=(10,10))

    # Draw the text
    screen.blit(game_over_text, game_over_rect)
    screen.blit(restart_text, restart_rect)
    screen.blit(close_text, close_rect)
    screen.blit(wave_text, wave_rect)

    return restart_rect, close_rect #return the rect

# Function to draw a timer
def draw_timer(screen, time_left, x, y, color=(128, 128, 128)):  # Default color is grey
    if time_left > 0:
        timer_text = font.render(f"{time_left:.1f}", True, color)  # 1 decimal place
        screen.blit(timer_text, (x, y))

#new enemy types
enemy_size = 20 # Define enemy_size
enemy_color = (255, 0, 0)  # Red
enemy_speed = 1
enemy_health = 3 #define enemy health
triangle_speed = 1.3 #changed to 1.3
triangle_health = 1
triangle_size = player_size # Define triangle_size
circle_speed = 0.2
circle_health = 12
circle_size = player_size # Define circle_size

# Create initial enemies (now using Enemy class)
enemies = []



last_sq_spawn_time = 0
last_tr_spawn_time = 0
last_cr_spawn_time = 0
spawn_sq_interval = 5  #seconds
spawn_tr_interval = 5
spawn_cr_interval = 20
first_circle_spawn = False #circle doesn't spawn at the very beginning
wave_start_time = 0
health_pickups = []  # Define health_pickups as a global list before using it

for hp in health_pickups[:]:
    if (
        player_x + player_size > hp.x and
        player_x < hp.x + hp.size and
        player_y + player_size > hp.y and
        player_y < hp.y + hp.size
    ):
        player_health = min(player_health + 5, 20)
        health_pickups.remove(hp)
# Define spawn points near the walls
spawn_points = [
    (screen_width // 4, 0),          # Top
    (screen_width // 4 * 3, 0),      # Top
    (0, screen_height // 4),          # Left
    (0, screen_height // 4 * 3),      # Left
    (screen_width, screen_height // 4),  # Right
    (screen_width, screen_height // 4 * 3),# Right
    (screen_width // 4, screen_height),        # Bottom
    (screen_width // 4 * 3, screen_height)      # Bottom
]


def spawn_wave():
    global game_wave, enemies, enemy_count, wave_start_time, wave_in_progress, enemies_spawned, wave_end_time
    game_wave += 1
    enemies = []  # Clear existing enemies
    enemy_count = 0
    enemies_spawned = True  # Set to True after spawning
    wave_in_progress = True

    # Determine number of each enemy type for this wave
    if game_wave == 1:
        num_squares, num_triangles, num_circles = 1, 0, 0
    elif game_wave == 2:
        num_squares, num_triangles, num_circles = 2, 0, 0
    elif game_wave == 3:
        num_squares, num_triangles, num_circles = 3, 1, 0
    elif game_wave == 4:
        num_squares, num_triangles, num_circles = 3, 1, 0
    elif game_wave == 5:
        num_squares, num_triangles, num_circles = 4, 1, 0
    elif game_wave == 6:
        num_squares, num_triangles, num_circles = 4, 2, 0
    elif game_wave == 7:
        num_squares, num_triangles, num_circles = 5, 2, 0
    elif game_wave == 8:
        num_squares, num_triangles, num_circles = 5, 2, 1
    elif game_wave == 9:
        num_squares, num_triangles, num_circles = 6, 2, 1
    elif game_wave == 10:
        num_squares, num_triangles, num_circles = 6, 3, 1
    else:  # waves after 10
        num_squares = 7 + (game_wave - 4) * 2
        num_triangles = 3 + (game_wave - 4)
        num_circles = 1 + (game_wave - 4) // 2

    # Spawn squares
    for _ in range(num_squares):
        while True:
            x = random.randint(0, world_width - enemy_size)
            y = random.randint(0, world_height - enemy_size)
            if math.sqrt((x - player_x) ** 2 + (y - player_y) ** 2) > 150:
                break
        enemies.append(Enemy(x, y, enemy_size, enemy_color, enemy_speed, enemy_health, "square", 1))
        enemy_count += 1

    # Spawn triangles
    for _ in range(num_triangles):
        while True:
            x = random.randint(0, world_width - triangle_size)
            y = random.randint(0, world_height - triangle_size)
            if math.sqrt((x - player_x) ** 2 + (y - player_y) ** 2) > 150:
                break
        enemies.append(Enemy(x, y, triangle_size, (0, 255, 255), triangle_speed, triangle_health, "triangle", 2))
        enemy_count += 1

    # Spawn circles
    for _ in range(num_circles):
        while True:
            x = random.randint(0, world_width - circle_size)
            y = random.randint(0, world_height - circle_size)
            if math.sqrt((x - player_x) ** 2 + (y - player_y) ** 2) > 150:
                break
        enemies.append(Enemy(x, y, circle_size, (255, 0, 255), circle_speed, circle_health, "circle", 3))
        enemy_count += 1

# Game loop
running = True
spawn_wave() #spawn the first wave
while running:
    current_time = pygame.time.get_ticks() / 1000 #get time in seconds

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if not game_over: #only process events if not game over
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    # Create a new arrow at the player's position, aiming at the mouse
                    mouse_x, mouse_y = pygame.mouse.get_pos()
                    # Convert mouse position to world coordinates.
                    world_mouse_x = mouse_x + camera_x
                    world_mouse_y = mouse_y + camera_y
                    angle = math.atan2(world_mouse_y - player_y - player_size // 2, world_mouse_x - player_x - player_size // 2)
                    arrows.append({
                        'x': player_x + player_size // 2 - arrow_width // 2,
                        'y': player_y + player_size // 2 - arrow_height // 2,
                        'angle': angle
                    })
                    if q_ability_active:
                        arrows.append({  #create a second arrow
                            'x': player_x + player_size // 2 - arrow_width // 2,
                            'y': player_y + player_size // 2 - arrow_height // 2,
                            'angle': angle + 0.2  #slightly different angle
                        })

                elif event.key == pygame.K_e:
                    if not e_ability_active and pygame.time.get_ticks() / 1000 - e_cooldown_start_time >= e_ability_cooldown:
                        e_ability_active = True
                        e_ability_start_time = pygame.time.get_ticks() / 1000
                        player_speed = 3
                        print("E Ability Activated - Speed Boost")

                elif event.key == pygame.K_q:
                    if not q_ability_active and pygame.time.get_ticks() / 1000 - q_cooldown_start_time >= q_ability_cooldown:
                        q_ability_active = True
                        q_ability_start_time = pygame.time.get_ticks() / 1000
                        double_arrows = True
                        print("Q Ability Activated - Double Arrows")
        else: #if game over, check for mouse click
            # Draw the game over screen and get the button rects
            restart_rect, close_rect = draw_game_over_screen()
            pygame.display.flip()
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = event.pos #get mouse position
                if restart_rect.collidepoint(mouse_pos):
                    # Reset the game
                    game_over = False
                    player_health = 20
                    player_x = world_width // 2 - player_size // 2
                    player_y = world_height // 2 - player_size // 2
                    enemies = []
                    arrows = []
                    last_sq_spawn_time = current_time
                    last_tr_spawn_time = current_time
                    last_cr_spawn_time = current_time
                    first_circle_spawn = False
                    game_wave = 0 #reset wave
                    wave_in_progress = False # Reset this as well
                    enemies_spawned = False
                    e_ability_active = False
                    q_ability_active = False
                    e_cooldown_start_time = 0
                    q_cooldown_start_time = 0
                    spawn_wave() #spawn first wave
                elif close_rect.collidepoint(mouse_pos):
                    running = False

    if not game_over: #main game loop
        # Handle player movement (Diagonal speed bug fix)
        dx = 0
        dy = 0
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]:
            dy -= player_speed
        if keys[pygame.K_s]:
            dy += player_speed
        if keys[pygame.K_a]:
            dx -= player_speed
        if keys[pygame.K_d]:
            dx += player_speed

        # Normalize diagonal movement
        if dx != 0 and dy != 0:
            magnitude = math.sqrt(dx**2 + dy**2)
            dx /= magnitude
            dy /= magnitude
            player_x += dx * player_speed
            player_y += dy * player_speed
        else:
            player_x += dx * player_speed
            player_y += dy * player_speed

        # Keep player within bounds
        if player_x < 0:
            player_x = 0
        elif player_x > world_width - player_size:
            player_x = world_width - player_size
        if player_y < 0:
            player_y = 0
        elif player_y > world_height - player_size:
            player_y = world_height - player_size

        # Move the enemy towards the player
        for enemy in enemies:
            enemy.move(player_x, player_y)

        # Move and draw arrows
        for arrow in arrows[:]:  # Iterate through a copy to allow removal
            arrow['x'] += arrow_speed * math.cos(arrow['angle'])
            arrow['y'] += arrow_speed * math.sin(arrow['angle'])
            #pygame.draw.rect(screen, arrow_color, (arrow['x'], arrow['y'], arrow_width, arrow_height)) #removed drawing here
        # Remove arrows that go off-screen
        for current_arrow in arrows[:]:
            if current_arrow['x'] < 0 or current_arrow['x'] > world_width or current_arrow['y'] < 0 or current_arrow['y'] > world_height:
                arrows.remove(current_arrow)

        # Update the camera position
        update_camera()

        # Drawing
        screen.fill((0, 0, 0))  # Black background
        draw_checkered_background()

        # Calculate offsets for drawing relative to the camera
        offset_x = -camera_x
        offset_y = -camera_y

        # Draw the player, relative to the camera
        pygame.draw.rect(screen, player_color, (int(player_x + offset_x), int(player_y + offset_y), player_size, player_size))
        # Draw health bars
        # Player health bar
        pygame.draw.rect(screen, (0, 255, 0), (int(player_x + offset_x), int(player_y + offset_y) - 10, player_size * (player_health / 20), 5))  # Green bar
        pygame.draw.rect(screen, (255, 0, 0), (int(player_x + offset_x) + player_size * (player_health / 20), int(player_y+ offset_y) - 10, player_size * ((20 - player_health) / 20), 5))  # Red bar



        # Draw the enemies, relative to the camera
        for enemy in enemies:
            enemy.draw() #use the enemy's draw method
            # Enemy health bar
            health_bar_width = enemy.size * (enemy.health / enemy.max_health)
            pygame.draw.rect(screen, (0, 255, 0), (int(enemy.x + offset_x), int(enemy.y + offset_y) - 10, health_bar_width, 5))
            pygame.draw.rect(screen, (255, 0, 0), (int(enemy.x + offset_x) + health_bar_width, int(enemy.y + offset_y) - 10, enemy.size - health_bar_width, 5))

        # Draw the arrows, relative to the camera
        for arrow in arrows:
            pygame.draw.rect(screen, arrow_color, (int(arrow['x'] + offset_x), int(arrow['y'] + offset_y), arrow_width, arrow_height))

        wave_text = font.render(f"Wave: {game_wave}", True, (128,128,128)) #changed to grey
        screen.blit(wave_text, (10,10))

        #draw the timers
        if e_ability_active:
            time_left = e_ability_start_time + e_ability_duration - pygame.time.get_ticks() / 1000
            draw_timer(screen, time_left, 10, 50, (0, 255, 0))  # Green for active
            if time_left <= 0:
                e_ability_active = False
                player_speed = base_player_speed
                e_cooldown_start_time = pygame.time.get_ticks() / 1000
                print("E Ability Deactivated")
        else:
            time_left = e_cooldown_start_time + e_ability_cooldown - pygame.time.get_ticks() / 1000
            draw_timer(screen, time_left, 10, 50) #default grey
        if q_ability_active:
            time_left = q_ability_start_time + q_ability_duration - pygame.time.get_ticks() / 1000
            draw_timer(screen, time_left, 10, 100, (0, 255, 0))
            if time_left <= 0:
                q_ability_active = False
                double_arrows = False
                q_cooldown_start_time = pygame.time.get_ticks() / 1000
                print("Q Ability Deactivated")
        else:
            time_left = q_cooldown_start_time + q_ability_cooldown - pygame.time.get_ticks() / 1000
            draw_timer(screen, time_left, 10, 100)

        pygame.display.flip()

        # Collision detection
        for enemy in enemies[:]: # Iterate through a copy since we might remove
            if enemy.is_collision(player_x, player_y, player_size):
                print("Collision!")
                #check if it is time to deal damage
                if current_time - enemy.last_hit_time >= 1:
                    enemy.last_hit_time = current_time #update last hit time
                    player_health -= enemy.damage  # Player loses health
                    print(f"Player hit by {enemy.shape}, taking {enemy.damage} damage.Player health: {player_health}")
                    if player_health <= 0:
                        print("Game Over - Player Died")
                        game_over = True #setgame over
                if enemy.shape== "triangle": #remove triangle
                    enemies.remove(enemy)
                    enemy_count -= 1

        # Check for arrow collision with enemy
        for arrow in arrows[:]:
            for enemy in enemies[:]:
                if (
                    arrow['x'] < enemy.x + enemy.size
                    and arrow['x'] + arrow_width > enemy.x
                    and arrow['y'] < enemy.y + enemy.size
                    and arrow['y'] + arrow_height > enemy.y
                ):
                    print("Arrow hit enemy!")
                    arrows.remove(arrow)  # Remove the arrow that hit
                    enemy.health -= 1  # Reduce enemy health
                    if enemy.health <= 0:
                        print("Enemy defeated!")
                        enemies.remove(enemy)  # Remove the enemy
                        enemy_count -= 1
                        # Reposition the enemy, ensuring it's not too close to the player
                        while True:
                            enemy_x = random.randint(0, world_width - enemy_size)
                            enemy_y = random.randint(0, world_height - enemy_size)
                            if math.sqrt((enemy_x - player_x) ** 2 + (enemy_y - player_y) ** 2) > 150:  # Adjust 150 as needed
                                break
                        enemy_health = 3 # Reset enemy health
                    break  # Important: Only handle one arrow hit per frame

        # Enemy spawning logic
        if not enemies_spawned: # Only spawn if enemies haven't been spawned yet for this wave
            spawn_wave()

        # Wave management
        if enemy_count == 0 and wave_in_progress:
            print(f"Wave {game_wave} cleared.  Waiting for next wave.")
            wave_in_progress = False
            enemies_spawned = False
            wave_end_time = pygame.time.get_ticks() + 5000  # 5 second delay (5000 milliseconds)
        # Enemy spawning logic
        # (No need to spawn enemies here, handled by wave logic below)

        # Wave management
        if enemy_count == 0 and wave_in_progress:
            print(f"Wave {game_wave} cleared.  Waiting for next wave.")
            wave_in_progress = False
            enemies_spawned = False
            wave_end_time = pygame.time.get_ticks() + 5000  # 5 second delay (5000 milliseconds)

        if pygame.time.get_ticks() >= wave_end_time and not wave_in_progress and not enemies_spawned:
            spawn_wave()

        elif enemy_count > 0: #if there are still enemies
            wave_in_progress = True #keep wave in progress
