import mathutils
from .constants import METERS_TO_STUDS # NEW

def get_roblox_transform(obj, accumulated_matrix, depsgraph):
    obj_eval = obj.evaluated_get(depsgraph)
    mesh = obj_eval.to_mesh()
    
    if not mesh or not mesh.vertices:
        if mesh: obj_eval.to_mesh_clear()
        return [1, 1, 1],[0,0,0, 1,0,0, 0,1,0, 0,0,1]

    verts =[v.co for v in mesh.vertices]
    obj_eval.to_mesh_clear()

    min_x = min(v.x for v in verts)
    max_x = max(v.x for v in verts)
    min_y = min(v.y for v in verts)
    max_y = max(v.y for v in verts)
    min_z = min(v.z for v in verts)
    max_z = max(v.z for v in verts)

    local_center = mathutils.Vector(((min_x + max_x) / 2.0, (min_y + max_y) / 2.0, (min_z + max_z) / 2.0))
    raw_size = mathutils.Vector((max_x - min_x, max_y - min_y, max_z - min_z))

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