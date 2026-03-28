import bpy
from .texture_utils import ensure_dummy_image

BASE_NAME = "robloxMaterialTemplate"

def create_roblox_shader_instance():
    """Creates a new instance of the Roblox Uber-Shader."""
    
    # This automatically handles .001, .002, etc. if the name exists
    mat = bpy.data.materials.new(name=BASE_NAME)
    
    if hasattr(mat, "use_nodes"):
        try: mat.use_nodes = True
        except: pass
    
    # --- VERSION SAFE SETTINGS ---
    if hasattr(mat, 'blend_method'):
        mat.blend_method = 'HASHED'
        
    if hasattr(mat, 'shadow_method'):
        mat.shadow_method = 'HASHED'
    
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear() # Clear default Principled BSDF
    
    dummy_img = ensure_dummy_image()

    # --- HELPER: Create Node ---
    def make_node(type_name, name, label, x, y):
        n = nodes.new(type_name)
        n.name = name
        n.label = label
        n.location = (x, y)
        return n

    # --- HELPER: Create Texture Setup ---
    tex_coord = make_node('ShaderNodeTexCoord', 'textCoordinateForMappings', '', -1500, -100)

    def create_face_chain(face_name, label, x_base, y_base, loc_vec):
        mapping = make_node('ShaderNodeMapping', f"{face_name}Mapping", f"{face_name}Mapping", x_base, y_base)
        mapping.inputs['Location'].default_value = loc_vec
        mapping.inputs['Scale'].default_value = (4, 4, 4) 
        
        # Rotation Logic
        if face_name in ['top', 'bottom']:
            mapping.inputs['Rotation'].default_value = (0, 0, 0)
        else:
            mapping.inputs['Rotation'].default_value = (0, 0, 1.5708) # 90 degrees Z

        tex = make_node('ShaderNodeTexImage', f"{face_name}Texture", label, x_base + 250, y_base)
        tex.image = dummy_img
        
        # FIX: Set extension to CLIP to prevent repeating
        tex.extension = 'CLIP' 
        
        links.new(tex_coord.outputs['UV'], mapping.inputs['Vector'])
        links.new(mapping.outputs['Vector'], tex.inputs['Vector'])
        return tex

    # --- 1. BUILD THE 6 FACES ---
    tex_l = create_face_chain('left', 'Left', -1300, -320, (1.0, -1.5, 0))
    tex_f = create_face_chain('front', 'Front', -1300, -380, (2.0, -1.5, 0))
    tex_r = create_face_chain('right', 'Right', -1300, -220, (3.0, -1.5, 0))
    tex_b = create_face_chain('back', 'Back', -1300, -160, (4.0, -1.5, 0))
    tex_t = create_face_chain('top', 'Top', -1300, -270, (-2.5, -2.0, 0))
    tex_bo = create_face_chain('bottom', 'Bottom', -1300, -100, (-0.5, -2.0, 0))

    # --- 2. MIX THE FACES ---
    def make_mix(name, x, y, input_a, input_b, factor_plug=None):
        mix = make_node('ShaderNodeMix', name, '', x, y)
        mix.data_type = 'RGBA'
        mix.blend_type = 'MIX'
        if input_a: links.new(input_a, mix.inputs[6]) # A
        if input_b: links.new(input_b, mix.inputs[7]) # B
        if factor_plug: links.new(factor_plug, mix.inputs[0])
        else: mix.inputs[0].default_value = 0.5
        return mix.outputs[2]

    res_lf = make_mix('(L+F)', -800, -330, tex_l.outputs['Color'], tex_f.outputs['Color'], tex_f.outputs['Alpha'])
    res_rlf = make_mix('(R+LF)', -600, -220, res_lf, tex_r.outputs['Color'], tex_r.outputs['Alpha'])
    res_brlf = make_mix('(B+RLF)', -400, -150, res_rlf, tex_b.outputs['Color'], tex_b.outputs['Alpha'])
    res_tbrlf = make_mix('(T+BRLF)', -250, -90, res_brlf, tex_t.outputs['Color'], tex_t.outputs['Alpha'])
    res_all_faces = make_mix('(Bo+TBRLF)', -100, -20, res_tbrlf, tex_bo.outputs['Color'], tex_bo.outputs['Alpha'])

    # --- 3. MESHPART LOGIC ---
    val_is_meshpart = make_node('ShaderNodeValue', 'isMeshPart?', 'isMeshPart?', -300, 350)
    val_is_meshpart.outputs[0].default_value = 0.0 # Default False

    tex_meshpart = make_node('ShaderNodeTexImage', 'textureMeshPart', 'textureMeshPart', -400, 450)
    tex_meshpart.image = dummy_img
    
    # FIX: Set extension to CLIP here as well
    tex_meshpart.extension = 'CLIP'

    mix_mp_vs_std = make_node('ShaderNodeMix', 'textureMeshPart_or_partTexture_mixer', '', 100, 300)
    mix_mp_vs_std.data_type = 'RGBA'
    links.new(val_is_meshpart.outputs[0], mix_mp_vs_std.inputs[0]) 
    links.new(res_all_faces, mix_mp_vs_std.inputs[6])
    links.new(tex_meshpart.outputs['Color'], mix_mp_vs_std.inputs[7])

    # --- 4. BASE COLOR FALLBACK ---
    val_use_texture = make_node('ShaderNodeValue', 'useTexture?', 'useTexture?', -100, 200)
    val_use_texture.outputs[0].default_value = 1.0 # Default True
    
    col_base = make_node('ShaderNodeRGB', 'baseColor', 'baseColor', 0, 150)
    col_base.outputs[0].default_value = (0.6, 0.6, 0.6, 1.0)

    mix_final = make_node('ShaderNodeMix', 'texture_or_baseColor_mixer', '', 400, 250)
    mix_final.data_type = 'RGBA'
    links.new(val_use_texture.outputs[0], mix_final.inputs[0])
    links.new(col_base.outputs[0], mix_final.inputs[6])
    links.new(mix_mp_vs_std.outputs[2], mix_final.inputs[7])

    # --- 5. OUTPUT ---
    bsdf = make_node('ShaderNodeBsdfPrincipled', 'Principled BSDF', '', 600, 250)
    out = make_node('ShaderNodeOutputMaterial', 'Material Output', '', 900, 250)
    links.new(mix_final.outputs[2], bsdf.inputs['Base Color'])
    links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    
    return mat

def apply_template_to_object(obj):
    """Creates a NEW material instance and assigns it to the object."""
    new_mat = create_roblox_shader_instance()
    
    if not obj.data.materials:
        obj.data.materials.append(new_mat)
    else:
        obj.active_material = new_mat
        
    return new_mat