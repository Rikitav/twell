import unittest
import math
import sys
import os

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import twell
from twell import (
    Context, SpringConfig, Vector2, Vector3, UnitType, MappingCurve,
    Quaternion, Transform3D
)

class TestTwellPython(unittest.TestCase):
    def setUp(self):
        self.ctx = Context(max_properties=64, max_gestures=16)

    def test_spring_animation_and_rest(self):
        prop = self.ctx.create_property(0.0)
        self.assertEqual(prop.model_value, 0.0)
        self.assertEqual(prop.presentation_value, 0.0)

        spring = SpringConfig(mass=1.0, stiffness=100.0, damping=15.0, initial_velocity=0.0)
        prop.animate_to_target(100.0, spring, absolute_time=0.0)
        self.assertEqual(prop.model_value, 100.0)

        rested = []
        for i in range(1, 300):
            t = i * 0.01
            res = self.ctx.tick(t)
            rested.extend(res)
            if prop.id in rested:
                break

        self.assertIn(prop.id, rested)
        self.assertAlmostEqual(prop.presentation_value, 100.0, delta=0.5)

    def test_vector_properties_2d_3d(self):
        v2_init = Vector2(10.0, 20.0)
        p2d = self.ctx.create_property_2d(v2_init)
        self.assertEqual(p2d.presentation_value, Vector2(10.0, 20.0))

        v3_init = Vector3(100.0, 200.0, 300.0)
        p3d = self.ctx.create_property_3d(v3_init)
        self.assertEqual(p3d.presentation_value, Vector3(100.0, 200.0, 300.0))

        spring = SpringConfig(mass=1.0, stiffness=100.0, damping=15.0)
        p2d.animate_to_target(Vector2(50.0, 60.0), spring, absolute_time=0.0)

        for step in range(1, 200):
            self.ctx.tick(step * 0.01)

        val = p2d.presentation_value
        self.assertAlmostEqual(val.x, 50.0, delta=0.5)
        self.assertAlmostEqual(val.y, 60.0, delta=0.5)

    def test_driven_properties(self):
        driven = self.ctx.create_property(0.0)
        driver = self.ctx.create_property(0.0)

        driven.add_driver(driver, 0.0, 100.0, 0.0, 50.0, curve_type=MappingCurve.LINEAR, clamp_to_range=True)
        driver.set_value_immediate(50.0)

        self.ctx.tick(0.0)
        self.assertAlmostEqual(driven.presentation_value, 25.0, delta=1e-3)

    def test_quaternion_and_transform(self):
        q1 = Quaternion.make_axis_angle(0.0, 1.0, 0.0, 0.0)
        q2 = Quaternion.make_axis_angle(0.0, 1.0, 0.0, math.pi)
        q_mid = q1.slerp(q2, 0.5)
        
        m_mid = q_mid.to_transform3d()
        self.assertAlmostEqual(m_mid.m11, 0.0, delta=1e-2)

    def test_decay_no_visual_jump(self):
        prop = self.ctx.create_property(100.0)
        prop.animate_decay(initial_velocity=500.0, deceleration_rate=10.0, absolute_time=0.0)
        
        self.ctx.tick(0.0001)
        self.assertAlmostEqual(prop.presentation_value, 100.0, delta=5.0)

        for i in range(1, 200):
            self.ctx.tick(i * 0.01)

        self.assertAlmostEqual(prop.presentation_value, 150.0, delta=1.0)


if __name__ == "__main__":
    unittest.main()
