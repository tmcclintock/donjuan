import os

import matplotlib as mpl

from donjuan import Dungeon, RandomFilled, Renderer

# Instantiate donjuan objects
renderer = Renderer()
dungeon = Dungeon(n_rows=4, n_cols=5)
rng = RandomFilled()
rng.randomize_grid(dungeon.grid)

# Render the image
file_path = "test.png"
renderer.render(dungeon, file_path)

# Look at it
mpl.image.imread(file_path)
mpl.pyplot.show()

# Delete the image from on disk
os.remove(file_path)
