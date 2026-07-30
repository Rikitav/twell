# This code was partially written using AI assistance

import ctypes
import math
import sys
import time

import sdl3
import skia
import twell

from dataclasses import dataclass
from typing import Optional, Callable, Tuple


# MARK: - CoreGraphics

@dataclass
class CGPoint:
    x: float
    y: float

@dataclass
class CGSize:
    width: float
    height: float

@dataclass
class CGRect:
    origin: CGPoint
    size: CGSize

    @property
    def min_x(self) -> float: return self.origin.x
    @property
    def max_x(self) -> float: return self.origin.x + self.size.width
    @property
    def min_y(self) -> float: return self.origin.y
    @property
    def max_y(self) -> float: return self.origin.y + self.size.height
    @property
    def mid_x(self) -> float: return self.origin.x + (self.size.width / 2.0)
    @property
    def mid_y(self) -> float: return self.origin.y + (self.size.height / 2.0)

    def contains(self, point: CGPoint) -> bool:
        return (self.min_x <= point.x <= self.max_x) and (self.min_y <= point.y <= self.max_y)

    @staticmethod
    def zero() -> 'CGRect':
        return CGRect(CGPoint(0, 0), CGSize(0, 0))


# MARK: - Theme

class UISpringConfiguration:
    @staticmethod
    def make_spring(response: float = 0.45, damping_ratio: float = 0.85, initial_velocity: float = 0.0) -> twell.SpringConfig:
        omega = (2.0 * math.pi) / max(0.01, response)
        stiffness = omega * omega
        damping = 2.0 * damping_ratio * omega
        return twell.SpringConfig(mass=1.0, stiffness=stiffness, damping=damping, initial_velocity=initial_velocity)

class UITheme:
    COLOR_BACKGROUND_HOST = skia.Color(24, 24, 30)
    COLOR_BACKGROUND_SHEET = skia.Color(32, 32, 38)
    COLOR_CLEAR_CANVAS = skia.Color(16, 16, 20)
    COLOR_TEXT_PRIMARY = skia.Color(255, 255, 255)
    COLOR_TEXT_SECONDARY = skia.Color(180, 180, 190)
    COLOR_DIVIDER = skia.Color(60, 60, 68)
    COLOR_HANDLE = skia.Color(140, 140, 145, 180)
    FONT_FAMILY = "Segoe UI"

class UIAnimationSprings:
    SHEET_SETTLE   = UISpringConfiguration.make_spring(0.30, 1.00)
    SHEET_TRACKING = UISpringConfiguration.make_spring(0.10, 1.00)
    ALPHA_SMOOTH   = UISpringConfiguration.make_spring(0.30, 1.00)
    BUTTON_HOVER   = UISpringConfiguration.make_spring(0.38, 0.75)
    BUTTON_PRESS   = UISpringConfiguration.make_spring(0.22, 1.00)
    BUTTON_RELEASE = UISpringConfiguration.make_spring(0.30, 1.00)


# MARK: - Physics

class UIScrollViewPhysics:
    """Encapsulates Apple's scroll view math and kinetic physics"""
    @staticmethod
    def apply_rubber_band(unconstrained_y: float, pos_open: float, pos_closed: float, container_height: float) -> float:
        c = 0.715  # __UIScrollViewRubberBandCoefficient
        
        if unconstrained_y < pos_open:
            u = pos_open - unconstrained_y
            e = 100.0
            fraction = c / (c * (u / e) + 1.0)
            return pos_open - (fraction * u)
            
        elif unconstrained_y > pos_closed:
            u = unconstrained_y - pos_closed
            e = max(1.0, min(200.0, container_height * 0.25))
            fraction = c / (c * (u / e) + 1.0)
            return pos_closed + (fraction * u)
            
        return unconstrained_y

    @staticmethod
    def project_velocity(current_y: float, velocity: float) -> float:
        # Phase 4.4: Inertial Projection Deceleration
        # Velocity decays at 0.995 per frame @ 120Hz -> ≈ velocity * 1.658
        return current_y + (velocity * 1.658)


