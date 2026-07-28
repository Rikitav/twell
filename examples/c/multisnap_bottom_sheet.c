#include <stdio.h>
#include <stdlib.h>
#include <math.h>

#define TWELL_IMPL
#include "twell.h"
#include "raylib.h"
#include "common.h"

#define SNAP_EXPANDED 80.0
#define SNAP_MEDIUM   320.0
#define SNAP_COLLAPSED 550.0

int main(void) {
    const int screenWidth = 500;
    const int screenHeight = 700;

    SetConfigFlags(FLAG_WINDOW_HIGHDPI | FLAG_MSAA_4X_HINT);
    SetTraceLogLevel(LOG_WARNING);
    InitWindow(screenWidth, screenHeight, "Twell Demo 02: iOS 18 Bottom Sheet & Drivers");
    SetTargetFPS(120);

    // Load High-DPI Font safely using executable path
    g_app_font = LoadAppFont();

    // Initialize Twell memory arena
    size_t req_mem = twell_get_memory_requirement(64, 16);
    void* arena = malloc(req_mem);
    twell_context* ctx = twell_context_create(arena, req_mem, 64, 16);

    // Create Property for Sheet Y position initialized at COLLAPSED
    twell_property_id prop_sheet_y = twell_property_create(ctx, SNAP_COLLAPSED);

    // Create Driven Property for Backdrop Opacity (0.0 to 0.65)
    twell_property_id prop_backdrop = twell_property_create(ctx, 0.0);

    // Drive backdrop opacity based on prop_sheet_y
    twell_property_add_driver(
        ctx,
        prop_backdrop,   // driven
        prop_sheet_y,    // driver
        SNAP_COLLAPSED,  // driver min
        SNAP_EXPANDED,   // driver max
        0.0,             // driven min
        0.65,            // driven max
        TWELL_MAP_LINEAR,
        true             // clamp
    );

    twell_gesture_id gesture = twell_gesture_create(ctx);

    // iOS Bottom Sheet Spring Tuning
    twell_spring_config spring = {
        .mass = 1.0,
        .stiffness = 195.0,
        .damping = 22.0,
        .initial_velocity = 0.0
    };

    bool is_dragging = false;
    double drag_offset_y = 0.0;
    double current_target_y = SNAP_COLLAPSED;

    while (!WindowShouldClose()) {
        double time = GetTime();
        Vector2 mouse = GetMousePosition();
        double sheet_y = twell_property_get_presentation_value(ctx, prop_sheet_y);

        Rectangle sheet_header_rec = { 0, (float)sheet_y, (float)screenWidth, 60.0f };
        Rectangle card_buttons = { 30, 95, (float)(screenWidth - 60), 65 };
        Rectangle b1 = { 45, 110, 126, 35 };
        Rectangle b2 = { 186, 110, 126, 35 };
        Rectangle b3 = { 327, 110, 126, 35 };

        if (IsMouseButtonPressed(MOUSE_BUTTON_LEFT)) {
            // Check snap buttons first to prevent drag collision when sheet is expanded
            bool button_clicked = false;
            if (CheckCollisionPointRec(mouse, b1)) {
                button_clicked = true;
                current_target_y = SNAP_EXPANDED;
                twell_property_animate_to_target(ctx, prop_sheet_y, SNAP_EXPANDED, spring, time);
            } else if (CheckCollisionPointRec(mouse, b2)) {
                button_clicked = true;
                current_target_y = SNAP_MEDIUM;
                twell_property_animate_to_target(ctx, prop_sheet_y, SNAP_MEDIUM, spring, time);
            } else if (CheckCollisionPointRec(mouse, b3)) {
                button_clicked = true;
                current_target_y = SNAP_COLLAPSED;
                twell_property_animate_to_target(ctx, prop_sheet_y, SNAP_COLLAPSED, spring, time);
            }

            if (!button_clicked && (CheckCollisionPointRec(mouse, sheet_header_rec) || mouse.y >= sheet_y)) {
                is_dragging = true;
                drag_offset_y = mouse.y - sheet_y;
                twell_property_track_gesture(ctx, prop_sheet_y, gesture, SNAP_EXPANDED, SNAP_COLLAPSED);
            }
        }

        if (is_dragging) {
            if (IsMouseButtonDown(MOUSE_BUTTON_LEFT)) {
                double touch_y = mouse.y - drag_offset_y;
                twell_gesture_add_touch(ctx, gesture, touch_y, time);
            }

            if (IsMouseButtonReleased(MOUSE_BUTTON_LEFT)) {
                is_dragging = false;
                double vel_y = twell_gesture_get_velocity(ctx, gesture);

                if (vel_y > 450.0) {
                    if (sheet_y < SNAP_MEDIUM) current_target_y = SNAP_MEDIUM;
                    else current_target_y = SNAP_COLLAPSED;
                } else if (vel_y < -450.0) {
                    if (sheet_y > SNAP_MEDIUM) current_target_y = SNAP_MEDIUM;
                    else current_target_y = SNAP_EXPANDED;
                } else {
                    double dist_exp = fabs(sheet_y - SNAP_EXPANDED);
                    double dist_med = fabs(sheet_y - SNAP_MEDIUM);
                    double dist_col = fabs(sheet_y - SNAP_COLLAPSED);

                    if (dist_exp <= dist_med && dist_exp <= dist_col) {
                        current_target_y = SNAP_EXPANDED;
                    } else if (dist_med <= dist_exp && dist_med <= dist_col) {
                        current_target_y = SNAP_MEDIUM;
                    } else {
                        current_target_y = SNAP_COLLAPSED;
                    }
                }

                twell_property_release_gesture_spring(ctx, prop_sheet_y, gesture, current_target_y, spring, time);
            }
        }

        // Advance Twell state machine
        twell_context_tick(ctx, time, NULL, 0);

        // Fetch presentation values for render frame
        sheet_y = twell_property_get_presentation_value(ctx, prop_sheet_y);
        double backdrop_opacity = twell_property_get_presentation_value(ctx, prop_backdrop);

        // Drawing
        BeginDrawing();
        ClearBackground(COLOR_BG);

        // Background App Content
        DrawCustomText("iOS 18 Bottom Sheet", 30, 24, 22, COLOR_TEXT_MAIN);
        DrawCustomText("Twell Property Driver maps Y position -> Backdrop Opacity", 30, 52, 13, COLOR_TEXT_SUB);

        // Quick Snap Buttons Card
        DrawRectangleRounded(card_buttons, 0.2f, 8, COLOR_CARD_BG);

        DrawRectangleRounded(b1, 0.25f, 6, (Color){ 235, 235, 240, 255 });
        DrawCustomText("Expanded", 68, 118, 13, COLOR_IOS_BLUE);

        DrawRectangleRounded(b2, 0.25f, 6, (Color){ 235, 235, 240, 255 });
        DrawCustomText("Medium", 222, 118, 13, COLOR_IOS_BLUE);

        DrawRectangleRounded(b3, 0.25f, 6, (Color){ 235, 235, 240, 255 });
        DrawCustomText("Collapsed", 355, 118, 13, COLOR_IOS_BLUE);

        // Backdrop overlay
        if (backdrop_opacity > 0.001) {
            DrawRectangle(0, 0, screenWidth, screenHeight, (Color){ 0, 0, 0, (unsigned char)(255 * backdrop_opacity) });
        }

        // Modal Sheet Drawer (Pure White iOS Card)
        float sheet_h = (float)(screenHeight - sheet_y + 100);
        DrawRectangleRounded((Rectangle){ 0, (float)sheet_y, (float)screenWidth, sheet_h }, 0.06f, 16, COLOR_CARD_BG);
        DrawRectangle(0, (float)sheet_y + 30, screenWidth, (int)sheet_h, COLOR_CARD_BG);

        // Pill Grab Handle
        DrawRectangleRounded((Rectangle){ (screenWidth - 38) / 2.0f, (float)sheet_y + 10.0f, 38.0f, 5.0f }, 1.0f, 8, COLOR_IOS_HANDLE);

        // Sheet Header Text
        DrawCustomText("Modal Sheet Actions", 30, (float)sheet_y + 32, 19, COLOR_TEXT_MAIN);
        DrawCustomText("Drag handle or flick to switch snap states", 30, (float)sheet_y + 56, 13, COLOR_TEXT_SUB);

        // Grouped List Items inside sheet
        const char* list_items[] = { "Multi-Snap Spring Kinetics", "Zero-Allocation Arena Model", "Additive Superposition Stacks" };
        for (int i = 0; i < 3; i++) {
            float item_y = (float)sheet_y + 90 + i * 55;
            if (item_y < screenHeight - 10) {
                DrawCircle(46, (int)item_y + 16, 12, COLOR_IOS_BLUE);
                DrawCustomText(list_items[i], 70, item_y + 8, 15, COLOR_TEXT_MAIN);
                if (i < 2) DrawLine(70, (int)item_y + 42, screenWidth - 30, (int)item_y + 42, COLOR_BORDER);
            }
        }

        // Stats Debug Line
        char dbg[128];
        snprintf(dbg, sizeof(dbg), "Sheet Y: %.1f px | Backdrop: %.2f", sheet_y, backdrop_opacity);
        DrawCustomText(dbg, 30, screenHeight - 25, 12, COLOR_TEXT_SUB);

        EndDrawing();
    }

    twell_property_destroy(ctx, prop_sheet_y);
    twell_property_destroy(ctx, prop_backdrop);
    twell_gesture_destroy(ctx, gesture);
    UnloadAppFont();
    CloseWindow();
    free(arena);

    return 0;
}
