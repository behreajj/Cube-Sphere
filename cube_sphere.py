import bpy
import math
import mathutils
import bmesh
from bpy.props import (
    IntProperty,
    BoolProperty,
    EnumProperty,
    FloatProperty)


class ObjMesh:
    def __init__(self, vs, vts, v_idcs, vt_idcs, name="Mesh"):

        self.vs = vs
        self.vts = vts

        self.v_idcs = v_idcs
        self.vt_idcs = vt_idcs

        self.name = name

    def subdiv_faces_center(self, itr):
        i_range = range(0, itr)
        for i in i_range:
            k = 0
            faces_len = len(self.v_idcs)
            j_range = range(0, faces_len)
            for j in j_range:
                vert_len = len(self.v_idcs[k])
                self.subdiv_face_center(k)
                k += vert_len
        return self

    def subdiv_face_center(self, face_index):

        # Get the loop of indices for the requested face.
        v_idx_loop = self.v_idcs[face_index]
        vt_idx_loop = self.vt_idcs[face_index]

        # Measure the length of each array of data.
        vs_old_len = len(self.vs)
        vts_old_len = len(self.vts)

        # All index loops should be of the same length.
        face_len = min(len(v_idx_loop),
                       len(vt_idx_loop))
        face_len_p1 = face_len + 1

        # New vertices.
        vs_new = face_len_p1 * [(0.0, 0.0, 0.0)]
        vts_new = face_len_p1 * [(0.5, 0.5)]

        # New indices.
        v_idcs_new = face_len * [(0, 0, 0, 0)]
        vt_idcs_new = face_len * [(0, 0, 0, 0)]

        # Central vertex.
        v_center = (0.0, 0.0, 0.0)
        vt_center = (0.0, 0.0)

        # Central vertex will be the last element in v, vt, vn arrays.
        v_center_idx = vs_old_len + face_len
        vt_center_idx = vts_old_len + face_len

        # Loop over all vertices in the face.
        face_range = range(0, face_len)
        for j in face_range:

            # Find current vertex in the loop.
            v_idx_curr = v_idx_loop[j]
            vt_idx_curr = vt_idx_loop[j]

            v_curr = self.vs[v_idx_curr]
            vt_curr = self.vts[vt_idx_curr]

            # Sum the vertices of the original face. These will later be
            # averaged to find a center.
            v_center = (v_center[0] + v_curr[0],
                        v_center[1] + v_curr[1],
                        v_center[2] + v_curr[2])

            vt_center = (vt_center[0] + vt_curr[0],
                         vt_center[1] + vt_curr[1])

            # Find next vertex in the loop.
            k = (j + 1) % face_len
            v_idx_next = v_idx_loop[k]
            vt_idx_next = vt_idx_loop[k]

            v_next = self.vs[v_idx_next]
            vt_next = self.vts[vt_idx_next]

            # Find midpoints of edges between vertices.
            vs_new[j] = (0.5 * (v_curr[0] + v_next[0]),
                         0.5 * (v_curr[1] + v_next[1]),
                         0.5 * (v_curr[2] + v_next[2]))

            vts_new[j] = (0.5 * (vt_curr[0] + vt_next[0]),
                          0.5 * (vt_curr[1] + vt_next[1]))

            # New faces will be quadrilaterals that connect the center to two
            # mid points and the next coordinate.
            v_idcs_new[j] = (v_center_idx,
                             vs_old_len + j,
                             v_idx_next,
                             vs_old_len + k)

            vt_idcs_new[j] = (vt_center_idx,
                              vts_old_len + j,
                              vt_idx_next,
                              vts_old_len + k)

        # Find median center of face by dividing the summed centers by the
        # number of vertices in the face.
        if face_len > 0:
            fl_inv = 1.0 / face_len

            vs_new[face_len] = (fl_inv * v_center[0],
                                fl_inv * v_center[1],
                                fl_inv * v_center[2])

            vts_new[face_len] = (fl_inv * vt_center[0],
                                 fl_inv * vt_center[1])

        # Concatenate old and new lists.
        self.vs += vs_new
        self.vts += vts_new

        # Splice new indices into old, replacing the original face.
        face_idx_p1 = face_index + 1
        self.v_idcs = self.v_idcs[:face_index] + \
            v_idcs_new + self.v_idcs[face_idx_p1:]
        self.vt_idcs = self.vt_idcs[:face_index] + \
            vt_idcs_new + self.vt_idcs[face_idx_p1:]

        return self

    @staticmethod
    def cube_sphere(itr=3, radius=0.5, profile="CROSS", name="Sphere"):
        target = ObjMesh.cube(
            size=1.0,
            profile=profile,
            name=name)
        target.subdiv_faces_center(itr=itr)
        target.cast_to_sphere(radius=radius)

        return target

    def cast_to_sphere(self, radius=0.5):
        verif_rad = max(0.000001, radius)

        len_vs = len(self.vs)
        i_range = range(0, len_vs)
        self.vns = len_vs * [(0.0, 0.0, 1.0)]

        for i in i_range:
            v = self.vs[i]
            x = v[0]
            y = v[1]
            z = v[2]

            xsq = x * x
            ysq = y * y
            zsq = z * z

            xsq_2 = xsq * 0.5
            ysq_2 = ysq * 0.5
            zsq_2 = zsq * 0.5

            one_third = 0.3333333333333333
            xn = x * ((1.0 - (ysq_2 + zsq_2)
                + ysq * zsq * one_third) ** 0.5)
            yn = y * ((1.0 - (zsq_2 + xsq_2)
                + zsq * xsq * one_third) ** 0.5)
            zn = z * ((1.0 - (xsq_2 + ysq_2)
                + xsq * ysq * one_third) ** 0.5)

            self.vs[i] = (verif_rad * xn,
                          verif_rad * yn,
                          verif_rad * zn)

        return self

    @staticmethod
    def cube(size=0.5, profile="CROSS", name="Cube"):
        verif_size = max(0.000001, size)

        vs = [
            (-verif_size, -verif_size, -verif_size),
            (-verif_size, -verif_size, verif_size),
            (-verif_size, verif_size, -verif_size),
            (-verif_size, verif_size, verif_size),
            (verif_size, -verif_size, -verif_size),
            (verif_size, -verif_size, verif_size),
            (verif_size, verif_size, -verif_size),
            (verif_size, verif_size, verif_size)]

        v_idcs = [
            (6, 7, 5, 4),
            (7, 3, 1, 5),
            (2, 6, 4, 0),
            (4, 5, 1, 0),
            (0, 1, 3, 2),
            (2, 3, 7, 6)]

        vts = [
            (0.0, 1.0),
            (0.0, 0.0),
            (1.0, 0.0),
            (1.0, 1.0)]

        vt_idcs = [
            (2, 3, 0, 1),
            (1, 2, 3, 0),
            (1, 2, 3, 0),
            (2, 3, 0, 1),
            (2, 3, 0, 1),
            (2, 3, 0, 1)]

        if profile == "CROSS":
            vts = [
                (0.625, 1.0),
                (0.375, 1.0),
                (0.375, 0.25),
                (0.625, 0.25),
                (0.375, 0.0),
                (0.625, 0.0),
                (0.625, 0.5),
                (0.375, 0.5),
                (0.625, 0.75),
                (0.375, 0.75),
                (0.125, 0.5),
                (0.125, 0.75),
                (0.875, 0.75),
                (0.875, 0.5)]

            vt_idcs = [
                (7, 6, 8, 9),
                (6, 13, 12, 8),
                (10, 7, 9, 11),
                (9, 8, 0, 1),
                (4, 5, 3, 2),
                (2, 3, 6, 7)]
        elif profile == "DIAGONAL":
            one_third =  0.3333333333333333
            two_thirds = 0.6666666666666667

            vts = [
                (two_thirds, 1.0),
                (1.0, 1.0),
                (one_third, 0.75),
                (two_thirds, 0.75),
                (1.0, 0.75),
                (0.0, 0.5),
                (one_third, 0.5),
                (two_thirds, 0.5),
                (1.0, 0.5),
                (0.0, 0.25),
                (one_third, 0.25),
                (two_thirds, 0.25),
                (0.0, 0.0),
                (one_third, 0.0)]

            vt_idcs = [
                (7, 6, 2, 3),
                (6, 10, 9, 5),
                (8, 7, 3, 4),
                (3, 0, 1, 4),
                (12, 9, 10, 13),
                (11, 10, 6, 7)]

        return ObjMesh(vs=vs, vts=vts, v_idcs=v_idcs, vt_idcs=vt_idcs, name=name)


