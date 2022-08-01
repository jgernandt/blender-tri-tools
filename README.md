# TRI Tools
A Blender addon for working with Skyrim face morphs.

## About
This addon adds three functions to Blender: import and export FaceGen TRI files, and transfer shape keys between objects. It's purpose is to quickly generate the various morphs required by Skyrim head parts.

## Import-export
The import-export functionality follows the FaceGen specification (https://facegen.com/dl/sdk/doc/manual/fileformats.html). There exist other file formats that use the .tri extension, but those will not be readable. 

The data that is processed includes vertices, faces (tris and quads only), (optionally) UV coordinates and shape morphs. Some data is discarded, since it cannot be represented in a simple way in Blender. This includes labels for vertices and surface points.

FaceGen TRI supports both absolute/static and relative/difference morphs. Blender doesn't really have the former concept, so any imported morph will come out as a relative shape key. The names of absolute morphs is prefixed by an asterisk to indicate the difference. You can edit and export them as normal, or add/remove the asterisk to interconvert between the types.

Import-export supports coordinate system transforms. Default settings make sense for Skyrim models: scaled by a factor 10 and facing the opposite direction (positive Y). To import or export the model exactly as it is, set Scale to 1, Forward to -Y and Up to Z.

TRI Tools never changes the vertex order of any model, but a NIF exporter might. If you are making a new mesh from scratch, it is wise to export it to NIF and import it back again before making a TRI for it.

## Transfer Shapes
This simple tool allows transferring shape keys between unrelated objects. That is, instead of transferring the shape keys by vertex order (the built-in way), it transfers them by proximity between the meshes. Each vertex on the target mesh is morphed the same way as the closest point on the surface of the source mesh.

Optionally, the influence of the source morph on a target vertex may be set to decay (exponentially) with distance to the source surface.
