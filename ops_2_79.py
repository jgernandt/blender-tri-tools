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
import bpy_extras

import tri_tools.io
import tri_tools.transfer


class TRIOperator(bpy.types.Operator):
    def execute(self, context):
        try:
            self.execute_impl(context)
        
        except Exception as e:
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}
        
        return {'FINISHED'}

TRIOrientationHelper = bpy_extras.io_utils.orientation_helper_factory("TRIOrientationHelper", axis_forward='Y', axis_up='Z')

class TRIExport(TRIOperator, bpy_extras.io_utils.ExportHelper, TRIOrientationHelper):
    bl_label = 'Export TRI'
    bl_idname = 'export_mesh.facegen_tri'
    bl_description = "Export FaceGen TRI file"
    
    filename_ext = ".tri"
    
    filter_glob = bpy.props.StringProperty(
        default="*.tri",
        options={'HIDDEN'})
    
    length_scale = bpy.props.FloatProperty(
        name="Scale",
        description="Scale of exported model",
        default=10.0)
    
    uv_format = bpy.props.EnumProperty(
        items=[("UV_FACE", "Per Face", "UV coordinates per face"),
                ("UV_VERTEX", "Per Vertex", "UV coordinates per vertex (mesh must not have any UV seams)"),
                ("UV_NONE", "None", "No UV coordinates")],
        name="UV Format",
        description="",
        default="UV_FACE")
    
    def invoke(self, context, event):
        obj = context.active_object
        
        if obj == None or obj.type != 'MESH':
            self.report({'ERROR'}, "No active mesh")
            return {'CANCELLED'}
        
        self.filepath = obj.name
        return bpy_extras.io_utils.ExportHelper.invoke(self, context, event)
    
    def execute_impl(self, context):
        tri_tools.io.export_tri(self, context.active_object)


class TRIImport(TRIOperator, bpy_extras.io_utils.ImportHelper, TRIOrientationHelper):
    bl_label = 'Import TRI'
    bl_idname = 'import_mesh.facegen_tri'
    bl_description = "Import FaceGen TRI file"
    bl_options = {'UNDO'}
    
    filename_ext = ".tri"
    
    filter_glob = bpy.props.StringProperty(
        default="*.tri",
        options={'HIDDEN'})
    
    length_scale = bpy.props.FloatProperty(
        name="Scale",
        description="Scale of imported model",
        default=10.0)
    
    def execute_impl(self, context):
        tri_tools.io.import_tri(self, context)


class TRITransferShapes(TRIOperator):
    bl_description = "Transfer shape keys from selected to active object"
    bl_idname = "object.tri_transfer_shapes"
    bl_label = "Transfer Shapes"
    bl_options = {'UNDO'}
    
    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'
    
    def execute_impl(self, context):
        target = context.active_object
        if target == None or target.type != 'MESH':
            raise RuntimeError("No active mesh")
    
        source = None

        for obj in bpy.context.selected_objects:
            if obj != target and obj.type == 'MESH':
                source = obj
                break
        if source == None:
            raise RuntimeError("No second selected mesh")
        
        tri_tools.transfer.transfer_shapes(self, source, target)

def exportop(self, context):
    self.layout.operator(TRIExport.bl_idname, text="FaceGen TRI (.tri)")
    
def importop(self, context):
    self.layout.operator(TRIImport.bl_idname, text="FaceGen TRI (.tri)")

def register():
    bpy.utils.register_class(TRIExport)
    bpy.utils.register_class(TRIImport)
    bpy.utils.register_class(TRITransferShapes)
    
    bpy.types.INFO_MT_file_import.append(importop)
    bpy.types.INFO_MT_file_export.append(exportop)

def unregister():
    bpy.types.INFO_MT_file_export.remove(exportop)
    bpy.types.INFO_MT_file_import.remove(importop)
    
    bpy.utils.unregister_class(TRIExport)
    bpy.utils.unregister_class(TRIImport)
    bpy.utils.unregister_class(TRITransferShapes)
