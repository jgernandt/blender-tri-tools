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

import math

import bpy
import mathutils


def target_diff(d, diffs, indices, weights, falloff):
    result = sum([diffs[indices[i]] * weights[i] for i in range(len(indices))], mathutils.Vector())
    result *= math.exp(-falloff * d)
    return result

def transfer_shapes(operator, source, target):
    """Transfer all shape keys in source mesh to target mesh, as determined from the closest point"""
    if source.data.shape_keys != None:
        
        #Warn about different world space transforms
        if source.matrix_world != target.matrix_world:
            operator.report({'WARNING'}, "World-space transforms are not accounted for")

        if target.data.shape_keys == None:
            target.shape_key_add(name="Basis", from_mix=False)
        
        #gather distance info and interpolation parameters (will be the same for all shapes)
        distances = [0.0] * len(target.data.vertices)
        indices = [[]] * len(target.data.vertices)
        weights = [[]] * len(target.data.vertices)
        for v in target.data.vertices:
            result, location, _, index = source.closest_point_on_mesh(v.co)
            if result:
                src_verts = [source.data.vertices[source.data.loops[i].vertex_index]
                    for i in source.data.polygons[index].loop_indices]
                
                distances[v.index] = (v.co - location).length
                indices[v.index] = [vtx.index for vtx in src_verts]
                weights[v.index] = mathutils.interpolate.poly_3d_calc([mathutils.Vector(vtx.co) for vtx in src_verts], location)

        for src_shape in source.data.shape_keys.key_blocks:
            ref = source.data.shape_keys.reference_key
            if src_shape == ref:
                continue
            
            #calc the difference vectors of the source shape
            src_diff = [src_shape.data[i].co - ref.data[i].co for i in range(len(source.data.vertices))]
            
            #calc the corresponding difference vectors of the target shape
            tgt_diff = [target_diff(distances[i], src_diff, indices[i], weights[i], target.tri_transfer_shapes.distance_falloff) 
                for i in range(len(target.data.vertices))]
            
            #filter out empty morphs
            null = mathutils.Vector()
            for d in tgt_diff:
                if d != null:
                    #not empty, add this shape key
                    if target.tri_transfer_shapes.replace and src_shape.name in target.data.shape_keys.key_blocks:
                        tgt_shape = target.data.shape_keys.key_blocks[src_shape.name]
                    else:
                        tgt_shape = target.shape_key_add(name=src_shape.name, from_mix=False)
    
                    for i in range(len(target.data.vertices)):
                        tgt_shape.data[i].co = target.data.vertices[i].co + tgt_diff[i]
                    
                    break
