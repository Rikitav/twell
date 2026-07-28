#define TWELL_IMPL
#include "../twell.h"
#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <assert.h>

#define MAX_PROPS 64
#define MAX_GESTURES 16
static uint8_t arena[1024 * 128];

static void test_problem_1_ring_buffer_baking(void) {
    printf("Ring buffer overflow baking...\n");

    size_t req = twell_get_memory_requirement(MAX_PROPS, MAX_GESTURES);
    assert(req <= sizeof(arena));
    twell_context* ctx = twell_context_create(arena, sizeof(arena), MAX_PROPS, MAX_GESTURES);
    assert(ctx != NULL);

    twell_property_id prop = twell_property_create(ctx, 0.0);
    twell_spring_config spring = { .mass = 1.0, .stiffness = 100.0, .damping = 10.0, .initial_velocity = 0.0 };

    double t = 0.0;
    /* Trigger 15 rapid target changes (buffer size is 8) */
    for (int i = 1; i <= 15; i++) {
        t += 0.005; /* 5ms between ticks */
        twell_property_animate_to_target(ctx, prop, (double)(i * 10), spring, t);
        twell_context_tick(ctx, t, NULL, 0);
    }

    double pres_before_overflow = twell_property_get_presentation_value(ctx, prop);

    /* Advance time slightly and verify presentation value changes smoothly without any sudden pop */
    double prev_pres = pres_before_overflow;
    for (int step = 0; step < 100; step++) {
        t += 0.01;
        twell_context_tick(ctx, t, NULL, 0);
        double pres = twell_property_get_presentation_value(ctx, prop);
        double delta = fabs(pres - prev_pres);
        /* Check that per-frame delta is smooth and bounded (no infinite or huge step pop) */
        assert(delta < 30.0);
        prev_pres = pres;
    }

    /* Eventually spring settles to final target 150.0 */
    for (int step = 0; step < 500; step++) {
        t += 0.01;
        twell_context_tick(ctx, t, NULL, 0);
    }
    double final_pres = twell_property_get_presentation_value(ctx, prop);
    assert(fabs(final_pres - 150.0) < 0.2);

    twell_property_destroy(ctx, prop);
    printf("Passed Test 1: Ring Buffer Overflow Baking successfully!\n\n");
}

static void test_problem_2_per_property_epsilons(void) {
    printf("Running Test 2: Per-Property Rest Thresholds (Problem 2)...\n");

    twell_context* ctx = twell_context_create(arena, sizeof(arena), MAX_PROPS, MAX_GESTURES);

    /* Pixel property: initial 0, target 100 */
    twell_property_id prop_px = twell_property_create_with_unit(ctx, 0.0, TWELL_UNIT_PIXELS);
    /* Normalized property: initial 0, target 1.0 */
    twell_property_id prop_norm = twell_property_create_with_unit(ctx, 0.0, TWELL_UNIT_NORMALIZED);

    twell_spring_config spring = { .mass = 1.0, .stiffness = 100.0, .damping = 20.0, .initial_velocity = 0.0 };

    double t = 0.0;
    twell_property_animate_to_target(ctx, prop_px, 100.0, spring, t);
    twell_property_animate_to_target(ctx, prop_norm, 1.0, spring, t);

    twell_property_id resting[16];
    bool px_rested = false;
    bool norm_rested = false;

    for (int step = 0; step < 500; step++) {
        t += 0.01;
        uint32_t count = twell_context_tick(ctx, t, resting, 16);
        for (uint32_t i = 0; i < count; i++) {
            if (resting[i] == prop_px) px_rested = true;
            if (resting[i] == prop_norm) norm_rested = true;
        }
        if (px_rested && norm_rested) break;
    }

    assert(px_rested);
    assert(norm_rested);

    /* Verify model and presentation values match target */
    assert(fabs(twell_property_get_presentation_value(ctx, prop_px) - 100.0) < 0.1);
    assert(fabs(twell_property_get_presentation_value(ctx, prop_norm) - 1.0) < 0.0002);

    twell_property_destroy(ctx, prop_px);
    twell_property_destroy(ctx, prop_norm);
    printf("Passed Test 2: Per-Property Rest Thresholds successfully!\n\n");
}

