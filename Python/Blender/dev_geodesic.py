import bpy
import bmesh

import numpy
import sys
sys.path.append('/d/bandrieu/GitHub/Code/Python')
import lib_blender_edit as lbe
import lib_blender_util as lbu
from mathutils import Vector
import random



scene = bpy.context.scene
lbu.clear_scene(meshes=True, lamps=True, cameras=False)

## add mesh
"""
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3)
obj = bpy.data.objects["Icosphere"]
"""

"""
bpy.ops.mesh.primitive_monkey_add()
obj = bpy.data.objects["Suzanne"]
bpy.ops.object.modifier_add(type='SUBSURF')
obj.modifiers['Subsurf'].levels = 2
bpy.ops.object.modifier_apply(apply_as='DATA', modifier='Subsurf')
"""

bpy.ops.mesh.primitive_cylinder_add(vertices=32,
                                    radius=1.0,
                                    depth=2.0,
                                    end_fill_type='NGON')
obj = bpy.data.objects["Cylinder"]

msh = obj.data



############################################
length_max = 10.0
geodesic = []
crossedfaces = []

# switch to edit mode
bpy.ops.object.mode_set(mode='EDIT')

# Get a BMesh representation
bmsh = bmesh.from_edit_mesh(msh)

# random first point
face = bmsh.faces[random.randint(0,len(bmsh.faces))]
x = [v.co for v in face.verts]
u = numpy.random.rand(len(x))
uv = u/numpy.sum(u)

xyz = Vector([0,0,0])
for i in range(len(x)):
    xyz = xyz + x[i]*uv[i]

# initial direction
direction = Vector(2*numpy.random.rand(3) - 1).normalized()

geodesic.append(lbe.IntersectionPoint(faces=[face], uvs=uv, xyz=xyz))
length = 0.0

while length < length_max:
    #print("face #",face.index, ", length=",length,"/",length_max)
    print("length=",length,"/",length_max)
    normal = face.normal
    # project displacement onto local tangent plane
    direction_t = (direction - direction.project(normal)).normalized()
    displacement = (length_max - length)*direction_t
    #
    if face in crossedfaces:
        print("self intersection")
    else:
        crossedfaces.append(face)
    #
    nv = len(face.verts)
    leaves_face = False
    for i in range(nv):
        vi = face.verts[i]
        vj = face.verts[(i+1)%nv]
        # plane generated by edge ij and face normal
        planeorig = 0.5*(vi.co + vj.co)
        vecij = vj.co - vi.co
        vecijsqr = vecij.dot(vecij)
        # normal of that plane, pointing towards the face's exterior
        planenormal = normal.cross(vecij)
        planenormal.normalize()
        # check if displacement crosses the plane
        if planenormal.dot(xyz - planeorig + displacement) > 0 and planenormal.dot(displacement) > 1.e-7:
            leaves_face = True
            # get intersection point between displacement and plane
            fracdisp = planenormal.dot(planeorig - xyz)/planenormal.dot(displacement)
            targetpoint = xyz + fracdisp*displacement
            # project that point onto edge ij
            fracvij = vecij.dot(targetpoint - vi.co)/vecijsqr
            if fracvij < 0 or fracvij > 1:
                continue
            else:
                edge = face.edges[i]
                for otherface in edge.link_faces:
                    if otherface != face:
                        xyzprev = xyz.copy()
                        xyz = vi.co + fracvij*vecij
                        length += (xyz - xyzprev).length
                        direction = xyzprev - xyz + displacement
                        geodesic.append(lbe.IntersectionPoint(faces=[face, otherface], uvs=[], xyz=xyz))
                        face = otherface
                        break
                break
    if not leaves_face:
        
        break

# leave edit mode
bpy.ops.object.mode_set(mode='OBJECT')
bmsh.free()

XYZ = [p.xyz for p in geodesic]
obj = lbu.pydata_to_polyline(XYZ,
                       name='geodesic',
                       thickness=0.005,
                       resolution_u=24,
                       bevel_resolution=4,
                       fill_mode='FULL')
mat = bpy.data.materials.new("mat_geodesic")
mat.diffuse_color = [1,1,0]
mat.diffuse_intensity = 1
mat.emit = 1
mat.use_shadeless = True
obj.data.materials.append(mat)
