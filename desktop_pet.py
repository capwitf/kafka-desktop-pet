from __future__ import annotations

import argparse
import ctypes
import sys
import time
from ctypes import wintypes
from pathlib import Path

from PIL import Image, ImageDraw


FRAME_NAMES = (
    "keyboard_ready",
    "keyboard_left_up",
    "keyboard_left_down",
    "keyboard_right_up",
    "keyboard_right_down",
    "game_ready",
    "game_wasd_up",
    "game_wasd_down",
    "game_mouse_move",
    "game_mouse_click",
)

LEFT_KEYS = set("qwertasdfgzxcvb")
RIGHT_KEYS = set("yuiophjklnm")
GAME_WINDOW_KEYWORDS = (
    "valorant",
    "无畏契约",
    "deltaforce",
    "delta force",
    "三角洲行动",
    "deltaforceclient-win64-shipping.exe",
)

MIN_SIZE = 220
MAX_SIZE = 720
DEFAULT_SIZE = 360


user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32
kernel32 = ctypes.windll.kernel32

HINSTANCE = wintypes.HINSTANCE
HICON = getattr(wintypes, "HICON", wintypes.HANDLE)
HCURSOR = getattr(wintypes, "HCURSOR", wintypes.HANDLE)
HBRUSH = getattr(wintypes, "HBRUSH", wintypes.HANDLE)
HMENU = getattr(wintypes, "HMENU", wintypes.HANDLE)
HBITMAP = getattr(wintypes, "HBITMAP", wintypes.HANDLE)
HWND = wintypes.HWND
HDC = wintypes.HDC
LRESULT = getattr(wintypes, "LRESULT", ctypes.c_ssize_t)
WPARAM = getattr(wintypes, "WPARAM", ctypes.c_size_t)
LPARAM = getattr(wintypes, "LPARAM", ctypes.c_ssize_t)
UINT_PTR = getattr(wintypes, "UINT_PTR", ctypes.c_size_t)

WS_POPUP = 0x80000000
WS_EX_LAYERED = 0x00080000
WS_EX_TOPMOST = 0x00000008
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_NOACTIVATE = 0x08000000
SW_SHOWNOACTIVATE = 4
HWND_TOPMOST = -1
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
SWP_NOACTIVATE = 0x0010
SWP_SHOWWINDOW = 0x0040
WM_DESTROY = 0x0002
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
WM_MOUSEMOVE = 0x0200
WM_RBUTTONDOWN = 0x0204
WM_TIMER = 0x0113
MK_LBUTTON = 0x0001
ULW_ALPHA = 0x00000002
AC_SRC_OVER = 0x00
AC_SRC_ALPHA = 0x01
BI_RGB = 0
DIB_RGB_COLORS = 0
WM_APP = 0x8000
WM_CLOSE_PET = WM_APP + 1
VK_LBUTTON = 0x01
VK_SPACE = 0x20
VK_RETURN = 0x0D
VK_BACK = 0x08
VK_TAB = 0x09
VK_SHIFT = 0x10
VK_CONTROL = 0x11
VK_MENU = 0x12
VK_ESCAPE = 0x1B
VK_CAPITAL = 0x14
VK_HOME = 0x24
VK_LEFT = 0x25
VK_UP = 0x26
VK_RIGHT = 0x27
VK_DOWN = 0x28
VK_INSERT = 0x2D
VK_DELETE = 0x2E
VK_LWIN = 0x5B
VK_RWIN = 0x5C
VK_APPS = 0x5D
VK_LSHIFT = 0xA0
VK_RSHIFT = 0xA1
VK_LCONTROL = 0xA2
VK_RCONTROL = 0xA3
VK_LMENU = 0xA4
VK_RMENU = 0xA5
VK_OEM_1 = 0xBA
VK_OEM_PLUS = 0xBB
VK_OEM_COMMA = 0xBC
VK_OEM_MINUS = 0xBD
VK_OEM_PERIOD = 0xBE
VK_OEM_2 = 0xBF
VK_OEM_3 = 0xC0
VK_OEM_4 = 0xDB
VK_OEM_5 = 0xDC
VK_OEM_6 = 0xDD
VK_OEM_7 = 0xDE
VK_OEM_102 = 0xE2

