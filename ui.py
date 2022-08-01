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

import bpy


class TRITransferShapesProps(bpy.types.PropertyGroup):
    distance_falloff: bpy.props.FloatProperty(name="Distance Falloff", min=0.0, default=0.0,
        description="Decrease the influence of the shape by distance from the source mesh")
    
    replace: bpy.props.BoolProperty(name="Replace", default=True,
        description="Replace existing shape keys if names are identical")


class TRITransferShapesPanel(bpy.types.Panel):
    bl_idname = "VIEW3D_PT_tri_transfer_shapes"
    bl_label = "Transfer Shapes"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "TRI Tools"
    
    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'
    
    def draw(self, context):
        obj = context.object
        
        if obj:
            self.layout.operator("object.tri_transfer_shapes", icon='SHAPEKEY_DATA')
            self.layout.prop(obj.tri_transfer_shapes, "distance_falloff")
            self.layout.prop(obj.tri_transfer_shapes, "replace")


def register():
    bpy.utils.register_class(TRITransferShapesProps)
    bpy.types.Object.tri_transfer_shapes = bpy.props.PointerProperty(type=TRITransferShapesProps)
    bpy.utils.register_class(TRITransferShapesPanel)


def unregister():
    bpy.utils.unregister_class(TRITransferShapesPanel)
    del bpy.types.Object.tri_transfer_shapes
    bpy.utils.unregister_class(TRITransferShapesProps)