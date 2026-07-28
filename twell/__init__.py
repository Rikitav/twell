"""
Twell (Python bindings)
A tiny, embeddable physics engine for remarkably fluid graphical user interfaces.
"""

import ctypes
import ctypes.util
import glob
import os
import platform
from dataclasses import dataclass
from enum import IntEnum
from typing import List, Optional, Tuple, Union

__version__ = "1.1.0"


def _load_library() -> ctypes.CDLL:
    env_path = os.environ.get("TWELL_LIBRARY_PATH")
    if env_path:
        if os.path.exists(env_path):
            try:
                return ctypes.CDLL(env_path)
            except Exception as e:
                raise ImportError(f"Failed to load Twell library specified by TWELL_LIBRARY_PATH='{env_path}': {e}")
        else:
            raise FileNotFoundError(f"TWELL_LIBRARY_PATH specifies file '{env_path}' which does not exist.")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(base_dir)
    system = platform.system()

    if system == "Windows":
        patterns = ["twell.dll", "libtwell.dll", "_twell*.pyd", "_twell*.dll", "libtwell*.dll"]
    elif system == "Darwin":
        patterns = ["libtwell.dylib", "twell.dylib", "_twell*.so", "_twell*.dylib", "libtwell*.dylib"]
    else:
        patterns = ["libtwell.so", "twell.so", "_twell*.so", "libtwell*.so"]

    # search package directory first
    for pattern in patterns:
        matches = glob.glob(os.path.join(base_dir, pattern))
        for match in sorted(matches):
            try:
                return ctypes.CDLL(match)
            except Exception:
                continue

    # search parent directory (repository root i guess)
    for pattern in patterns:
        matches = glob.glob(os.path.join(parent_dir, pattern))
        for match in sorted(matches):
            try:
                return ctypes.CDLL(match)
            except Exception:
                continue

    # search system library paths via ctypes.util.find_library
    found_lib = ctypes.util.find_library("twell") or ctypes.util.find_library("libtwell")
    if found_lib:
        try:
            return ctypes.CDLL(found_lib)
        except Exception:
            pass

    # direct ctypes search on default system search paths
    default_names = ["twell", "libtwell"]
    if system == "Windows":
        default_names.extend(["twell.dll", "libtwell.dll"])
    elif system == "Darwin":
        default_names.extend(["libtwell.dylib", "twell.dylib"])
    else:
        default_names.extend(["libtwell.so", "twell.so"])

    for name in default_names:
        try:
            return ctypes.CDLL(name)
        except Exception:
            pass

    raise FileNotFoundError(
        "Could not find the Twell native shared library.\n"
        "Please ensure the library binary (twell.dll / libtwell.so / libtwell.dylib) is included in the package directory,\n"
        "installed system-wide, or point to it using the TWELL_LIBRARY_PATH environment variable."
    )


_lib = _load_library()


class _CSpringConfig(ctypes.Structure):
    _fields_ = [
        ("mass", ctypes.c_double),
        ("stiffness", ctypes.c_double),
        ("damping", ctypes.c_double),
        ("initial_velocity", ctypes.c_double),
    ]


class _CVector2(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_double),
        ("y", ctypes.c_double),
    ]


class _CVector3(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_double),
        ("y", ctypes.c_double),
        ("z", ctypes.c_double),
    ]


class _CTransform3D(ctypes.Structure):
    _fields_ = [
        ("m11", ctypes.c_double), ("m12", ctypes.c_double), ("m13", ctypes.c_double), ("m14", ctypes.c_double),
        ("m21", ctypes.c_double), ("m22", ctypes.c_double), ("m23", ctypes.c_double), ("m24", ctypes.c_double),
        ("m31", ctypes.c_double), ("m32", ctypes.c_double), ("m33", ctypes.c_double), ("m34", ctypes.c_double),
        ("m41", ctypes.c_double), ("m42", ctypes.c_double), ("m43", ctypes.c_double), ("m44", ctypes.c_double),
    ]