LEFT_KEY_VKS = (
    {ord(char.upper()) for char in LEFT_KEYS}
    | {ord(str(number)) for number in range(1, 6)}
    | set(range(0x70, 0x75))
    | {
        VK_ESCAPE,
        VK_TAB,
        VK_CAPITAL,
        VK_SHIFT,
        VK_CONTROL,
        VK_MENU,
        VK_LSHIFT,
        VK_LCONTROL,
        VK_LMENU,
        VK_LWIN,
        VK_OEM_3,
    }
)
RIGHT_KEY_VKS = (
    {ord(char.upper()) for char in RIGHT_KEYS}
    | {ord(str(number)) for number in range(6, 10)}
    | {ord("0")}
    | set(range(0x75, 0x7C))
    | set(range(0x60, 0x70))
    | {
        VK_SPACE,
        VK_RETURN,
        VK_BACK,
        VK_HOME,
        VK_LEFT,
        VK_UP,
        VK_RIGHT,
        VK_DOWN,
        VK_INSERT,
        VK_DELETE,
        VK_RSHIFT,
        VK_RCONTROL,
        VK_RMENU,
        VK_RWIN,
        VK_APPS,
        VK_OEM_1,
        VK_OEM_PLUS,
        VK_OEM_COMMA,
        VK_OEM_MINUS,
        VK_OEM_PERIOD,
        VK_OEM_2,
        VK_OEM_4,
        VK_OEM_5,
        VK_OEM_6,
        VK_OEM_7,
        VK_OEM_102,
    }
)
WATCHED_KEY_VKS = sorted(set(range(0x08, 0xFF)) - {VK_LBUTTON})


class POINT(ctypes.Structure):
    _fields_ = (("x", ctypes.c_long), ("y", ctypes.c_long))


class SIZE(ctypes.Structure):
    _fields_ = (("cx", ctypes.c_long), ("cy", ctypes.c_long))


class BLENDFUNCTION(ctypes.Structure):
    _fields_ = (
        ("BlendOp", ctypes.c_byte),
        ("BlendFlags", ctypes.c_byte),
        ("SourceConstantAlpha", ctypes.c_byte),
        ("AlphaFormat", ctypes.c_byte),
    )


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = (
        ("biSize", wintypes.DWORD),
        ("biWidth", wintypes.LONG),
        ("biHeight", wintypes.LONG),
        ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD),
        ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD),
        ("biXPelsPerMeter", wintypes.LONG),
        ("biYPelsPerMeter", wintypes.LONG),
        ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD),
    )


class BITMAPINFO(ctypes.Structure):
    _fields_ = (("bmiHeader", BITMAPINFOHEADER), ("bmiColors", wintypes.DWORD * 3))


class WNDCLASS(ctypes.Structure):
    _fields_ = (
        ("style", wintypes.UINT),
        ("lpfnWndProc", ctypes.c_void_p),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", HINSTANCE),
        ("hIcon", HICON),
        ("hCursor", HCURSOR),
        ("hbrBackground", HBRUSH),
        ("lpszMenuName", wintypes.LPCWSTR),
        ("lpszClassName", wintypes.LPCWSTR),
    )


class MSG(ctypes.Structure):
    _fields_ = (
        ("hwnd", HWND),
        ("message", wintypes.UINT),
        ("wParam", WPARAM),
        ("lParam", LPARAM),
        ("time", wintypes.DWORD),
        ("pt", POINT),
    )


WNDPROC = ctypes.WINFUNCTYPE(LRESULT, HWND, wintypes.UINT, WPARAM, LPARAM)

