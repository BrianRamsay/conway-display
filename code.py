#### Conway Game of Life for LED Matrix
#
# See README.md
#
#### Implementation Details
#
# Creates a directory with two patterns if one doesn't exist.
# Randomly selects a starting position from the patterns/ directory
#   If the pattern is too big for the matrix, a new pattern is selected.
# The starting position is set up in a grid of 1s and 0s, maintained
#   separately from the displayio Bitmap.
#
# Main loop
#  - get new starting grid if needed
#  - display the grid
#  - get the next population
#  - check for an end state (to restart)
#
# TODO automatically rotate patterns?
# TODO check for up/down buttons (pattern switch? speed change?)
# TODO figure out button listening during sleep (timers?)
# TODO Optimize nextgen calculation and display

# Notes to self. CircuitPython has no: 
# re.findall(), isAlpha(), isDigit(), os.path.isDir(), FileExistsError

import time
import random
import os
import re
import displayio
from adafruit_matrixportal.matrix import Matrix

# --------------------------------------------------
# Change parameters to suit your application
# --------------------------------------------------
MATRIX_WIDTH=64     # width of the LED matrix
MATRIX_HEIGHT=32    # height of the LED matrix
GRID_MARGIN=2       # undisplayed pixels at the edge of the grid

COLORS=1024         # number of random colors to choose from
MAX_GENERATIONS=500 # number of generations before a restart

TIMING_OUTPUT=True # display timing information for generation and display
PATTERNS_DIR='patterns' # directory where we store the *.rle patterns

# Create the patterns directory and add patterns if it doesn't exist
# XXX waiting for boot.py and pin jumper setup
"""
os.mkdir(PATTERNS_DIR)
with open(f"{PATTERNS_DIR}/rpentomino.rle",'w') as file:
    file.write("#N R-Pentomino\n#C A methuselah with lifespan 1103.\n#C www.conwaylife.com/wiki/index.php?title=R-pentomino\nx = 3, y = 3, rule = B3/S23\nb2o$2ob$bo!")
with open(f"{PATTERNS_DIR}/glider.rle",'w') as file:
    file.write("#N Glider\n#O Richard K. Guy\n#C www.conwaylife.com/wiki/index.php?title=Glider\nx = 3, y = 3, rule = B3/S23\nbob$2bo$3o!")
print("Created patterns directory with two patterns.")
"""

# --- Drawing setup ---
matrix = Matrix()
display = matrix.display
group = displayio.Group(max_size=22)
bitmap = displayio.Bitmap(MATRIX_WIDTH, MATRIX_HEIGHT, COLORS)

color = displayio.Palette(COLORS)
color[0] = (0,0,0)
for i in range(1,COLORS):
  color[i] = (random.randint(0,255), random.randint(0,255), random.randint(0,255))

group.append(displayio.TileGrid(bitmap, pixel_shader=color))
# ---------------------

GRID_WIDTH = MATRIX_WIDTH + GRID_MARGIN * 2
GRID_HEIGHT = MATRIX_HEIGHT + GRID_MARGIN * 2
def init_grid(random_fill=False):
    return [[random.randint(0,1) if random_fill else 0]*GRID_WIDTH 
            for i in range(0,GRID_HEIGHT)]

