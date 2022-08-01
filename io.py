"""I/O of the TRI file format according to the FaceGen specification (https://facegen.com/dl/sdk/doc/manual/fileformats.html)"""

#Copyright 2022 Jonas Gernandt
#
#This file is part of TRI Tools, a Blender addon for working with 
#Skyrim face morphs.
#
#TRI Tools is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#TRI Tools is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with TRI Tools. If not, see <https://www.gnu.org/licenses/>.

import os
import struct

import bpy
import mathutils
import bpy_extras

SIGNATURE = b"FRTRI003"

IS_2_79 = bpy.app.version[0] == 2 and bpy.app.version[1] < 80

def export_tri(op, mesh):
    if mesh.matrix_world != mathutils.Matrix.Identity(4):
        op.report({'WARNING'}, "Object's world-space transform is not exported")
    
    #Gather data and validate export settings
    
    basis = bpy_extras.io_utils.axis_conversion(
        from_forward='-Y', 
        from_up='Z', 
        to_forward=op.axis_forward, 
        to_up=op.axis_up).to_4x4()
    
    V = len(mesh.data.vertices)
    
    tris = []
    quads = []
    for f in mesh.data.polygons:
        if len(f.vertices) == 3:
            tris.append(f)
        elif len(f.vertices) == 4:
            quads.append(f)
        else:
            raise RuntimeError("Only tris and quads are supported")
    
    T = len(tris)
    Q = len(quads)
    LV = 0
    LS = 0
    
    if op.uv_format == 'UV_VERTEX':
        if mesh.data.uv_layers.active == None:
            raise RuntimeError("Add a UV Map or choose UV Format: None.")
        
        #the uv coords to export
        uvs = [0] * len(mesh.data.vertices)
        #a temp set of vertices we have passed
        passed = set()
        
        for i, loop in enumerate(mesh.data.uv_layers.active.data):
            uv = struct.pack("<ff", loop.uv[0], loop.uv[1])
            vertex_index = mesh.data.loops[i].vertex_index
            #If we have already passed this vertex, its uv must be the same. Else there's a seam.
            if vertex_index in passed:
                if uvs[vertex_index] != uv:
                    raise RuntimeError("Mesh has UV seams. Choose another UV Format.")
            else:
                passed.add(vertex_index)
                uvs[vertex_index] = uv
        
        del passed
        
        X = 0
        ext = 1
    elif op.uv_format == 'UV_FACE':
        if mesh.data.uv_layers.active == None:
            raise RuntimeError("Add a UV Map or choose UV Format: None.")
        
        #the uv coords to export
        uvs = []
        #loop indices into the list of uvs
        li = [-1] * len(mesh.data.loops)
        #a temp map of uv -> index in file
        used_map = {}
        
        #We don't want to store duplicate UV coords. We could, but let's do this right.
        #This will filter them out.
        for i, loop in enumerate(mesh.data.uv_layers.active.data):
            uv = struct.pack("<ff", loop.uv[0], loop.uv[1])
            if uv in used_map:
                li[i] = used_map[uv]
            else:
                li[i] = len(uvs)
                used_map[uv] = len(uvs)
                uvs.append(uv)
        
        del used_map
        
        X = len(uvs)
        ext = 1
    else:
        #No uvs
        X = 0
        ext = 0
    
    abs_morphs = []
    abs_morph_verts = []
    rel_morphs = []
    morph_targets = []
    
    if mesh.data.shape_keys != None:
        for shape in mesh.data.shape_keys.key_blocks:
            if shape == mesh.data.shape_keys.reference_key:
                continue
            
            if is_abs_morph(shape):
                #Find all morphed vertices. They are our targets.
                vtx_ind_list = []
                for i in range(V):
                    if shape.data[i].co != mesh.data.shape_keys.reference_key.data[i].co:
                        morph_targets.append(shape.data[i].co)
                        vtx_ind_list.append(i)
                
                abs_morphs.append(shape)
                abs_morph_verts.append(vtx_ind_list)
                
            else:
                rel_morphs.append(shape)
    
    Md = len(rel_morphs)
    Ms = len(abs_morphs)
    K = len(morph_targets)
    
    #Start export
    with open(op.filepath, "wb") as file:
        
        #Header
        file.write(struct.pack("<8s10i16s", SIGNATURE, V, T, Q, LV, LS, X, ext, Md, Ms, K, bytes(16)))
        
        #Vertices and morph targets
        if IS_2_79:
            for v in mesh.data.vertices:
                file.write(pack_vector3(basis * (op.length_scale * v.co)))
            for r in morph_targets:
                file.write(pack_vector3(basis * (op.length_scale * r)))
        else:
            for v in mesh.data.vertices:
                file.write(pack_vector3(basis @ (op.length_scale * v.co)))
            for r in morph_targets:
                file.write(pack_vector3(basis @ (op.length_scale * r)))
        
        #Faces
        for f in tris:
            file.write(struct.pack("<3i", f.vertices[0], f.vertices[1], f.vertices[2]))
        for f in quads:
            file.write(struct.pack("<4i", f.vertices[0], f.vertices[1], f.vertices[2], f.vertices[3]))
        
        #We don't support labels
        
        #UVs
        if op.uv_format == 'UV_VERTEX':
            file.write(bytes(0).join(uvs))
        elif op.uv_format == 'UV_FACE':
            file.write(bytes(0).join(uvs))
            for f in tris:
                file.write(struct.pack("<3i", li[f.loop_indices[0]], li[f.loop_indices[1]], li[f.loop_indices[2]]))
            for f in quads:
                file.write(struct.pack("<4i", li[f.loop_indices[0]], li[f.loop_indices[1]], li[f.loop_indices[2]], li[f.loop_indices[3]]))
        
        #Diff morphs
        for shape in rel_morphs:
            ref = mesh.data.shape_keys.reference_key
                
            #calc deltas to ref key (or base mesh? Not necessarily the same!)
            if IS_2_79:
                deltas = [basis * (op.length_scale * (shape.data[i].co - ref.data[i].co)) for i in range(V)]
            else:
                deltas = [basis @ (op.length_scale * (shape.data[i].co - ref.data[i].co)) for i in range(V)]
            
            #choose the scale so that the largest component in any delta vector equals the largest short int
            delta_max = max([max([abs(d[0]), abs(d[1]), abs(d[2])]) for d in deltas])
            
            if delta_max == 0.0:
                op.report({'INFO'}, "Shape %s is identical to reference" % shape.name)
                scale = 1.0
            else:
                scale = delta_max / 32767
            
            write_morph_label(file, shape)
            
            file.write(struct.pack("<f", scale))
            for d in deltas:
                file.write(struct.pack("<3h", round(d[0] / scale), round(d[1] / scale), round(d[2] / scale)))
        
        #Stat morphs
        for shape, vtx_ind_list in zip(abs_morphs, abs_morph_verts):
            write_morph_label(file, shape)
            file.write(len(vtx_ind_list).to_bytes(4, byteorder="little", signed=True))
            for i in vtx_ind_list:
                file.write(i.to_bytes(4, byteorder="little", signed=True))
        
        op.report({'INFO'}, op.filepath + " exported successfully")


