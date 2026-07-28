"""
features:
- four spring-suspended cards with 2D positions, scale squish, and rotation wobble
- interactive dragging with 1:1 gesture tracking and rubber-banding
- momentum transfer and physical impact collisions between cards
- dynamic coiled spring visualization.
- particle burst effects on impacts.
- 3 interactive presets

This example was developed using AI assistance
"""

import sys
import math
import random
import pyray as pr

from twell import Context, SpringConfig, UnitType

WINDOW_WIDTH = 960
WINDOW_HEIGHT = 640
NUM_CARDS = 4

CARD_WIDTH = 110.0
CARD_HEIGHT = 130.0
ANCHOR_Y = 90.0
REST_Y = 340.0
SPACING_X = 145.0

# calculate centered initial X positions for 4 cards
START_X = (WINDOW_WIDTH - ((NUM_CARDS - 1) * SPACING_X)) / 2.0
REST_POSITIONS = [(START_X + i * SPACING_X, REST_Y) for i in range(NUM_CARDS)]
ANCHOR_POSITIONS = [(START_X + i * SPACING_X, ANCHOR_Y) for i in range(NUM_CARDS)]

CARD_COLORS = [
    {"main": pr.Color(0, 195, 255, 255),  "dark": pr.Color(0, 130, 200, 255),  "accent": pr.Color(180, 240, 255, 255), "name": "Cyan"},
    {"main": pr.Color(165, 95, 255, 255), "dark": pr.Color(110, 50, 200, 255),  "accent": pr.Color(220, 190, 255, 255), "name": "Violet"},
    {"main": pr.Color(255, 105, 120, 255),"dark": pr.Color(200, 50, 70, 255),   "accent": pr.Color(255, 200, 210, 255), "name": "Coral"},
    {"main": pr.Color(45, 215, 155, 255), "dark": pr.Color(20, 150, 100, 255),  "accent": pr.Color(180, 255, 220, 255), "name": "Mint"},
]

# Spring physics presets
PRESETS = {
    1: {"name": "Bouncy", "mass": 1.0, "stiffness": 220.0, "damping": 11.0, "desc": "High oscillation & reactive chain reactions"},
    2: {"name": "Damped", "mass": 1.0, "stiffness": 380.0, "damping": 26.0, "desc": "Firm, rapid settling with tight control"},
    3: {"name": "Heavy",  "mass": 2.5, "stiffness": 180.0, "damping": 14.0, "desc": "Weighted, powerful impact momentum"},
}


class Particle:
    """Impact spark particle effect."""
    def __init__(self, x: float, y: float, color: pr.Color):
        angle = random.uniform(0.0, 2.0 * math.pi)
        speed = random.uniform(80.0, 320.0)
        self.x = x
        self.y = y
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.radius = random.uniform(3.0, 7.0)
        self.color = color
        self.alpha = 1.0
        self.decay = random.uniform(2.5, 4.0)

    def update(self, dt: float) -> bool:
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.alpha -= self.decay * dt
        return self.alpha > 0.0

    def draw(self):
        c = pr.Color(self.color.r, self.color.g, self.color.b, int(max(0, self.alpha) * 255))
        pr.draw_circle(int(self.x), int(self.y), self.radius * self.alpha, c)


def draw_coiled_spring(
    start_x: float, start_y: float, end_x: float, end_y: float,
    coils: int = 10, width: float = 12.0, color: pr.Color = pr.Color(160, 175, 195, 255), thickness: float = 2.5
):
    """Renders a 2D coiled spring line connecting anchor pin to rectangle."""
    dx = end_x - start_x
    dy = end_y - start_y
    length = math.hypot(dx, dy)
    if length < 1.0:
        return

    angle = math.atan2(dy, dx)
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)

    lead = 15.0
    tail = 15.0
    coil_length = max(1.0, length - lead - tail)

    points = []
    points.append((start_x, start_y))

    # Lead straight segment
    p1_x = start_x + lead * cos_a
    p1_y = start_y + lead * sin_a
    points.append((p1_x, p1_y))

    # Coils
    num_steps = coils * 2
    for i in range(1, num_steps):
        t = i / float(num_steps)
        lx = lead + t * coil_length
        ly = width if (i % 2 == 1) else -width
        px = start_x + lx * cos_a - ly * sin_a
        py = start_y + lx * sin_a + ly * cos_a
        points.append((px, py))

    # Tail straight segment
    p2_x = start_x + (length - tail) * cos_a
    p2_y = start_y + (length - tail) * sin_a
    points.append((p2_x, p2_y))
    points.append((end_x, end_y))

    for i in range(len(points) - 1):
        pa = points[i]
        pb = points[i + 1]
        pr.draw_line_ex(
            pr.Vector2(pa[0], pa[1]),
            pr.Vector2(pb[0], pb[1]),
            thickness,
            color
        )


