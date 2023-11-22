import math
import os

import bpy
import mathutils

from ..utils.helpers import AutoImageSize
from ..utils.ioutils import ClearTempFolder, CreateTempFolder, GetTempFolder
from ..utils.tileutils import TilePathsIntoImage


def get_scene_framerate(context):
    frame_start = context.scene.frame_start
    frame_end = context.scene.frame_end


class MK_SPRITES_OP_render_sprite_animation(bpy.types.Operator):
    """render subject to sprite atlass"""

    bl_idname = "mk_sprites.render_sprite_animation"
    bl_label = "Render"
    bl_options = {"REGISTER"}

    subject_rotations: bpy.props.IntProperty(default=0)
    use_animations: bpy.props.BoolProperty(default=False)

    n = 0

    def render(self, context, renderpaths):
        mk_subject_props = context.scene.mk_sprites_subject_panel_properties
        subject = mk_subject_props.obj

        if self.use_animations:
            self.render_animations(context, renderpaths, subject)
        else:
            self.render_frames(context, renderpaths, 0, 0, subject)

    def render_frames(
        self, context, renderpaths, first_frame=0, frames=0, subject=None
    ):
        arc = (math.pi * 2) / self.subject_rotations

        rotations = max(1, self.subject_rotations)
        if subject == None:
            rotations = 1

        # Find the "CameraTrack" child object
        camera_track = None
        if subject:
            for child in subject.children:
                if child.name == "CameraTrack":
                    camera_track = child
                    break

        if not camera_track:
            self.report(
                {"ERROR"}, "CameraTrack object not found as a child of the subject."
            )
            return {"CANCELLED"}

        file_type_ext = context.scene.render.file_extension
        frame_step = context.scene.frame_step

        for i in range(rotations):
            img_path = os.path.join(GetTempFolder(), str(self.n))
            self.n += 1

            context.scene.render.filepath = img_path

            if frames > 0:
                bpy.ops.render.render(animation=True)

                for f in range(first_frame, first_frame + frames + 1, frame_step):
                    renderpaths.append(img_path + str(f).zfill(4) + file_type_ext)

            else:
                renderpaths.append(img_path + file_type_ext)
                bpy.ops.render.render(animation=False, write_still=True)

            # Apply rotation to the "CameraTrack" object instead of the subject
            if camera_track and self.subject_rotations > 0:
                print("Rotating by arc:", arc)
                camera_track.rotation_euler[2] += arc

    # Function to bake cloth simulation
    def bake_cloth_simulation(self, context, objs):
        for obj in objs:

            if obj.hide_render:
                print(f"Skipping baking for: {obj.name} as it is not enabled for rendering.")
                continue

            # Make sure the object is the active object and is selected
            bpy.context.view_layer.objects.active = obj
            obj.select_set(True)
            
            for modifier in obj.modifiers:
                if modifier.type == 'CLOTH':
                    # Clear previous bake
                    
                    # Keep defined modifier simulation range
                    # modifier.point_cache.frame_start = context.scene.frame_start
                    # modifier.point_cache.frame_end = context.scene.frame_end
                    bpy.ops.ptcache.free_bake_all()
                    print(f"Cleared previous bake for: {obj.name}")

                    print(f"Baking cloth simulation for: {obj.name}")
                    # Override the context for baking
                    override = context.copy()
                    override['active_object'] = obj
                    override['object'] = obj
                    override['point_cache'] = modifier.point_cache
                    bpy.ops.ptcache.bake(override, bake=True)
                    break  # Assuming we only have one cloth modifier per object

            # Deselect the object after baking
            obj.select_set(False)

    def prepare_for_rendering(self, context, subject):
        # Check the subject and its siblings for cloth modifiers and bake if necessary
        if subject:
            objs_to_bake = [subject] + [obj for obj in subject.children if obj.type == 'MESH']
            self.bake_cloth_simulation(context, objs_to_bake)

    # render the animation or sprites for each animation
    # these animations are stored in scene.mk_sprites_subject_panel_properties
    def render_animations(self, context, renderpaths, subject):
        mk_subject_props = context.scene.mk_sprites_subject_panel_properties

        # render each animation
        for anim in mk_subject_props.obj_actions:

            print(f"Rendering animation: {anim.action.name}")

            frame_start = int(anim.action.frame_range[0])
            frame_end = int(anim.action.frame_range[1])
            frame_step = context.scene.frame_step
            frame_range = frame_end - frame_start

            context.scene.frame_start = frame_start
            context.scene.frame_end = frame_end

            subject.animation_data.action = anim.action

            # Bake any physics simulations etc.
            self.prepare_for_rendering(context, subject)
            self.render_frames(context, renderpaths, frame_start, frame_range, subject)

    def execute(self, context):
        scene = context.scene
        mk_export_props = scene.mk_sprites_export_panel_properties
        mk_render_props = scene.mk_sprites_render_panel_properties
        mk_subject_props = scene.mk_sprites_subject_panel_properties
        frame_step = scene.frame_step

        # set up folders to render into
        old_path = bpy.context.scene.render.filepath
        if not CreateTempFolder():
            return {"FINISHED"}
        bpy.context.scene.render.filepath = GetTempFolder()

        # set render settings
        old_x = context.scene.render.resolution_x
        old_y = context.scene.render.resolution_y
        context.scene.render.resolution_x = mk_render_props.resolution_x
        context.scene.render.resolution_y = mk_render_props.resolution_y

        renderpaths = []

        self.render(context, renderpaths)

        # once all images rendered
        size = (mk_render_props.image_resolution_x, mk_render_props.image_resolution_y)

        print(
            "Auto resolution: ",
            mk_render_props.auto_resolution,
            mk_render_props.resolution_x,
            mk_render_props.resolution_y,
            mk_subject_props.rotations,
        )
        print("Auto resolution: ", mk_subject_props.obj_actions)
        if mk_render_props.auto_resolution:
            size = AutoImageSize(
                mk_render_props.resolution_x,
                mk_render_props.resolution_y,
                mk_subject_props.obj_actions,
                mk_subject_props.rotations,
                frame_step,
            )
            print(size)

        name = mk_subject_props.obj.name
        img = TilePathsIntoImage(name, renderpaths, size[0], size[1])

        image_prop = mk_export_props.image_props.add()
        image_prop.image = img
        image_prop.object_angles = mk_subject_props.rotations
        for anim in mk_subject_props.obj_actions:
            item = image_prop.object_actions.add()
            item.action = anim.action

        print(image_prop.object_actions)

        mk_export_props.image = img
        mk_export_props.active_image = len(mk_export_props.image_props) - 1

        # cleanup
        bpy.context.scene.render.filepath = old_path
        context.scene.render.resolution_x = old_x
        context.scene.render.resolution_y = old_y

        ClearTempFolder()
        return {"FINISHED"}
