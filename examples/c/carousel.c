#include <stdio.h>
#include <stdlib.h>
#include <math.h>

#define TWELL_IMPL
#include "twell.h"
#include "raylib.h"
#include "common.h"

#define CARD_WIDTH 230
#define CARD_HEIGHT 340
#define CARD_GAP 28
#define NUM_CARDS 6

typedef struct {
    const char* title;
    const char* subtitle;
    Color color;
} CardData;

static CardData cards[NUM_CARDS] = {
    {"Nebula", "Deep Space Optics", (Color){ 88, 86, 214, 255 }},  // System Indigo
    {"Cyberpunk", "Neon Horizon 2099", (Color){ 255, 45, 85, 255 }}, // System Pink
    {"Aurora", "Arctic Emerald Glow", (Color){ 48, 176, 199, 255 }},// System Teal
    {"Solar", "Coronal Flare Dynamics", (Color){ 255, 149, 0, 255 }},// System Orange
    {"Midnight", "Oceanic Abyss Depth", (Color){ 0, 122, 255, 255 }},// System Blue
    {"Prism", "Chromatic Dispersion", (Color){ 175, 82, 222, 255 }}  // System Purple
};

int main(void) {
    const int screenWidth = 900;
    const int screenHeight = 600;

    SetConfigFlags(FLAG_WINDOW_HIGHDPI | FLAG_MSAA_4X_HINT);
    SetTraceLogLevel(LOG_WARNING);
    InitWindow(screenWidth, screenHeight, "Twell Demo 01: iOS 18 Dynamic Carousel");
    SetTargetFPS(120);

    // Load High-DPI Font safely using executable path
    g_app_font = LoadAppFont();

    // Arena allocation for Twell context
    size_t req_mem = twell_get_memory_requirement(128, 32);
    void* arena = malloc(req_mem);
    twell_context* ctx = twell_context_create(arena, req_mem, 128, 32);

    // Property for track scroll X position
    double center_offset = (screenWidth - CARD_WIDTH) / 2.0;
    twell_property_id prop_scroll = twell_property_create(ctx, 0.0);
    twell_gesture_id gesture_scroll = twell_gesture_create(ctx);

    // Responsive spring config
    twell_spring_config spring = {
        .mass = 1.0,
        .stiffness = 220.0,
        .damping = 20.0,
        .initial_velocity = 0.0
    };

    double min_scroll = 0.0;
    double max_scroll = (NUM_CARDS - 1) * (CARD_WIDTH + CARD_GAP);

    bool is_dragging = false;
    double grab_x = 0.0;
    double start_scroll = 0.0;

    while (!WindowShouldClose()) {
        double time = GetTime();
        Vector2 mouse = GetMousePosition();

        double current_scroll = twell_property_get_presentation_value(ctx, prop_scroll);

        if (IsMouseButtonPressed(MOUSE_BUTTON_LEFT)) {
            is_dragging = true;
            grab_x = mouse.x;
            start_scroll = current_scroll;
            twell_property_track_gesture(ctx, prop_scroll, gesture_scroll, min_scroll, max_scroll);
        }

        if (is_dragging) {
            if (IsMouseButtonDown(MOUSE_BUTTON_LEFT)) {
                double delta_x = grab_x - mouse.x;
                double touch_pos = start_scroll + delta_x;
                twell_gesture_add_touch(ctx, gesture_scroll, touch_pos, time);
            }

            if (IsMouseButtonReleased(MOUSE_BUTTON_LEFT)) {
                is_dragging = false;
                double vel = twell_gesture_get_velocity(ctx, gesture_scroll);

                double projected_scroll = current_scroll + vel * 0.25;
                int target_index = (int)round(projected_scroll / (CARD_WIDTH + CARD_GAP));
                if (target_index < 0) target_index = 0;
                if (target_index >= NUM_CARDS) target_index = NUM_CARDS - 1;

                double target_scroll = target_index * (CARD_WIDTH + CARD_GAP);
                twell_property_release_gesture_spring(ctx, prop_scroll, gesture_scroll, target_scroll, spring, time);
            }
        }

        // Advance Twell state machine
        twell_context_tick(ctx, time, NULL, 0);

        // Fetch presentation value for render frame
        double scroll_val = twell_property_get_presentation_value(ctx, prop_scroll);

        // Rendering phase
        BeginDrawing();
        ClearBackground(COLOR_BG);

        // Header text (iOS 18 typography)
        DrawCustomText("iOS 18 Card Carousel & Momentum", 40, 24, 22, COLOR_TEXT_MAIN);
        DrawCustomText("1:1 Gesture tracking with asymptotic boundary rubber-banding", 40, 52, 14, COLOR_TEXT_SUB);

        // Draw cards
        for (int i = 0; i < NUM_CARDS; i++) {
            double card_base_x = center_offset + i * (CARD_WIDTH + CARD_GAP) - scroll_val;
            double card_center_x = card_base_x + CARD_WIDTH / 2.0;
            double screen_center_x = screenWidth / 2.0;

            double dist = fabs(card_center_x - screen_center_x);
            double normalized_dist = dist / 350.0;
            if (normalized_dist > 1.0) normalized_dist = 1.0;

            float scale = 1.0f - (float)(0.22 * normalized_dist);
            float alpha = 1.0f - (float)(0.45 * normalized_dist);

            float w = CARD_WIDTH * scale;
            float h = CARD_HEIGHT * scale;
            float x = (float)(card_center_x - w / 2.0);
            float y = (float)((screenHeight - h) / 2.0 + 15);

            // Card Drop Shadow
            DrawRectangleRounded((Rectangle){ x + 2, y + 8, w, h }, 0.12f, 10, (Color){ 0, 0, 0, (unsigned char)(25 * alpha) });

            // Card Body
            Color col = cards[i].color;
            col.a = (unsigned char)(255 * alpha);
            DrawRectangleRounded((Rectangle){ x, y, w, h }, 0.12f, 10, col);

            // Glass Accent Header Bar
            DrawRectangleRounded((Rectangle){ x, y, w, 65 * scale }, 0.12f, 10, (Color){ 255, 255, 255, (unsigned char)(40 * alpha) });

            // Card Text
            float font_size_title = 22.0f * scale;
            float font_size_sub = 13.0f * scale;
            DrawCustomText(cards[i].title, x + 20.0f * scale, y + 20.0f * scale, font_size_title, WHITE);
            DrawCustomText(cards[i].subtitle, x + 20.0f * scale, y + 80.0f * scale, font_size_sub, (Color){ 255, 255, 255, (unsigned char)(220 * alpha) });

            // Card Index badge
            char badge[16];
            snprintf(badge, sizeof(badge), "#0%d", i + 1);
            DrawCustomText(badge, x + 20.0f * scale, y + h - 35.0f * scale, font_size_sub, (Color){ 255, 255, 255, (unsigned char)(200 * alpha) });
        }

        // Realtime stats bar
        double vel = twell_gesture_get_velocity(ctx, gesture_scroll);
        char stats[128];
        snprintf(stats, sizeof(stats), "Scroll: %.1f px | Velocity: %.0f px/s | State: %s",
            scroll_val, vel, is_dragging ? "DRAGGING" : "SPRING");
        DrawCustomText(stats, 40, screenHeight - 35, 13, COLOR_TEXT_SUB);

        EndDrawing();
    }

    twell_property_destroy(ctx, prop_scroll);
    twell_gesture_destroy(ctx, gesture_scroll);
    UnloadAppFont();
    CloseWindow();
    free(arena);

    return 0;
}
