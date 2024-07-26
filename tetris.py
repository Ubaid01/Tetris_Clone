import pygame
import pickle
import sys
import random
import time
import datetime
import csv

# Some information for game rules is taken from :-  https://tetris.wiki/Scoring

# Define constants
GRID_WIDTH = 15
GRID_HEIGHT = 20
CELL_SIZE = 30
GRID_COLOR = (255, 255, 255)
EMPTY_COLOR = (0 , 0 , 0)
HIGH_SCORE_FILE = r"_internal\high_scores.csv" # Can also use .pkl ( python pickle file )
STREAK_FILE = r"_internal\abc.csv"

# Tetris block shapes with color information
SHAPES = [
    {'shape': [[0, 0, 1],
               [1, 1, 1]], 'color': ( 255 , 0 , 0 )  },  # Red

    {'shape': [[0, 2, 2],
               [2, 2, 0]], 'color': ( 0 , 255 , 0 ) },  # Green

    {'shape': [[3, 3, 0],
               [0, 3, 3]], 'color': ( 0 , 0 , 255 ) },  # Blue

    {'shape': [[4, 4, 4],
               [0, 4, 0]], 'color': ( 255 , 255 , 0 ) },  # Yellow

    {'shape': [[0, 5, 5, 0],
               [0, 5, 5, 0], ], 'color': ( 255 , 0 , 255 ) },  # Purple

    {'shape': [[0, 6, 0],
               [6, 6, 6], ], 'color': ( 0 ,  255 , 255 ) },  # Cyan

    {'shape': [[7, 0, 0],
               [7, 7, 7], ], 'color': ( 255 , 165 , 0 ) },  # Orange

    {'shape': [[0, 8, 0],
               [0, 8, 0],
               [0, 8, 0],
               [0, 8, 0]], 'color': ( 128 , 128 , 128 ) }  # Gray
]

class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.dx = random.uniform(-2, 2)
        self.dy = random.uniform(-2, 2)
        self.lifetime = random.randint(30, 60)  # Lifetime of the particle
        self.age = 0

    def update(self):
        self.x += self.dx
        self.y += self.dy
        self.age += 1

    def is_alive(self):
        return self.age < self.lifetime

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, (self.x, self.y, 5, 5))

class HighestStreak:
    def __init__(self, username, streak, total_time):
        self.username = username
        self.streak = streak
        self.total_time = total_time
    