static void test_problem_3_variable_dt_velocity(void) {
    printf("Running Test 3: Variable dt Velocity Estimator (Problem 3)...\n");

    twell_context* ctx = twell_context_create(arena, sizeof(arena), MAX_PROPS, MAX_GESTURES);
    twell_gesture_id g = twell_gesture_create(ctx);

    /* Simulate uneven/jittery touch events along constant velocity 1000 px/sec */
    double times[] = { 0.000, 0.007, 0.019, 0.024, 0.038, 0.045, 0.052 };
    int num_samples = sizeof(times) / sizeof(times[0]);

    for (int i = 0; i < num_samples; i++) {
        double pos = times[i] * 1000.0; /* 1000 px/s */
        twell_gesture_add_touch(ctx, g, pos, times[i]);
    }

    double estimated_v = twell_gesture_get_velocity(ctx, g);
    printf("Estimated velocity from jittery samples: %f px/sec (expected ~1000.0)\n", estimated_v);
    assert(fabs(estimated_v - 1000.0) < 30.0);

    twell_gesture_destroy(ctx, g);
    printf("Passed Test 3: Variable dt Velocity Estimator successfully!\n\n");
}

static void test_problem_4_soa_and_vector_api(void) {
    printf("Running Test 4: SoA & 2D/3D Vector API (Problem 4)...\n");

    twell_context* ctx = twell_context_create(arena, sizeof(arena), MAX_PROPS, MAX_GESTURES);

    twell_vector2 init2 = { 10.0, 20.0 };
    twell_property_id prop2d = twell_property_create_2d(ctx, init2);
    assert(prop2d != TWELL_INVALID_ID);

    twell_vector3 init3 = { 100.0, 200.0, 300.0 };
    twell_property_id prop3d = twell_property_create_3d(ctx, init3);
    assert(prop3d != TWELL_INVALID_ID);

    /* Check contiguous allocation */
    assert(prop3d == prop2d + 2);

    /* Test 2D getter */
    twell_vector2 p2 = twell_property_get_presentation_value_2d(ctx, prop2d);
    assert(fabs(p2.x - 10.0) < 1e-5 && fabs(p2.y - 20.0) < 1e-5);

    /* Test 3D getter */
    twell_vector3 p3 = twell_property_get_presentation_value_3d(ctx, prop3d);
    assert(fabs(p3.x - 100.0) < 1e-5 && fabs(p3.y - 200.0) < 1e-5 && fabs(p3.z - 300.0) < 1e-5);

    /* Test 2D animation */
    twell_spring_config spring = { .mass = 1.0, .stiffness = 100.0, .damping = 15.0, .initial_velocity = 0.0 };
    twell_vector2 target2 = { 50.0, 60.0 };
    twell_property_animate_to_target_2d(ctx, prop2d, target2, spring, 0.0);

    for (int step = 1; step <= 200; step++) {
        twell_context_tick(ctx, step * 0.01, NULL, 0);
    }

    twell_vector2 final2 = twell_property_get_presentation_value_2d(ctx, prop2d);
    assert(fabs(final2.x - 50.0) < 0.1 && fabs(final2.y - 60.0) < 0.1);

    twell_property_destroy(ctx, prop2d);
    twell_property_destroy(ctx, prop3d);
    printf("Passed Test 4: SoA & 2D/3D Vector API successfully!\n\n");
}

