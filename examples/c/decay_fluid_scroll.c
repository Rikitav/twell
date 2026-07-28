#include <stdio.h>
#include <stdlib.h>
#include <math.h>

#define TWELL_IMPL
#include "twell.h"
#include "raylib.h"
#include "common.h"

#define ITEM_COUNT 15
#define ITEM_HEIGHT 72
#define ITEM_GAP 12
#define LIST_TOP 120
#define DECELERATION_RATE 3.5 // Exponential friction rate for twell_math (v = v0 * e^(-d*t))

typedef enum {
    SCROLL_STATE_IDLE,
    SCROLL_STATE_DRAGGING,
    SCROLL_STATE_DECAYING,
    SCROLL_STATE_BOUNCING
} ScrollState;

typedef struct {
    const char* title;
    const char* category;
    Color tag_color;
} FeedItem;

static FeedItem feed[ITEM_COUNT] = {
    {"Quantum Computing Breakthrough", "Technology", (Color){ 0, 122, 255, 255 }},    // System Blue
    {"Neural Superposition Networks", "AI Research", (Color){ 88, 86, 214, 255 }},   // System Indigo
    {"Fluid Dynamics in Interface Design", "Design", (Color){ 48, 176, 199, 255 }},  // System Teal
    {"Zero-Allocation C Physics Engines", "Engineering", (Color){ 255, 149, 0, 255 }},// System Orange
    {"CoreAnimation Superposition Stack", "iOS Architecture", (Color){ 255, 45, 85, 255 }},// System Pink
    {"Asymptotic Rubber-Banding Math", "Mathematics", (Color){ 0, 122, 255, 255 }},
    {"Viscous Fluid Decay Models", "Physics", (Color){ 175, 82, 222, 255 }},         // System Purple
    {"Low-Pass Filter Gesture Kinetics", "Input Systems", (Color){ 88, 86, 214, 255 }},
    {"Embedded Real-Time Graphical UI", "Embedded", (Color){ 52, 199, 89, 255 }},   // System Green
    {"Gimbal-Lock Free SLERP Rotation", "Spatial 3D", (Color){ 255, 45, 85, 255 }},
    {"Additive Impulse Stacks in C", "Low-Level", (Color){ 142, 142, 147, 255 }},
    {"Hardware Absolute Time Clocks", "Performance", (Color){ 255, 149, 0, 255 }},
    {"Raylib High-FPS Render Loop", "Graphics", (Color){ 0, 122, 255, 255 }},
    {"Memory Arena Allocation Pattern", "Systems", (Color){ 175, 82, 222, 255 }},
    {"Fluid Scroll Inertial Handoff", "Interaction", (Color){ 48, 176, 199, 255 }}
};

