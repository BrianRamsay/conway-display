# Conway's Game of Life

Written for the Matrix Portal M4 & 64x32 RGB Matrix using CircuitPython and Adafruit libraries.

Reads from \*.rle files to set the initial starting positions. There are two patterns included by default. Find more patterns at https://www.conwaylife.com/ and https://copy.sh/life/examples/.

Evolves from the starting position according to Game of Life rules
  - Living cells with 2 or 3 neighbors survive
  - Dead cells with 3 neighbors come alive
  - All other cells die (or stay dead)
 
The simulation restarts with a new random position if equilibrium is reached or 500 generations has passed.

## Installation

  - Edit parameters in `code.py` to match the size of the LED matrix.
  - Copy all repo contents to microcontroller, OR
	  - Copy `code.py` to your microcontroller.
	  - Copy the `lib/` directory to your microcontroller.
	  - Copy `boot.py` to your microcontroller.
	  - Copy `patterns/` to your microcontroller if you want more than 2 patterns
  - Add \*.rle files to `patterns/` to add more starting positions.

  **Note:** After the initial reboot, you will need to jump D1 to ground in order to write to the filesystem again. This is so that the python process can write to the filesystem and save patterns.

## Usage

Patterns are stored as \*.rle files in a patterns directory \\
Use the Reset button to start over with a new pattern.

TODO Toggle Speed, Color, or pattern with buttons \\
TODO Read new patterns from web url

## Pattern File

The format for the pattern files is expected to be like the ones from https://www.conwaylife.com. The only required line is the RLE itself. You can control how the pattern fits on display by providing the pattern extent or specifying it directly with a #X line.

Example:

    #N Name of Pattern. e.g., Glider
    #O Author/Originator. e.g., Richard K Guy
    #C Pattern information. e.g., The smallest, most common, and first discovered spaceship. Diagonal, has period 4 and speed c/4.
    #C Multiple #C lines are ok.
	#X designate a starting x and/or y for the pattern. e.g., x = 1, y= 1
    x = 3, y = 3, rule = B3/S23 # specify the extent of the pattern. Helps determine initial placement and fit in the matrix. Pattern will be centered if no #X is given.
    bob$2bo$3o!
