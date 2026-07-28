import pyray as rl

from twell import Context, SpringConfig

VIRTUAL_WIDTH: int = 828
VIRTUAL_HEIGHT: int = 1792
SCALE: float = 0.6
WINDOW_WIDTH: int = int(VIRTUAL_WIDTH * SCALE)
WINDOW_HEIGHT: int = int(VIRTUAL_HEIGHT * SCALE)
MIN_WINDOW_WIDTH: int = 300
MIN_WINDOW_HEIGHT: int = 650

OPEN_Y: float = 280.0
CLOSED_Y: float = float(VIRTUAL_HEIGHT)
COLOR_APPLE_BLUE = rl.Color(0, 122, 255, 255)
COLOR_APPLE_RED = rl.Color(255, 59, 48, 255)
COLOR_HANDLE = rl.Color(255, 255, 255, 140)
COLOR_HINT = rl.Color(255, 255, 255, 220)


def main() -> None:
    rl.set_config_flags(rl.FLAG_WINDOW_RESIZABLE)
    rl.init_window(WINDOW_WIDTH, WINDOW_HEIGHT, "iOS Bottom Sheet (Twell Engine)")
    rl.set_window_min_size(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)
    rl.set_target_fps(120)

    screen_w = float(WINDOW_WIDTH)
    screen_h = float(WINDOW_HEIGHT)
    open_y = screen_h * (OPEN_Y / VIRTUAL_HEIGHT)
    closed_y = screen_h

    # 1. Initialize Twell Context & Property
    ctx = Context(max_properties=32, max_gestures=8)
    sheet_prop = ctx.create_property(closed_y)
    gesture = ctx.create_gesture()

    # iOS Spring physics params (response=0.48, damping_ratio=0.88)
    # stiffness = (2*pi/0.48)^2 = 171.37, damping = (4*pi*0.88)/0.48 = 23.04
    spring_config = SpringConfig(mass=1.0, stiffness=171.37, damping=23.04)

    is_dragging = False
    drag_offset_y = 0.0
    target_y = closed_y

    while not rl.window_should_close():
        current_time = rl.get_time()
        screen_w = float(rl.get_screen_width())
        screen_h = float(rl.get_screen_height())

        open_y = screen_h * (OPEN_Y / VIRTUAL_HEIGHT)
        closed_y = screen_h
        midpoint_y = (open_y + closed_y) / 2.0

        mouse_y = float(rl.get_mouse_y())
        sheet_y = sheet_prop.presentation_value

        # --- INPUT & GESTURE KINETICS ---
        if rl.is_mouse_button_pressed(rl.MOUSE_BUTTON_LEFT):
            if abs(target_y - closed_y) < 1.0:
                target_y = open_y
                sheet_prop.animate_to_target(open_y, spring_config, current_time)
            elif abs(target_y - open_y) < 1.0 and mouse_y >= sheet_y:
                is_dragging = True
                drag_offset_y = mouse_y - sheet_y
                sheet_prop.track_gesture(gesture, boundary_min=open_y, boundary_max=float("inf"))

        if is_dragging:
            if rl.is_mouse_button_down(rl.MOUSE_BUTTON_LEFT):
                touch_y = mouse_y - drag_offset_y
                gesture.add_touch(touch_y, current_time)

            if rl.is_mouse_button_released(rl.MOUSE_BUTTON_LEFT):
                is_dragging = False
                rel_vel = gesture.get_velocity()

                if rel_vel > 600.0:
                    target_y = closed_y
                elif rel_vel < -600.0:
                    target_y = open_y
                else:
                    target_y = closed_y if sheet_y > midpoint_y else open_y

                sheet_prop.release_gesture_spring(gesture, target_y, spring_config, current_time)

        # --- PHYSICS ENGINE TICK ---
        ctx.tick(current_time)

        # --- RENDERING ---
        progress = max(0.0, min(1.0, (closed_y - sheet_y) / (closed_y - open_y) if closed_y != open_y else 0.0))

        rl.begin_drawing()
        rl.clear_background(rl.BLACK)

        # Background View A
        scale_view_a = 1.0 - 0.08 * progress
        scaled_w = screen_w * scale_view_a
        scaled_h = screen_h * scale_view_a
        pos_x_a = (screen_w - scaled_w) / 2.0
        pos_y_a = (screen_h - scaled_h) / 2.0 * progress + (20.0 * progress)

        rl.draw_rectangle_rounded(rl.Rectangle(pos_x_a, pos_y_a, scaled_w, scaled_h), 0.04, 16, COLOR_APPLE_BLUE)
        rl.draw_text("A", int((screen_w - 40) / 2), int(screen_h / 2 - 60), 80, rl.WHITE)
        rl.draw_text("Click to Open | Drag Down to Close", int((screen_w - 240) / 2), int(screen_h / 2 + 40), 16, rl.Color(255, 255, 255, 200))

        if progress > 0.0:
            rl.draw_rectangle_rec(rl.Rectangle(pos_x_a, pos_y_a, scaled_w, scaled_h), rl.Color(0, 0, 0, int(120 * progress)))

        # Modal Sheet View B
        if sheet_y < closed_y:
            sheet_h = screen_h + 400.0
            rl.draw_rectangle_rounded(rl.Rectangle(0, sheet_y, screen_w, sheet_h), 0.05, 16, COLOR_APPLE_RED)
            rl.draw_rectangle_rec(rl.Rectangle(0, sheet_y + 40.0, screen_w, sheet_h), COLOR_APPLE_RED)

            # Drag Handle
            handle_w = 48.0
            handle_h = 6.0
            rl.draw_rectangle_rounded(rl.Rectangle((screen_w - handle_w) / 2.0, sheet_y + 14.0, handle_w, handle_h), 1.0, 8, COLOR_HANDLE)

            rl.draw_text("B", int((screen_w - 40) / 2), int(sheet_y + 100), 80, rl.WHITE)
            rl.draw_text("Swipe down to close", int((screen_w - 160) / 2), int(sheet_y + 220), 18, COLOR_HINT)

        rl.end_drawing()

    sheet_prop.destroy()
    gesture.destroy()
    rl.close_window()


if __name__ == "__main__":
    main()