class UISheetPresentationMetrics:
    """Encapsulates the deep math behind iOS 15+ background sheet transforms"""
    @staticmethod
    def calculate_transform(sheet_y: float, open_y: float, closed_y: float, host_width: float, host_height: float) -> Tuple[float, float, float, float]:
        # Returns: (Scale S, Translation Y, Corner Radius, Depth Progress D)
        denom = closed_y - open_y
        
        # 1. REMOVE the clamp! Allow `d` to exceed 1.0 when the sheet is pulled above its open position.
        d = max(0.0, (closed_y - sheet_y) / denom if denom > 0 else 0.0)
        
        if d <= 0.001:
            return 1.0, 0.0, 0.0, d
            
        m = 2.0                 # maximumSheetDepthLevel
        top_offset = 10.0       # Offset shift at full depth
        margin = 20.0           # Side padding estimation
        
        # 2. Apply exponential attenuation directly to the unclamped `d`.
        # As `d` climbs past 1.0, 2.0^(-d) naturally and smoothly asymptotes, 
        # ensuring the background shrinks perfectly in sync with the spring physics.
        lam = 2.0 ** (-d)                  # Attenuation (λ)
        kappa = 2.0 * (1.0 - lam)          # Base scale modifier (κ)

        s = 1.0 - (2.0 * margin * kappa) / host_height
        s = max(s, 0.8)
        
        delta_s = host_height * (1.0 - s) * 0.5
        psi = kappa * top_offset * max(0.0, min(1.0, m - d))
        
        t_y = psi - delta_s
        
        # 3. KEEP the clamp on the corner radius so it doesn't get excessively round during overshoot.
        corner_radius = 24.0 * min(d, 1.0)
        
        return s, t_y, corner_radius, d


# MARK: - UIKitCore

class UIResponder:
    def touches_began(self, point: CGPoint, time: float) -> bool: return False
    def touches_moved(self, point: CGPoint, time: float) -> bool: return False
    def touches_ended(self, point: CGPoint, time: float) -> bool: return False

class UIView(UIResponder):
    def __init__(self, frame: CGRect = None):
        self.frame = frame or CGRect.zero()
        
    def layout_subviews(self):
        pass
        
    def draw(self, canvas: skia.Canvas):
        pass

class UIViewController(UIResponder):
    def __init__(self):
        self.view = UIView()
        
    def load_view(self):
        """Override to map self.view to a custom UIView subclass"""
        pass
        
    def view_did_layout_subviews(self):
        """Called when the view's frame changes"""
        pass

class UIWindow(UIView):
    def __init__(self, frame: CGRect):
        super().__init__(frame)
        self.root_view_controller: Optional[UIViewController] = None
        
    def draw(self, canvas: skia.Canvas):
        if self.root_view_controller:
            self.root_view_controller.view.draw(canvas)

    def touches_began(self, point: CGPoint, time: float) -> bool:
        return self.root_view_controller.touches_began(point, time) if self.root_view_controller else False

    def touches_moved(self, point: CGPoint, time: float) -> bool:
        return self.root_view_controller.touches_moved(point, time) if self.root_view_controller else False

    def touches_ended(self, point: CGPoint, time: float) -> bool:
        return self.root_view_controller.touches_ended(point, time) if self.root_view_controller else False


# MARK: - UIViews