static void test_driven_properties_and_geometry(void) {
    printf("Running Test 5: Driven Properties & Spatial Geometry...\n");

    twell_context* ctx = twell_context_create(arena, sizeof(arena), MAX_PROPS, MAX_GESTURES);

    twell_property_id driver = twell_property_create(ctx, 0.0);
    twell_property_id driven = twell_property_create(ctx, 1.0);

    /* Map driven property (scale 1.0 to 0.5) as driver (sheet Y 0 to 500) moves */
    twell_property_add_driver(ctx, driven, driver, 0.0, 500.0, 1.0, 0.5, TWELL_MAP_LINEAR, true);

    twell_property_set_value_immediate(ctx, driver, 250.0);
    twell_context_tick(ctx, 0.0, NULL, 0);

    double driven_val = twell_property_get_presentation_value(ctx, driven);
    /* At driver = 250 (50%), driven scale should be 0.75 */
    assert(fabs(driven_val - 0.75) < 1e-4);

    /* Test Geometry: Quaternion SLERP */
    twell_quaternion q1 = twell_quaternion_make_axis_angle(0.0, 1.0, 0.0, 0.0);
    twell_quaternion q2 = twell_quaternion_make_axis_angle(0.0, 1.0, 0.0, 3.1415926535);
    twell_quaternion q_mid = twell_quaternion_slerp(q1, q2, 0.5);
    twell_transform3d m_mid = twell_transform3d_from_quaternion(q_mid);

    /* At mid angle (90 deg around Y), m11 ~ 0, m13 ~ -1 */
    assert(fabs(m_mid.m11) < 1e-2);

    twell_property_destroy(ctx, driver);
    twell_property_destroy(ctx, driven);
    printf("Passed Test 5: Driven Properties & Spatial Geometry successfully!\n\n");
}

static void test_fragmented_2d_3d_allocation(void) {
    printf("Running Test 6: Fragmented 2D/3D Property Allocation...\n");

    twell_context* ctx = twell_context_create(arena, sizeof(arena), MAX_PROPS, MAX_GESTURES);
    assert(ctx != NULL);

    /* Allocate slot 0 and slot 2, leave slot 1 free to create memory fragmentation */
    twell_property_id p0 = twell_property_create(ctx, 0.0);
    twell_property_id p1 = twell_property_create(ctx, 0.0);
    twell_property_id p2 = twell_property_create(ctx, 0.0);
    assert(p0 == 0 && p1 == 1 && p2 == 2);

    /* Free slot 1 only */
    twell_property_destroy(ctx, p1);

    /* Now allocate a 2D property. Slots 0, 2 are taken, slot 1 is free.
     * Contiguous block search will skip slot 1 and pick slots 3 and 4!
     */
    twell_vector2 v2 = { 42.0, 84.0 };
    twell_property_id prop2d = twell_property_create_2d(ctx, v2);
    assert(prop2d != TWELL_INVALID_ID);
    assert(prop2d == 3); /* Must allocate contiguous block at 3 and 4 */

    twell_vector2 fetched = twell_property_get_presentation_value_2d(ctx, prop2d);
    assert(fabs(fetched.x - 42.0) < 1e-5);
    assert(fabs(fetched.y - 84.0) < 1e-5);

    twell_property_destroy(ctx, p0);
    twell_property_destroy(ctx, p2);
    twell_property_destroy(ctx, prop2d);
    printf("Passed Test 6: Fragmented 2D/3D Property Allocation successfully!\n\n");
}