def import_tri(op, context):
    with open(op.filepath, "rb") as file:
        
        #Check validity of file and read header data
        if file.read(8) != SIGNATURE:
            raise RuntimeError("Not a FaceGen TRI file")
        V, T, Q, LV, LS, X, ext, Md, Ms, K, _ = struct.unpack("<10i16s", file.read(56))
        
        #Warn about discarded data (we can't reproduce labels within Blender, I think)
        if LV > 0 or LS > 0:
            op.report({'WARNING'}, "Labels were discarded")
        
        #Create and activate new mesh
        name = os.path.splitext(os.path.basename(op.filepath))[0]
        mesh_data = context.blend_data.meshes.new(name)
        mesh = bpy.data.objects.new(name, mesh_data)
        
        bpy.ops.object.select_all(action='DESELECT')
        
        if IS_2_79:
            bpy.context.scene.objects.link(mesh)
            mesh.select = True
            context.scene.objects.active = mesh
        else:
            bpy.context.collection.objects.link(mesh)
            mesh.select_set(True)
            context.view_layer.objects.active = mesh
        
        
        #Start import
        
        #Read geometry
        vertices = [struct.unpack("<3f", file.read(12)) for _ in range(V)]
        
        morph_targets = [struct.unpack("<3f", file.read(12)) for _ in range(K)]
        
        tris = [struct.unpack("<3i", file.read(12)) for _ in range(T)]
        quads = [struct.unpack("<4i", file.read(16)) for _ in range(Q)]
        
        mesh.data.from_pydata(vertices, [], tris + quads)
        
        #discard vertex labels
        for _ in range(LV):
            skip_vertex_label(file)
        
        #discard surface point labels
        for _ in range(LS):
            skip_surface_label(file, ext & 2 == 2)
        
        #UVs
        if ext & 1:
            #Add UV map
            if IS_2_79:
                bpy.ops.mesh.uv_texture_add()
            else:
                mesh.data.uv_layers.new(do_init=False)
            
            if X == 0:
                #UVs per vertex
                uvs = [struct.unpack("<ff", file.read(8)) for _ in range(V)]
                for loop in mesh.data.loops:
                    mesh.data.uv_layers.active.data[loop.index].uv = uvs[loop.vertex_index]
            else:
                #UVs per face
                uvs = [struct.unpack("<ff", file.read(8)) for _ in range(X)]
                for i in range(T):
                    set_face_uvs(mesh.data, mesh.data.polygons[i], struct.unpack("<3i", file.read(12)), uvs)
                for i in range(T, T + Q):
                    set_face_uvs(mesh.data, mesh.data.polygons[i], struct.unpack("<4i", file.read(16)), uvs)
        
        if Md > 0 or Ms > 0:
            mesh.shape_key_add(name="Basis", from_mix=False)
            
        #Relative morphs
        for _ in range(Md):
            read_diff_morph(file, mesh)
        
        #Absolute morphs
        K_pos = 0
        for _ in range(Ms):
            K_pos = read_stat_morph(file, mesh, morph_targets, K_pos)
        assert(K_pos == len(morph_targets))
        
        
        #Apply user transforms
        mesh.matrix_world = bpy_extras.io_utils.axis_conversion(
            from_forward=op.axis_forward, 
            from_up=op.axis_up, 
            to_forward='-Y', 
            to_up='Z').to_4x4()
        
        mesh.scale = (1 / op.length_scale, 1 / op.length_scale, 1 / op.length_scale)
        bpy.ops.object.transform_apply(rotation=True, scale=True)
        
        op.report({'INFO'}, op.filepath + " imported successfully")