class _CQuaternion(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_double),
        ("y", ctypes.c_double),
        ("z", ctypes.c_double),
        ("w", ctypes.c_double),
    ]


# Function signatures

_lib.twell_get_memory_requirement.argtypes = [ctypes.c_uint32, ctypes.c_uint32]
_lib.twell_get_memory_requirement.restype = ctypes.c_size_t

_lib.twell_context_create.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_uint32, ctypes.c_uint32]
_lib.twell_context_create.restype = ctypes.c_void_p

_lib.twell_context_tick.argtypes = [ctypes.c_void_p, ctypes.c_double, ctypes.POINTER(ctypes.c_uint32), ctypes.c_uint32]
_lib.twell_context_tick.restype = ctypes.c_uint32

_lib.twell_math_spring_evaluate.argtypes = [
    ctypes.c_double, _CSpringConfig, ctypes.c_double,
    ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double)
]
_lib.twell_math_spring_evaluate.restype = None

_lib.twell_math_decay_evaluate.argtypes = [
    ctypes.c_double, ctypes.c_double, ctypes.c_double,
    ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double)
]
_lib.twell_math_decay_evaluate.restype = None

_lib.twell_math_rubber_band.argtypes = [ctypes.c_double, ctypes.c_double, ctypes.c_double]
_lib.twell_math_rubber_band.restype = ctypes.c_double

_lib.twell_math_set_rest_thresholds.argtypes = [ctypes.c_void_p, ctypes.c_double, ctypes.c_double]
_lib.twell_math_set_rest_thresholds.restype = None

_lib.twell_property_create.argtypes = [ctypes.c_void_p, ctypes.c_double]
_lib.twell_property_create.restype = ctypes.c_uint32

_lib.twell_property_create_with_unit.argtypes = [ctypes.c_void_p, ctypes.c_double, ctypes.c_int]
_lib.twell_property_create_with_unit.restype = ctypes.c_uint32

_lib.twell_property_create_2d.argtypes = [ctypes.c_void_p, _CVector2]
_lib.twell_property_create_2d.restype = ctypes.c_uint32

_lib.twell_property_create_2d_with_unit.argtypes = [ctypes.c_void_p, _CVector2, ctypes.c_int]
_lib.twell_property_create_2d_with_unit.restype = ctypes.c_uint32

_lib.twell_property_create_3d.argtypes = [ctypes.c_void_p, _CVector3]
_lib.twell_property_create_3d.restype = ctypes.c_uint32

_lib.twell_property_create_3d_with_unit.argtypes = [ctypes.c_void_p, _CVector3, ctypes.c_int]
_lib.twell_property_create_3d_with_unit.restype = ctypes.c_uint32

_lib.twell_property_destroy.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
_lib.twell_property_destroy.restype = None

_lib.twell_property_get_model_value.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
_lib.twell_property_get_model_value.restype = ctypes.c_double

_lib.twell_property_get_model_value_2d.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
_lib.twell_property_get_model_value_2d.restype = _CVector2

_lib.twell_property_get_model_value_3d.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
_lib.twell_property_get_model_value_3d.restype = _CVector3

_lib.twell_property_get_presentation_value.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
_lib.twell_property_get_presentation_value.restype = ctypes.c_double

_lib.twell_property_get_presentation_value_2d.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
_lib.twell_property_get_presentation_value_2d.restype = _CVector2

_lib.twell_property_get_presentation_value_3d.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
_lib.twell_property_get_presentation_value_3d.restype = _CVector3

_lib.twell_property_set_value_immediate.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_double]
_lib.twell_property_set_value_immediate.restype = None

_lib.twell_property_set_value_immediate_2d.argtypes = [ctypes.c_void_p, ctypes.c_uint32, _CVector2]
_lib.twell_property_set_value_immediate_2d.restype = None

