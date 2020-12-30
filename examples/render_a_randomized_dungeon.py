import os

import matplotlib as mpl

from donjuan import Dungeon, DungeonRoomRandomizer, Renderer, RoomRandomizer

# Create and randomize the dungeon
room_randomizer = RoomRandomizer(max_size=4)
randomizer = DungeonRoomRandomizer(max_num_rooms=10, room_randomizers=[room_randomizer])
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