class SpringButton(UIView):
    def __init__(self, physics_context: twell.Context, title: str, default_color: int, hover_color: int):
        super().__init__()
        self.title = title
        self.default_color = default_color
        self.hover_color = hover_color
        
        self.is_hovered = False
        self.is_pressed = False
        self.action_handler: Optional[Callable[[float], None]] = None
        
        self.scale_property = physics_context.create_property(1.0, twell.UnitType.NORMALIZED)
        self.font = skia.Font(skia.Typeface.MakeFromName(UITheme.FONT_FAMILY, skia.FontStyle.Bold()), 16)
        self.text_paint = skia.Paint(Color=UITheme.COLOR_TEXT_PRIMARY, AntiAlias=True)

    def touches_began(self, point: CGPoint, current_time: float) -> bool:
        if self.frame.contains(point):
            self.is_pressed = True
            self.scale_property.animate_to_target(0.95, UIAnimationSprings.BUTTON_PRESS, current_time)
            return True
        return False

    def touches_moved(self, point: CGPoint, current_time: float) -> bool:
        was_hovered = self.is_hovered
        self.is_hovered = self.frame.contains(point)
        
        if self.is_hovered != was_hovered and not self.is_pressed:
            target_scale = 1.04 if self.is_hovered else 1.0
            spring = UIAnimationSprings.BUTTON_HOVER if self.is_hovered else UIAnimationSprings.BUTTON_RELEASE
            self.scale_property.animate_to_target(target_scale, spring, current_time)
            
        return self.is_hovered

    def touches_ended(self, point: CGPoint, current_time: float):
        if not self.is_pressed: return False
            
        self.is_pressed = False
        target_scale = 1.04 if self.is_hovered else 1.0
        self.scale_property.animate_to_target(target_scale, UIAnimationSprings.BUTTON_RELEASE, current_time)
        
        if self.frame.contains(point) and self.action_handler:
            self.action_handler(current_time)
        return True

    def draw(self, canvas: skia.Canvas):
        scale = float(self.scale_property.presentation_value)
        
        canvas.save()
        canvas.translate(self.frame.mid_x, self.frame.mid_y)
        canvas.scale(scale, scale)
        canvas.translate(-self.frame.mid_x, -self.frame.mid_y)

        bg_color = self.hover_color if self.is_hovered else self.default_color
        bg_paint = skia.Paint(Color=bg_color, AntiAlias=True)
        skia_rect = skia.Rect.MakeXYWH(self.frame.origin.x, self.frame.origin.y, self.frame.size.width, self.frame.size.height)
        canvas.drawRRect(skia.RRect.MakeRectXY(skia_rect, 14.0, 14.0), bg_paint)

        text_width = self.font.measureText(self.title)
        text_x = self.frame.origin.x + (self.frame.size.width - text_width) / 2.0
        text_y = self.frame.origin.y + (self.frame.size.height / 2.0) + 6.0 
        canvas.drawString(self.title, text_x, text_y, self.font, self.text_paint)
        canvas.restore()


class ModalBottomSheetView(UIView):
    def __init__(self):
        super().__init__()
        self.prop_y: Optional[twell.Property] = None
        self.prop_backdrop_alpha: Optional[twell.Property] = None
        self.close_button: Optional[SpringButton] = None
        self.sheet_height = 400.0

    def draw(self, canvas: skia.Canvas):
        if not self.prop_y or not self.prop_backdrop_alpha: return
        
        sheet_y = float(self.prop_y.presentation_value)
        backdrop_alpha = float(self.prop_backdrop_alpha.presentation_value)
        width, height = self.frame.size.width, self.frame.size.height

        # Ensure close button position stays synchronized with animated sheet_y every frame
        if self.close_button:
            cb_width, cb_height = 200.0, 48.0
            cb_x = (width - cb_width) / 2.0
            self.close_button.frame = CGRect(CGPoint(cb_x, sheet_y + 240.0), CGSize(cb_width, cb_height))

        if backdrop_alpha > 0.001:
            backdrop_color = skia.Color(0, 0, 0, int(150 * backdrop_alpha))
            canvas.drawRect(skia.Rect.MakeWH(width, height), skia.Paint(Color=backdrop_color, AntiAlias=True))

        if sheet_y >= height + 10.0:
            return
            
        canvas.save()
        canvas.clipRect(skia.Rect.MakeXYWH(0, sheet_y, width, self.sheet_height + 100.0))
        
        bg_rect = skia.Rect.MakeXYWH(0, sheet_y, width, self.sheet_height + 200.0)
        canvas.drawRRect(skia.RRect.MakeRectXY(bg_rect, 28.0, 28.0), skia.Paint(Color=UITheme.COLOR_BACKGROUND_SHEET, AntiAlias=True))

        handle_w, handle_h = 40.0, 5.0
        handle_x = (width - handle_w) / 2.0
        handle_rect = skia.Rect.MakeXYWH(handle_x, sheet_y + 12.0, handle_w, handle_h)
        canvas.drawRRect(skia.RRect.MakeRectXY(handle_rect, 2.5, 2.5), skia.Paint(Color=UITheme.COLOR_HANDLE, AntiAlias=True))

        title_font = skia.Font(skia.Typeface.MakeFromName(UITheme.FONT_FAMILY, skia.FontStyle.Bold()), 22)
        canvas.drawString("Header", 32.0, sheet_y + 60.0, title_font, skia.Paint(Color=UITheme.COLOR_TEXT_PRIMARY, AntiAlias=True))
        canvas.drawLine(32.0, sheet_y + 80.0, width - 32.0, sheet_y + 80.0, skia.Paint(Color=UITheme.COLOR_DIVIDER, AntiAlias=True))

        hello_font = skia.Font(skia.Typeface.MakeFromName(UITheme.FONT_FAMILY, skia.FontStyle.Bold()), 36)
        canvas.drawString("Hello World!", 32.0, sheet_y + 145.0, hello_font, skia.Paint(Color=skia.Color(0, 122, 255), AntiAlias=True))

        desc_font = skia.Font(skia.Typeface.MakeFromName(UITheme.FONT_FAMILY, skia.FontStyle.Normal()), 16)
        desc_text = "Built with Twell"
        canvas.drawString(desc_text, 32.0, sheet_y + 185.0, desc_font, skia.Paint(Color=UITheme.COLOR_TEXT_SECONDARY, AntiAlias=True))

        if self.close_button:
            self.close_button.draw(canvas)
            
        canvas.restore()


