import ctypes
import sys
import time
import sdl3
import skia

from twell import Context, SpringConfig, Vector2


def main():
    if not sdl3.SDL_Init(sdl3.SDL_INIT_VIDEO):
        print(f"Failed to initialize SDL3: {sdl3.SDL_GetError().decode('utf-8', errors='replace')}")
        sys.exit(1)

    window_width = 800
    window_height = 600
    window_title = b"Hello, Twell!"

    window = sdl3.SDL_CreateWindow(window_title, window_width, window_height, 0)
    if not window:
        print("Failed to create SDL3 window")
        sdl3.SDL_Quit()
        sys.exit(1)

    renderer = sdl3.SDL_CreateRenderer(window, None)
    if not renderer:
        print("Failed to create SDL3 renderer")
        sdl3.SDL_DestroyWindow(window)
        sdl3.SDL_Quit()
        sys.exit(1)

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

    is_dragging = False
    grab_offset = Vector2(0.0, 0.0)
    render_pos = center
    mouse_x = center.x
    mouse_y = center.y

    bounds_min = Vector2(100.0, 100.0)
    bounds_max = Vector2(700.0, 500.0)

    card_width = 120.0
    card_height = 120.0

    image_info = skia.ImageInfo.Make(
        window_width,
        window_height,
        skia.ColorType.kRGBA_8888_ColorType,
        skia.AlphaType.kPremul_AlphaType
    )
    skia_surface = skia.Surface.MakeRaster(image_info)
    canvas = skia_surface.getCanvas()

    sdl_texture = sdl3.SDL_CreateTexture(
        renderer,
        sdl3.SDL_PIXELFORMAT_RGBA32,
        sdl3.SDL_TEXTUREACCESS_STREAMING,
        window_width,
        window_height
    )

    title_font = skia.Font(skia.Typeface('sans-serif', skia.FontStyle.Bold()), 26)
    subtitle_font = skia.Font(skia.Typeface('sans-serif'), 15)
    small_font = skia.Font(skia.Typeface('sans-serif'), 13)

    bg_color = skia.Color(240, 243, 248, 255)
    bounds_paint = skia.Paint(
        Color=skia.Color(210, 218, 230, 255),
        Style=skia.Paint.kStroke_Style,
        StrokeWidth=2.0,
        AntiAlias=True
    )
    shadow_paint = skia.Paint(
        Color=skia.Color(30, 50, 90, 40),
        AntiAlias=True
    )
    card_paint = skia.Paint(
        Color=skia.Color(45, 120, 230, 255),
        AntiAlias=True
    )
    center_paint = skia.Paint(
        Color=skia.Color(200, 70, 70, 255),
        AntiAlias=True
    )
    text_paint = skia.Paint(
        Color=skia.Color(90, 105, 125, 255),
        AntiAlias=True
    )
    subtext_paint = skia.Paint(
        Color=skia.Color(140, 155, 175, 255),
        AntiAlias=True
    )

    running = True
    event = sdl3.SDL_Event()

    while running:
        current_time = time.time()

        while sdl3.SDL_PollEvent(ctypes.byref(event)):
            if event.type == sdl3.SDL_EVENT_QUIT:
                running = False
            elif event.type == sdl3.SDL_EVENT_KEY_DOWN:
                if event.key.key == sdl3.SDLK_ESCAPE:
                    running = False

            elif event.type == sdl3.SDL_EVENT_MOUSE_BUTTON_DOWN:
                if event.button.button == sdl3.SDL_BUTTON_LEFT:
                    mx, my = float(event.button.x), float(event.button.y)
                    # Define current card collision rect
                    card_left = render_pos.x - card_width / 2.0
                    card_top = render_pos.y - card_height / 2.0
                    if card_left <= mx <= card_left + card_width and card_top <= my <= card_top + card_height:
                        is_dragging = True
                        # Record grab offset so card position doesn't snap to mouse cursor
                        grab_offset.x = mx - render_pos.x
                        grab_offset.y = my - render_pos.y
                        mouse_x, mouse_y = mx, my

                        # Seed initial touch position before gesture tracking begins
                        touch_pos = Vector2(mx - grab_offset.x, my - grab_offset.y)
                        gesture_pos.add_touch(touch_pos, current_time)

                        # Lock property to 1:1 tracking with rubber-banding boundaries
                        prop_pos.track_gesture(gesture_pos, bounds_min, bounds_max)

            elif event.type == sdl3.SDL_EVENT_MOUSE_BUTTON_UP:
                if event.button.button == sdl3.SDL_BUTTON_LEFT and is_dragging:
                    is_dragging = False
                    # Seamless handoff: release tracking and spring back to center using gesture release velocity
                    prop_pos.release_gesture_spring(gesture_pos, center, spring, current_time)

            elif event.type == sdl3.SDL_EVENT_MOUSE_MOTION:
                mouse_x, mouse_y = float(event.motion.x), float(event.motion.y)

        if is_dragging:
            # Feed current touch position into gesture low-pass filter
            touch_pos = Vector2(mouse_x - grab_offset.x, mouse_y - grab_offset.y)
            gesture_pos.add_touch(touch_pos, current_time)

        # Tick physics engine
        ctx.tick(current_time)

        # Get latest presentation position from Twell
        render_pos = prop_pos.presentation_value

        # Render frame with Skia
        canvas.clear(bg_color)

        # Header Titles
        title_str = "Hello, Twell!"
        subtitle_str = "This card is spring-loaded. You can flick it!"

        title_w = title_font.measureText(title_str)
        subtitle_w = subtitle_font.measureText(subtitle_str)

        canvas.drawString(title_str, (window_width - title_w) / 2.0, 45, title_font, text_paint)
        canvas.drawString(subtitle_str, (window_width - subtitle_w) / 2.0, 75, subtitle_font, subtext_paint)

        # Draw rubber-banding boundary box
        bounds_rect = skia.Rect.MakeLTRB(bounds_min.x, bounds_min.y, bounds_max.x, bounds_max.y)
        canvas.drawRect(bounds_rect, bounds_paint)
        canvas.drawString("Rubber-band boundary", bounds_min.x + 10, bounds_min.y + 20, small_font, subtext_paint)

        # Card shadow
        shadow_offset = 12.0 if is_dragging else 6.0
        shadow_rect = skia.Rect.MakeXYWH(
            render_pos.x - card_width / 2.0,
            render_pos.y - card_height / 2.0 + shadow_offset,
            card_width,
            card_height
        )
        canvas.drawRRect(skia.RRect.MakeRectXY(shadow_rect, 12, 12), shadow_paint)

        # Card body
        card_rect = skia.Rect.MakeXYWH(
            render_pos.x - card_width / 2.0,
            render_pos.y - card_height / 2.0,
            card_width,
            card_height
        )
        canvas.drawRRect(skia.RRect.MakeRectXY(card_rect, 12, 12), card_paint)

        # Center target pin
        canvas.drawCircle(center.x, center.y, 5, center_paint)
        canvas.drawString("Center", center.x + 10, center.y + 4, small_font, center_paint)

        # Status text at bottom
        vel = gesture_pos.get_velocity_2d()
        status_str = f"Presentation: ({render_pos.x:.1f}, {render_pos.y:.1f}) | Velocity: ({vel.x:.1f}, {vel.y:.1f}) px/s"
        canvas.drawString(status_str, 20, window_height - 25, small_font, subtext_paint)

        # Update SDL texture with Skia rendered pixels & present
        img_bytes = skia_surface.makeImageSnapshot().tobytes()
        sdl3.SDL_UpdateTexture(sdl_texture, None, img_bytes, window_width * 4)

        sdl3.SDL_RenderClear(renderer)
        sdl3.SDL_RenderTexture(renderer, sdl_texture, None, None)
        sdl3.SDL_RenderPresent(renderer)

    prop_pos.destroy()
    gesture_pos.destroy()
    sdl3.SDL_DestroyTexture(sdl_texture)
    sdl3.SDL_DestroyRenderer(renderer)
    sdl3.SDL_DestroyWindow(window)
    sdl3.SDL_Quit()


if __name__ == "__main__":
    main()
