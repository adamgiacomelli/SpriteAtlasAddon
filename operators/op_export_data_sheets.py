import bpy
import os
import xml.etree.ElementTree as xml
import json

from bpy.types import PropertyGroup
from bpy.props import PointerProperty, StringProperty, IntProperty, BoolProperty, CollectionProperty, EnumProperty

from ..utils.xmlutils import GetMonoXMLHeader, GetXMLHeader, XMLIndent, ExportXml
from ..utils.helpers import GetTilePos, GetActionFrameCount

def make_mono_source(width, height, pos_x, pos_y):
    return str(pos_x) + " " + str(pos_y) + " " + str(width) + " " + str(height)

class MK_SPRITES_OP_export_bevy_image_json(bpy.types.Operator):
    """open_action_menu"""
    bl_idname = "mk_sprites.export_bevy_image_json"
    bl_label = "Add Action"
    bl_options = {'REGISTER'}

    filepath: bpy.props.StringProperty(name="filepath")

    def execute(self, context):
        mk_render_props = context.scene.mk_sprites_render_panel_properties
        export_props = context.scene.mk_sprites_export_panel_properties
        frame_step = context.scene.frame_step
        active_image = export_props.image_props[export_props.active_image]

        if active_image.image is None:
            return {'FINISHED'}

        image_width = active_image.image.size[0]
        image_height = active_image.image.size[1]

        animations = {}
        n = 0
        for action_obj in active_image.object_actions:
            for obj_rot in range(active_image.object_angles):
                if action_obj is None or action_obj.action is None:
                    continue

                action_mode =  action_obj.action.get("mode", "Repeat X")
                print(f"Setting up action {action_obj.action.name}, r:{obj_rot},n:{n}, mode: {action_mode}")
                action_name = action_obj.action.name + "_" + str(obj_rot)
                animations[action_name] = {
                    "mode": action_mode,
                    "fps": context.scene.render.fps,
                    "size_x": mk_render_props.resolution_x,
                    "size_y": mk_render_props.resolution_y,
                    "frames": list(range(GetActionFrameCount(action_obj.action, frame_step))),
                    "row": n
                }
                n += 1

        img_path = os.path.splitext(self.filepath)

        output = {
            "width": image_width,
            "height": image_height,
            "animations": animations
        }

        with open(img_path[0] + ".animation_set.json", 'w') as f:
            json.dump(output, f, indent=2, sort_keys=True)

        return {'FINISHED'}

