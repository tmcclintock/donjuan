import os

import matplotlib as mpl
import numpy as np

from donjuan import Dungeon, DungeonRandomizer, Renderer, RoomSizeRandomizer

np.random.seed(123)

# Create and randomize the dungeon
room_randomizer = RoomSizeRandomizer(max_size=8, min_size=6)
randomizer = DungeonRandomizer(max_num_rooms=10, room_size_randomizer=room_randomizer)
randomizer.seed(54321)
dungeon = Dungeon(30, 30, randomizers=[randomizer])

dungeon.randomize()
dungeon.emplace_rooms()

# Render the dungeon
renderer = Renderer()
file_path = "test.png"
renderer.render(dungeon, file_path=file_path)

# Look at it
mpl.image.imread(file_path)
mpl.pyplot.show()

# Delete the image from on disk
os.remove(file_path)