int main(void) {
    const int screenWidth = 600;
    const int screenHeight = 750;

    SetConfigFlags(FLAG_WINDOW_HIGHDPI | FLAG_MSAA_4X_HINT);
    SetTraceLogLevel(LOG_WARNING);
    InitWindow(screenWidth, screenHeight, "Twell Demo 04: iOS 18 Viscous Fluid Scroll");
    SetTargetFPS(120);

    // Load High-DPI Font safely using executable path
    g_app_font = LoadAppFont();

    // Initialize Twell
    size_t req_mem = twell_get_memory_requirement(64, 16);
    void* arena = malloc(req_mem);
    twell_context* ctx = twell_context_create(arena, req_mem, 64, 16);

    // Vertical scroll position property (0.0 = top)
    twell_property_id prop_scroll_y = twell_property_create(ctx, 0.0);
    twell_gesture_id gesture = twell_gesture_create(ctx);

    // Soft spring for boundary snap back
    twell_spring_config bounce_spring = {
        .mass = 1.0,
        .stiffness = 160.0,
        .damping = 17.0,
        .initial_velocity = 0.0
    };

    double min_scroll = 0.0;
    double max_scroll = (ITEM_COUNT * (ITEM_HEIGHT + ITEM_GAP)) - (screenHeight - LIST_TOP - 40);
    if (max_scroll < 0.0) max_scroll = 0.0;

    ScrollState state = SCROLL_STATE_IDLE;
    double drag_start_mouse_y = 0.0;
    double drag_start_scroll_y = 0.0;

    while (!WindowShouldClose()) {
        double time = GetTime();
        Vector2 mouse = GetMousePosition();

        // --- INPUT HANDLING ---
        if (IsMouseButtonPressed(MOUSE_BUTTON_LEFT)) {
            double current_before_drag = twell_property_get_presentation_value(ctx, prop_scroll_y);
            state = SCROLL_STATE_DRAGGING;
            drag_start_mouse_y = mouse.y;
            drag_start_scroll_y = current_before_drag;
            twell_property_track_gesture(ctx, prop_scroll_y, gesture, min_scroll, max_scroll);
        }

        if (state == SCROLL_STATE_DRAGGING) {
            if (IsMouseButtonDown(MOUSE_BUTTON_LEFT)) {
                double delta_y = drag_start_mouse_y - mouse.y;
                double touch_scroll = drag_start_scroll_y + delta_y;
                twell_gesture_add_touch(ctx, gesture, touch_scroll, time);
            }

            if (IsMouseButtonReleased(MOUSE_BUTTON_LEFT)) {
                double release_scroll = twell_property_get_presentation_value(ctx, prop_scroll_y);
                if (release_scroll < min_scroll) {
                    state = SCROLL_STATE_BOUNCING;
                    twell_property_release_gesture_spring(ctx, prop_scroll_y, gesture, min_scroll, bounce_spring, time);
                } else if (release_scroll > max_scroll) {
                    state = SCROLL_STATE_BOUNCING;
                    twell_property_release_gesture_spring(ctx, prop_scroll_y, gesture, max_scroll, bounce_spring, time);
                } else {
                    state = SCROLL_STATE_DECAYING;
                    twell_property_release_gesture_decay(ctx, prop_scroll_y, gesture, DECELERATION_RATE, time);
                }
            }
        }

        // --- ADVANCE PHYSICS TICK ---
        twell_property_id resting[16];
        uint32_t resting_count = twell_context_tick(ctx, time, resting, 16);

        for (uint32_t i = 0; i < resting_count; i++) {
            if (resting[i] == prop_scroll_y && (state == SCROLL_STATE_BOUNCING || state == SCROLL_STATE_DECAYING)) {
                state = SCROLL_STATE_IDLE;
            }
        }

        double curr_scroll = twell_property_get_presentation_value(ctx, prop_scroll_y);

        // --- DECAY BOUNDARY OVERFLOW CHECK ---
        if (state == SCROLL_STATE_DECAYING) {
            if (curr_scroll < min_scroll) {
                state = SCROLL_STATE_BOUNCING;
                twell_property_set_value_immediate(ctx, prop_scroll_y, curr_scroll);
                twell_property_animate_to_target(ctx, prop_scroll_y, min_scroll, bounce_spring, time);
            } else if (curr_scroll > max_scroll) {
                state = SCROLL_STATE_BOUNCING;
                twell_property_set_value_immediate(ctx, prop_scroll_y, curr_scroll);
                twell_property_animate_to_target(ctx, prop_scroll_y, max_scroll, bounce_spring, time);
            }
        }

        // Elastic Jelly Overshoot Computation
        double overshoot = 0.0;
        bool is_top_overshoot = false;

        if (curr_scroll < min_scroll) {
            overshoot = min_scroll - curr_scroll;
            is_top_overshoot = true;
        } else if (curr_scroll > max_scroll) {
            overshoot = curr_scroll - max_scroll;
            is_top_overshoot = false;
        }

        float jelly_factor = (float)(tanh(overshoot / 180.0));

        // --- RENDERING ---
        BeginDrawing();
        ClearBackground(COLOR_BG);

        // Clip list content area below header
        BeginScissorMode(0, LIST_TOP, screenWidth, screenHeight - LIST_TOP);

        for (int i = 0; i < ITEM_COUNT; i++) {
            double base_item_y = LIST_TOP + 10 + i * (ITEM_HEIGHT + ITEM_GAP) - curr_scroll;

            float card_height = ITEM_HEIGHT;
            float extra_stretch = 0.0f;

            if (overshoot > 0.1) {
                if (is_top_overshoot) {
                    float factor = 1.0f - (i * 0.15f);
                    if (factor < 0.0f) factor = 0.0f;
                    extra_stretch = jelly_factor * 20.0f * factor;
                    base_item_y += extra_stretch * 0.5f;
                } else {
                    float factor = 1.0f - ((ITEM_COUNT - 1 - i) * 0.15f);
                    if (factor < 0.0f) factor = 0.0f;
                    extra_stretch = jelly_factor * 20.0f * factor;
                    base_item_y -= extra_stretch * 0.5f;
                }
            }

            card_height += extra_stretch;
            float item_y = (float)base_item_y;

            if (item_y + card_height < LIST_TOP || item_y > screenHeight) continue;

            // iOS 18 Grouped White Card
            Rectangle card_rec = { 24, item_y, (float)(screenWidth - 48), card_height };
            DrawRectangleRounded(card_rec, 0.15f, 8, COLOR_CARD_BG);
            DrawRectangleRoundedLines(card_rec, 0.15f, 8, COLOR_BORDER);

            // Category Tag Pillar
            DrawRectangleRounded((Rectangle){ 36, item_y + 14, 5, card_height - 28 }, 0.5f, 4, feed[i].tag_color);

            // Text
            DrawCustomText(feed[i].title, 54, item_y + card_height * 0.20f, 16, COLOR_TEXT_MAIN);
            DrawCustomText(feed[i].category, 54, item_y + card_height * 0.56f, 13, COLOR_TEXT_SUB);

            // Item number
            char num[8];
            snprintf(num, sizeof(num), "#%02d", i + 1);
            DrawCustomText(num, screenWidth - 65, item_y + card_height * 0.35f, 14, COLOR_TEXT_SUB);
        }

        EndScissorMode();

        // Top Header Overlay (iOS 18 Glass Gray)
        DrawRectangle(0, 0, screenWidth, LIST_TOP, COLOR_BG);
        DrawLine(0, LIST_TOP, screenWidth, LIST_TOP, COLOR_BORDER);

        DrawCustomText("iOS 18 Viscous Feed Scroll", 24, 24, 22, COLOR_TEXT_MAIN);
        DrawCustomText("Flick feed to experience silky smooth viscous fluid decay.", 24, 52, 13, COLOR_TEXT_SUB);

        // Status indicator pill
        const char* mode_str = (state == SCROLL_STATE_DRAGGING) ? "GESTURE TRACKING" :
                               (state == SCROLL_STATE_BOUNCING) ? "SOFT ELASTIC BOUNCE" :
                               (state == SCROLL_STATE_DECAYING) ? "FLUID DECAY" : "IDLE";
        Color mode_color = (state == SCROLL_STATE_DRAGGING) ? COLOR_IOS_BLUE :
                           (state == SCROLL_STATE_BOUNCING) ? (Color){ 255, 45, 85, 255 } :
                           (state == SCROLL_STATE_DECAYING) ? (Color){ 52, 199, 89, 255 } : COLOR_TEXT_SUB;

        DrawRectangleRounded((Rectangle){ 24, 86, 170, 20 }, 0.5f, 4, mode_color);
        DrawCustomText(mode_str, 32, 89, 10, WHITE);

        // Scrollbar Indicator
        float track_h = (float)(screenHeight - LIST_TOP - 20);
        float thumb_h = track_h * ((float)(screenHeight - LIST_TOP) / (float)(ITEM_COUNT * (ITEM_HEIGHT + ITEM_GAP)));
        if (thumb_h < 30.0f) thumb_h = 30.0f;

        float scroll_pct = (float)(curr_scroll / max_scroll);
        if (scroll_pct < 0.0f) scroll_pct = 0.0f;
        if (scroll_pct > 1.0f) scroll_pct = 1.0f;

        float thumb_y = LIST_TOP + 10 + scroll_pct * (track_h - thumb_h);
        DrawRectangleRounded((Rectangle){ (float)(screenWidth - 10), thumb_y, 4, thumb_h }, 1.0f, 4, COLOR_IOS_HANDLE);

        // Realtime stats bar
        double vel = twell_gesture_get_velocity(ctx, gesture);
        char dbg[128];
        snprintf(dbg, sizeof(dbg), "Scroll: %.1f px | Velocity: %.0f px/s | Overshoot: %.1f px",
            curr_scroll, vel, overshoot);
        DrawCustomText(dbg, 24, screenHeight - 25, 12, COLOR_TEXT_SUB);

        EndDrawing();
    }

    twell_property_destroy(ctx, prop_scroll_y);
    twell_gesture_destroy(ctx, gesture);
    UnloadAppFont();
    CloseWindow();
    free(arena);

    return 0;
}