_lib.twell_property_set_value_immediate_3d.argtypes = [ctypes.c_void_p, ctypes.c_uint32, _CVector3]
_lib.twell_property_set_value_immediate_3d.restype = None

_lib.twell_property_animate_to_target.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_double, _CSpringConfig, ctypes.c_double]
_lib.twell_property_animate_to_target.restype = None

_lib.twell_property_animate_to_target_2d.argtypes = [ctypes.c_void_p, ctypes.c_uint32, _CVector2, _CSpringConfig, ctypes.c_double]
_lib.twell_property_animate_to_target_2d.restype = None

_lib.twell_property_animate_to_target_3d.argtypes = [ctypes.c_void_p, ctypes.c_uint32, _CVector3, _CSpringConfig, ctypes.c_double]
_lib.twell_property_animate_to_target_3d.restype = None

_lib.twell_property_animate_decay.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_double, ctypes.c_double, ctypes.c_double]
_lib.twell_property_animate_decay.restype = None

_lib.twell_gesture_create.argtypes = [ctypes.c_void_p]
_lib.twell_gesture_create.restype = ctypes.c_uint32

_lib.twell_gesture_destroy.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
_lib.twell_gesture_destroy.restype = None

_lib.twell_gesture_add_touch.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_double, ctypes.c_double]
_lib.twell_gesture_add_touch.restype = None

_lib.twell_gesture_add_touch_2d.argtypes = [ctypes.c_void_p, ctypes.c_uint32, _CVector2, ctypes.c_double]
_lib.twell_gesture_add_touch_2d.restype = None

_lib.twell_gesture_add_touch_3d.argtypes = [ctypes.c_void_p, ctypes.c_uint32, _CVector3, ctypes.c_double]
_lib.twell_gesture_add_touch_3d.restype = None

_lib.twell_gesture_get_velocity.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
_lib.twell_gesture_get_velocity.restype = ctypes.c_double

_lib.twell_gesture_get_velocity_2d.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
_lib.twell_gesture_get_velocity_2d.restype = _CVector2

_lib.twell_gesture_get_velocity_3d.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
_lib.twell_gesture_get_velocity_3d.restype = _CVector3

_lib.twell_property_track_gesture.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_double, ctypes.c_double]
_lib.twell_property_track_gesture.restype = None

_lib.twell_property_track_gesture_2d.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32, _CVector2, _CVector2]
_lib.twell_property_track_gesture_2d.restype = None

_lib.twell_property_track_gesture_3d.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32, _CVector3, _CVector3]
_lib.twell_property_track_gesture_3d.restype = None

_lib.twell_property_release_gesture_spring.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_double, _CSpringConfig, ctypes.c_double]
_lib.twell_property_release_gesture_spring.restype = None

_lib.twell_property_release_gesture_spring_2d.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32, _CVector2, _CSpringConfig, ctypes.c_double]
_lib.twell_property_release_gesture_spring_2d.restype = None

_lib.twell_property_release_gesture_spring_3d.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32, _CVector3, _CSpringConfig, ctypes.c_double]
_lib.twell_property_release_gesture_spring_3d.restype = None

_lib.twell_property_release_gesture_decay.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_double, ctypes.c_double]
_lib.twell_property_release_gesture_decay.restype = None

_lib.twell_property_add_driver.argtypes = [
    ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32,
    ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double,
    ctypes.c_int, ctypes.c_bool
]
_lib.twell_property_add_driver.restype = None

_lib.twell_property_remove_driver.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32]
_lib.twell_property_remove_driver.restype = None

_lib.twell_transform3d_identity.argtypes = []
_lib.twell_transform3d_identity.restype = _CTransform3D

_lib.twell_transform3d_make_translation.argtypes = [ctypes.c_double, ctypes.c_double, ctypes.c_double]
_lib.twell_transform3d_make_translation.restype = _CTransform3D

_lib.twell_transform3d_make_scale.argtypes = [ctypes.c_double, ctypes.c_double, ctypes.c_double]
_lib.twell_transform3d_make_scale.restype = _CTransform3D

