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

if bpy.app.version[0] == 2 and bpy.app.version[1] < 80:
    import tri_tools.ops_2_79 as ops
    import tri_tools.ui_2_79 as ui
else:
    import tri_tools.ops as ops
    import tri_tools.ui as ui

bl_info = {
    'name': "TRI Tools",
    'author': "Jonas Gernandt",
    'version': (1, 1, 0),
    'blender': (3, 2, 0),
    'location': "File > Import-Export and View3D > Tools",
    'description': "Import and export FaceGen TRI files, and transfer shape keys by proximity between meshes",
    'doc_url': "",
    'category': "Mesh"}

def register():
    ops.register()
    ui.register()

def unregister():
    ui.unregister()
    ops.unregister()