user32.RegisterClassW.argtypes = [ctypes.POINTER(WNDCLASS)]
user32.RegisterClassW.restype = wintypes.ATOM
user32.CreateWindowExW.argtypes = [
    wintypes.DWORD,
    wintypes.LPCWSTR,
    wintypes.LPCWSTR,
    wintypes.DWORD,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    HWND,
    HMENU,
    HINSTANCE,
    wintypes.LPVOID,
]
user32.CreateWindowExW.restype = HWND
user32.DefWindowProcW.argtypes = [HWND, wintypes.UINT, WPARAM, LPARAM]
user32.DefWindowProcW.restype = LRESULT
user32.UpdateLayeredWindow.argtypes = [
    HWND,
    HDC,
    ctypes.POINTER(POINT),
    ctypes.POINTER(SIZE),
    HDC,
    ctypes.POINTER(POINT),
    wintypes.COLORREF,
    ctypes.POINTER(BLENDFUNCTION),
    wintypes.DWORD,
]
user32.UpdateLayeredWindow.restype = wintypes.BOOL
user32.GetDC.argtypes = [HWND]
user32.GetDC.restype = HDC
user32.ReleaseDC.argtypes = [HWND, HDC]
user32.ReleaseDC.restype = ctypes.c_int
user32.SetWindowPos.argtypes = [HWND, HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.UINT]
user32.SetWindowPos.restype = wintypes.BOOL
user32.SetTimer.argtypes = [HWND, UINT_PTR, wintypes.UINT, ctypes.c_void_p]
user32.SetTimer.restype = UINT_PTR
user32.KillTimer.argtypes = [HWND, UINT_PTR]
user32.KillTimer.restype = wintypes.BOOL
user32.SetCapture.argtypes = [HWND]
user32.SetCapture.restype = HWND
user32.ReleaseCapture.argtypes = []
user32.ReleaseCapture.restype = wintypes.BOOL
user32.DestroyWindow.argtypes = [HWND]
user32.DestroyWindow.restype = wintypes.BOOL
user32.PostMessageW.argtypes = [HWND, wintypes.UINT, WPARAM, LPARAM]
user32.PostMessageW.restype = wintypes.BOOL
user32.PostQuitMessage.argtypes = [ctypes.c_int]
user32.ShowWindow.argtypes = [HWND, ctypes.c_int]
user32.ShowWindow.restype = wintypes.BOOL
user32.GetMessageW.argtypes = [ctypes.POINTER(MSG), HWND, wintypes.UINT, wintypes.UINT]
user32.GetMessageW.restype = wintypes.BOOL
user32.TranslateMessage.argtypes = [ctypes.POINTER(MSG)]
user32.DispatchMessageW.argtypes = [ctypes.POINTER(MSG)]
user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
user32.GetAsyncKeyState.restype = ctypes.c_short
user32.GetCursorPos.argtypes = [ctypes.POINTER(POINT)]
user32.GetCursorPos.restype = wintypes.BOOL
gdi32.CreateCompatibleDC.argtypes = [HDC]
gdi32.CreateCompatibleDC.restype = HDC
gdi32.CreateDIBSection.argtypes = [
    HDC,
    ctypes.POINTER(BITMAPINFO),
    wintypes.UINT,
    ctypes.POINTER(ctypes.c_void_p),
    wintypes.HANDLE,
    wintypes.DWORD,
]
gdi32.CreateDIBSection.restype = HBITMAP
gdi32.SelectObject.argtypes = [HDC, wintypes.HANDLE]
gdi32.SelectObject.restype = wintypes.HANDLE
gdi32.DeleteObject.argtypes = [wintypes.HANDLE]
gdi32.DeleteObject.restype = wintypes.BOOL
gdi32.DeleteDC.argtypes = [HDC]
gdi32.DeleteDC.restype = wintypes.BOOL
kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
kernel32.GetModuleHandleW.restype = HINSTANCE


def app_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)  # type: ignore[attr-defined]
    return Path(__file__).resolve().parent


FRAME_DIR = app_base_dir() / "assets" / "frames"


def signed_word(value: int) -> int:
    value &= 0xFFFF
    return value - 0x10000 if value & 0x8000 else value


def point_from_lparam(lparam: int) -> tuple[int, int]:
    return signed_word(lparam), signed_word(lparam >> 16)