class RootSceneView(UIView):
    def __init__(self):
        super().__init__()
        self.sheet_controller: Optional['ModalBottomSheetController'] = None
        self.present_button: Optional[SpringButton] = None

    def draw(self, canvas: skia.Canvas):
        width, height = self.frame.size.width, self.frame.size.height

        sheet_y = float(self.sheet_controller.prop_y.presentation_value)
        closed_y = self.sheet_controller.position_closed
        open_y = self.sheet_controller.position_open
        
        s, t_y, corner_radius, d = UISheetPresentationMetrics.calculate_transform(
            sheet_y, open_y, closed_y, width, height
        )

        canvas.save()
        if d > 0.001:
            cx, cy = width / 2.0, height / 2.0
            canvas.translate(cx, cy)
            canvas.scale(s, s)
            canvas.translate(-cx, -cy)
            canvas.translate(0, t_y)

        host_rect = skia.Rect.MakeWH(width, height)
        bg_paint = skia.Paint(Color=UITheme.COLOR_BACKGROUND_HOST, AntiAlias=True)
        if corner_radius > 0.5:
            canvas.drawRRect(skia.RRect.MakeRectXY(host_rect, corner_radius, corner_radius), bg_paint)
        else:
            canvas.drawRect(host_rect, bg_paint)

        title_font = skia.Font(skia.Typeface.MakeFromName(UITheme.FONT_FAMILY, skia.FontStyle.Bold()), 32)
        title_str = "iOS modal bottom sheet"
        title_w = title_font.measureText(title_str)
        canvas.drawString(title_str, (width - title_w) / 2.0, (height / 2.0) - 60.0, title_font, skia.Paint(Color=UITheme.COLOR_TEXT_PRIMARY, AntiAlias=True))

        if self.present_button:
            self.present_button.draw(canvas)
            
        canvas.restore()
        
        if self.sheet_controller:
            self.sheet_controller.view.draw(canvas)


# MARK: - View controllers

