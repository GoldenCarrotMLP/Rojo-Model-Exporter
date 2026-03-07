import mathutils
import bpy
from .constants import METERS_TO_STUDS 

def get_roblox_transform(obj, accumulated_matrix, depsgraph):
    # Retrieve properties from the original object
    props = getattr(obj.original, "roblox_props", None)
    
    # 1. Determine Calculation Mode
    # MeshPart = Clean Size (Scale * 1), but Center must still be geometric center
    is_meshpart = (props and props.rbx_type == 'MeshPart')

    # 2. Fast Bounding Box Calculation
    # obj.bound_box gives us the 8 corners in Local Space instantly (no heavy to_mesh)
    bbox = obj.bound_box
    
    # Extract min/max from the 8 corners
    min_x = min(v[0] for v in bbox)
    max_x = max(v[0] for v in bbox)
    min_y = min(v[1] for v in bbox)
    max_y = max(v[1] for v in bbox)
    min_z = min(v[2] for v in bbox)
    max_z = max(v[2] for v in bbox)

    # 3. Calculate Local Center (The visual center of the geometry)
    local_center = mathutils.Vector((
        (min_x + max_x) / 2.0,
        (min_y + max_y) / 2.0,
        (min_z + max_z) / 2.0
    ))

    # 4. Calculate Raw Size
    if is_meshpart:
        # MeshParts: Assume Unit Cube (1x1x1) * Scale
        # This keeps numbers clean (e.g. Size 4, 10, 1) regardless of messy verts
        raw_size = mathutils.Vector((1, 1, 1))
    else:
        # Primitives: Use actual bounding box size
        raw_size = mathutils.Vector((
            max_x - min_x,
            max_y - min_y,
            max_z - min_z
        ))

    # 5. Transform to World Space
    # Apply parent matrix to the geometric center
    world_center = accumulated_matrix @ local_center
    
    # Extract Rotation and Scale
    _, rot_quat, world_scale = accumulated_matrix.decompose()
    rot = rot_quat.to_matrix()

    # 6. Convert to Roblox Coordinate System (Studs)
    
    # Size Calculation
    sx = raw_size.x * world_scale.x * METERS_TO_STUDS
    sy = raw_size.z * world_scale.z * METERS_TO_STUDS
    sz = raw_size.y * world_scale.y * METERS_TO_STUDS

    # Position Calculation (Swap Y/Z and invert Z for Roblox space)
    rx = world_center.x * METERS_TO_STUDS
    ry = world_center.z * METERS_TO_STUDS
    rz = -world_center.y * METERS_TO_STUDS

    # Rotation Matrix Conversion (Blender Right-Handed Z-Up -> Roblox Right-Handed Y-Up)
    # [ X,  Z, -Y ]
    r00, r01, r02 = rot[0][0], rot[0][2], -rot[0][1]
    r10, r11, r12 = rot[2][0], rot[2][2], -rot[2][1]
    r20, r21, r22 = -rot[1][0], -rot[1][2], rot[1][1]

    size = [round(sx, 3), round(sy, 3), round(sz, 3)]
    cframe = [
        round(rx, 3), round(ry, 3), round(rz, 3),
        round(r00, 4), round(r01, 4), round(r02, 4),
        round(r10, 4), round(r11, 4), round(r12, 4),
        round(r20, 4), round(r21, 4), round(r22, 4)
    ]

    return size, cframe