def get_starting_grid():
    random_fill = not random.randint(0,24)   # 1 in 25 chance of a random 50% fill
    grid = init_grid(random_fill)

    # create grid from a pattern file
    if not random_fill:
        name, author, comment, rule, rle = '','','','',''
        x_extent, y_extent, x_start, y_start = 0,0,0,0

        # --------------------------------------------------
        # Get the information from a random pattern file
        # --------------------------------------------------
        patternfile = random.choice(os.listdir(PATTERNS_DIR))
        extent_details = re.compile("x ?= ?(\d+).*y ?= ?(\d+)(.*rule ?=(.*))?")
        start_details = re.compile("(x ?= ?(\d+))?,? ?(y ?= ?(\d+))?")
        print(f"Loading {patternfile}")
        for line in open(f"{PATTERNS_DIR}/{patternfile}",'r'):
            if line[0] == '#':
                if line[1] == 'N':
                    name += line[2:].strip()
                elif line[1] == 'O':
                    author += line[2:].strip()
                elif line[1] == 'X':
                    match = start_details.match(line[2:].strip())
                    if match:
                        (toss, x_start, toss, y_start) = match.groups()
                else: # treat unknown comments as 'C' comments
                    comment += line[2:].strip()
            elif line[0] == 'x':
		match = extent_details.match(line)
                if match:
                    (x_extent, y_extent, toss, rule) = match.groups()

            # we are left with the RLE
            elif line.strip():
                rle += line.strip()


        # --------------------------------------------------
        # Create grid from pattern
        # --------------------------------------------------

	x_extent, y_extent = int(x_extent), int(y_extent)
        if x_extent > GRID_WIDTH or y_extent > GRID_HEIGHT:
            print(f"The pattern from {patternfile} is too big!")
            return get_starting_grid() # try again

        # Find pattern starting position
        # TODO rotate if necessary
        x,y= 5,5        # if we don't know anything about it
        if x_start:     # if the pattern tells us where to start
            x = int(x_start)
        elif x_extent:  # if we know the size of the pattern
            x = (GRID_WIDTH-x_extent) // 2

        if y_start:     # if the pattern tells us where to start
            y = int(y_start)
        elif y_extent:    # if we know the size of the pattern
            y = (GRID_HEIGHT-y_extent) // 2

        # Expand RLE and add to grid
        print(f"Expanding {rle}")
        is_digit = re.compile("\d")
        is_alpha = re.compile("[a-zA-Z]")
        x_reset = x
        counter = ''
        for char in rle:
            if char == "$":
                counter = ''
                y += 1
                x = x_reset
            if is_digit.match(char):
                counter += char
            elif is_alpha.match(char):
                counter = counter or '1'
                for xx in range(x, x+int(counter)):
                    #print(f"Updating grid position x: {xx}, y: {y}, val: {char}")
                    grid[y][xx] = 0 if char == 'b' else 1
                x += int(counter)
                counter = ''
            else:
                pass

    # done creating grid
            
    global color
    grid_color = random.randint(0,COLORS-1)
    disp_color = f"{color[grid_color]:02X}"
    if not random.randint(0,19): # 5% chance for multicolor
	grid_color = 'multicolor'
        disp_color = grid_color

    print(f"Starting {'random_fill' if random_fill else patternfile} with color {disp_color}")
    return grid, grid_color

def live_cells(row, col, grid):
    neighbors = 0
    min_col = col - 1 if col > 0 else col
    if row > 0:
        neighbors += sum(grid[row-1][min_col:col+2])

    neighbors += sum(grid[row][min_col:col+2])
    neighbors -= grid[row][col] # remove the middle

    if row < GRID_HEIGHT - 1:
        neighbors += sum(grid[row+1][min_col:col+2])

    return neighbors
    
def next_population(oldgrid):
    # seems naive
    new_grid = init_grid()
    for row in range(0,GRID_HEIGHT):
        for col in range(0,GRID_WIDTH):
            alive = bool(oldgrid[row][col])
	    cell_count = live_cells(row, col, oldgrid)
            new_grid[row][col] = int(
                (alive and cell_count in [2,3]) or
                (not alive and cell_count == 3))
    return new_grid

def display_grid(grid, grid_color):
    # seems naive - better to only change the pixels that have changed
    global bitmap
    global display

    random_color = grid_color
    for row in range(0,MATRIX_HEIGHT):
        for col in range(0,MATRIX_WIDTH):
	    if grid_color == 'multicolor':
		random_color = random.randint(1,COLORS-1) # avoid black
      	    bitmap[col,row] = grid[row+GRID_MARGIN][col+GRID_MARGIN] * random_color

    display.show(group)


#####################################################
# Start the hot Conway action!
#####################################################
restart = True
while True:
    if restart:
	if TIMING_OUTPUT:
	    tic = time.monotonic()
	grid, grid_color = get_starting_grid()
	if TIMING_OUTPUT:
	    toc = time.monotonic()
	    print(f"{toc - tic:0.4f} seconds to create starting grid")
	prev_grid = grid        # detect equilibrium
	prev_prev_grid = None   # detect simple cycle
	generation = 0
	restart = False

    # TODO Check for button presses

    if TIMING_OUTPUT:
	tic = time.monotonic()
    display_grid(grid, grid_color)
    if TIMING_OUTPUT:
	toc = time.monotonic()
	print(f"{toc - tic:0.4f} seconds to display grid")
    if generation == 0:
        time.sleep(5)

    prev_prev_grid = prev_grid
    prev_grid = grid
    if TIMING_OUTPUT:
	tic = time.monotonic()
    grid = next_population(grid)
    generation += 1

    if TIMING_OUTPUT:
	toc = time.monotonic()
	print(f"{toc - tic:0.4f} seconds to generate next population")

    # Check for end states
    if prev_prev_grid == grid:
        print("Cycle Detected")
	restart = True

    if prev_grid == grid:
        print(f"Equilibrium reached in generation {generation}")
	restart = True

    if generation > MAX_GENERATIONS:
        print(f"{MAX_GENERATIONS} generations reached! Starting over")
	restart = True