class ModalBottomSheetController(UIViewController):
    def __init__(self, physics_context: twell.Context):
        super().__init__()
        self.physics_context = physics_context
        self.sheet_height = 400.0
        self.is_presented = False
        self.is_dragging = False
        self.drag_offset_y = 0.0
        
        self.prop_y = physics_context.create_property(0.0)
        self.prop_backdrop_alpha = physics_context.create_property(0.0, twell.UnitType.NORMALIZED)
        self.gesture = physics_context.create_gesture()

        self.load_view()

    def load_view(self):
        sheet_view = ModalBottomSheetView()
        sheet_view.prop_y = self.prop_y
        sheet_view.prop_backdrop_alpha = self.prop_backdrop_alpha
        sheet_view.sheet_height = self.sheet_height
        
        self.close_button = SpringButton(self.physics_context, "Dismiss", skia.Color(45, 45, 52), skia.Color(60, 60, 70))
        self.close_button.action_handler = self.dismiss
        sheet_view.close_button = self.close_button
        
        self.view = sheet_view

    @property
    def position_open(self) -> float:
        return max(60.0, float(self.view.frame.size.height - self.sheet_height))
        
    @property
    def position_closed(self) -> float:
        return float(self.view.frame.size.height + 40.0)

    def view_did_layout_subviews(self):
        if self.is_presented and not self.is_dragging:
            self.prop_y.set_value_immediate(self.position_open)
        elif not self.is_presented:
            self.prop_y.set_value_immediate(self.position_closed)
            
        self._update_close_button_frame(float(self.prop_y.presentation_value))

    def present(self, current_time: float):
        self.is_presented = True
        self.prop_y.animate_to_target(self.position_open, UIAnimationSprings.SHEET_SETTLE, current_time)
        self.prop_backdrop_alpha.animate_to_target(1.0, UIAnimationSprings.ALPHA_SMOOTH, current_time)

    def dismiss(self, current_time: float):
        self.is_presented = False
        self.prop_y.animate_to_target(self.position_closed, UIAnimationSprings.SHEET_SETTLE, current_time)
        self.prop_backdrop_alpha.animate_to_target(0.0, UIAnimationSprings.ALPHA_SMOOTH, current_time)

    def _update_close_button_frame(self, sheet_y: float):
        cb_width, cb_height = 200.0, 48.0
        cb_x = (self.view.frame.size.width - cb_width) / 2.0
        self.close_button.frame = CGRect(CGPoint(cb_x, sheet_y + 240.0), CGSize(cb_width, cb_height))

    def touches_began(self, point: CGPoint, current_time: float) -> bool:
        if not self.is_presented: return False

        current_y = float(self.prop_y.presentation_value)
        if point.y >= current_y:
            self._update_close_button_frame(current_y)
            if self.close_button.touches_began(point, current_time): 
                return True

        if point.y < current_y:
            self.dismiss(current_time)
            return True

        self.is_dragging = True
        self.drag_offset_y = point.y - current_y
        unconstrained_y = point.y - self.drag_offset_y
        
        self.gesture.add_touch(unconstrained_y, current_time)
        self.prop_y.animate_to_target(unconstrained_y, UIAnimationSprings.SHEET_TRACKING, current_time)
        return True

    def touches_moved(self, point: CGPoint, current_time: float) -> bool:
        current_y = float(self.prop_y.presentation_value)
        self._update_close_button_frame(current_y)
        
        if self.is_presented and not self.is_dragging:
            self.close_button.touches_moved(point, current_time)

        if not self.is_dragging: return False

        unconstrained_y = point.y - self.drag_offset_y
        self.gesture.add_touch(unconstrained_y, current_time)

        constrained_y = UIScrollViewPhysics.apply_rubber_band(
            unconstrained_y, self.position_open, self.position_closed, self.view.frame.size.height
        )
        self.prop_y.animate_to_target(constrained_y, UIAnimationSprings.SHEET_TRACKING, current_time)
        return True

    def touches_ended(self, point: CGPoint, current_time: float) -> bool:
        self.close_button.touches_ended(point, current_time)
        if not self.is_dragging: return False

        self.is_dragging = False
        velocity = self.gesture.get_velocity()
        current_y = float(self.prop_y.presentation_value)

        projected_y = UIScrollViewPhysics.project_velocity(current_y, velocity)
        midpoint = (self.position_open + self.position_closed) / 2.0

        if projected_y > midpoint:
            self.is_presented = False
            self.prop_backdrop_alpha.animate_to_target(0.0, UIAnimationSprings.ALPHA_SMOOTH, current_time)
            self.prop_y.release_gesture_spring(self.gesture, self.position_closed, UIAnimationSprings.SHEET_SETTLE, current_time)
        else:
            self.is_presented = True
            self.prop_y.release_gesture_spring(self.gesture, self.position_open, UIAnimationSprings.SHEET_SETTLE, current_time)
        return True