_lib.twell_transform3d_set_perspective.argtypes = [ctypes.POINTER(_CTransform3D), ctypes.c_double]
_lib.twell_transform3d_set_perspective.restype = None

_lib.twell_quaternion_make_axis_angle.argtypes = [ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double]
_lib.twell_quaternion_make_axis_angle.restype = _CQuaternion

_lib.twell_quaternion_make_euler.argtypes = [ctypes.c_double, ctypes.c_double, ctypes.c_double]
_lib.twell_quaternion_make_euler.restype = _CQuaternion

_lib.twell_quaternion_slerp.argtypes = [_CQuaternion, _CQuaternion, ctypes.c_double]
_lib.twell_quaternion_slerp.restype = _CQuaternion

_lib.twell_transform3d_from_quaternion.argtypes = [_CQuaternion]
_lib.twell_transform3d_from_quaternion.restype = _CTransform3D


# High-Level API

class UnitType(IntEnum):
    PIXELS = 0
    NORMALIZED = 1
    DEGREES = 2
    RADIANS = 3
    CUSTOM = 4


class MappingCurve(IntEnum):
    LINEAR = 0
    EASE_IN = 1
    EASE_OUT = 2


class ImpulseType(IntEnum):
    SPRING = 0
    DECAY = 1


@dataclass
class SpringConfig:
    mass: float = 1.0
    stiffness: float = 100.0
    damping: float = 10.0
    initial_velocity: float = 0.0

    def _to_c(self) -> _CSpringConfig:
        return _CSpringConfig(self.mass, self.stiffness, self.damping, self.initial_velocity)


@dataclass
class Vector2:
    x: float = 0.0
    y: float = 0.0

    def _to_c(self) -> _CVector2:
        return _CVector2(self.x, self.y)

    @classmethod
    def _from_c(cls, c_vec: _CVector2) -> "Vector2":
        return cls(c_vec.x, c_vec.y)


@dataclass
class Vector3:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def _to_c(self) -> _CVector3:
        return _CVector3(self.x, self.y, self.z)

    @classmethod
    def _from_c(cls, c_vec: _CVector3) -> "Vector3":
        return cls(c_vec.x, c_vec.y, c_vec.z)


@dataclass
class Quaternion:
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    w: float = 1.0

    def _to_c(self) -> _CQuaternion:
        return _CQuaternion(self.x, self.y, self.z, self.w)

    @classmethod
    def _from_c(cls, c_q: _CQuaternion) -> "Quaternion":
        return cls(c_q.x, c_q.y, c_q.z, c_q.w)

    @classmethod
    def make_axis_angle(cls, x: float, y: float, z: float, angle_rad: float) -> "Quaternion":
        return cls._from_c(_lib.twell_quaternion_make_axis_angle(x, y, z, angle_rad))

    @classmethod
    def make_euler(cls, pitch: float, yaw: float, roll: float) -> "Quaternion":
        return cls._from_c(_lib.twell_quaternion_make_euler(pitch, yaw, roll))

    def slerp(self, other: "Quaternion", t: float) -> "Quaternion":
        return Quaternion._from_c(_lib.twell_quaternion_slerp(self._to_c(), other._to_c(), t))

    def to_transform3d(self) -> "Transform3D":
        return Transform3D._from_c(_lib.twell_transform3d_from_quaternion(self._to_c()))