class Tetris:
    def __init__(self):
        pygame.mixer.init() 
        pygame.font.init()
        self.width = GRID_WIDTH
        self.height = GRID_HEIGHT
        self.grid = [['.' for _ in range(self.width)] for _ in range(self.height)]
        self.color_grid = [[None for _ in range(self.width)] for _ in range(self.height)]
        self.screen_width = self.width * CELL_SIZE + 200  # Increased width for displaying next block and player info
        self.screen_height = self.height * CELL_SIZE
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption('Tetris')
        self.clock = pygame.time.Clock()
        self.speed_factor = 1.0  # Speed factor for block falling
        self.fall_interval = 500 / self.speed_factor  # milliseconds
        self.level = 0
        self.last_fall_time = 0
        self.current_block = self.create_new_block()
        self.next_block = self.create_new_block() 
        self.game_over = False
        self.offset = [self.width // 2 - len(self.current_block['shape'][0]) // 2, 0]
        self.points = 0
        self.player_name = None 
        self.high_scores = self.load_high_scores()
        self.soft_drops = 0
        self.hard_drops = 0
        self.highest_streak = self.load_highest_streak()
        self.current_streak = self.level  
        self.sounds = [r"_internal\start_game.mp3", r"_internal\sound_track.mp3"]  # List of sounds to play in sequence
        self.current_sound_index = 0
        self.play_sound(loop=True)
        self.menu()

    def menu(self):
        menu_font = pygame.font.Font(None, 36)
        menu_options = ["Instructions", "Play", "High Scores", "Close"]
        self.selected_option = 0

        while True:
            self.screen.fill((173, 216, 230))
            for i, option in enumerate(menu_options):
                color = (255, 255, 255) if i == self.selected_option else (128, 128, 128)
                text_surface = menu_font.render(option, True, color)
                text_rect = text_surface.get_rect(center=(self.screen_width // 2, 200 + i * 50))
                self.screen.blit(text_surface, text_rect)

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        if menu_options[self.selected_option] == "Instructions":
                            self.display_instructions()
                        elif menu_options[self.selected_option] == "Play":
                            self.screen.fill((173, 216, 230))
                            pygame.display.flip()

                            # Show a countdown for 5 seconds
                            countdown_font = pygame.font.Font(None, 72)
                            for i in range(5, 0, -1):
                                self.screen.fill((173, 216, 230))
                                countdown_text = countdown_font.render(str(i), True, (255, 255, 255))
                                countdown_rect = countdown_text.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
                                self.screen.blit(countdown_text, countdown_rect)
                                pygame.display.flip()
                                time.sleep(1)

                            self.get_player_name()
                            self.run()
                            return
                        elif menu_options[self.selected_option] == "High Scores":
                            self.display_high_scores()
                        elif menu_options[self.selected_option] == "Close":
                            pygame.quit()
                            sys.exit()
                    elif event.key == pygame.K_UP:
                        self.selected_option = (self.selected_option - 1) % len(menu_options)
                    elif event.key == pygame.K_DOWN:
                        self.selected_option = (self.selected_option + 1) % len(menu_options)

    def display_instructions(self):
        instruction_font = pygame.font.Font(None, self.screen_height // 23)
        instructions = [
            "Instructions:",
            "- Use the LEFT and RIGHT arrow keys to move the blocks horizontally.",
            "- Use the DOWN arrow key to make the block fall faster(SOFT-DROP).",
            "- Use the UP arrow key with key to rotate the block.",
            "- Use the END key to quickly move block to bottom(HARD-DROP).",
            "- Complete horizontal lines to clear them and earn points.",
            "- The game ends when the blocks reach the top of the grid." ,
            "- Try your best to beat the highest score and become the Ultimate Champion." ,
            "- Scoring System is Like :- " , 
            "- For 1 , 2 , 3 lines cleared :- 40 , 100 , 300 , 1200 * (level + 1)." ,
            "- For SOFT_DROP ( 1 point per cell ) ; For HARD_DROP ( 2 points per cell )" , 
            "- Rule to achieve best streak is reaching previous maximum level in short time." , 
        ]

        while True:
            self.screen.fill((173, 216, 230))
            for i, line in enumerate(instructions):
                text_surface = instruction_font.render(line, True, (128 , 128 , 128))
                text_rect = text_surface.get_rect(center=(self.screen_width // 2, 100 + 1.25*i * 30))
                self.screen.blit(text_surface, text_rect)

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN or event.key == pygame.K_ESCAPE:
                        return

    def create_new_block(self):
        self.last_fall_time = pygame.time.get_ticks()
        block = random.choice(SHAPES)
        if self.level >= 2: 
            block['color'] = ( random.randint( 1 , 254 ), random.randint( 1 , 254 ) , random.randint( 1 , 254 ) ) # Directly changed the Sequence "SHAPES" colour each time.
        return {'shape': block['shape'], 'color': block['color']}

    def draw_grid(self):
        for y in range(self.height):
            for x in range(self.width):
                if self.grid[y][x] == '.':
                    # If the cell is empty, check if it contains a placed block with a color
                    color = self.color_grid[y][x]
                    if color is None:
                        color = EMPTY_COLOR
                else:
                    color = self.color_grid[y][x] if self.color_grid[y][x] is not None else self.current_block['color']
                pygame.draw.rect(self.screen, color, (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE))
                pygame.draw.rect(self.screen, GRID_COLOR, (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE), 1)

    def draw_block(self, block, offset):
        for y, row in enumerate(block['shape']):
            for x, cell in enumerate(row):
                if cell != 0:
                    color = block['color']
                    pygame.draw.rect(self.screen, color, ((x + offset[0]) * CELL_SIZE, (y + offset[1]) * CELL_SIZE, CELL_SIZE, CELL_SIZE))

    def draw_next_block(self):
        next_block_font = pygame.font.Font(None, 24)
        next_block_text = next_block_font.render("Next Block:", True, (255, 255, 255))
        next_block_rect = next_block_text.get_rect(center=(self.screen_width - 97, 50))
        self.screen.blit(next_block_text, next_block_rect)

        # Draw box border around the next block
        pygame.draw.rect(self.screen, (255, 255, 255), (self.screen_width - 162, 100, 135, 153), 2)

        # Draw next block shape
        next_block_shape = self.next_block['shape']
        for y, row in enumerate(next_block_shape):
            for x, cell in enumerate(row):
                if cell != 0:
                    color = self.next_block['color']
                    pygame.draw.rect(self.screen, color, ((x + self.width + 1.25) * CELL_SIZE + 20, (y + 3.25) * CELL_SIZE + 20, CELL_SIZE, CELL_SIZE))

    def draw_player_info(self):
        player_info_font = pygame.font.Font(None, 24)
        player_name_text = player_info_font.render(f"Player: {self.player_name}", True, (255, 255, 255))
        player_name_rect = player_name_text.get_rect(center=(self.screen_width - 100, 300))
        self.screen.blit(player_name_text, player_name_rect)
        player_score_text = player_info_font.render(f"Score: {self.points}", True, (255, 255, 255))
        player_score_rect = player_score_text.get_rect(center=(self.screen_width - 100, 350))
        self.screen.blit(player_score_text, player_score_rect)
        level_text = player_info_font.render(f"Level: {self.level}", True, (255, 255, 255))
        level_rect = level_text.get_rect(center=(self.screen_width - 100, 400))
        self.screen.blit(level_text, level_rect)

    def check_collision(self, block, offset):
        for y, row in enumerate(block['shape']):
            for x, cell in enumerate(row):
                if cell != 0:
                    if y + offset[1] >= self.height or x + offset[0] < 0 or x + offset[0] >= self.width or self.grid[y + offset[1]][x + offset[0]] != '.':
                        return True
        return False

    def merge_block(self):
        for y, row in enumerate(self.current_block['shape']):
            for x, cell in enumerate(row):
                if cell != 0:
                    self.grid[y + self.offset[1]][x + self.offset[0]] = 'x'
                    self.color_grid[y + self.offset[1]][x + self.offset[0]] = self.current_block['color']

    def check_lines(self):
        lines_cleared = 0
        for y in range(self.height):
            if '.' not in self.grid[y]:
                del self.grid[y]
                self.grid.insert(0, ['.'] * self.width)
                # Clear color information for the cleared line
                del self.color_grid[y]
                self.color_grid.insert(0, [None] * self.width)
                lines_cleared += 1
        # Calculate score based on lines cleared and current level ( Same as Original Tetris )
        if lines_cleared == 1:
            self.points += 40 * (self.level + 1) # Update points
        elif lines_cleared == 2:
            self.points += 100 * (self.level + 1)
        elif lines_cleared == 3:
            self.points += 300 * (self.level + 1)
        elif lines_cleared >= 4:  # Tetris
            self.points += 1200 * (self.level + 1)
            # self.points += lines_cleared * 100  # MY Deprecated One 
        return lines_cleared

    def check_mega_tetris(self, lines_cleared):
        if lines_cleared >= 4: 
            self.fade_lines()
            pygame.mixer.music.load(r"_internal\mega_tetris_sound.mp3")
            pygame.mixer.music.play(-1)
            self.display_message("Mega Tetris!")
            pygame.time.wait(2000)
            self.play_sound(loop = False)

    def fade_lines(self):
        for i in range(255, 0, -10):
            self.screen.fill((0, 0, 0))
            self.draw_grid()
            alpha_surface = pygame.Surface((self.screen_width, self.screen_height))
            alpha_surface.set_alpha(i)
            self.screen.blit(alpha_surface, (0, 0))
            pygame.display.flip()
            pygame.time.delay(50)
    
    def display_level_up_animation(self):
        # Create particles
        particles = []
        num_particles = 100

        for _ in range(num_particles):
            x = random.randint(0, self.screen_width)
            y = random.randint(0, self.screen_height)
            color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            particle = Particle(x, y, color)
            particles.append(particle)

        pygame.mixer.music.load(r"_internal\level_upgrade.mp3")
        pygame.mixer.music.play()

        duration = 2000  # milliseconds
        start_time = pygame.time.get_ticks()
        while ( pygame.time.get_ticks() - start_time < duration ) :
            # Update particles
            for particle in particles:
                particle.update()
            # Draw particles
            self.screen.fill((0, 0, 0))  # Clear the screen
            for particle in particles:
                if particle.is_alive():
                    particle.draw(self.screen)
            self.display_message(f"Level {self.level} reached!")
            pygame.display.flip()
            pygame.time.delay(20)  # Delay between frames

        self.fade_lines()
        pygame.time.wait(600)
        self.play_sound(loop=False)

    def display_message(self, message):
        message_font = pygame.font.Font(None, 72)
        message_text = message_font.render(message, True, (255, 255, 255))
        message_rect = message_text.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
        self.screen.blit(message_text, message_rect)
        pygame.display.flip()

    def play_sound(self, loop=False):
        pygame.mixer.music.load( self.sounds[self.current_sound_index] )
        pygame.mixer.music.play(-1 if loop else 0)

        # Increment current_sound_index for the next sound sequence
        self.current_sound_index = (self.current_sound_index + 1) % len(self.sounds)

    def move_block(self, direction):
        new_offset = [self.offset[0] + direction[0], self.offset[1] + direction[1]]
        if not self.check_collision(self.current_block, new_offset):
            self.offset = new_offset
            return True
        return False

    def rotate_block(self):
        rotated_block = [[self.current_block['shape'][y][x] for y in range(len(self.current_block['shape']))] for x in range(len(self.current_block['shape'][0]) - 1, -1, -1)]
        # Check if the rotation will go beyond the grid dimensions
        if self.offset[0] + len(rotated_block[0]) > self.width or self.offset[1] + len(rotated_block) > self.height:
            return  # Cancel rotation if it exceeds the grid dimensions
        self.current_block['shape'] = rotated_block

    def get_player_name(self):
        input_font = pygame.font.Font(None, 36)
        input_text = ""
        while True:
            self.screen.fill((0, 0, 0))
            prompt_text = input_font.render("Enter Your Name:", True, (255, 255, 255))
            prompt_rect = prompt_text.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
            self.screen.blit(prompt_text, prompt_rect)

            input_rendered = input_font.render(input_text, True, (255, 255, 255))
            input_rect = input_rendered.get_rect(center=(self.screen_width // 2, self.screen_height // 2 + 50))
            self.screen.blit(input_rendered, input_rect)

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        if input_text.strip():
                            # Truncate player name if longer than 10 characters
                            self.player_name = input_text.strip()[:10]
                            return
                    elif event.key == pygame.K_BACKSPACE:
                        input_text = input_text[:-1]
                    else:
                        input_text += event.unicode

    def run(self):
        running = True
        highest_streak_time = 0  # Track the time for highest streak
        start_time = pygame.time.get_ticks()  # Record start time
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or event.type == pygame.K_ESCAPE:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        self.move_block([-1, 0])
                    elif event.key == pygame.K_RIGHT:
                        self.move_block([1, 0])
                    elif event.key == pygame.K_DOWN:
                        # Increment point for each SOFT_DROP cell
                        self.soft_drops += 1
                        self.move_block([0, 1])
                    elif event.key == pygame.K_UP:
                        # Rotate block
                        self.rotate_block()
                    elif event.key == pygame.K_UP and (event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT):
                        # Rotate block and move left or right simultaneously
                        self.rotate_block()
                        if event.key == pygame.K_LEFT:
                            self.move_block([-1, 0])
                        elif event.key == pygame.K_RIGHT:
                            self.move_block([1, 0])
                    elif event.key == pygame.K_END:
                    # Find the maximum possible downward movement for the block
                        max_downward_movement = 0
                        while self.move_block([0, 1]):
                            max_downward_movement += 1
                        # Move the block to the bottom of its column
                        for _ in range(max_downward_movement):
                            self.move_block([0, 1]) 
                        self.hard_drops += max_downward_movement * 2
                        
            # Automatic falling of blocks
            current_time = pygame.time.get_ticks()
            if current_time - self.last_fall_time > self.fall_interval:
                self.last_fall_time = current_time
                lines_cleared = 0
                if not self.move_block([0, 1]):
                    self.merge_block()
                    lines_cleared = self.check_lines()
                    if lines_cleared > 0:
                        # Increase speed factor when lines are cleared and level when speed reaches to next integer
                        self.speed_factor += ( 0.1 * lines_cleared ) 
                        self.points += ( self.soft_drops + self.hard_drops ) # Only add cell_points when lines are cleared
                        self.soft_drops = self.hard_drops = 0 
                        if self.speed_factor >= ( self.level + 2 ) :
                            self.level += 1
                            self.current_streak += 1  # Increment current streak when level increases
                            self.display_level_up_animation() 
                    if any(cell != '.' for cell in self.grid[0]) :
                        self.game_over = True
                        highest_streak_time = pygame.time.get_ticks() - start_time
                        # Check if level is higher than previous So streak MUST BE replaced BUT if level is same as previous BUT time takes is lower so then also run this block
                        if self.highest_streak is not None:
                            if (self.level > self.highest_streak.streak) or ( ( self.level == self.highest_streak.streak) and highest_streak_time < self.highest_streak.total_time) :
                                self.highest_streak = HighestStreak(self.player_name, self.current_streak, highest_streak_time)
                                self.save_highest_streak()
                        elif self.level >= 0 and highest_streak_time < float('inf'):
                            self.highest_streak = HighestStreak(self.player_name, self.current_streak, highest_streak_time)
                            self.save_highest_streak()
                        self.show_game_over_screen(highest_streak_time)
                        return
                    self.current_block = self.next_block  # Set the next block as the current block
                    self.next_block = self.create_new_block()  # Create a new next block
                    self.offset = [self.width // 2 - len(self.current_block['shape'][0]) // 2, 0]

                # Check for mega tetris
                self.check_mega_tetris(lines_cleared)

            self.screen.fill((0, 0, 0))
            self.draw_grid()
            self.draw_block(self.current_block, self.offset)
            self.draw_next_block() 
            self.draw_player_info()  
            pygame.display.flip()
            self.clock.tick(30 * self.speed_factor)  # Adjust the clock tick based on the speed factor

        # pygame.quit()
        # sys.exit()
        

    def show_game_over_screen(self , highest_streak_time):
        game_over_font = pygame.font.Font(None, 72)
        game_over_text = game_over_font.render("Game Over", True, (255, 255, 255) )
        game_over_rect = game_over_text.get_rect(center=(self.screen_width // 2, self.screen_height // 2 - 90))

        points_font = pygame.font.Font(None, 36)
        points_text = points_font.render(f"Points: {self.points}", True, (255, 255, 255))
        points_rect = points_text.get_rect(center=(self.screen_width // 2, self.screen_height // 2 + 20))

        # Calculate survival time
        survival_time_font = pygame.font.Font(None, 28)
        survival_time = self.format_time(float(highest_streak_time / 1000))
        survival_time_text = survival_time_font.render(f"Survival Time: {survival_time}", True, (255, 255, 255))
        survival_time_rect = survival_time_text.get_rect(center=(self.screen_width // 2, self.screen_height // 2 + 60))

        self.screen.fill(( 0 , 0 , 0 ))
        self.screen.blit(game_over_text, game_over_rect)
        self.screen.blit(survival_time_text, survival_time_rect) 
        self.screen.blit(points_text, points_rect)
        pygame.display.flip()
        pygame.mixer.music.load(r"_internal\game_over.mp3")
        pygame.mixer.music.play()

        # Save high score
        self.save_high_score()

        # Display level reached
        level_font = pygame.font.Font(None, 34)
        level_text = level_font.render(f"Level Reached: {self.level}", True, (255, 255, 255))
        level_rect = level_text.get_rect(center=(self.screen_width // 2, self.screen_height // 2 + 105))
        self.screen.blit(level_text, level_rect)

        # Wait for a while before proceeding
        text_font = pygame.font.Font(None, 28)
        text = text_font.render(f"Press Escape to Return to Menu.", True, (255, 255, 0 ))
        text_rect = text.get_rect(center=(self.screen_width // 2, self.screen_height // 2 + 145))
        self.screen.blit(text, text_rect)
        pygame.display.flip()

        # Wait for user input to either return to menu or exit game
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        waiting = False
                        # self.menu()  # Go back to the menu
                        self.__init__()  # Reinitialize the game
                else :
                # If the loop ends, it means the user didn't press Escape and wants to exit the game
                    pygame.time.wait(5000)
                    pygame.quit()
                    sys.exit()

    def load_highest_streak(self):
        try:
            with open(STREAK_FILE, 'rb') as file:
                highest_streak = pickle.load(file)
        except FileNotFoundError:
            # If file doesn't exist, set highest streak to None
            highest_streak = None

        return highest_streak  # Return the loaded highest streak
        
    def save_highest_streak(self):
        if self.highest_streak:
            # with open(STREAK_FILE, 'w', newline='') as file:
            #     writer = csv.writer(file)
            #     writer.writerow([self.highest_streak.username, str(self.highest_streak.streak), str(self.highest_streak.total_time)])
             with open(STREAK_FILE, 'wb') as file:
                pickle.dump(self.highest_streak, file)

    def load_high_scores(self):
        try:        
            with open(HIGH_SCORE_FILE, "rb") as file:
                high_scores = pickle.load(file)
            return high_scores
        except FileNotFoundError:
            return []

    def save_high_score(self):
        current_datetime = datetime.datetime.now().strftime("%d-%b-%Y %H:%M:%S") # %b instead of %m for month names
        score_entry = [current_datetime, self.player_name, str(self.points)]  # Store in list for CSV format
        self.high_scores.append(score_entry)

        # Sort the high scores list based on the scores
        self.high_scores.sort(key=lambda x: int(x[-1]) if x[-1].isdigit() else float('-inf'), reverse=True)


        last_rank = 0 
        # Update ranks based on position in the sorted list
        for rank, entry in enumerate(self.high_scores, start=1):
            # Check if the rank already exists for the entry
            if len(entry) == 3:  
                entry.insert(0, str(rank))  # Insert rank at the beginning of each new entry
                last_rank = rank  # Update the last assigned rank
            else:
                entry[0] = str(last_rank + 1)  # Update the existing rank to the next available rank
                last_rank += 1 

        # Limit the high scores to the top 8 scores
        self.high_scores = self.high_scores[:8]

        # Write the updated high scores list to the binary file using pickle
        with open(HIGH_SCORE_FILE, "wb") as file:
            pickle.dump(self.high_scores, file)

    def format_time(self , seconds):
        hours = round( seconds // 3600 , 2 )
        minutes = round( (seconds % 3600) // 60 , 2 )
        # print(f"{type(hours)} , {type(minutes)} , {type(hours)}") # CHECK-LABEL
        seconds = round( seconds % 60 , 3 )
        return f"{hours} hrs {minutes} min {seconds} sec"
    
    def display_high_scores(self):
        high_score_font = pygame.font.Font(None, 36)
        title_text = high_score_font.render("High Scores", True, ( 0 , 0 , 0 ))
        title_rect = title_text.get_rect(center=(self.screen_width // 2, 50))
        self.screen.fill((173, 216, 230))
        self.screen.blit(title_text, title_rect)

        # Display headers
        headers = ['Rank', 'Date', 'Player', 'Score']
        total_width = len(headers) * 150  # Total width of all headers
        start_x = ( (self.screen_width - total_width) // 2 ) - 7.5

        for i, header in enumerate(headers):
            header_text = high_score_font.render(header, True, ( 28 , 128 , 128 ))
            header_rect = header_text.get_rect(center=(start_x + (i * 150) + 75, 100))  
            self.screen.blit(header_text, header_rect)

        line_height = 40
        high_score_font = pygame.font.Font(None, 26)
        # Display high scores
        for i, score in enumerate(self.high_scores):
            for j, data in enumerate(score):
                column_width = self.screen_width // len(score)
                x_position = (column_width * j) + (column_width // 2)
                y_position = 150 + i * line_height
                
                # Truncate player name if longer than 10 characters for proper formatting
                if j == 2:  # Player name column
                    data = data[:10] if len(data) > 10 else data
                score_text = high_score_font.render(data, True, ( 28 , 128 , 128 ))
                score_rect = score_text.get_rect(center=(x_position, y_position))
                self.screen.blit(score_text, score_rect)

        # Display highest streak information
        if self.highest_streak :
            high_streak_font = pygame.font.Font( None , 23 )
            total_formatted_time = self.format_time(float(self.highest_streak.total_time / 1000))
            highest_streak_text = high_streak_font.render(f"Best Streak :- \"{self.highest_streak.username}\" reached in {self.highest_streak.streak} levels, taking time ({total_formatted_time}).", True, ( 0 , 0 , 0 ) )
            highest_streak_rect = highest_streak_text.get_rect(center=(self.screen_width // 2, 530))
            self.screen.blit(highest_streak_text, highest_streak_rect)
        else:
            highest_streak_text = high_score_font.render("Highest Streak: None", True, (255, 255, 255))
            highest_streak_rect = highest_streak_text.get_rect(center=(self.screen_width // 2, 550))
            self.screen.blit(highest_streak_text, highest_streak_rect)

        pygame.display.flip()
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN or event.key == pygame.K_ESCAPE:
                        return

if __name__ == "__main__":
    tetris_game = Tetris()