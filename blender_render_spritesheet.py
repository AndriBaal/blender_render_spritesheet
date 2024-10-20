import bpy
import os
import math

bl_info = {
    "name": "Render Spritesheet",
    "bpy": (4, 10, 0),
    "category": "Render",
}

class SpritesheetOperator(bpy.types.Operator):
    bl_idname = "render.render_spritesheet"
    bl_label = "Render Spritesheet"
    bl_description = "Render Spritesheet from Animation"

    BYTES_PER_PIXEL = 4
    DIRECTIONS = [
        'SW',
        'W',
        'NW',
        'N',
        'NE',
        'E',
        'SE',
        'S'
    ]
    ROTATION = math.radians(360.0 / len(DIRECTIONS))

    def execute(self, context):
        return self.render_sprite_sheet()
    
    def render_sprite_sheet(self):
        active_object = bpy.context.active_object
        action = active_object.animation_data.action
        scene = bpy.context.scene
        output_path = os.path.dirname(bpy.data.filepath)
        camera = scene.camera
        temp_path = bpy.app.tempdir

        sprite_width = scene.render.resolution_x
        sprite_height = scene.render.resolution_y

        if scene.render.image_settings.file_format != 'PNG':
            self.report({"WARNING"}, "Only PNG is supported!")
            return {"CANCELLED"}
        original_frame = scene.frame_current
        
        frame_step = 1
        frame_start = int(action.frame_start if action.use_frame_range else scene.frame_start)
        frame_end = int(action.frame_end if action.use_frame_range else scene.frame_end) + 1
        frame_amount = frame_end - frame_start
        
        bpy.context.scene.objects[active_object.name].select_set(True)
        original_camera = camera.location, camera.rotation_euler[2]

        action_folder = os.path.join(temp_path, action.name)
        if not os.path.exists(action_folder):
            os.makedirs(action_folder)

        sprite_sheet_width = sprite_width * frame_amount
        sprite_sheet_height = sprite_height * len(self.DIRECTIONS)
        sprite_sheet = bpy.data.images.new('SpriteSheet', width=sprite_sheet_width,
                                                height=sprite_sheet_height, alpha=True)
        buffer = [0.0] * (sprite_sheet_width * sprite_sheet_height * self.BYTES_PER_PIXEL)
        sprite_sheet_row_size = sprite_sheet.size[0] * self.BYTES_PER_PIXEL
        sprite_row_size = sprite_width * self.BYTES_PER_PIXEL
        
        for idx, direction in enumerate(self.DIRECTIONS):
            animation_folder = os.path.join(action_folder, direction)
            if not os.path.exists(animation_folder):
                os.makedirs(animation_folder)

            pivot_point = active_object.location

            translated_x = camera.location.x - pivot_point[0]
            translated_y = camera.location.y - pivot_point[1]
            translated_z = camera.location.z - pivot_point[2]

            rotated_x = translated_x * math.cos(self.ROTATION) - translated_y * math.sin(self.ROTATION)
            rotated_y = translated_x * math.sin(self.ROTATION) + translated_y * math.cos(self.ROTATION)

            camera.location.x = rotated_x + pivot_point[0]
            camera.location.y = rotated_y + pivot_point[1]
            camera.location.z = translated_z + pivot_point[2]

            camera.rotation_euler[2] += self.ROTATION


            sprite_row_offset = sprite_sheet_row_size * sprite_height * idx
            for i, frame in enumerate(range(frame_start, frame_end, frame_step)):
                scene.frame_current = frame

                file_path = os.path.join(animation_folder, f'{scene.frame_current}.png')
                scene.render.filepath = file_path
                bpy.ops.render.render(write_still=True)
                sprite = bpy.data.images.load(file_path)

                frame_offset = sprite_row_size * i
                for row in range(sprite_height):
                    row_offset = row * sprite_sheet_row_size
                    offset = sprite_row_offset + frame_offset + row_offset
                    row_offset_sprite = row * sprite_row_size
                    buffer[offset:offset + sprite_row_size] = sprite.pixels[row_offset_sprite:row_offset_sprite + sprite_row_size]
        
        sprite_sheet.pixels = buffer
        sprite_sheet.save(filepath=os.path.join(output_path, action.name + '.png'))
        camera.location, camera.rotation_euler[2] = original_camera

        scene.render.filepath = output_path
        scene.frame_current = original_frame
        
        print('Finished rendering Spritesheet!')
        return {'FINISHED'}

def draw_func(self, _context):
    layout = self.layout
    layout.separator()
    layout.operator('render.render_spritesheet', icon='RENDER_ANIMATION')

def register():
    bpy.utils.register_class(SpritesheetOperator)
    bpy.types.TOPBAR_MT_render.append(draw_func)

def unregister():
    bpy.utils.unregister_class(SpritesheetOperator)
    bpy.types.TOPBAR_MT_render.remove(draw_func)

if __name__ == '__main__':
    register()
