import time
import pygame

from twell import Context, SpringConfig, Vector2


def main():
    pygame.init()
    pygame.font.init()

    window_width = 800
    window_height = 600
    screen = pygame.display.set_mode((window_width, window_height))
    pygame.display.set_caption("Hello, Twell! (Pygame)")
    clock = pygame.time.Clock()

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

    # rubber banding boundary
    bounds_min = Vector2(100.0, 100.0)
    bounds_max = Vector2(700.0, 500.0)

    card_width = 120
    card_height = 120

    # font stuff
    title_font = pygame.font.SysFont("sans-serif", 28, bold=True)
    subtitle_font = pygame.font.SysFont("sans-serif", 18)
    small_font = pygame.font.SysFont("sans-serif", 14)

    bg_color = (240, 243, 248)
    bounds_color = (210, 218, 230)
    card_color = (45, 120, 230)
    shadow_color = (30, 50, 90, 40)
    text_color = (90, 105, 125)
    subtext_color = (140, 155, 175)
    center_color = (200, 70, 70)

    running = True
    while running:
        current_time = time.time()
        mouse_x, mouse_y = pygame.mouse.get_pos()

        # current card collision rect
        card_rect = pygame.Rect(
            render_pos.x - card_width / 2.0,
            render_pos.y - card_height / 2.0,
            card_width,
            card_height
        )

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if card_rect.collidepoint(mouse_x, mouse_y):
                    is_dragging = True
                    # record grab offset so card position doesn't snap to mouse cursor
                    grab_offset.x = mouse_x - render_pos.x
                    grab_offset.y = mouse_y - render_pos.y

                    # lock property to 1:1 tracking with rubber-banding boundaries
                    prop_pos.track_gesture(gesture_pos, bounds_min, bounds_max)

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if is_dragging:
                    is_dragging = False
                    # seamless handoff: release tracking and spring back to center using gesture release velocity
                    prop_pos.release_gesture_spring(gesture_pos, center, spring, current_time)

        if is_dragging:
            # feed mouse position into gesture low-pass filter
            touch_pos = Vector2(mouse_x - grab_offset.x, mouse_y - grab_offset.y)
            gesture_pos.add_touch(touch_pos, current_time)

        ctx.tick(current_time)
        render_pos = prop_pos.presentation_value
        screen.fill(bg_color)

        # header titles
        title_surf = title_font.render("Hello, Twell!", True, text_color)
        subtitle_surf = subtitle_font.render("This card is spring-loaded. You can flick it!", True, subtext_color)
        screen.blit(title_surf, title_surf.get_rect(center=(window_width // 2, 40)))
        screen.blit(subtitle_surf, subtitle_surf.get_rect(center=(window_width // 2, 72)))

        # draw rb boundary box
        bounds_rect = pygame.Rect(
            bounds_min.x,
            bounds_min.y,
            bounds_max.x - bounds_min.x,
            bounds_max.y - bounds_min.y
        )
        pygame.draw.rect(screen, bounds_color, bounds_rect, width=2)
        boundary_lbl = small_font.render("Rubber-band boundary", True, subtext_color)
        screen.blit(boundary_lbl, (bounds_min.x + 10, bounds_min.y + 10))

        # card shadow
        shadow_offset = 12 if is_dragging else 6
        shadow_surface = pygame.Surface((card_width, card_height), pygame.SRCALPHA)
        pygame.draw.rect(shadow_surface, shadow_color, (0, 0, card_width, card_height), border_radius=12)
        screen.blit(
            shadow_surface,
            (render_pos.x - card_width / 2.0, render_pos.y - card_height / 2.0 + shadow_offset)
        )

        # card body
        curr_card_rect = pygame.Rect(
            render_pos.x - card_width / 2.0,
            render_pos.y - card_height / 2.0,
            card_width,
            card_height
        )
        pygame.draw.rect(screen, card_color, curr_card_rect, border_radius=12)

        # center target pin
        pygame.draw.circle(screen, center_color, (int(center.x), int(center.y)), 5)
        center_lbl = small_font.render("Center", True, center_color)
        screen.blit(center_lbl, (center.x + 10, center.y - 8))

        # status text at bottom
        vel = gesture_pos.get_velocity_2d()
        status_str = f"Presentation: ({render_pos.x:.1f}, {render_pos.y:.1f}) | Velocity: ({vel.x:.1f}, {vel.y:.1f}) px/s"
        status_surf = small_font.render(status_str, True, subtext_color)
        screen.blit(status_surf, (20, window_height - 30))

        pygame.display.flip()
        clock.tick(120)

    prop_pos.destroy()
    gesture_pos.destroy()
    pygame.quit()

if __name__ == "__main__":
    main()
