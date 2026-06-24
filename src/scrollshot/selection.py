from __future__ import annotations

from dataclasses import dataclass
import tkinter as tk
from typing import Optional, Tuple

from PIL import Image, ImageGrab, ImageTk


@dataclass(frozen=True)
class Selection:
    pixel_box: Tuple[int, int, int, int]
    point_box: Tuple[int, int, int, int]
    scale_x: float
    scale_y: float

    @property
    def center_point(self) -> Tuple[int, int]:
        left, top, right, bottom = self.point_box
        return ((left + right) // 2, (top + bottom) // 2)


class RegionSelector:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.withdraw()
        self.screen_w = self.root.winfo_screenwidth()
        self.screen_h = self.root.winfo_screenheight()
        self.screenshot = ImageGrab.grab().convert("RGB")
        self.scale_x = self.screenshot.width / self.screen_w
        self.scale_y = self.screenshot.height / self.screen_h
        self.result: Optional[Selection] = None
        self.start: Optional[Tuple[int, int]] = None
        self.rect_id: Optional[int] = None

    def run(self) -> Optional[Selection]:
        win = tk.Toplevel(self.root)
        win.attributes("-fullscreen", True)
        win.attributes("-topmost", True)
        win.configure(cursor="crosshair")
        win.title("Scroll Shot Region Selection")

        display = self.screenshot.resize((self.screen_w, self.screen_h), Image.Resampling.LANCZOS)
        dark = Image.blend(display, Image.new("RGB", display.size, "black"), 0.35)
        self.photo = ImageTk.PhotoImage(dark)

        canvas = tk.Canvas(win, width=self.screen_w, height=self.screen_h, highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True)
        canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
        canvas.create_text(
            self.screen_w // 2,
            34,
            text="Drag around the scrollable area. Press Esc to cancel.",
            fill="white",
            font=("Helvetica", 18, "bold"),
        )

        def on_down(event: tk.Event) -> None:
            self.start = (event.x, event.y)
            if self.rect_id is not None:
                canvas.delete(self.rect_id)
            self.rect_id = canvas.create_rectangle(
                event.x,
                event.y,
                event.x,
                event.y,
                outline="#44d7ff",
                width=3,
            )

        def on_drag(event: tk.Event) -> None:
            if self.start is None or self.rect_id is None:
                return
            x0, y0 = self.start
            canvas.coords(self.rect_id, x0, y0, event.x, event.y)

        def on_up(event: tk.Event) -> None:
            if self.start is None:
                return
            x0, y0 = self.start
            x1, y1 = event.x, event.y
            left, right = sorted((max(0, x0), min(self.screen_w, x1)))
            top, bottom = sorted((max(0, y0), min(self.screen_h, y1)))
            if right - left < 40 or bottom - top < 40:
                return
            pixel_box = (
                round(left * self.scale_x),
                round(top * self.scale_y),
                round(right * self.scale_x),
                round(bottom * self.scale_y),
            )
            self.result = Selection(pixel_box, (left, top, right, bottom), self.scale_x, self.scale_y)
            win.destroy()

        def on_escape(_: tk.Event) -> None:
            self.result = None
            win.destroy()

        canvas.bind("<ButtonPress-1>", on_down)
        canvas.bind("<B1-Motion>", on_drag)
        canvas.bind("<ButtonRelease-1>", on_up)
        win.bind("<Escape>", on_escape)
        win.focus_force()
        self.root.wait_window(win)
        self.root.destroy()
        return self.result


def choose_region() -> Optional[Selection]:
    return RegionSelector().run()