class RootSceneController(UIViewController):
    def __init__(self, physics_context: twell.Context):
        super().__init__()
        self.physics_context = physics_context
        self.sheet_controller = ModalBottomSheetController(physics_context)
        
        self.present_button = SpringButton(physics_context, "Present", skia.Color(0, 122, 255), skia.Color(30, 140, 255))
        self.present_button.action_handler = self.sheet_controller.present
        
        self.load_view()

    def load_view(self):
        root_view = RootSceneView()
        root_view.sheet_controller = self.sheet_controller
        root_view.present_button = self.present_button
        self.view = root_view

    def view_did_layout_subviews(self):
        width, height = self.view.frame.size.width, self.view.frame.size.height
        
        btn_w, btn_h = 240.0, 54.0
        self.present_button.frame = CGRect(CGPoint((width - btn_w) / 2.0, (height - btn_h) / 2.0 + 30.0), CGSize(btn_w, btn_h))
        
        self.sheet_controller.view.frame = self.view.frame
        self.sheet_controller.view_did_layout_subviews()

    def touches_began(self, point: CGPoint, time: float) -> bool:
        if self.sheet_controller.touches_began(point, time): return True
        if not self.sheet_controller.is_presented:
            return self.present_button.touches_began(point, time)
        return False

    def touches_moved(self, point: CGPoint, time: float) -> bool:
        self.sheet_controller.touches_moved(point, time)
        if not self.sheet_controller.is_presented:
            self.present_button.touches_moved(point, time)
        else:
            self.present_button.is_hovered = False 
        return True

    def touches_ended(self, point: CGPoint, time: float) -> bool:
        self.sheet_controller.touches_ended(point, time)
        self.present_button.touches_ended(point, time)
        return True


# MARK: - Application Delegate

class UIApplicationDelegate:
    def application_did_finish_launching(self, app: 'UIApplication'):
        pass