def get_abs_morph_name(name):
    return "*" + name

def get_shape_name(shape):
    return shape.name if not is_abs_morph(shape) else shape.name[1:]

def is_abs_morph(shape):
    return shape.name[0] == "*"


def pack_vector3(v):
    return struct.pack("<3f", v[0], v[1], v[2])


def read_diff_morph(file, mesh):
    label = read_morph_label(file)
    shape = mesh.shape_key_add(name=label, from_mix=False)
    
    scale = struct.unpack("<f", file.read(4))[0]
    
    for i in range(len(mesh.data.vertices)):
        dx, dy, dz = struct.unpack("<3h", file.read(6))
        shape.data[i].co[0] += scale * dx
        shape.data[i].co[1] += scale * dy
        shape.data[i].co[2] += scale * dz


def read_morph_label(file):
    N = int.from_bytes(file.read(4), byteorder="little", signed=True)
    return file.read(N).decode()


def read_stat_morph(file, mesh, morph_targets, K_pos):
    label = read_morph_label(file)
    shape = mesh.shape_key_add(name=get_abs_morph_name(label), from_mix=False)
    
    L = int.from_bytes(file.read(4), byteorder="little", signed=True)
    
    #If I got this straight, these will be indices to our V geometry vertices,
    #and their targets will be the positions from the list of morph_targets in order.
    #So, we need to keep track of our accumulated position (hence the K_pos)
    for i in range(L):
        vtx_ind = int.from_bytes(file.read(4), byteorder="little", signed=True)
        shape.data[vtx_ind].co = morph_targets[K_pos]
        shape.data[vtx_ind].co[0] = morph_targets[K_pos][0]
        shape.data[vtx_ind].co[1] = morph_targets[K_pos][1]
        shape.data[vtx_ind].co[2] = morph_targets[K_pos][2]
        K_pos += 1
    
    return K_pos


def set_face_uvs(mesh_data, face, indices, uv_list):
    for i in range(len(indices)):
        mesh_data.uv_layers.active.data[face.loop_indices[i]].uv = uv_list[indices[i]]


def skip_surface_label(file, wchar):
    #first a face index (?) and position
    file.seek(16, 1)
    #next is the length of the label string
    S = int.from_bytes(file.read(4), byteorder="little", signed=True)
    #then the string
    if wchar:
        file.seek(2 * S, 1)
    else:
        file.seek(S, 1)
    

def skip_vertex_label(file):
    #first a vertex index
    file.seek(4, 1)
    #next is the length of the label string
    S = int.from_bytes(file.read(4), byteorder="little", signed=True)
    #then the string
    file.seek(S, 1)


def write_morph_label(file, shape):
    label = get_shape_name(shape).encode() + b"\x00"
    file.write(len(label).to_bytes(4, byteorder="little", signed=True))
    file.write(label)