bl_info = {
    "name": "Create Cube Sphere",
    "author": "Jeremy Behreandt",
    "version": (0, 2),
    "blender": (2, 93, 5),
    "category": "Add Mesh",
    "description": "Creates a hard surface modeling friendly Cube Sphere.",
    "tracker_url": "https://github.com/behreajj/Cube-Sphere/"
}


class CubeSphereMaker(bpy.types.Operator):
    """Creates a hard surface modeling friendly cube-sphere"""

    bl_idname = "mesh.primitive_cubesphere_add"
    bl_label = "Cube Sphere"
    bl_options = {"REGISTER", "UNDO"}

    itrs: IntProperty(
        name="Iterations",
        description="Number of subdivisions",
        min=1,
        soft_max=16,
        default=3)

    radius: FloatProperty(
        name="Radius",
        description="Sphere radius",
        min=0.0001,
        soft_max=100.0,
        default=0.5)

    shade_smooth: BoolProperty(
        name="Shade Smooth",
        description="Whether to use smooth shading",
        default=True)

    auto_normals: BoolProperty(
        name="Auto Smooth",
        description="Auto smooth (based on smooth/sharp faces/edges and angle between faces)",
        default=True)

    auto_angle: FloatProperty(
        name="Auto Smooth Angle",
        description="Maximum angle between face normals that will be considered as smooth",
        subtype="ANGLE",
        min=0.0,
        max=3.14159,
        step=100,
        default=0.523599)

    calc_uvs: BoolProperty(
        name="Calc UVs",
        description="Calculate texture coordinates",
        default=True)

    uv_profile: EnumProperty(
        items=[
            ("CROSS", "Cross", "UVs form a cross pattern", 1),
            ("DIAGONAL", "Diagonal", "UVs form a diagonal pattern", 2),
            ("FACE", "Per Face", "A rectangle per face", 3)],
        name="UV Profile",
        default="FACE",
        description="How to distribute texture coordinates")

    bevel_segs: IntProperty(
        name="Bevel Segments",
        description="Number of bevel segments",
        min=0,
        soft_max=16,
        default=0)

    bevel_amt: FloatProperty(
        name="Bevel Amount",
        description="Width to bevel",
        min=0.0,
        soft_max=100.0,
        default=0.0,
        step=1,
        precision=3)

    def execute(self, context):
        sphere = ObjMesh.cube_sphere(
            itr=self.itrs,
            radius=self.radius,
            profile=self.uv_profile,
            name="Sphere")

        mesh_data = bpy.data.meshes.new(sphere.name)
        mesh_data.from_pydata(sphere.vs, [], sphere.v_idcs)
        mesh_data.validate(verbose=True)
        mesh_data.use_auto_smooth = self.auto_normals
        mesh_data.auto_smooth_angle = self.auto_angle

        bm = bmesh.new()
        bm.from_mesh(mesh_data)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.000001)

        bm.verts.sort(key=CubeSphereMaker.vert_comparator)
        bm.faces.sort(key=CubeSphereMaker.face_comparator)

        if self.calc_uvs:
            uv_layer = bm.loops.layers.uv.verify()
            for face in bm.faces:
                vt_idcs = sphere.vt_idcs[face.index]
                for i, loop in enumerate(face.loops):
                    bmvt = loop[uv_layer]
                    bmvt.uv = sphere.vts[vt_idcs[i]]

        if self.shade_smooth:
            for face in bm.faces:
                face.smooth = True

        # For some reason, faces were left as selected
        # in the editor...
        for face in bm.faces:
            face.select = False

        bm.to_mesh(mesh_data)
        bm.free()

        mesh_obj = bpy.data.objects.new(mesh_data.name, mesh_data)
        mesh_obj.location = context.scene.cursor.location

        if self.bevel_segs > 0 and self.bevel_amt > 0.0:
            bvl_mod = mesh_obj.modifiers.new("Bevel", "BEVEL")
            bvl_mod.width = self.bevel_amt
            bvl_mod.limit_method = "ANGLE"
            bvl_mod.angle_limit = 0.523599
            bvl_mod.miter_outer = "MITER_ARC"
            bvl_mod.segments = self.bevel_segs
            bvl_mod.harden_normals = self.auto_normals
            bvl_mod.show_in_editmode = False

        context.scene.collection.objects.link(mesh_obj)
        return {"FINISHED"}

    def execute_old(self, context):

        bm = bmesh.new()
        bmesh.ops.create_cube(bm, calc_uvs=False)

        bmesh.ops.subdivide_edges(
            bm, edges=bm.edges, cuts=self.cuts, use_grid_fill=True)

        for bm_vert in bm.verts:
            co = bm_vert.co
            bm_vert.normal = co.normalized()
            bm_vert.co = self.radius * bm_vert.normal

        mesh_data = bpy.data.meshes.new("Sphere")
        bm.to_mesh(mesh_data)
        bm.free()
        mesh_obj = bpy.data.objects.new(mesh_data.name, mesh_data)
        mesh_obj.location = context.scene.cursor.location

        context.scene.collection.objects.link(mesh_obj)

        return {"FINISHED"}

    @staticmethod
    def face_comparator(x):
        center = x.calc_center_median()
        if center.z != 0.0:
            return center.z
        if center.y != 0.0:
            return center.y
        return center.x

    @staticmethod
    def vert_comparator(x):
        co = x.co
        if co.z != 0.0:
            return co.z
        if co.y != 0.0:
            return co.y
        return co.x

    @classmethod
    def poll(cls, context):
        return context.area.type == "VIEW_3D"


def menu_func(self, context):
    self.layout.operator(CubeSphereMaker.bl_idname, icon="SHADING_WIRE")


def register():
    bpy.utils.register_class(CubeSphereMaker)
    bpy.types.VIEW3D_MT_mesh_add.append(menu_func)


def unregister():
    bpy.utils.unregister_class(CubeSphereMaker)
    bpy.types.VIEW3D_MT_mesh_add.remove(menu_func)
