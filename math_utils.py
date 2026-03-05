import bpy
import mathutils

def get_roblox_transform(obj):
    """
    Takes a Blender object and returns Roblox-formatted Size and CFrame arrays.
    Handles the Z-Up (Right-hand) to Y-Up (Left-hand) conversion.
    """
    # Use matrix_world for absolute transforms (handles parented offsets)
    loc, rot_quat, sca = obj.matrix_world.decompose()
    rot = rot_quat.to_matrix()
    dims = obj.dimensions
    
    # 1. Position Translation: Blender (X, Y, Z) -> Roblox (X, Z, -Y)
    rx, ry, rz = loc.x, loc.z, -loc.y
    
    # 2. Size Translation: Blender (X, Y, Z) -> Roblox (X, Z, Y)
    sx, sy, sz = dims.x, dims.z, dims.y
    
    # 3. Rotation Matrix Translation for Roblox 12-element CFrame
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