@dataclass
class Transform3D:
    m11: float = 1.0; m12: float = 0.0; m13: float = 0.0; m14: float = 0.0
    m21: float = 0.0; m22: float = 1.0; m23: float = 0.0; m24: float = 0.0
    m31: float = 0.0; m32: float = 0.0; m33: float = 1.0; m34: float = 0.0
    m41: float = 0.0; m42: float = 0.0; m43: float = 0.0; m44: float = 1.0

    def _to_c(self) -> _CTransform3D:
        return _CTransform3D(
            self.m11, self.m12, self.m13, self.m14,
            self.m21, self.m22, self.m23, self.m24,
            self.m31, self.m32, self.m33, self.m34,
            self.m41, self.m42, self.m43, self.m44
        )

    @classmethod
    def _from_c(cls, c_m: _CTransform3D) -> "Transform3D":
        return cls(
            c_m.m11, c_m.m12, c_m.m13, c_m.m14,
            c_m.m21, c_m.m22, c_m.m23, c_m.m24,
            c_m.m31, c_m.m32, c_m.m33, c_m.m34,
            c_m.m41, c_m.m42, c_m.m43, c_m.m44
        )

    @classmethod
    def identity(cls) -> "Transform3D":
        return cls._from_c(_lib.twell_transform3d_identity())

    @classmethod
    def make_translation(cls, tx: float, ty: float, tz: float) -> "Transform3D":
        return cls._from_c(_lib.twell_transform3d_make_translation(tx, ty, tz))

    @classmethod
    def make_scale(cls, sx: float, sy: float, sz: float) -> "Transform3D":
        return cls._from_c(_lib.twell_transform3d_make_scale(sx, sy, sz))

    def set_perspective(self, depth: float) -> None:
        c_m = self._to_c()
        _lib.twell_transform3d_set_perspective(ctypes.byref(c_m), depth)
        self.m34 = c_m.m34