static void test_decay_no_visual_jump(void) {
    printf("Running Test 7: Decay Animation Continuity (No Visual Jump)...\n");

    twell_context* ctx = twell_context_create(arena, sizeof(arena), MAX_PROPS, MAX_GESTURES);

    twell_property_id prop = twell_property_create(ctx, 100.0);
    double initial_val = twell_property_get_presentation_value(ctx, prop);
    assert(fabs(initial_val - 100.0) < 1e-5);

    /* Start decay with v0 = 500.0, rate = 10.0 (total travel = 50.0). Destination = 150.0 */
    twell_property_animate_decay(ctx, prop, 500.0, 10.0, 0.0);

    /* Evaluate at t = 0.0001 (start of scroll) */
    twell_context_tick(ctx, 0.0001, NULL, 0);
    double pres_at_start = twell_property_get_presentation_value(ctx, prop);

    /* Must start near 100.0 (NOT jump to 50.0 or 0.0!) */
    assert(fabs(pres_at_start - 100.0) < 5.0);

    /* Tick to completion and verify it coasts smoothly to 150.0 */
    for (int i = 1; i <= 200; i++) {
        twell_context_tick(ctx, i * 0.01, NULL, 0);
    }
    double final_pres = twell_property_get_presentation_value(ctx, prop);
    assert(fabs(final_pres - 150.0) < 0.5);

    twell_property_destroy(ctx, prop);
    printf("Passed Test 7: Decay Animation Continuity successfully!\n\n");
}

static void test_driven_property_zero_latency(void) {
    printf("Running Test 8: Driven Property Zero Latency (Two-Pass Tick)...\n");

    twell_context* ctx = twell_context_create(arena, sizeof(arena), MAX_PROPS, MAX_GESTURES);

    /* Allocate driven property FIRST so driven_id (0) < driver_id (1) */
    twell_property_id driven = twell_property_create(ctx, 0.0);
    twell_property_id driver = twell_property_create(ctx, 0.0);
    assert(driven < driver);

    /* Map driven = driver 1:1 */
    twell_property_add_driver(ctx, driven, driver, 0.0, 100.0, 0.0, 100.0, TWELL_MAP_LINEAR, true);

    twell_spring_config spring = { .mass = 1.0, .stiffness = 100.0, .damping = 10.0, .initial_velocity = 0.0 };
    twell_property_animate_to_target(ctx, driver, 100.0, spring, 0.0);

    /* Tick at t = 0.05 */
    twell_context_tick(ctx, 0.05, NULL, 0);

    double driver_pres = twell_property_get_presentation_value(ctx, driver);
    double driven_pres = twell_property_get_presentation_value(ctx, driven);

    /* Driven presentation value MUST match driver presentation value exactly in the SAME tick */
    assert(fabs(driver_pres - driven_pres) < 1e-5);

    twell_property_destroy(ctx, driver);
    twell_property_destroy(ctx, driven);
    printf("Passed Test 8: Driven Property Zero Latency successfully!\n\n");
}

static void test_component_destruction_safety(void) {
    printf("Running Test 9: Component Destruction Safety...\n");

    twell_context* ctx = twell_context_create(arena, sizeof(arena), MAX_PROPS, MAX_GESTURES);

    twell_vector2 init = { 10.0, 20.0 };
    twell_property_id vec2d = twell_property_create_2d(ctx, init);
    assert(vec2d != TWELL_INVALID_ID);

    /* Destroy using component handle (vec2d + 1) instead of primary handle (vec2d) */
    twell_property_destroy(ctx, vec2d + 1);

    /* Both primary and component handles must be cleanly freed */
    twell_property_id new_prop = twell_property_create(ctx, 99.0);
    assert(new_prop == vec2d); /* Slot vec2d is reusable! */

    twell_property_destroy(ctx, new_prop);
    printf("Passed Test 9: Component Destruction Safety successfully!\n\n");
}

int main(void) {
    printf("=========================================\n");
    printf("      Running Twell Test Suite           \n");
    printf("=========================================\n\n");

    test_problem_1_ring_buffer_baking();
    test_problem_2_per_property_epsilons();
    test_problem_3_variable_dt_velocity();
    test_problem_4_soa_and_vector_api();
    test_driven_properties_and_geometry();
    test_fragmented_2d_3d_allocation();
    test_decay_no_visual_jump();
    test_driven_property_zero_latency();
    test_component_destruction_safety();

    printf("=========================================\n");
    printf("  ALL TESTS PASSED SUCCESSFULLY (9/9)!   \n");
    printf("=========================================\n");
    return 0;
}
