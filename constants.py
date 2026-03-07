# constants.py

# Conversion factor: 1 Stud = 0.5 Meters 
# (You mentioned 0.5 in your previous math_utils, adjust if needed)
METERS_TO_STUDS = 1.0 / 0.5

# Scale applied when exporting the FBX to Roblox.
# Blender exports in cm by default, which can make meshes huge in Roblox.
# Adjust this if your meshes are importing too large or too small.
FBX_EXPORT_SCALE = 0.001 * METERS_TO_STUDS


# Roblox API Details
ASSETS_API_URL = "https://apis.roblox.com/assets/v1/assets"
MULTIPART_BOUNDARY = "----WebKitFormBoundaryRbxBlenderAddon123"

# A comprehensive list of Roblox BasePart Materials
ROBLOX_MATERIALS = [
    ('Asphalt', "Asphalt", ""),
    ('Basalt', "Basalt", ""),
    ('Brick', "Brick", ""),
    ('Cardboard', "Cardboard", ""),
    ('Carpet', "Carpet", ""),
    ('CeramicTiles', "Ceramic Tiles", ""),
    ('ClayRoofTiles', "Clay Roof Tiles", ""),
    ('Cobblestone', "Cobblestone", ""),
    ('Concrete', "Concrete", ""),
    ('CorrugatedMetal', "Corrugated Metal", ""),
    ('CrackedLava', "Cracked Lava", ""),
    ('DiamondPlate', "Diamond Plate", ""),
    ('Fabric', "Fabric", ""),
    ('Foil', "Foil", ""),
    ('ForceField', "ForceField", ""),
    ('Glacier', "Glacier", ""),
    ('Glass', "Glass", ""),
    ('Granite', "Granite", ""),
    ('Grass', "Grass", ""),
    ('Ground', "Ground", ""),
    ('Ice', "Ice", ""),
    ('LeafyGrass', "Leafy Grass", ""),
    ('Leather', "Leather", ""),
    ('Limestone', "Limestone", ""),
    ('Marble', "Marble", ""),
    ('Metal', "Metal", ""),
    ('Mud', "Mud", ""),
    ('Neon', "Neon", ""),
    ('Pavement', "Pavement", ""),
    ('Pebble', "Pebble", ""),
    ('Plaster', "Plaster", ""),
    ('Plastic', "Plastic", ""),
    ('Rock', "Rock", ""),
    ('RoofShingles', "Roof Shingles", ""),
    ('Rubber', "Rubber", ""),
    ('Salt', "Salt", ""),
    ('Sand', "Sand", ""),
    ('Sandstone', "Sandstone", ""),
    ('Slate', "Slate", ""),
    ('SmoothPlastic', "Smooth Plastic", ""),
    ('Snow', "Snow", ""),
    ('Wood', "Wood", ""),
    ('WoodPlanks', "Wood Planks", ""),
]