class Property:
    def __init__(self, context: "Context", prop_id: int, dimensions: int = 1):
        self._ctx = context
        self.id = prop_id
        self.dimensions = dimensions

    def destroy(self) -> None:
        if self._ctx and self.id != 0xFFFFFFFF:
            _lib.twell_property_destroy(self._ctx._handle, self.id)
            self.id = 0xFFFFFFFF

    @property
    def model_value(self) -> Union[float, Vector2, Vector3]:
        if self.dimensions == 2:
            return Vector2._from_c(_lib.twell_property_get_model_value_2d(self._ctx._handle, self.id))
        elif self.dimensions == 3:
            return Vector3._from_c(_lib.twell_property_get_model_value_3d(self._ctx._handle, self.id))
        return _lib.twell_property_get_model_value(self._ctx._handle, self.id)

    @property
    def presentation_value(self) -> Union[float, Vector2, Vector3]:
        if self.dimensions == 2:
            return Vector2._from_c(_lib.twell_property_get_presentation_value_2d(self._ctx._handle, self.id))
        elif self.dimensions == 3:
            return Vector3._from_c(_lib.twell_property_get_presentation_value_3d(self._ctx._handle, self.id))
        return _lib.twell_property_get_presentation_value(self._ctx._handle, self.id)

    def set_rest_thresholds(self, displacement_eps: float, velocity_eps: float) -> None:
        _lib.twell_property_set_rest_thresholds(self._ctx._handle, self.id, displacement_eps, velocity_eps)

    def set_value_immediate(self, value: Union[float, Vector2, Vector3]) -> None:
        if isinstance(value, Vector2):
            _lib.twell_property_set_value_immediate_2d(self._ctx._handle, self.id, value._to_c())
        elif isinstance(value, Vector3):
            _lib.twell_property_set_value_immediate_3d(self._ctx._handle, self.id, value._to_c())
        else:
            _lib.twell_property_set_value_immediate(self._ctx._handle, self.id, float(value))

    def animate_to_target(
        self,
        target_value: Union[float, Vector2, Vector3],
        config: SpringConfig,
        absolute_time: float
    ) -> None:
        c_config = config._to_c()
        if isinstance(target_value, Vector2):
            _lib.twell_property_animate_to_target_2d(self._ctx._handle, self.id, target_value._to_c(), c_config, absolute_time)
        elif isinstance(target_value, Vector3):
            _lib.twell_property_animate_to_target_3d(self._ctx._handle, self.id, target_value._to_c(), c_config, absolute_time)
        else:
            _lib.twell_property_animate_to_target(self._ctx._handle, self.id, float(target_value), c_config, absolute_time)

    def animate_decay(self, initial_velocity: float, deceleration_rate: float, absolute_time: float) -> None:
        _lib.twell_property_animate_decay(self._ctx._handle, self.id, initial_velocity, deceleration_rate, absolute_time)

    def track_gesture(
        self,
        gesture: "Gesture",
        boundary_min: Union[float, Vector2, Vector3] = float("-inf"),
        boundary_max: Union[float, Vector2, Vector3] = float("inf")
    ) -> None:
        if isinstance(boundary_min, Vector2) and isinstance(boundary_max, Vector2):
            _lib.twell_property_track_gesture_2d(self._ctx._handle, self.id, gesture.id, boundary_min._to_c(), boundary_max._to_c())
        elif isinstance(boundary_min, Vector3) and isinstance(boundary_max, Vector3):
            _lib.twell_property_track_gesture_3d(self._ctx._handle, self.id, gesture.id, boundary_min._to_c(), boundary_max._to_c())
        else:
            _lib.twell_property_track_gesture(self._ctx._handle, self.id, gesture.id, float(boundary_min), float(boundary_max))

    def release_gesture_spring(
        self,
        gesture: "Gesture",
        target_value: Union[float, Vector2, Vector3],
        config: SpringConfig,
        absolute_time: float
    ) -> None:
        c_config = config._to_c()
        if isinstance(target_value, Vector2):
            _lib.twell_property_release_gesture_spring_2d(self._ctx._handle, self.id, gesture.id, target_value._to_c(), c_config, absolute_time)
        elif isinstance(target_value, Vector3):
            _lib.twell_property_release_gesture_spring_3d(self._ctx._handle, self.id, gesture.id, target_value._to_c(), c_config, absolute_time)
        else:
            _lib.twell_property_release_gesture_spring(self._ctx._handle, self.id, gesture.id, float(target_value), c_config, absolute_time)

    def release_gesture_decay(self, gesture: "Gesture", deceleration_rate: float, absolute_time: float) -> None:
        _lib.twell_property_release_gesture_decay(self._ctx._handle, self.id, gesture.id, deceleration_rate, absolute_time)

    def add_driver(
        self,
        driver: "Property",
        driver_range_min: float,
        driver_range_max: float,
        driven_range_min: float,
        driven_range_max: float,
        curve_type: MappingCurve = MappingCurve.LINEAR,
        clamp_to_range: bool = True
    ) -> None:
        _lib.twell_property_add_driver(
            self._ctx._handle,
            self.id,
            driver.id,
            driver_range_min,
            driver_range_max,
            driven_range_min,
            driven_range_max,
            int(curve_type),
            clamp_to_range
        )

    def remove_driver(self, driver: "Property") -> None:
        _lib.twell_property_remove_driver(self._ctx._handle, self.id, driver.id)


class Gesture:
    def __init__(self, context: "Context", gesture_id: int):
        self._ctx = context
        self.id = gesture_id

    def destroy(self) -> None:
        if self._ctx and self.id != 0xFFFFFFFF:
            _lib.twell_gesture_destroy(self._ctx._handle, self.id)
            self.id = 0xFFFFFFFF

    def add_touch(self, position: Union[float, Vector2, Vector3], absolute_time: float) -> None:
        if isinstance(position, Vector2):
            _lib.twell_gesture_add_touch_2d(self._ctx._handle, self.id, position._to_c(), absolute_time)
        elif isinstance(position, Vector3):
            _lib.twell_gesture_add_touch_3d(self._ctx._handle, self.id, position._to_c(), absolute_time)
        else:
            _lib.twell_gesture_add_touch(self._ctx._handle, self.id, float(position), absolute_time)

    def get_velocity(self) -> float:
        return _lib.twell_gesture_get_velocity(self._ctx._handle, self.id)

    def get_velocity_2d(self) -> Vector2:
        return Vector2._from_c(_lib.twell_gesture_get_velocity_2d(self._ctx._handle, self.id))

    def get_velocity_3d(self) -> Vector3:
        return Vector3._from_c(_lib.twell_gesture_get_velocity_3d(self._ctx._handle, self.id))


