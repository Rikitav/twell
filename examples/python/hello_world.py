import pyray as raylib

from twell import Context, SpringConfig, Vector2

def main():
    window_width = 800
    window_height = 600
    raylib.init_window(window_width, window_height, "Hello, Twell!")
    raylib.set_target_fps(120)

    ctx = Context(max_properties=128, max_gestures=32)
    center = Vector2(window_width / 2.0, window_height / 2.0)

    prop_pos = ctx.create_property_2d(center)

    gesture_pos = ctx.create_gesture()

    spring = SpringConfig(
        mass=1.0,
        stiffness=250.0,
        damping=18.0,
        initial_velocity=0.0
    )

    # state
    is_dragging = False
    grab_offset = Vector2(0.0, 0.0)
    render_pos = center

    # boundary limits for rubber-banding
    bounds_min = Vector2(100.0, 100.0)
    bounds_max = Vector2(700.0, 500.0)

    card_width = 120
    card_height = 120

    # colors
    bg_color = raylib.Color(240, 243, 248, 255)
    bounds_color = raylib.Color(210, 218, 230, 255)
    card_color = raylib.Color(45, 120, 230, 255)
    shadow_color = raylib.Color(30, 50, 90, 40)
    text_color = raylib.Color(90, 105, 125, 255)
    subtext_color = raylib.Color(140, 155, 175, 255)

    while not raylib.window_should_close():
        time = raylib.get_time()

        # input handling
        mouse = raylib.get_mouse_position()
        card_rec = raylib.Rectangle(
            render_pos.x - card_width / 2.0,
            render_pos.y - card_height / 2.0,
            card_width,
            card_height
        )

        if raylib.is_mouse_button_pressed(raylib.MOUSE_BUTTON_LEFT) and raylib.check_collision_point_rec(mouse, card_rec):
            is_dragging = True
            # record grab offset so the card doesn't jump to mouse center
            grab_offset.x = mouse.x - render_pos.x
            grab_offset.y = mouse.y - render_pos.y

            # lock property to 1:1 tracking with rubber-banding boundaries
            prop_pos.track_gesture(gesture_pos, bounds_min, bounds_max)

        if is_dragging:
            # feed current touch position into gesture low-pass filter
            current_touch = Vector2(mouse.x - grab_offset.x, mouse.y - grab_offset.y)
            gesture_pos.add_touch(current_touch, time)

            if raylib.is_mouse_button_released(raylib.MOUSE_BUTTON_LEFT):
                is_dragging = False
                # seamless handoff: releases tracking and fires spring with gesture velocity
                prop_pos.release_gesture_spring(gesture_pos, center, spring, time)

        # tick physics
        ctx.tick(time)

        # resolve state
        render_pos = prop_pos.presentation_value

        # render
        raylib.begin_drawing()
        raylib.clear_background(bg_color)

        # Header Instructions
        title = "Hello, Twell!"
        subtitle = "This card is spring-loaded. You can flick it!"

        title_width = raylib.measure_text(title, 22)
        subtitle_width = raylib.measure_text(subtitle, 15)
        
        raylib.draw_text(title, int((window_width - title_width) / 2), 40, 22, text_color)
        raylib.draw_text(subtitle, int((window_width - subtitle_width) / 2), 72, 15, subtext_color)

        # Draw rubber-banding Boundary Box
        bounds_rec = raylib.Rectangle(
            bounds_min.x,
            bounds_min.y,
            bounds_max.x - bounds_min.x,
            bounds_max.y - bounds_min.y
        )
        raylib.draw_rectangle_lines_ex(bounds_rec, 2, bounds_color)
        raylib.draw_text("Rubber-band boundary", int(bounds_min.x + 10), int(bounds_min.y + 10), 12, subtext_color)

        # card shadow
        shadow_offset = 12 if is_dragging else 6
        shadow_rec = raylib.Rectangle(
            render_pos.x - card_width / 2.0,
            render_pos.y - card_height / 2.0 + shadow_offset,
            card_width,
            card_height
        )
        raylib.draw_rectangle_rounded(shadow_rec, 0.2, 8, shadow_color)

        # card
        curr_card_rec = raylib.Rectangle(
            render_pos.x - card_width / 2.0,
            render_pos.y - card_height / 2.0,
            card_width,
            card_height
        )
        raylib.draw_rectangle_rounded(curr_card_rec, 0.2, 8, card_color)

        # center target pin
        raylib.draw_circle(int(center.x), int(center.y), 4, raylib.Color(200, 70, 70, 255))
        raylib.draw_text("Center", int(center.x + 10), int(center.y - 6), 12, raylib.Color(200, 70, 70, 200))

        # status text at bottom
        vel = gesture_pos.get_velocity_2d()
        status_str = f"Presentation: ({render_pos.x:.1f}, {render_pos.y:.1f}) | Velocity: ({vel.x:.1f}, {vel.y:.1f}) px/s"
        raylib.draw_text(status_str, 20, window_height - 30, 14, subtext_color)

        raylib.end_drawing()

    # cleanup
    prop_pos.destroy()
    gesture_pos.destroy()
    raylib.close_window()

if __name__ == "__main__":
    main()