def foreground_window_text() -> str:
    if not sys.platform.startswith("win"):
        return ""

    hwnd = user32.GetForegroundWindow()
    title_length = user32.GetWindowTextLengthW(hwnd)
    title_buffer = ctypes.create_unicode_buffer(title_length + 1)
    user32.GetWindowTextW(hwnd, title_buffer, title_length + 1)

    process_id = ctypes.c_ulong()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))
    if not process_id.value:
        return title_buffer.value.lower()

    process_query_limited_information = 0x1000
    handle = kernel32.OpenProcess(process_query_limited_information, False, process_id.value)
    if not handle:
        return title_buffer.value.lower()

    try:
        size = ctypes.c_ulong(260)
        buffer = ctypes.create_unicode_buffer(size.value)
        ok = kernel32.QueryFullProcessImageNameW(handle, 0, buffer, ctypes.byref(size))
        process_name = Path(buffer.value).name if ok else ""
        return f"{process_name} {title_buffer.value}".lower()
    finally:
        kernel32.CloseHandle(handle)


def is_game_window_text(window_text: str, keywords: tuple[str, ...]) -> bool:
    text = window_text.lower()
    return any(keyword.lower() in text for keyword in keywords if keyword)


def premultiplied_bgra_bytes(image: Image.Image) -> bytes:
    rgba = image.convert("RGBA")
    data = bytearray(rgba.tobytes())
    for i in range(0, len(data), 4):
        r, g, b, a = data[i], data[i + 1], data[i + 2], data[i + 3]
        data[i] = (b * a) // 255
        data[i + 1] = (g * a) // 255
        data[i + 2] = (r * a) // 255
        data[i + 3] = a
    return bytes(data)


