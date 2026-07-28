#ifndef TWELL_EXAMPLES_COMMON_H
#define TWELL_EXAMPLES_COMMON_H

#include <stdio.h>
#include "raylib.h"

// --- IOS 18 DESIGN TOKENS ---
#define COLOR_BG               (Color){ 242, 242, 247, 255 } // iOS Light System Gray (#F2F2F7)
#define COLOR_CARD_BG          (Color){ 255, 255, 255, 255 } // Pure White Grouped Card
#define COLOR_BORDER           (Color){ 230, 230, 235, 255 } // Thin separator border
#define COLOR_TEXT_MAIN        (Color){ 28, 28, 30, 255 }    // Primary Text (#1C1C1E)
#define COLOR_TEXT_SUB         (Color){ 142, 142, 147, 255 }  // Secondary Label (#8E8E93)
#define COLOR_IOS_BLUE         (Color){ 0, 122, 255, 255 }   // System Blue
#define COLOR_IOS_INDIGO       (Color){ 88, 86, 214, 255 }   // System Indigo
#define COLOR_IOS_HANDLE       (Color){ 199, 199, 204, 255 } // System Gray 3 Handle

static Font g_app_font = { 0 };

static Font LoadAppFont(void) {
    Font f = { 0 };
    const char* app_dir = GetApplicationDirectory();
    char path[512];
    snprintf(path, sizeof(path), "%sfont.ttf", app_dir);
    if (FileExists(path)) {
        f = LoadFontEx(path, 36, NULL, 0);
    } else if (FileExists("font.ttf")) {
        f = LoadFontEx("font.ttf", 36, NULL, 0);
    }
    if (f.texture.id > 0) {
        SetTextureFilter(f.texture, TEXTURE_FILTER_BILINEAR);
    }
    return f;
}

static void UnloadAppFont(void) {
    if (g_app_font.texture.id > 0) {
        UnloadFont(g_app_font);
        g_app_font = (Font){ 0 };
    }
}

static void DrawCustomText(const char* text, float x, float y, float fontSize, Color color) {
    if (g_app_font.texture.id > 0) {
        Vector2 pos = { x, y };
        DrawTextEx(g_app_font, text, pos, fontSize, 1.0f, color);
    } else {
        DrawText(text, (int)x, (int)y, (int)fontSize, color);
    }
}

#endif // TWELL_EXAMPLES_COMMON_H