class UIApplication:
    def __init__(self, delegate: UIApplicationDelegate, title: str, width: int, height: int):
        self.delegate = delegate
        self.title = title
        self.initial_width = width
        self.initial_height = height
        
        self.window: Optional[UIWindow] = None
        self.physics_context: Optional[twell.Context] = None
        self.running = False

    def _init_sdl_and_gl(self):
        if sys.platform == "win32":
            try: ctypes.windll.winmm.timeBeginPeriod(1)
            except Exception: pass

        if not sdl3.SDL_Init(sdl3.SDL_INIT_VIDEO):
            raise RuntimeError(f"Failed to init SDL3: {sdl3.SDL_GetError().decode('utf-8')}")

        sdl3.SDL_GL_SetAttribute(sdl3.SDL_GL_CONTEXT_MAJOR_VERSION, 3)
        sdl3.SDL_GL_SetAttribute(sdl3.SDL_GL_CONTEXT_MINOR_VERSION, 3)
        sdl3.SDL_GL_SetAttribute(sdl3.SDL_GL_CONTEXT_PROFILE_MASK, sdl3.SDL_GL_CONTEXT_PROFILE_CORE)
        sdl3.SDL_GL_SetAttribute(sdl3.SDL_GL_DOUBLEBUFFER, 1)

        self.sdl_window = sdl3.SDL_CreateWindow(self.title.encode('utf-8'), self.initial_width, self.initial_height, sdl3.SDL_WINDOW_OPENGL | sdl3.SDL_WINDOW_RESIZABLE)
        
        self.gl_context = sdl3.SDL_GL_CreateContext(self.sdl_window)
        sdl3.SDL_GL_MakeCurrent(self.sdl_window, self.gl_context)
        try: sdl3.SDL_GL_SetSwapInterval(1)
        except Exception: pass

        self.gr_context = skia.GrDirectContext.MakeGL()

    def _rebuild_graphics_buffers(self):
        w_buf, h_buf = ctypes.c_int(), ctypes.c_int()
        sdl3.SDL_GetWindowSize(self.sdl_window, ctypes.byref(w_buf), ctypes.byref(h_buf))
        self.width = max(320.0, float(w_buf.value))
        self.height = max(240.0, float(h_buf.value))

        px_w, px_h = ctypes.c_int(), ctypes.c_int()
        sdl3.SDL_GetWindowSizeInPixels(self.sdl_window, ctypes.byref(px_w), ctypes.byref(px_h))
        self.pixel_w = max(320, px_w.value)
        self.pixel_h = max(240, px_h.value)

        target = skia.GrBackendRenderTarget(self.pixel_w, self.pixel_h, 0, 8, skia.GrGLFramebufferInfo(0, 0x8058))
        self.skia_surface = skia.Surface.MakeFromBackendRenderTarget(
            self.gr_context, target, skia.kBottomLeft_GrSurfaceOrigin, skia.kRGBA_8888_ColorType, None
        )
        self.canvas = self.skia_surface.getCanvas()

        # Propagate window resizing via UIWindow bounds
        if self.window:
            self.window.frame.size = CGSize(self.width, self.height)
            if self.window.root_view_controller:
                self.window.root_view_controller.view.frame = self.window.frame
                self.window.root_view_controller.view_did_layout_subviews()

    def run(self):
        self._init_sdl_and_gl()
        self.physics_context = twell.Context(max_properties=1024, max_gestures=256)
        
        # UIWindow serves as the core rendering base and layout parent frame
        self.window = UIWindow(CGRect(CGPoint(0, 0), CGSize(self.initial_width, self.initial_height)))
        
        # Hook into delegate lifecycle
        self.delegate.application_did_finish_launching(self)
        
        # Propagate subviews immediately
        self._rebuild_graphics_buffers()

        self.running = True
        event = sdl3.SDL_Event()

        while self.running:
            t_start = time.perf_counter()
            current_time = t_start

            while sdl3.SDL_PollEvent(ctypes.byref(event)):
                if event.type == sdl3.SDL_EVENT_QUIT:
                    self.running = False
                elif event.type == sdl3.SDL_EVENT_KEY_DOWN and event.key.key == sdl3.SDLK_ESCAPE:
                    self.running = False
                elif event.type in (sdl3.SDL_EVENT_WINDOW_RESIZED, sdl3.SDL_EVENT_WINDOW_PIXEL_SIZE_CHANGED):
                    self._rebuild_graphics_buffers()
                elif event.type == sdl3.SDL_EVENT_MOUSE_BUTTON_DOWN and event.button.button == sdl3.SDL_BUTTON_LEFT:
                    self.window.touches_began(CGPoint(float(event.button.x), float(event.button.y)), current_time)
                elif event.type == sdl3.SDL_EVENT_MOUSE_MOTION:
                    self.window.touches_moved(CGPoint(float(event.motion.x), float(event.motion.y)), current_time)
                elif event.type == sdl3.SDL_EVENT_MOUSE_BUTTON_UP and event.button.button == sdl3.SDL_BUTTON_LEFT:
                    self.window.touches_ended(CGPoint(float(event.button.x), float(event.button.y)), current_time)

            self.physics_context.tick(current_time)

            self.canvas.save()
            if self.pixel_w > 0 and self.width > 0:
                scale_x, scale_y = float(self.pixel_w) / self.width, float(self.pixel_h) / self.height
                if abs(scale_x - 1.0) > 1e-4 or abs(scale_y - 1.0) > 1e-4:
                    self.canvas.scale(scale_x, scale_y)
                    
            self.canvas.clear(UITheme.COLOR_CLEAR_CANVAS)
            self.window.draw(self.canvas)
            self.canvas.restore()

            self.gr_context.flushAndSubmit()
            sdl3.SDL_GL_SwapWindow(self.sdl_window)

            elapsed = time.perf_counter() - t_start
            if elapsed < (1.0 / 60.0):
                time.sleep((1.0 / 60.0) - elapsed)

        self._cleanup()

    def _cleanup(self):
        self.skia_surface = None
        if self.gr_context: self.gr_context.abandonContext()
        if self.gl_context: sdl3.SDL_GL_DestroyContext(self.gl_context)
        if self.sdl_window: sdl3.SDL_DestroyWindow(self.sdl_window)
        sdl3.SDL_Quit()


class AppDelegate(UIApplicationDelegate):
    def application_did_finish_launching(self, app: UIApplication):
        root_controller = RootSceneController(app.physics_context)
        app.window.root_view_controller = root_controller


if __name__ == "__main__":
    app = UIApplication(
        delegate=AppDelegate(), 
        title="Twell bottom sheet example", 
        width=480,
        height=854
    )
    app.run()