class Context:
    def __init__(self, max_properties: int = 64, max_gestures: int = 16):
        self.max_properties = max_properties
        self.max_gestures = max_gestures

        req_size = _lib.twell_get_memory_requirement(max_properties, max_gestures)
        self._arena = ctypes.create_string_buffer(req_size)
        self._handle = _lib.twell_context_create(
            ctypes.cast(self._arena, ctypes.c_void_p),
            req_size,
            max_properties,
            max_gestures
        )
        if not self._handle:
            raise RuntimeError("Failed to create Twell context.")

    def create_property(self, initial_value: float, unit: UnitType = UnitType.PIXELS) -> Property:
        p_id = _lib.twell_property_create_with_unit(self._handle, float(initial_value), int(unit))
        if p_id == 0xFFFFFFFF:
            raise RuntimeError("Property allocation failed.")
        return Property(self, p_id, dimensions=1)

    def create_property_2d(self, initial_value: Vector2, unit: UnitType = UnitType.PIXELS) -> Property:
        p_id = _lib.twell_property_create_2d_with_unit(self._handle, initial_value._to_c(), int(unit))
        if p_id == 0xFFFFFFFF:
            raise RuntimeError("Property 2D allocation failed.")
        return Property(self, p_id, dimensions=2)

    def create_property_3d(self, initial_value: Vector3, unit: UnitType = UnitType.PIXELS) -> Property:
        p_id = _lib.twell_property_create_3d_with_unit(self._handle, initial_value._to_c(), int(unit))
        if p_id == 0xFFFFFFFF:
            raise RuntimeError("Property 3D allocation failed.")
        return Property(self, p_id, dimensions=3)

    def create_gesture(self) -> Gesture:
        g_id = _lib.twell_gesture_create(self._handle)
        if g_id == 0xFFFFFFFF:
            raise RuntimeError("Gesture allocation failed.")
        return Gesture(self, g_id)

    def tick(self, absolute_time: float, max_resting: int = 16) -> List[int]:
        out_resting = (ctypes.c_uint32 * max_resting)()
        count = _lib.twell_context_tick(self._handle, float(absolute_time), out_resting, max_resting)
        return [out_resting[i] for i in range(count)]

    def set_global_rest_thresholds(self, displacement_eps: float, velocity_eps: float) -> None:
        _lib.twell_math_set_rest_thresholds(self._handle, displacement_eps, velocity_eps)

    @staticmethod
    def math_spring_evaluate(
        t: float, config: SpringConfig, initial_displacement: float
    ) -> Tuple[float, float]:
        out_x = ctypes.c_double()
        out_v = ctypes.c_double()
        _lib.twell_math_spring_evaluate(t, config._to_c(), initial_displacement, ctypes.byref(out_x), ctypes.byref(out_v))
        return out_x.value, out_v.value

    @staticmethod
    def math_decay_evaluate(t: float, initial_velocity: float, deceleration_rate: float) -> Tuple[float, float]:
        out_x = ctypes.c_double()
        out_v = ctypes.c_double()
        _lib.twell_math_decay_evaluate(t, initial_velocity, deceleration_rate, ctypes.byref(out_x), ctypes.byref(out_v))
        return out_x.value, out_v.value

    @staticmethod
    def math_rubber_band(input_displacement: float, max_displacement: float, tension: float = 0.55) -> float:
        return _lib.twell_math_rubber_band(input_displacement, max_displacement, tension)


__all__ = [
    "Context",
    "Property",
    "Gesture",
    "SpringConfig",
    "Vector2",
    "Vector3",
    "Quaternion",
    "Transform3D",
    "UnitType",
    "MappingCurve",
    "ImpulseType",
    "__version__",
]
