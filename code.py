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
# TODO check for up/down buttons (pattern rotate? speed change?)
# TODO figure out button listening during sleep (timers?)
# TODO Optimize nextgen calculation and display
# TODO make grid larger than display to avoid edge artifacts
# TODO patterns to add
# https://copy.sh/life/examples/
# https://copy.sh/life/?pattern=blinkerpuffer1
# https://copy.sh/life/?pattern=blinkerpuffer2
# https://copy.sh/life/?pattern=hivenudger2
# https://copy.sh/life/?pattern=noahsark
# https://copy.sh/life/?pattern=puffer1
# https://copy.sh/life/?pattern=puffer2
# https://copy.sh/life/?pattern=pufferfish

# Notes to self. CircuitPython has no: 
# re.findall(), isAlpha(), isDigit(), os.path.isDir(), FileExistsError

import time
import random
import os
import re
import displayio
from adafruit_matrixportal.matrix import Matrix

MATRIX_WIDTH=64
MATRIX_HEIGHT=32
COLORS=5
MAX_GENERATIONS=500
TIMING_ON=False
PATTERNS_DIR='patterns'


# Create the patterns directory and add patterns if it doesn't exist
# Tried with a FileExistsError and found that doesn't exist in CircuitPython
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

def get_blank_grid():
    return [[0]*MATRIX_WIDTH for i in range(0,MATRIX_HEIGHT)]

def get_starting_grid():
    print()
    grid = get_blank_grid()

    # 1 in 25 chance of a random 50% fill
    if not random.randint(0,24):
      name = 'random fill'
      for row in range(0,MATRIX_HEIGHT):
        for col in range(0,MATRIX_WIDTH):
          grid[row][col] = random.randint(0,1)

    # create grid from a pattern file
    else:
        name, author, comment, rule, rle = '','','','',''
        x_extent, y_extent = 0,0

        # Get the information from a random file
        # -------------------------
        patternfile = random.choice(os.listdir(PATTERNS_DIR))
        extent_details = re.compile("x ?= ?(\d+).*y ?= ?(\d+)(.*rule ?=(.*))?")
        print(f"Loading {patternfile}")
        for line in open(f"{PATTERNS_DIR}/{patternfile}",'r'):
            if line[0] == '#':
                if line[1] == 'N':
                    name += line[2:].strip()
                elif line[2] == 'O':
                    author += line[2:].strip()
                else: # treat unknown comments as 'C' comments
                    comment += line[2:].strip()
            elif line[0] == 'x':
		match = extent_details.match(line)
                if match:
                    (x_extent, y_extent, throwaway, rule) = match.groups()

            # we are left with the RLE
            elif line.strip():
                rle += line.strip()


        # Create grid from pattern
        # -------------------------
	x_extent, y_extent = int(x_extent), int(y_extent)
        if x_extent > MATRIX_WIDTH or y_extent > MATRIX_HEIGHT:
            print(f"The pattern from {patternfile} is too big!")
            return get_starting_grid() # try again

        # Find pattern starting position
        # Center the pattern (or put it in the top-left corner)
        # TODO rotate if necessary
        x,y= 5,5
        if x_extent:
            x = (MATRIX_WIDTH-x_extent) // 2
        if y_extent:
            y = (MATRIX_HEIGHT-y_extent) // 2

        # Expand RLE and add to grid
        print(f"Expanding {rle}")
        is_digit = re.compile("\d")
        is_alpha = re.compile("[a-zA-Z]")
        x_start = x
        for line in rle.split("$"):
            counter = ''
            for c in line:
                if is_digit.match(c):
                    counter += c
                elif is_alpha.match(c):
                    counter = counter or '1'
                    for xx in range(x, x+int(counter)):
                        #print(f"Updating grid position x: {xx}, y: {y}, val: {c}")
                        grid[y][xx] = 0 if c == 'b' else 1
                    x += int(counter)
                    counter = ''
                else:
                    pass
            y += 1
            x = x_start

    # done creating grid
            
    grid_color = random.randint(0,COLORS-1)
    if not grid_color:
	grid_color = 'multicolor'

    print(f"Starting {name or patternfile} with color {grid_color}")
    return grid, grid_color

def live_cells(row, col, grid):
    neighbors = 0
    min_col = col - 1 if col > 0 else col
    if row > 0:
        neighbors += sum(grid[row-1][min_col:col+2])

    neighbors += sum(grid[row][min_col:col+2])
    neighbors -= grid[row][col] # remove the middle

    if row < MATRIX_HEIGHT - 1:
        neighbors += sum(grid[row+1][min_col:col+2])

    return neighbors
    
def next_population(oldgrid):
    # seems naive
    new_grid = get_blank_grid()
    for row in range(0,MATRIX_HEIGHT):
        for col in range(0,MATRIX_WIDTH):
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
      	    bitmap[col,row] = grid[row][col] * random_color

    display.show(group)


#####################################################
# Start the hot Conway action!
#####################################################
restart = True
while True:
    if restart:
	if TIMING_ON:
	    tic = time.monotonic()
	grid, grid_color = get_starting_grid()
	if TIMING_ON:
	    toc = time.monotonic()
	    print(f"{toc - tic:0.4f} seconds to create starting grid")
	prev_grid = grid        # detect equilibrium
	prev_prev_grid = None   # detect simple cycle
	generation = 0
	restart = False

    # TODO Check for button presses

    if TIMING_ON:
	tic = time.monotonic()
    display_grid(grid, grid_color)
    if TIMING_ON:
	toc = time.monotonic()
	print(f"{toc - tic:0.4f} seconds to display grid")
    if generation == 0:
        time.sleep(5)

    prev_prev_grid = prev_grid
    prev_grid = grid
    if TIMING_ON:
	tic = time.monotonic()
    grid = next_population(grid)
    generation += 1

    if TIMING_ON:
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
        print("Starting New Pattern")
	restart = True