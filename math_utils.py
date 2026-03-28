import mathutils
import bpy
from .constants import METERS_TO_STUDS 

def get_roblox_transform(obj, accumulated_matrix, depsgraph):
    props = getattr(obj.original, "roblox_props", None)
    is_meshpart = (props and props.rbx_type == 'MeshPart')

    # 1. Safe Bounding Box Calculation
    if obj.type == 'MESH' and len(obj.bound_box) == 8:
        bbox = obj.bound_box
        min_x = min(v[0] for v in bbox)
        max_x = max(v[0] for v in bbox)
        min_y = min(v[1] for v in bbox)
        max_y = max(v[1] for v in bbox)
        min_z = min(v[2] for v in bbox)
        max_z = max(v[2] for v in bbox)
    else:
        # Fallback for Empties, Lights, etc (1x1x1 box)
        min_x, max_x = -0.5, 0.5
        min_y, max_y = -0.5, 0.5
        min_z, max_z = -0.5, 0.5

        # If it's an Area light, map the size exactly
        if obj.type == 'LIGHT' and obj.data.type == 'AREA':
            sx = obj.data.size
            sy = getattr(obj.data, "size_y", sx) if obj.data.shape in['RECTANGLE', 'ELLIPSE'] else sx
            min_x, max_x = -sx/2, sx/2
            min_y, max_y = -sy/2, sy/2
            min_z, max_z = -0.1, 0.1 # Flat container

    local_center = mathutils.Vector((
        (min_x + max_x) / 2.0,
        (min_y + max_y) / 2.0,
        (min_z + max_z) / 2.0
    ))

    if is_meshpart:
        raw_size = mathutils.Vector((1, 1, 1))
    else:
        raw_size = mathutils.Vector((
            max_x - min_x,
            max_y - min_y,
            max_z - min_z
        ))

    world_center = accumulated_matrix @ local_center
    _, rot_quat, world_scale = accumulated_matrix.decompose()
    rot = rot_quat.to_matrix()

    sx = raw_size.x * world_scale.x * METERS_TO_STUDS
    sy = raw_size.z * world_scale.z * METERS_TO_STUDS
    sz = raw_size.y * world_scale.y * METERS_TO_STUDS

    rx = world_center.x * METERS_TO_STUDS
    ry = world_center.z * METERS_TO_STUDS
    rz = -world_center.y * METERS_TO_STUDS

    r00, r01, r02 = rot[0][0], rot[0][2], -rot[0][1]
    r10, r11, r12 = rot[2][0], rot[2][2], -rot[2][1]
    r20, r21, r22 = -rot[1][0], -rot[1][2], rot[1][1]

    size =[round(sx, 3), round(sy, 3), round(sz, 3)]
    cframe =[
        round(rx, 3), round(ry, 3), round(rz, 3),
        round(r00, 4), round(r01, 4), round(r02, 4),
        round(r10, 4), round(r11, 4), round(r12, 4),
        round(r20, 4), round(r21, 4), round(r22, 4)
    ]

    return size, cframe