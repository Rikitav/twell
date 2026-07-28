#include <stdio.h>
#include <stdlib.h>
#include <math.h>

#define TWELL_IMPL
#include "twell.h"
#include "raylib.h"
#include "raymath.h"
#include "rlgl.h"
#include "common.h"

int main(void) {
    const int screenWidth = 800;
    const int screenHeight = 600;

    SetConfigFlags(FLAG_WINDOW_HIGHDPI | FLAG_MSAA_4X_HINT);
    SetTraceLogLevel(LOG_WARNING);
    InitWindow(screenWidth, screenHeight, "Twell Demo 03: iOS 18 Spatial 3D Physics");
    SetTargetFPS(120);

    // Load High-DPI Font safely using executable path
    g_app_font = LoadAppFont();

    // Initialize Twell
    size_t req_mem = twell_get_memory_requirement(64, 16);
    void* arena = malloc(req_mem);
    twell_context* ctx = twell_context_create(arena, req_mem, 64, 16);

    // 3D Property for Pitch (X), Yaw (Y), Roll (Z) Euler Angles in Degrees
    twell_vector3 initial_rot = { 15.0, 45.0, 0.0 };
    twell_property_id prop_rot_3d = twell_property_create_3d_with_unit(ctx, initial_rot, TWELL_UNIT_DEGREES);
    twell_gesture_id gesture_rot_3d = twell_gesture_create(ctx);

    // Bouncy 3D Spring
    twell_spring_config spring = {
        .mass = 1.0,
        .stiffness = 180.0,
        .damping = 16.0,
        .initial_velocity = 0.0
    };

    Camera3D camera = { 0 };
    camera.position = (Vector3){ 0.0f, 2.5f, 5.0f };
    camera.target = (Vector3){ 0.0f, 0.0f, 0.0f };
    camera.up = (Vector3){ 0.0f, 1.0f, 0.0f };
    camera.fovy = 45.0f;
    camera.projection = CAMERA_PERSPECTIVE;

    bool is_dragging = false;
    Vector2 drag_start_mouse = { 0 };
    twell_vector3 drag_start_rot = { 0 };

    while (!WindowShouldClose()) {
        double time = GetTime();
        Vector2 mouse = GetMousePosition();

        twell_vector3 rot = twell_property_get_presentation_value_3d(ctx, prop_rot_3d);

        if (IsMouseButtonPressed(MOUSE_BUTTON_LEFT)) {
            is_dragging = true;
            drag_start_mouse = mouse;
            drag_start_rot = rot;
            twell_vector3 bmin = { -720.0, -720.0, -720.0 };
            twell_vector3 bmax = {  720.0,  720.0,  720.0 };
            twell_property_track_gesture_3d(ctx, prop_rot_3d, gesture_rot_3d, bmin, bmax);
        }

        if (is_dragging) {
            if (IsMouseButtonDown(MOUSE_BUTTON_LEFT)) {
                double delta_x = (mouse.x - drag_start_mouse.x) * 0.5;
                double delta_y = (mouse.y - drag_start_mouse.y) * 0.5;

                twell_vector3 touch_rot = {
                    drag_start_rot.x + delta_y,
                    drag_start_rot.y + delta_x,
                    0.0
                };
                twell_gesture_add_touch_3d(ctx, gesture_rot_3d, touch_rot, time);
            }

            if (IsMouseButtonReleased(MOUSE_BUTTON_LEFT)) {
                is_dragging = false;

                double target_pitch = round(rot.x / 90.0) * 90.0;
                double target_yaw   = round(rot.y / 90.0) * 90.0;
                twell_vector3 target_rot = { target_pitch, target_yaw, 0.0 };

                twell_property_release_gesture_spring_3d(ctx, prop_rot_3d, gesture_rot_3d, target_rot, spring, time);
            }
        }

        // Twell State Machine Tick
        twell_context_tick(ctx, time, NULL, 0);

        // Fetch presentation rotation for render frame
        rot = twell_property_get_presentation_value_3d(ctx, prop_rot_3d);

        // Convert Euler degrees to Quaternion via Twell math kernel
        twell_quaternion q = twell_quaternion_make_euler(
            rot.x * DEG2RAD,
            rot.y * DEG2RAD,
            rot.z * DEG2RAD
        );
        twell_transform3d t3d = twell_transform3d_from_quaternion(q);

        BeginDrawing();
        ClearBackground(COLOR_BG);

        // 3D Rendering Mode
        BeginMode3D(camera);

        DrawGrid(10, 1.0f);

        // Draw 3D Object with Quaternion Transformation
        rlPushMatrix();
        Matrix mat = {
            (float)t3d.m11, (float)t3d.m12, (float)t3d.m13, (float)t3d.m14,
            (float)t3d.m21, (float)t3d.m22, (float)t3d.m23, (float)t3d.m24,
            (float)t3d.m31, (float)t3d.m32, (float)t3d.m33, (float)t3d.m34,
            (float)t3d.m41, (float)t3d.m42, (float)t3d.m43, (float)t3d.m44
        };
        rlMultMatrixf((const float*)&mat);

        // Glassmorphic iOS 18 Vision Cube Wireframe & Transparent faces
        DrawCube((Vector3){0, 0, 0}, 1.6f, 1.6f, 1.6f, (Color){0, 122, 255, 90});
        DrawCubeWires((Vector3){0, 0, 0}, 1.6f, 1.6f, 1.6f, COLOR_IOS_BLUE);

        // Internal 3D Axes
        DrawLine3D((Vector3){-1.0f, 0, 0}, (Vector3){1.0f, 0, 0}, (Color){ 255, 45, 85, 255 });
        DrawLine3D((Vector3){0, -1.0f, 0}, (Vector3){0, 1.0f, 0}, (Color){ 52, 199, 89, 255 });
        DrawLine3D((Vector3){0, 0, -1.0f}, (Vector3){0, 0, 1.0f}, COLOR_IOS_BLUE);

        rlPopMatrix();

        EndMode3D();

        // 2D HUD
        DrawCustomText("iOS 18 Spatial 3D Physics", 30, 24, 22, COLOR_TEXT_MAIN);
        DrawCustomText("Drag in 3D space to rotate. Release to trigger 3D spring face snapping!", 30, 52, 14, COLOR_TEXT_SUB);

        char rot_str[128];
        snprintf(rot_str, sizeof(rot_str), "Euler: Pitch=%.1f°, Yaw=%.1f°, Roll=%.1f° | Quaternion: (%.2f, %.2f, %.2f, %.2f)",
            rot.x, rot.y, rot.z, q.x, q.y, q.z, q.w);
        DrawCustomText(rot_str, 30, screenHeight - 35, 13, COLOR_TEXT_SUB);

        EndDrawing();
    }

    twell_property_destroy(ctx, prop_rot_3d);
    twell_gesture_destroy(ctx, gesture_rot_3d);
    UnloadAppFont();
    CloseWindow();
    free(arena);

    return 0;
}