class DesktopPet:
    def __init__(
        self,
        frame_dir: Path,
        size: int,
        x: int,
        y: int,
        mode: str,
        game_keywords: tuple[str, ...],
        min_size: int = MIN_SIZE,
        max_size: int = MAX_SIZE,
    ) -> None:
        self.frame_dir = frame_dir
        self.size = max(min_size, min(max_size, size))
        self.x = x
        self.y = y
        self.min_size = min_size
        self.max_size = max_size
        self.mode_setting = mode
        self.current_mode = "keyboard"
        self.game_keywords = tuple(keyword.lower() for keyword in game_keywords if keyword)

        self.down_keys: set[int] = set()
        self.mouse_left_down = False
        self.last_mouse_pos: tuple[int, int] | None = None
        self.last_side = "left"
        self.last_mouse_animation_at = 0.0
        self.animation_token = 0
        self.timeline: list[tuple[float, int, str]] = []
        self.next_mode_check_at = 0.0
        self.current_frame_name = "keyboard_ready"

        self.is_dragging = False
        self.is_resizing = False
        self.drag_offset_x = 0
        self.drag_offset_y = 0
        self.resize_start_pointer_x = 0
        self.resize_start_pointer_y = 0
        self.resize_start_size = self.size

        self.hwnd: int | None = None
        self.hinstance = kernel32.GetModuleHandleW(None)
        self._wndproc = WNDPROC(self.wndproc)
        self.source_frames = self.load_source_frames()
        self.rendered_frames: dict[str, Image.Image] = {}
        self.frame_bboxes: dict[str, tuple[int, int, int, int] | None] = {}
        self.render_frames()

    def load_source_frames(self) -> dict[str, Image.Image]:
        frames = {}
        for name in FRAME_NAMES:
            path = self.frame_dir / f"{name}.png"
            if not path.exists():
                raise FileNotFoundError(f"Missing frame: {path}")
            frames[name] = Image.open(path).convert("RGBA")
        return frames

    def render_frames(self) -> None:
        self.rendered_frames = {}
        self.frame_bboxes = {}
        for name, source in self.source_frames.items():
            image = source.copy()
            image.thumbnail((self.size, self.size), Image.Resampling.LANCZOS)
            canvas = Image.new("RGBA", (self.size, self.size), (0, 0, 0, 0))
            x = (self.size - image.width) // 2
            y = (self.size - image.height) // 2
            canvas.alpha_composite(image, (x, y))
            self.frame_bboxes[name] = canvas.getchannel("A").getbbox()
            self.draw_resize_handle(canvas)
            self.rendered_frames[name] = canvas

    def draw_resize_handle(self, canvas: Image.Image) -> None:
        draw = ImageDraw.Draw(canvas, "RGBA")
        s = self.size
        handle = max(22, s // 12)
        base_x = s - handle
        base_y = s - handle
        draw.polygon([(s, s), (base_x, s), (s, base_y)], fill=(18, 18, 22, 95))
        for offset in (8, 16, 24):
            x0 = s - offset
            y0 = s - 4
            x1 = s - 4
            y1 = s - offset
            draw.line((x0, y0, x1, y1), fill=(255, 255, 255, 205), width=2)

    def create_window(self) -> None:
        class_name = "ZhuocDesktopPetWindow"
        wc = WNDCLASS()
        wc.lpfnWndProc = ctypes.cast(self._wndproc, ctypes.c_void_p).value
        wc.hInstance = self.hinstance
        wc.lpszClassName = class_name
        wc.hCursor = user32.LoadCursorW(None, 32512)
        user32.RegisterClassW(ctypes.byref(wc))

        ex_style = WS_EX_LAYERED | WS_EX_TOPMOST | WS_EX_TOOLWINDOW | WS_EX_NOACTIVATE
        hwnd = user32.CreateWindowExW(
            ex_style,
            class_name,
            "Zhuoc Desktop Pet",
            WS_POPUP,
            self.x,
            self.y,
            self.size,
            self.size,
            None,
            None,
            self.hinstance,
            None,
        )
        if not hwnd:
            raise ctypes.WinError()

        self.hwnd = hwnd
        self.show_frame(self.current_frame_name)
        user32.ShowWindow(hwnd, SW_SHOWNOACTIVATE)
        user32.SetWindowPos(hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE | SWP_SHOWWINDOW)
        user32.SetTimer(hwnd, 1, 16, None)

    def update_layered_image(self, image: Image.Image) -> None:
        if not self.hwnd:
            return

        width, height = image.size
        screen_dc = user32.GetDC(None)
        mem_dc = gdi32.CreateCompatibleDC(screen_dc)
        bits = ctypes.c_void_p()

        bmi = BITMAPINFO()
        bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        bmi.bmiHeader.biWidth = width
        bmi.bmiHeader.biHeight = -height
        bmi.bmiHeader.biPlanes = 1
        bmi.bmiHeader.biBitCount = 32
        bmi.bmiHeader.biCompression = BI_RGB

        bitmap = gdi32.CreateDIBSection(screen_dc, ctypes.byref(bmi), DIB_RGB_COLORS, ctypes.byref(bits), None, 0)
        if not bitmap:
            user32.ReleaseDC(None, screen_dc)
            raise ctypes.WinError()

        old_bitmap = gdi32.SelectObject(mem_dc, bitmap)
        pixel_bytes = premultiplied_bgra_bytes(image)
        ctypes.memmove(bits, pixel_bytes, len(pixel_bytes))

        pos = POINT(self.x, self.y)
        size = SIZE(width, height)
        src = POINT(0, 0)
        blend = BLENDFUNCTION(AC_SRC_OVER, 0, 255, AC_SRC_ALPHA)
        ok = user32.UpdateLayeredWindow(self.hwnd, screen_dc, ctypes.byref(pos), ctypes.byref(size), mem_dc, ctypes.byref(src), 0, ctypes.byref(blend), ULW_ALPHA)

        gdi32.SelectObject(mem_dc, old_bitmap)
        gdi32.DeleteObject(bitmap)
        gdi32.DeleteDC(mem_dc)
        user32.ReleaseDC(None, screen_dc)

        if not ok:
            raise ctypes.WinError()

    def show_frame(self, frame_name: str) -> None:
        self.current_frame_name = frame_name
        self.update_layered_image(self.rendered_frames[frame_name])

    def ready_frame(self) -> str:
        return "game_ready" if self.current_mode == "game" else "keyboard_ready"

    def update_mode_if_needed(self) -> None:
        now = time.monotonic()
        if now < self.next_mode_check_at:
            return
        self.next_mode_check_at = now + 0.8

        previous_mode = self.current_mode
        if self.mode_setting == "auto":
            self.current_mode = "game" if is_game_window_text(foreground_window_text(), self.game_keywords) else "keyboard"
        else:
            self.current_mode = self.mode_setting

        if previous_mode != self.current_mode:
            self.cancel_animation()
            self.show_frame(self.ready_frame())

    def cancel_animation(self) -> None:
        self.animation_token += 1
        self.timeline.clear()

    def play_sequence(self, frames: tuple[str, ...], delays_ms: tuple[int, ...] = (70, 150)) -> None:
        self.animation_token += 1
        token = self.animation_token
        ready = self.ready_frame()
        now = time.monotonic()
        self.timeline.clear()

        elapsed = 0.0
        for index, frame_name in enumerate(frames):
            if index > 0:
                elapsed += delays_ms[min(index - 1, len(delays_ms) - 1)] / 1000
            self.timeline.append((now + elapsed, token, frame_name))

        return_delay = max(elapsed + 0.13, 0.12)
        self.timeline.append((now + return_delay, token, ready))

    def process_timeline(self) -> None:
        if not self.timeline:
            return
        now = time.monotonic()
        due = [item for item in self.timeline if item[0] <= now]
        self.timeline = [item for item in self.timeline if item[0] > now]
        for _when, token, frame_name in due:
            if token == self.animation_token:
                self.show_frame(frame_name)

    def classify_keyboard_side(self, vk: int) -> str:
        if vk in LEFT_KEY_VKS:
            return "left"
        if vk in RIGHT_KEY_VKS:
            return "right"
        return "right"

    def handle_key_press(self, vk: int) -> None:
        if self.current_mode == "game":
            self.play_sequence(("game_wasd_up", "game_wasd_down"), (65, 135))
            return

        side = self.classify_keyboard_side(vk)
        self.play_sequence((f"keyboard_{side}_up", f"keyboard_{side}_down"), (70, 145))

    def handle_mouse_move(self) -> None:
        if self.current_mode == "game":
            self.play_sequence(("game_mouse_move",), (120,))
        else:
            self.play_sequence(("keyboard_right_up", "keyboard_right_down"), (70, 140))

    def handle_mouse_click(self) -> None:
        if self.current_mode == "game":
            self.play_sequence(("game_mouse_move", "game_mouse_click"), (60, 145))
        else:
            self.play_sequence(("keyboard_right_up", "keyboard_right_down"), (60, 135))

    def poll_keyboard(self) -> None:
        current_down: set[int] = set()
        for vk in WATCHED_KEY_VKS:
            state = user32.GetAsyncKeyState(vk)
            if state & 0x8000:
                current_down.add(vk)
                if vk not in self.down_keys:
                    self.handle_key_press(vk)
        self.down_keys = current_down

    def poll_mouse(self) -> None:
        cursor = POINT()
        if not user32.GetCursorPos(ctypes.byref(cursor)):
            return

        current_pos = (cursor.x, cursor.y)
        now = time.monotonic()
        if self.last_mouse_pos is not None and current_pos != self.last_mouse_pos:
            if now - self.last_mouse_animation_at >= 0.12:
                self.last_mouse_animation_at = now
                self.handle_mouse_move()
        self.last_mouse_pos = current_pos

        left_down = bool(user32.GetAsyncKeyState(VK_LBUTTON) & 0x8000)
        if left_down and not self.mouse_left_down:
            self.handle_mouse_click()
        self.mouse_left_down = left_down

    def process_events(self) -> None:
        self.update_mode_if_needed()
        self.poll_keyboard()
        self.poll_mouse()
        self.process_timeline()

    def in_resize_zone(self, x: int, y: int) -> bool:
        handle = max(28, self.size // 10)
        return x >= self.size - handle and y >= self.size - handle

    def resize_to(self, new_size: int) -> None:
        new_size = max(self.min_size, min(self.max_size, int(new_size)))
        if new_size == self.size:
            return
        self.size = new_size
        self.render_frames()
        self.show_frame(self.current_frame_name)

    def point_is_on_head(self, x: int, y: int) -> bool:
        bbox = self.frame_bboxes.get(self.current_frame_name)
        if not bbox:
            return False
        left, top, right, bottom = bbox
        head_bottom = top + int((bottom - top) * 0.46)
        return left <= x <= right and top <= y <= head_bottom

    def wndproc(self, hwnd: int, msg: int, wparam: int, lparam: int) -> int:
        if msg == WM_TIMER:
            self.process_events()
            return 0
        if msg == WM_CLOSE_PET:
            user32.DestroyWindow(hwnd)
            return 0
        if msg == WM_LBUTTONDOWN:
            x, y = point_from_lparam(lparam)
            if self.in_resize_zone(x, y):
                self.is_resizing = True
                cursor = POINT()
                user32.GetCursorPos(ctypes.byref(cursor))
                self.resize_start_pointer_x = cursor.x
                self.resize_start_pointer_y = cursor.y
                self.resize_start_size = self.size
            else:
                self.is_dragging = True
                self.drag_offset_x = x
                self.drag_offset_y = y
            user32.SetCapture(hwnd)
            return 0
        if msg == WM_MOUSEMOVE and (wparam & MK_LBUTTON):
            cursor = POINT()
            user32.GetCursorPos(ctypes.byref(cursor))
            if self.is_resizing:
                dx = cursor.x - self.resize_start_pointer_x
                dy = cursor.y - self.resize_start_pointer_y
                self.resize_to(self.resize_start_size + max(dx, dy))
            elif self.is_dragging:
                self.x = cursor.x - self.drag_offset_x
                self.y = cursor.y - self.drag_offset_y
                user32.SetWindowPos(hwnd, HWND_TOPMOST, self.x, self.y, 0, 0, SWP_NOSIZE | SWP_NOACTIVATE | SWP_SHOWWINDOW)
            return 0
        if msg == WM_LBUTTONUP:
            self.is_dragging = False
            self.is_resizing = False
            user32.ReleaseCapture()
            return 0
        if msg == WM_RBUTTONDOWN:
            x, y = point_from_lparam(lparam)
            if self.point_is_on_head(x, y):
                user32.PostMessageW(hwnd, WM_CLOSE_PET, 0, 0)
            return 0
        if msg == WM_DESTROY:
            user32.KillTimer(hwnd, 1)
            user32.PostQuitMessage(0)
            return 0
        return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

    def run(self) -> None:
        self.create_window()
        msg = MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))


def main() -> int:
    parser = argparse.ArgumentParser(description="Transparent always-on-top keyboard desktop pet.")
    parser.add_argument("--frame-dir", type=Path, default=FRAME_DIR, help="Directory containing processed PNG frames.")
    parser.add_argument("--size", type=int, default=DEFAULT_SIZE, help="Displayed pet size in pixels.")
    parser.add_argument("--x", type=int, default=80, help="Initial window x position.")
    parser.add_argument("--y", type=int, default=420, help="Initial window y position.")
    parser.add_argument(
        "--mode",
        choices=("auto", "keyboard", "game"),
        default="auto",
        help="auto detects supported FPS games; keyboard keeps normal mode; game forces FPS mode.",
    )
    parser.add_argument(
        "--game-keyword",
        action="append",
        default=[],
        help="Extra foreground process/window keyword for auto game mode. Can be used multiple times.",
    )
    args = parser.parse_args()

    game_keywords = (*GAME_WINDOW_KEYWORDS, *args.game_keyword)
    pet = DesktopPet(args.frame_dir, args.size, args.x, args.y, args.mode, game_keywords)
    pet.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