class MK_SPRITES_OP_export_godot_sprite_frames(bpy.types.Operator):
    """Export Sprite Frames for Godot"""
    bl_idname = "mk_sprites.export_godot_sprite_frames"
    bl_label = "Export Godot Sprite Frames"
    bl_options = {'REGISTER'}

    filepath: bpy.props.StringProperty(name="filepath")

    def execute(self, context):
        mk_render_props = context.scene.mk_sprites_render_panel_properties
        export_props = context.scene.mk_sprites_export_panel_properties
        frame_step = context.scene.frame_step
        active_image = export_props.image_props[export_props.active_image]

        if active_image.image is None:
            return {'FINISHED'}

        image_width = active_image.image.size[0]
        image_height = active_image.image.size[1]
        sprite_width = mk_render_props.resolution_x
        sprite_height = mk_render_props.resolution_y
        frames_per_row = image_width // sprite_width
        image_name = os.path.basename(self.filepath)

        tres_content = '[gd_resource type="SpriteFrames" load_steps=20 format=3]\n\n'
        tres_content += f'[ext_resource type="Texture2D" path="res://sprites/animated/{image_name}" id=1]\n\n'

        sub_resources = ""
        animations = '[resource]\nanimations = ['
        frame_index = 0
        animation_counter = 0

        for action_obj in active_image.object_actions:
            for obj_rot in range(active_image.object_angles):
                if action_obj is None or action_obj.action is None:
                    continue

                action_frames = GetActionFrameCount(action_obj.action, frame_step)
                animation_frames = []

                for i in range(action_frames):
                    x = (frame_index % frames_per_row) * sprite_width
                    y = (frame_index // frames_per_row) * sprite_height

                    sub_resource_id = f"AtlasTexture_{frame_index}"
                    sub_resources += f'[sub_resource type="AtlasTexture" id="{sub_resource_id}"]\n'
                    sub_resources += 'atlas = ExtResource(1)\n'
                    sub_resources += f'region = Rect2({x}, {y}, {sprite_width}, {sprite_height})\n\n'
                    
                    animation_frames.append(f'{{"duration": 1.0, "texture": SubResource("{sub_resource_id}")}}')
                    frame_index += 1

                animation_name = action_obj.action.name + "_" + str(obj_rot)
                animations += '{\n'
                animations += '"frames": [\n' + ',\n'.join(animation_frames) + '\n],\n'
                animations += f'"loop": true,\n"name": "{animation_name}",\n"speed": 12.0\n'
                animations += '},\n'
                animation_counter += 1

        animations += ']'
        tres_content += sub_resources + animations

        # Write the .tres file
        tres_path = os.path.splitext(self.filepath)[0] + '.tres'
        with open(tres_path, 'w') as file:
            file.write(tres_content)

        return {'FINISHED'}

class MK_SPRITES_OP_export_image_json(bpy.types.Operator):
    """open_action_menu"""
    bl_idname = "mk_sprites.export_image_json"
    bl_label = "Add Action"
    bl_options = {'REGISTER'}

    filepath: bpy.props.StringProperty(name="filepath")

    def execute(self, context):
        mk_render_props = context.scene.mk_sprites_render_panel_properties
        export_props = context.scene.mk_sprites_export_panel_properties
        frame_step = context.scene.frame_step
        active_image = export_props.image_props[export_props.active_image]

        if active_image.image == None:
            return {'FINISHED'}

        image_width = active_image.image.size[0]
        image_height = active_image.image.size[1]

        n = 0
        items = []
        for obj_rot in range(active_image.object_angles):
            for action_obj in active_image.object_actions:
                if (action_obj == None or action_obj.action == None):
                    continue

                item = {}
                item["frames"] = GetActionFrameCount(action_obj.action, frame_step)
                item["framerate"] = context.scene.render.fps
                item["loop"] = True
                item["name"] = action_obj.action.name + "_" + str(obj_rot)
                item["width"] = mk_render_props.resolution_x
                item["height"] = mk_render_props.resolution_y
                posX, posY = GetTilePos(mk_render_props.resolution_x, mk_render_props.resolution_y, image_width, image_height, n)
                item["source_x"] = str(posX)
                item["source_y"] = str(posY)
                item["texture"] = os.path.basename(self.filepath)

                items.append(item)
                n += 1

        img_path = os.path.splitext(self.filepath)

        f = open(img_path[0] + ".json", 'w')
        f.write(json.dumps(items, indent=2, sort_keys=True))
        f.close()

        return {'FINISHED'}


class MK_SPRITES_OP_export_image_xml(bpy.types.Operator):
    """open_action_menu"""
    bl_idname = "mk_sprites.export_image_xml"
    bl_label = "Add Action"
    bl_options = {'REGISTER'}

    filepath: bpy.props.StringProperty(name="filepath")
    use_mono: bpy.props.BoolProperty(name="use_mono")

    def execute(self, context):
        mk_render_props = context.scene.mk_sprites_render_panel_properties
        export_props = context.scene.mk_sprites_export_panel_properties
        frame_step = context.scene.frame_step
        active_image = export_props.image_props[export_props.active_image]

        # start tree
        if self.use_mono:
            root, asset = GetMonoXMLHeader("animation")
        else:
            root, asset = GetXMLHeader()

        animations = xml.SubElement(asset, "animations")

        if active_image.image == None:
            return {'FINISHED'}

        image_width = active_image.image.size[0]
        image_height = active_image.image.size[1]
        n = 0

        for obj_rot in range(active_image.object_angles):
            for action_obj in active_image.object_actions:

                print(action_obj.action)
                if (action_obj == None or action_obj.action == None):
                    continue

                item = xml.SubElement(animations, "Item")

                xml.SubElement(item, "frames").text = str(GetActionFrameCount(action_obj.action, frame_step))
                xml.SubElement(item, "framerate").text = str(context.scene.render.fps)
                xml.SubElement(item, "loop").text = "True"
                xml.SubElement(item, "name").text = action_obj.action.name + "_" + str(obj_rot)

                width = mk_render_props.resolution_x
                height = mk_render_props.resolution_y
                posX, posY = GetTilePos(width, height, image_width, image_height, n)

                if self.use_mono:
                    xml.SubElement(item, "source").text = make_mono_source(width, height, posX, posY)
                else:
                    xml.SubElement(item, "width").text = str(width)
                    xml.SubElement(item, "height").text = str(height)
                    xml.SubElement(item, "source_x").text = str(posX)
                    xml.SubElement(item, "source_y").text = str(posY)

                xml.SubElement(item, "texture").text = os.path.basename(self.filepath)
                n+=1

        img_path = os.path.splitext(self.filepath)
        xml_path = img_path[0] + ".xml"

        XMLIndent(root)
        ExportXml(xml_path, root)

        return {'FINISHED'}