def main():
    # 1. Initialize Raylib Window
    pr.set_config_flags(pr.FLAG_MSAA_4X_HINT)
    pr.init_window(WINDOW_WIDTH, WINDOW_HEIGHT, "Twell + Raylib: Spring Impact & Chain Reaction")
    pr.set_target_fps(120)

    # 2. Initialize Twell Context
    ctx = Context(max_properties=64, max_gestures=16)

    # State per Card: Twell Properties for Position X, Position Y, Scale, Rotation
    props_x = []
    props_y = []
    props_scale = []
    props_rot = []
    gestures_x = []
    gestures_y = []

    for i in range(NUM_CARDS):
        rx, ry = REST_POSITIONS[i]
        px = ctx.create_property(rx, unit=UnitType.PIXELS)
        py = ctx.create_property(ry, unit=UnitType.PIXELS)
        ps = ctx.create_property(1.0, unit=UnitType.PIXELS)
        pr_rot = ctx.create_property(0.0, unit=UnitType.DEGREES)

        gx = ctx.create_gesture()
        gy = ctx.create_gesture()

        props_x.append(px)
        props_y.append(py)
        props_scale.append(ps)
        props_rot.append(pr_rot)
        gestures_x.append(gx)
        gestures_y.append(gy)

    # Interaction & Dragging state
    active_preset_id = 1
    preset = PRESETS[active_preset_id]

    dragged_card = -1
    grab_offset_x = 0.0
    grab_offset_y = 0.0

    # Impact particles & stats
    particles = []
    impact_count = 0
    max_impact_vel = 0.0
    last_impact_time = 0.0
    cooldown_matrix = [[0.0] * NUM_CARDS for _ in range(NUM_CARDS)]

    # Tracking previous frame presentation values for velocity calculation
    prev_pos_x = [REST_POSITIONS[i][0] for i in range(NUM_CARDS)]
    prev_pos_y = [REST_POSITIONS[i][1] for i in range(NUM_CARDS)]
    curr_vel_x = [0.0] * NUM_CARDS
    curr_vel_y = [0.0] * NUM_CARDS

    # Colors for UI
    bg_color = pr.Color(16, 20, 28, 255)
    panel_color = pr.Color(26, 32, 44, 220)
    border_color = pr.Color(50, 62, 84, 255)
    text_white = pr.Color(240, 244, 250, 255)
    text_muted = pr.Color(140, 155, 175, 255)
    text_accent = pr.Color(0, 195, 255, 255)
    pin_color = pr.Color(255, 180, 50, 255)

    is_test = "--test" in sys.argv or "--headless" in sys.argv
    frame_count = 0

    while not pr.window_should_close():
        frame_count += 1
        if is_test and frame_count > 60:
            break

        current_time = pr.get_time()
        dt = pr.get_frame_time() if not is_test else 1.0 / 120.0

        # Update spring configuration from active preset
        spring_config = SpringConfig(
            mass=preset["mass"],
            stiffness=preset["stiffness"],
            damping=preset["damping"],
            initial_velocity=0.0
        )

        # --- KEYBOARD CONTROLS ---
        if pr.is_key_pressed(pr.KEY_ONE):
            active_preset_id = 1
            preset = PRESETS[1]
        elif pr.is_key_pressed(pr.KEY_TWO):
            active_preset_id = 2
            preset = PRESETS[2]
        elif pr.is_key_pressed(pr.KEY_THREE):
            active_preset_id = 3
            preset = PRESETS[3]

        # Reset All Cards
        if pr.is_key_pressed(pr.KEY_R):
            for i in range(NUM_CARDS):
                rx, ry = REST_POSITIONS[i]
                props_x[i].set_value_immediate(rx)
                props_y[i].set_value_immediate(ry)
                props_scale[i].set_value_immediate(1.0)
                props_rot[i].set_value_immediate(0.0)

        # Auto-Pull & Launch Leftmost Card
        if pr.is_key_pressed(pr.KEY_SPACE):
            rx, ry = REST_POSITIONS[0]
            # Displace Card 0 far to the left and release with rightward launch velocity!
            props_x[0].set_value_immediate(rx - 160.0)
            launch_spring = SpringConfig(
                mass=preset["mass"],
                stiffness=preset["stiffness"],
                damping=preset["damping"],
                initial_velocity=750.0  # High spring launch impulse
            )
            props_x[0].animate_to_target(rx, launch_spring, current_time)

        # --- MOUSE INPUT & DRAGGING ---
        mouse_pos = pr.get_mouse_position()

        if pr.is_mouse_button_pressed(pr.MOUSE_BUTTON_LEFT):
            for i in range(NUM_CARDS):
                px = props_x[i].presentation_value
                py = props_y[i].presentation_value
                s = props_scale[i].presentation_value
                w = CARD_WIDTH * s
                h = CARD_HEIGHT * s
                card_rec = pr.Rectangle(px - w / 2.0, py - h / 2.0, w, h)

                if pr.check_collision_point_rec(mouse_pos, card_rec):
                    dragged_card = i
                    grab_offset_x = mouse_pos.x - px
                    grab_offset_y = mouse_pos.y - py

                    # Lock Twell properties to 1:1 gesture tracking with boundary resistance
                    rx, ry = REST_POSITIONS[i]
                    props_x[i].track_gesture(gestures_x[i], boundary_min=rx - 250.0, boundary_max=rx + 250.0)
                    props_y[i].track_gesture(gestures_y[i], boundary_min=ry - 200.0, boundary_max=ry + 200.0)

                    # Light squish when grabbed
                    props_scale[i].animate_to_target(1.08, SpringConfig(mass=0.2, stiffness=350, damping=15), current_time)
                    break

        if dragged_card != -1:
            target_touch_x = mouse_pos.x - grab_offset_x
            target_touch_y = mouse_pos.y - grab_offset_y

            # Feed touch positions into Twell low-pass gesture filter
            gestures_x[dragged_card].add_touch(target_touch_x, current_time)
            gestures_y[dragged_card].add_touch(target_touch_y, current_time)

            if pr.is_mouse_button_released(pr.MOUSE_BUTTON_LEFT):
                c_idx = dragged_card
                dragged_card = -1

                rx, ry = REST_POSITIONS[c_idx]
                # Hand off gesture velocity to Twell additive spring engine!
                props_x[c_idx].release_gesture_spring(gestures_x[c_idx], rx, spring_config, current_time)
                props_y[c_idx].release_gesture_spring(gestures_y[c_idx], ry, spring_config, current_time)

                # Return scale to 1.0
                props_scale[c_idx].animate_to_target(1.0, SpringConfig(mass=0.3, stiffness=300, damping=12), current_time)

        # --- PHYSICS STEP ---
        ctx.tick(current_time)

        # Calculate current presentation positions and frame velocities
        pos_x = [props_x[i].presentation_value for i in range(NUM_CARDS)]
        pos_y = [props_y[i].presentation_value for i in range(NUM_CARDS)]
        scale_val = [props_scale[i].presentation_value for i in range(NUM_CARDS)]
        rot_val = [props_rot[i].presentation_value for i in range(NUM_CARDS)]

        if dt > 0.0001:
            for i in range(NUM_CARDS):
                curr_vel_x[i] = (pos_x[i] - prev_pos_x[i]) / dt
                curr_vel_y[i] = (pos_y[i] - prev_pos_y[i]) / dt
                prev_pos_x[i] = pos_x[i]
                prev_pos_y[i] = pos_y[i]

        # --- PAIRWISE COLLISION DETECTION & MOMENTUM TRANSFER ---
        e = 0.82  # Restitution coefficient for spring impacts

        for i in range(NUM_CARDS):
            for j in range(i + 1, NUM_CARDS):
                # Update collision cooldown
                if cooldown_matrix[i][j] > 0.0:
                    cooldown_matrix[i][j] -= dt
                    continue

                dx = pos_x[j] - pos_x[i]
                dy = pos_y[j] - pos_y[i]
                w_avg = (CARD_WIDTH * scale_val[i] + CARD_WIDTH * scale_val[j]) / 2.0
                h_avg = (CARD_HEIGHT * scale_val[i] + CARD_HEIGHT * scale_val[j]) / 2.0

                # Check bounding overlap
                if abs(dx) < w_avg and abs(dy) < h_avg:
                    # Relative velocity vector
                    rel_vx = curr_vel_x[i] - curr_vel_x[j]
                    rel_vy = curr_vel_y[i] - curr_vel_y[j]

                    # Collision normal (from i to j)
                    dist = math.hypot(dx, dy)
                    nx = dx / dist if dist > 0.001 else 1.0
                    ny = dy / dist if dist > 0.001 else 0.0

                    # Relative speed along normal
                    v_normal = rel_vx * nx + rel_vy * ny

                    # Only collide if moving towards each other
                    if v_normal > 15.0:
                        impact_count += 1
                        max_impact_vel = max(max_impact_vel, v_normal)
                        last_impact_time = current_time
                        cooldown_matrix[i][j] = 0.06  # 60ms cooldown

                        # Impulse magnitude (assuming equal mass)
                        impulse = v_normal * (1.0 + e) / 2.0

                        # Calculate new velocities post-impact
                        new_vx_i = curr_vel_x[i] - impulse * nx
                        new_vy_i = curr_vel_y[i] - impulse * ny
                        new_vx_j = curr_vel_x[j] + impulse * nx
                        new_vy_j = curr_vel_y[j] + impulse * ny

                        rx_i, ry_i = REST_POSITIONS[i]
                        rx_j, ry_j = REST_POSITIONS[j]

                        # Inject impulse velocities into Twell springs targeting rest positions!
                        sp_i_x = SpringConfig(preset["mass"], preset["stiffness"], preset["damping"], initial_velocity=new_vx_i)
                        sp_i_y = SpringConfig(preset["mass"], preset["stiffness"], preset["damping"], initial_velocity=new_vy_i)
                        sp_j_x = SpringConfig(preset["mass"], preset["stiffness"], preset["damping"], initial_velocity=new_vx_j)
                        sp_j_y = SpringConfig(preset["mass"], preset["stiffness"], preset["damping"], initial_velocity=new_vy_j)

                        props_x[i].animate_to_target(rx_i, sp_i_x, current_time)
                        props_y[i].animate_to_target(ry_i, sp_i_y, current_time)
                        props_x[j].animate_to_target(rx_j, sp_j_x, current_time)
                        props_y[j].animate_to_target(ry_j, sp_j_y, current_time)

                        # Trigger squish animation on scale property
                        squish_intensity = min(0.3, v_normal * 0.0003)
                        props_scale[i].animate_to_target(1.0, SpringConfig(mass=0.25, stiffness=450, damping=12, initial_velocity=-v_normal * 0.0012), current_time)
                        props_scale[j].animate_to_target(1.0, SpringConfig(mass=0.25, stiffness=450, damping=12, initial_velocity=v_normal * 0.0012), current_time)

                        # Trigger wobble animation on rotation property
                        tilt_impulse = nx * v_normal * 0.035
                        props_rot[i].animate_to_target(0.0, SpringConfig(mass=0.3, stiffness=350, damping=10, initial_velocity=-tilt_impulse), current_time)
                        props_rot[j].animate_to_target(0.0, SpringConfig(mass=0.3, stiffness=350, damping=10, initial_velocity=tilt_impulse), current_time)

                        # Spawn impact spark particles at collision center
                        col_x = (pos_x[i] + pos_x[j]) / 2.0
                        col_y = (pos_y[i] + pos_y[j]) / 2.0
                        spark_color = CARD_COLORS[i]["main"]
                        for _ in range(random.randint(10, 16)):
                            particles.append(Particle(col_x, col_y, spark_color))

        # Update particles
        particles = [p for p in particles if p.update(dt)]

        # --- RENDERING ---
        pr.begin_drawing()
        pr.clear_background(bg_color)

        # 1. Background Grid & Header Accent
        for grid_x in range(0, WINDOW_WIDTH, 40):
            pr.draw_line(grid_x, 0, grid_x, WINDOW_HEIGHT, pr.Color(28, 36, 50, 120))
        for grid_y in range(0, WINDOW_HEIGHT, 40):
            pr.draw_line(0, grid_y, WINDOW_WIDTH, grid_y, pr.Color(28, 36, 50, 120))

        # Top Anchor Beam Bar
        pr.draw_line_ex(pr.Vector2(START_X - 60, ANCHOR_Y), pr.Vector2(START_X + (NUM_CARDS - 1) * SPACING_X + 60, ANCHOR_Y), 6, pr.Color(45, 58, 80, 255))

        # 2. Draw Coiled Springs & Top Anchor Pins
        for i in range(NUM_CARDS):
            ax, ay = ANCHOR_POSITIONS[i]
            px = pos_x[i]
            py = pos_y[i] - (CARD_HEIGHT * scale_val[i]) / 2.0

            # Dynamic spring color based on stretch/tension
            stretch = math.hypot(pos_x[i] - REST_POSITIONS[i][0], pos_y[i] - REST_POSITIONS[i][1])
            tension_ratio = min(1.0, stretch / 200.0)
            spring_clr = pr.Color(
                int(140 + tension_ratio * 115),
                int(160 - tension_ratio * 60),
                int(185 - tension_ratio * 85),
                255
            )

            draw_coiled_spring(ax, ay, px, py, coils=11, width=11.0, color=spring_clr, thickness=2.5)

            # Anchor Pin
            pr.draw_circle(int(ax), int(ay), 7, pin_color)
            pr.draw_circle(int(ax), int(ay), 3, pr.Color(255, 240, 200, 255))

        # 3. Draw Impact Particles
        for p in particles:
            p.draw()

        # 4. Draw Cards
        for i in range(NUM_CARDS):
            px = pos_x[i]
            py = pos_y[i]
            s = scale_val[i]
            rot = rot_val[i]
            w = CARD_WIDTH * s
            h = CARD_HEIGHT * s

            col_theme = CARD_COLORS[i]
            is_active = (i == dragged_card)

            # Shadow
            shadow_offset = 14 if is_active else 6
            shadow_rec = pr.Rectangle(px, py + shadow_offset, w, h)
            pr.draw_rectangle_pro(shadow_rec, pr.Vector2(w / 2.0, h / 2.0), rot, pr.Color(10, 14, 22, 100))

            # Main Card Body
            card_rec = pr.Rectangle(px, py, w, h)
            body_color = col_theme["main"] if not is_active else col_theme["accent"]
            pr.draw_rectangle_pro(card_rec, pr.Vector2(w / 2.0, h / 2.0), rot, body_color)

            # Inner Gradient / Accent Stripe
            inner_w = w * 0.82
            inner_h = h * 0.82
            inner_rec = pr.Rectangle(px, py, inner_w, inner_h)
            pr.draw_rectangle_pro(inner_rec, pr.Vector2(inner_w / 2.0, inner_h / 2.0), rot, col_theme["dark"])

            # Card Number Label
            num_str = f"#{i + 1}"
            label_size = int(28 * s)
            text_w = pr.measure_text(num_str, label_size)
            pr.draw_text(num_str, int(px - text_w / 2.0), int(py - label_size / 2.0 - 10 * s), label_size, text_white)

            # Card Subtext / Velocity Status
            v_mag = math.hypot(curr_vel_x[i], curr_vel_y[i])
            sub_str = f"{v_mag:.0f} px/s"
            sub_size = int(12 * s)
            sub_w = pr.measure_text(sub_str, sub_size)
            pr.draw_text(sub_str, int(px - sub_w / 2.0), int(py + 15 * s), sub_size, col_theme["accent"])

        # 5. UI Header & Controls Panel
        pr.draw_rectangle(0, 0, WINDOW_WIDTH, 70, panel_color)
        pr.draw_line(0, 70, WINDOW_WIDTH, 70, border_color)

        title = "TWELL PHYSICS ENGINE: SPRING IMPACT & CHAIN REACTION"
        pr.draw_text(title, 24, 16, 18, text_white)

        subtitle = "Click & Drag any card to stretch spring | Releases launch into adjacent cards for momentum transfer"
        pr.draw_text(subtitle, 24, 42, 13, text_muted)

        # Control Panel Box at Bottom
        panel_y = WINDOW_HEIGHT - 90
        pr.draw_rectangle(0, panel_y, WINDOW_WIDTH, 90, panel_color)
        pr.draw_line(0, panel_y, WINDOW_WIDTH, panel_y, border_color)

        # Presets Buttons Info
        pr.draw_text("SPRING PRESETS:", 24, panel_y + 16, 13, text_muted)
        for pid in (1, 2, 3):
            pinfo = PRESETS[pid]
            is_cur = (pid == active_preset_id)
            btn_color = text_accent if is_cur else text_white
            prefix = "[ACTIVE] " if is_cur else ""
            lbl = f"[{pid}] {prefix}{pinfo['name']}"
            pr.draw_text(lbl, 24 + (pid - 1) * 160, panel_y + 38, 14, btn_color)

        pr.draw_text(f"Active Preset: {preset['desc']}", 24, panel_y + 62, 12, text_muted)

        # Actions & Telemetry (Right side of bottom panel)
        pr.draw_text("ACTION SHORTCUTS:", 530, panel_y + 16, 13, text_muted)
        pr.draw_text("[SPACE] Launch Left Spring   [R] Reset Positions", 530, panel_y + 38, 14, text_white)

        telemetry_str = f"Impacts: {impact_count} | Peak Velocity: {max_impact_vel:.0f} px/s"
        pr.draw_text(telemetry_str, 530, panel_y + 62, 13, pin_color)

        pr.end_drawing()

    # Cleanup Twell Objects
    for i in range(NUM_CARDS):
        props_x[i].destroy()
        props_y[i].destroy()
        props_scale[i].destroy()
        props_rot[i].destroy()
        gestures_x[i].destroy()
        gestures_y[i].destroy()

    pr.close_window()


if __name__ == "__main__":
    main()
