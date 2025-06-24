import asyncio
import pygame
import math

pygame.init()

# Perbaiki posisi dan ukuran canvas agar lebih simetris dan tidak terlalu ke bawah
WIDTH, HEIGHT = 1000, 700  # Tambah tinggi agar area gambar lebih luas
UI_HEIGHT = 200  # Tambah tinggi UI agar UI tidak menutupi canvas
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Aplikasi Gambar Transformasi")

canvas = pygame.Surface((WIDTH, HEIGHT - UI_HEIGHT))
canvas.fill((255, 255, 255))

font = pygame.font.Font(None, 24)
clock = pygame.time.Clock()

MODES = ["TITIK", "TITIK BERSAMBUNG", "GARIS", "PERSEGI", "LINGKARAN", "ELIPS", "WINDOW"]  # Tambah mode WINDOW

COLORS = {
    "Merah": (255, 0, 0), "Hijau": (0, 255, 0), "Biru": (0, 0, 255), "Kuning": (255, 255, 0),
    "Hitam": (0, 0, 0), "Putih": (255, 255, 255), "Ungu": (128, 0, 128), "Oranye": (255, 165, 0),
    "Coklat": (139, 69, 19), "Pink": (255, 192, 203), "Abu": (128, 128, 128), "Cyan": (0, 255, 255),
    "Lime": (0, 255, 128), "Emas": (255, 215, 0), "Biru Laut": (70, 130, 180),
    "Zaitun": (128, 128, 0), "Indigo": (75, 0, 130), "Salmon": (250, 128, 114), "Perak": (192, 192, 192)
}

ROTATION_OPTIONS = [45, 90, 120, 180]
thickness_options = [2, 4, 6, 8, 10, 12]

current_mode = "TITIK"
current_color = COLORS["Hitam"]
current_thickness = 2
transform_mode = None
selected_object = None
resizing = False
offset = (0, 0)

objects = []

window_rect = None  # Simpan window (x0, y0, x1, y1)
window_obj = None   # Simpan objek window (DrawableObject)
window_color = (0, 180, 255)
window_highlight = (0, 220, 255, 60)
window_select_color = (0, 120, 255)
windowed_color = (255, 0, 255)  # Warna objek yang di dalam window

clipping_requested = False

class DrawableObject:
    def __init__(self, mode, start, end, color, thickness):
        self.mode = mode
        self.start = start
        self.end = end
        self.color = color
        self.thickness = thickness

    def draw(self, surface):
        draw_preview(surface, self.mode, self.start, self.end, self.color, self.thickness)

    def get_bounds(self):
        if self.mode == "TITIK":
            r = self.thickness
            x, y = self.start
            return pygame.Rect(x - r, y - r, r * 2, r * 2)
        elif self.mode == "LINGKARAN":
            cx, cy = self.start
            r = int(math.hypot(self.end[0] - cx, self.end[1] - cy))
            return pygame.Rect(cx - r, cy - r, r * 2, r * 2)
        elif self.mode == "TITIK BERSAMBUNG":
            # treat as a small line
            x1, y1 = self.start
            x2, y2 = self.end
            minx, miny = min(x1, x2), min(y1, y2)
            maxx, maxy = max(x1, x2), max(y1, y2)
            return pygame.Rect(minx, miny, maxx - minx + 1, maxy - miny + 1)
        else:
            x1, y1 = self.start
            x2, y2 = self.end
            return pygame.Rect(min(x1,x2), min(y1,y2), abs(x2 - x1), abs(y2 - y1))

    def contains_point(self, pos):
        if self.mode == "TITIK":
            x, y = self.start
            return math.hypot(pos[0] - x, pos[1] - y) <= max(8, self.thickness + 2)
        elif self.mode == "LINGKARAN":
            cx, cy = self.start
            r = int(math.hypot(self.end[0] - cx, self.end[1] - cy))
            dist = math.hypot(pos[0] - cx, pos[1] - cy)
            return abs(dist - r) <= max(8, self.thickness + 2)
        elif self.mode == "TITIK BERSAMBUNG" or self.mode == "GARIS":
            # Cek jarak ke garis
            x1, y1 = self.start
            x2, y2 = self.end
            px, py = pos
            dx, dy = x2 - x1, y2 - y1
            if dx == dy == 0:
                return math.hypot(px - x1, py - y1) <= max(8, self.thickness + 2)
            t = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)
            t = max(0, min(1, t))
            nearest = (x1 + t * dx, y1 + t * dy)
            return math.hypot(px - nearest[0], py - nearest[1]) <= max(8, self.thickness + 2)
        else:
            return self.get_bounds().collidepoint(pos)

    def translate(self, dx, dy):
        self.start = (self.start[0] + dx, self.start[1] + dy)
        self.end = (self.end[0] + dx, self.end[1] + dy)

    def scale(self, fx, fy):
        bounds = self.get_bounds()
        center = bounds.center
        def scale_point(p):
            return (
                int(center[0] + (p[0] - center[0]) * fx),
                int(center[1] + (p[1] - center[1]) * fy)
            )
        self.start = scale_point(self.start)
        self.end = scale_point(self.end)

    def rotate(self, degrees):
        radians = math.radians(degrees)
        cx, cy = self.get_center()
        def rotate_point(px, py):
            dx, dy = px - cx, py - cy
            qx = cx + dx * math.cos(radians) - dy * math.sin(radians)
            qy = cy + dx * math.sin(radians) + dy * math.cos(radians)
            return int(qx), int(qy)
        self.start = rotate_point(*self.start)
        self.end = rotate_point(*self.end)

    def get_center(self):
        if self.mode == "LINGKARAN":
            return self.start
        else:
            return ((self.start[0] + self.end[0]) / 2, (self.start[1] + self.end[1]) / 2)

def is_inside_window(obj, win_rect):
    # Cek apakah seluruh bounding box objek ada di dalam window
    if not win_rect:
        return False
    bounds = obj.get_bounds()
    return win_rect.contains(bounds)

def cohen_sutherland_clip(xmin, ymin, xmax, ymax, x0, y0, x1, y1):
    # Implementasi Cohen-Sutherland untuk clipping garis
    INSIDE, LEFT, RIGHT, BOTTOM, TOP = 0, 1, 2, 4, 8
    def compute_out_code(x, y):
        code = INSIDE
        if x < xmin: code |= LEFT
        elif x > xmax: code |= RIGHT
        if y < ymin: code |= BOTTOM
        elif y > ymax: code |= TOP
        return code

    outcode0 = compute_out_code(x0, y0)
    outcode1 = compute_out_code(x1, y1)
    accept = False

    while True:
        if not (outcode0 | outcode1):
            accept = True
            break
        elif outcode0 & outcode1:
            break
        else:
            x, y = 0, 0
            outcode_out = outcode0 if outcode0 else outcode1
            if outcode_out & TOP:
                x = x0 + (x1 - x0) * (ymax - y0) / (y1 - y0)
                y = ymax
            elif outcode_out & BOTTOM:
                x = x0 + (x1 - x0) * (ymin - y0) / (y1 - y0)
                y = ymin
            elif outcode_out & RIGHT:
                y = y0 + (y1 - y0) * (xmax - x0) / (x1 - x0)
                x = xmax
            elif outcode_out & LEFT:
                y = y0 + (y1 - y0) * (xmin - x0) / (x1 - x0)
                x = xmin
            if outcode_out == outcode0:
                x0, y0 = int(x), int(y)
                outcode0 = compute_out_code(x0, y0)
            else:
                x1, y1 = int(x), int(y)
                outcode1 = compute_out_code(x1, y1)
    if accept:
        return (int(x0), int(y0)), (int(x1), int(y1))
    else:
        return None

def draw_ui():
    # Mode buttons (centered)
    mode_buttons = []
    total_mode_w = sum([font.size(mode)[0] + 30 for mode in MODES]) + (len(MODES) - 1) * 10
    x = (WIDTH - total_mode_w) // 2
    y = 10
    for mode in MODES:
        text = font.render(mode, True, (0, 0, 0))
        rect = pygame.Rect(x, y, text.get_width() + 30, 35)
        pygame.draw.rect(screen, (180, 180, 180) if current_mode != mode else (180, 220, 255), rect, border_radius=5)
        pygame.draw.rect(screen, (0, 0, 0), rect, 1, border_radius=5)
        screen.blit(text, (rect.x + 15, rect.y + 7))
        mode_buttons.append((rect, mode))
        x += rect.width + 10

    # Color buttons (centered)
    color_buttons = []
    color_btn_w = 35
    color_btn_h = 30
    total_color_w = len(COLORS) * color_btn_w + (len(COLORS) - 1) * 5
    x = (WIDTH - total_color_w) // 2
    y = 55
    for name, color in COLORS.items():
        rect = pygame.Rect(x, y, color_btn_w, color_btn_h)
        pygame.draw.rect(screen, color, rect)
        border = 3 if color == current_color else 1
        pygame.draw.rect(screen, (0, 0, 0), rect, border)
        color_buttons.append((rect, color))
        x += color_btn_w + 5

    # Transformasi dan ketebalan (sudah simetris)
    bg_width = 700
    bg_x = (WIDTH - bg_width) // 2
    pygame.draw.rect(screen, (220, 255, 220), (bg_x, 90, bg_width, 90), border_radius=10)

    # Transform buttons (centered horizontally in bg)
    labels = ["None", "Translasi", "Rotasi", "Skala"]
    btn_w, btn_h, btn_gap = 90, 30, 10
    total_w = len(labels) * btn_w + (len(labels) - 1) * btn_gap
    x = bg_x + (bg_width - total_w) // 2
    y = 100
    transform_buttons = []
    for label in labels:
        rect = pygame.Rect(x, y, btn_w, btn_h)
        pygame.draw.rect(screen, (180, 240, 180) if transform_mode == label else (200, 200, 200), rect, border_radius=5)
        pygame.draw.rect(screen, (0, 0, 0), rect, 1, border_radius=5)
        text = font.render(label, True, (0, 0, 0))
        text_rect = text.get_rect(center=rect.center)
        screen.blit(text, text_rect)
        transform_buttons.append((rect, label))
        x += btn_w + btn_gap

    # --- CLIPPING BUTTON (kanan tombol Skala) ---
    clip_btn = None
    if window_rect:
        btn_w_clip, btn_h_clip = 120, 32
        # Posisi: setelah tombol Skala
        last_btn_rect = transform_buttons[-1][0]
        x_clip = last_btn_rect.right + 16  # beri jarak 16px dari tombol Skala
        y_clip = last_btn_rect.y + (last_btn_rect.height - btn_h_clip) // 2
        rect = pygame.Rect(x_clip, y_clip, btn_w_clip, btn_h_clip)
        pygame.draw.rect(screen, (255, 200, 200), rect, border_radius=8)
        pygame.draw.rect(screen, (180, 0, 0), rect, 2, border_radius=8)
        text = font.render("CLIPPING", True, (0, 0, 0))
        text_rect = text.get_rect(center=rect.center)
        screen.blit(text, text_rect)
        clip_btn = rect

    # Rotasi derajat (KEMBALIKAN tombol derajat)
    rot_buttons = []
    if transform_mode == "Rotasi":
        rot_btn_w, rot_btn_h, rot_btn_gap = 50, 30, 10
        total_rot_w = len(ROTATION_OPTIONS) * rot_btn_w + (len(ROTATION_OPTIONS) - 1) * rot_btn_gap
        x3 = bg_x + (bg_width - total_rot_w) // 2
        y3 = 140  # DIBAWAH tombol transform, sejajar dengan ketebalan
        for deg in ROTATION_OPTIONS:
            rect = pygame.Rect(x3, y3, rot_btn_w, rot_btn_h)
            pygame.draw.rect(screen, (255, 230, 200), rect, border_radius=5)
            pygame.draw.rect(screen, (0, 0, 0), rect, 1)
            text = font.render(str(deg), True, (0, 0, 0))
            text_rect = text.get_rect(center=rect.center)
            screen.blit(text, text_rect)
            rot_buttons.append((rect, deg))
            x3 += rot_btn_w + rot_btn_gap

    # Ketebalan (centered di bawah transform, geser ke bawah jika mode rotasi)
    thickness_buttons = []
    btn_w2, btn_h2, btn_gap2 = 40, 30, 8
    total_w2 = len(thickness_options) * btn_w2 + (len(thickness_options) - 1) * btn_gap2
    if transform_mode == "Rotasi":
        y2 = 180  # Lebih ke bawah jika mode rotasi
    else:
        y2 = 140
    x2 = bg_x + (bg_width - total_w2) // 2
    for val in thickness_options:
        rect = pygame.Rect(x2, y2, btn_w2, btn_h2)
        pygame.draw.rect(screen, (180, 255, 255) if val == current_thickness else (200, 200, 200), rect, border_radius=5)
        pygame.draw.rect(screen, (0, 0, 0), rect, 1, border_radius=5)
        text = font.render(str(val), True, (0, 0, 0))
        text_rect = text.get_rect(center=rect.center)
        screen.blit(text, text_rect)
        thickness_buttons.append((rect, val))
        x2 += btn_w2 + btn_gap2

    return mode_buttons, color_buttons, transform_buttons, thickness_buttons, rot_buttons, clip_btn

def draw_preview(surface, mode, start, end, color, thickness):
    if mode == "GARIS":
        pygame.draw.line(surface, color, start, end, thickness)
    elif mode == "PERSEGI":
        x0, y0 = start
        x1, y1 = end
        rect = pygame.Rect(min(x0,x1), min(y0,y1), abs(x1 - x0), abs(y1 - y0))
        pygame.draw.rect(surface, color, rect, thickness)
    elif mode == "LINGKARAN":
        radius = int(math.hypot(end[0]-start[0], end[1]-start[1]))
        pygame.draw.circle(surface, color, start, radius, thickness)
    elif mode == "ELIPS":
        cx = (start[0] + end[0]) // 2
        cy = (start[1] + end[1]) // 2
        rx = abs(end[0] - start[0]) // 2
        ry = abs(end[1] - start[1]) // 2
        rect = pygame.Rect(cx - rx, cy - ry, rx * 2, ry * 2)
        pygame.draw.ellipse(surface, color, rect, thickness)
    elif mode == "TITIK":
        pygame.draw.circle(surface, color, start, thickness // 2 or 1)
    elif mode == "TITIK BERSAMBUNG":
        pygame.draw.line(surface, color, start, end, thickness)

   

# Tambahkan highlight biru pada objek yang dipilih
def draw_all_objects(surface, selected_obj=None):
    global cursor_set
    cursor_set = False
    # Gambar window jika ada
    if window_obj:
        bounds = window_obj.get_bounds()
        # Hapus highlight window, hanya gambar border window saja
        pygame.draw.rect(surface, window_color, bounds, 3, border_radius=8)
    # Gambar objek, beri warna khusus jika beririsan dengan window
    for obj in objects:
        if window_rect and obj is not window_obj and obj.get_bounds().colliderect(window_rect):
            # Gambar objek dengan warna windowed_color
            draw_preview(surface, obj.mode, obj.start, obj.end, windowed_color, obj.thickness)
        else:
            obj.draw(surface)
        # Perbaikan: hanya gambar highlight jika bukan objek window
        if obj is not window_obj and obj is selected_obj:
            bounds = obj.get_bounds()
            # Highlight biru transparan seperti Paint
            highlight_color = (0, 120, 215, 80)  # biru muda transparan
            highlight_surf = pygame.Surface((bounds.width+16, bounds.height+16), pygame.SRCALPHA)
            pygame.draw.rect(highlight_surf, highlight_color, (0, 0, bounds.width+16, bounds.height+16), border_radius=8)
            surface.blit(highlight_surf, (bounds.left-8, bounds.top-8))
            # Border biru tebal
            pygame.draw.rect(surface, (0, 120, 215), bounds.inflate(8, 8), 3, border_radius=8)
            # 8 handle putih dengan border abu seperti Paint
            if transform_mode == "Skala":
                cx, cy = bounds.center
                handles = [
                    bounds.topleft,
                    ((bounds.left + bounds.right)//2, bounds.top),
                    bounds.topright,
                    (bounds.right, (bounds.top + bounds.bottom)//2),
                    bounds.bottomright,
                    ((bounds.left + bounds.right)//2, bounds.bottom),
                    bounds.bottomleft,
                    (bounds.left, (bounds.top + bounds.bottom)//2)
                ]
                mouse_pos = pygame.mouse.get_pos()
                mx, my = mouse_pos[0], mouse_pos[1] - UI_HEIGHT
                for i, pt in enumerate(handles):
                    # Perkecil handle agar lebih presisi
                    pygame.draw.rect(surface, (255,255,255), (pt[0]-5, pt[1]-5, 10, 10), border_radius=2)
                    pygame.draw.rect(surface, (160,160,160), (pt[0]-5, pt[1]-5, 10, 10), 2, border_radius=2)
                    handle_rect = pygame.Rect(pt[0]-7, pt[1]-7, 14, 14)
                    if handle_rect.collidepoint((mx, my)):
                        # Ubah kursor sesuai handle
                        if i in [0, 4]:
                            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_SIZENWSE)
                        elif i in [2, 6]:
                            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_SIZENESW)
                        elif i in [1, 5]:
                            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_SIZENS)
                        elif i in [3, 7]:
                            pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_SIZEWE)
                        cursor_set = True
    # Reset kursor jika tidak di handle
    if not cursor_set:
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

async def main():
    global current_mode, current_color, current_thickness, transform_mode, selected_object, resizing
    global window_rect, window_obj, clipping_requested
    drawing = False
    start_pos = None
    last_pos = None
    dragging = False
    drag_start = None
    scale_ref = None
    window_drawing = False
    window_start = None

    while True:
        screen.fill((230, 230, 230))
        canvas.fill((255, 255, 255))
        draw_all_objects(canvas, selected_obj=selected_object)
        screen.blit(canvas, (0, UI_HEIGHT))

        # Unpack clip_btn dari draw_ui
        mode_btns, color_btns, transform_btns, thickness_btns, rot_btns, clip_btn = draw_ui()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return

            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = event.pos
                if my < UI_HEIGHT:
                    for rect, mode in mode_btns:
                        if rect.collidepoint((mx, my)):
                            current_mode = mode
                            transform_mode = "None"
                            selected_object = None
                            resizing = False
                            dragging = False
                    for rect, color in color_btns:
                        if rect.collidepoint((mx, my)):
                            current_color = color
                    for rect, label in transform_btns:
                        if rect.collidepoint((mx, my)):
                            transform_mode = label
                            selected_object = None
                            resizing = False
                            dragging = False
                    for rect, thick in thickness_btns:
                        if rect.collidepoint((mx, my)):
                            current_thickness = thick
                    for rect, deg in rot_btns:  # <-- perbaiki: harusnya rot_btns, bukan rot_buttons
                        if rect.collidepoint((mx, my)) and selected_object and transform_mode == "Rotasi":
                            selected_object.rotate(deg)
                            canvas.fill((255,255,255))
                            draw_all_objects(canvas, selected_obj=selected_object)
                            transform_mode = "Rotasi"
                    # --- CLIPPING BUTTON (fix area) ---
                    if clip_btn and clip_btn.collidepoint((mx, my)):
                        clipping_requested = True
                else:
                    pos = (mx, my - UI_HEIGHT)
                    # --- WINDOW MODE ---
                    if current_mode == "WINDOW":
                        window_drawing = True
                        window_start = pos
                    if transform_mode == "Skala":
                        selected_object = None
                        for obj in reversed(objects):
                            if obj.contains_point(pos):
                                selected_object = obj
                                drag_start = pos
                                resizing = False
                                bounds = obj.get_bounds()
                                cx, cy = bounds.center
                                handles = [
                                    bounds.topleft,
                                    ((bounds.left + bounds.right)//2, bounds.top),
                                    bounds.topright,
                                    (bounds.right, (bounds.top + bounds.bottom)//2),
                                    bounds.bottomright,
                                    ((bounds.left + bounds.right)//2, bounds.bottom),
                                    bounds.bottomleft,
                                    (bounds.left, (bounds.top + bounds.bottom)//2)
                                ]
                                found_handle = False
                                for i, handle in enumerate(handles):
                                    handle_rect = pygame.Rect(handle[0]-6, handle[1]-6, 12, 12)
                                    if handle_rect.collidepoint(pos):
                                        resizing = True
                                        anchor = handles[(i+4)%8]
                                        scale_axis = None
                                        if selected_object.mode == "LINGKARAN":
                                            if i in [1, 5]:
                                                scale_axis = 'y'
                                            elif i in [3, 7]:
                                                scale_axis = 'x'
                                            else:
                                                scale_axis = None
                                        else:
                                            if i % 2 == 1:
                                                if i in [1, 5]:
                                                    scale_axis = 'y'
                                                else:
                                                    scale_axis = 'x'
                                            scale_ref = (anchor, handle, obj.start, obj.end, scale_axis)
                                            found_handle = True
                                            break
                                # Jika lingkaran dan tidak di handle, cek tepi bounding box
                                if selected_object.mode == "LINGKARAN" and not found_handle:
                                    # Perbesar margin tepi agar lebih mudah scaling
                                    edge_margin = 60
                                    edge_rect = bounds.inflate(edge_margin*2, edge_margin*2)
                                    inner_rect = bounds.inflate(-edge_margin*2, -edge_margin*2)
                                    # Cek jika mouse di tepi bounding box (antara edge_rect dan inner_rect)
                                    if edge_rect.collidepoint(pos) and not inner_rect.collidepoint(pos):
                                        resizing = True
                                        # Cari anchor terdekat dari 8 handle
                                        min_dist = float('inf')
                                        anchor = None
                                        handle = None
                                        for pt in handles:
                                            d = math.hypot(pos[0]-pt[0], pos[1]-pt[1])
                                            if d < min_dist:
                                                min_dist = d
                                                handle = pt
                                        idx = handles.index(handle)
                                        anchor = handles[(idx+4)%8]
                                        scale_axis = None
                                        if idx in [1, 5]:
                                            scale_axis = 'y'
                                        elif idx in [3, 7]:
                                            scale_axis = 'x'
                                        scale_ref = (anchor, handle, obj.start, obj.end, scale_axis)
                                break
                    elif transform_mode in ["Translasi", "Rotasi"]:
                        selected_object = None
                        for obj in reversed(objects):
                            if obj.contains_point(pos):
                                selected_object = obj
                                drag_start = pos
                                if transform_mode == "Translasi":
                                    dragging = True
                                break
                        if not selected_object:
                            dragging = False
                    elif transform_mode == "None":
                        selected_object = None
                        if current_mode == "TITIK":
                            # Titik: gambar dan simpan objek, lalu update canvas di layar
                            obj = DrawableObject("TITIK", pos, pos, current_color, current_thickness)
                            objects.append(obj)
                            obj.draw(canvas)
                            screen.blit(canvas, (0, UI_HEIGHT))
                        elif current_mode == "TITIK BERSAMBUNG":
                            if not drawing:
                                last_pos = pos
                                drawing = True
                            else:
                                obj = DrawableObject("TITIK BERSAMBUNG", last_pos, pos, current_color, current_thickness)
                                objects.append(obj)
                                obj.draw(canvas)
                                screen.blit(canvas, (0, UI_HEIGHT))
                                last_pos = pos
                        elif current_mode in ["GARIS", "PERSEGI", "LINGKARAN", "ELIPS"]:
                            start_pos = pos
                            drawing = True

            elif event.type == pygame.MOUSEBUTTONUP:
                mx, my = event.pos
                pos = (mx, my - UI_HEIGHT)
                # --- WINDOW MODE ---
                if window_drawing and window_start:
                    x0, y0 = window_start
                    x1, y1 = pos
                    rect = pygame.Rect(min(x0, x1), min(y0, y1), abs(x1 - x0), abs(y1 - y0))
                    window_rect = rect
                    window_obj = DrawableObject("PERSEGI", rect.topleft, rect.bottomright, window_color, 3)
                    window_drawing = False
                    window_start = None
                    # --- CLIPPING OTOMATIS SETELAH WINDOW DIBUAT ---
                    if window_rect:
                        xmin, ymin = window_rect.left, window_rect.top
                        xmax, ymax = window_rect.right, window_rect.bottom
                        new_objects = []
                        for obj in objects:
                            if obj.mode == "GARIS":
                                x0, y0 = obj.start
                                x1, y1 = obj.end
                                clipped = cohen_sutherland_clip(xmin, ymin, xmax, ymax, x0, y0, x1, y1)
                                if clipped:
                                    obj.start, obj.end = clipped
                                    new_objects.append(obj)
                                # Jika tidak ada bagian di window, hapus
                            elif obj.mode in ["PERSEGI", "LINGKARAN", "ELIPS"]:
                                # Hapus jika bounding box tidak overlap window
                                if window_rect.colliderect(obj.get_bounds()):
                                    new_objects.append(obj)
                            else:
                                # Titik: hapus jika di luar window
                                if window_rect.collidepoint(obj.start):
                                    new_objects.append(obj)
                        objects[:] = new_objects
                        selected_object = None
                elif drawing and start_pos and current_mode in ["GARIS", "PERSEGI", "LINGKARAN", "ELIPS"]:
                    end = pos
                    obj = DrawableObject(current_mode, start_pos, end, current_color, current_thickness)
                    objects.append(obj)
                    obj.draw(canvas)
                    drawing = False
                    start_pos = None
                elif drawing and current_mode == "TITIK BERSAMBUNG":
                    drawing = False
                    last_pos = None
                # Perbaikan: hanya reset resizing dan scale_ref jika memang sedang resizing
                if resizing:
                    resizing = False
                    scale_ref = None
                dragging = False
                drag_start = None

            elif event.type == pygame.MOUSEMOTION:
                mx, my = event.pos
                pos = (mx, my - UI_HEIGHT)
                # --- WINDOW MODE PREVIEW ---
                if window_drawing and window_start:
                    preview = canvas.copy()
                    draw_preview(preview, "PERSEGI", window_start, pos, window_color, 3)
                    screen.blit(preview, (0, UI_HEIGHT))
                elif drawing and current_mode == "TITIK BERSAMBUNG" and last_pos:
                    # Simpan objek dan gambar langsung ke canvas, bukan hanya preview
                    obj = DrawableObject("TITIK BERSAMBUNG", last_pos, pos, current_color, current_thickness)
                    objects.append(obj)
                    obj.draw(canvas)
                    last_pos = pos
                    screen.blit(canvas, (0, UI_HEIGHT))
                elif drawing and start_pos and current_mode in ["GARIS", "PERSEGI", "LINGKARAN", "ELIPS"]:
                    preview = canvas.copy()
                    draw_preview(preview, current_mode, start_pos, pos, current_color, current_thickness)
                    screen.blit(preview, (0, UI_HEIGHT))
                elif dragging and selected_object and transform_mode == "Translasi" and drag_start:
                    dx = pos[0] - drag_start[0]
                    dy = pos[1] - drag_start[1]
                    selected_object.translate(dx, dy)
                    drag_start = pos
                    canvas.fill((255,255,255))
                    draw_all_objects(canvas, selected_obj=selected_object)
                # Perbaikan utama: scaling tetap aktif selama resizing True, tidak peduli posisi mouse
                elif resizing and selected_object and transform_mode == "Skala" and scale_ref:
                    anchor, handle, orig_start, orig_end, scale_axis = scale_ref
                    def dist(a, b):
                        return math.hypot(a[0]-b[0], a[1]-b[1])
                    orig_vec = (handle[0] - anchor[0], handle[1] - anchor[1])
                    new_vec = (pos[0] - anchor[0], pos[1] - anchor[1])
                    if selected_object.mode == "LINGKARAN":
                        cx, cy = anchor
                        # --- Perbaikan scaling lingkaran di pojok: proporsional ---
                        if scale_axis == 'x':
                            fx = (new_vec[0] / orig_vec[0]) if orig_vec[0] != 0 else 1
                            fy = 1
                        elif scale_axis == 'y':
                            fx = 1
                            fy = (new_vec[1] / orig_vec[1]) if orig_vec[1] != 0 else 1
                        else:
                            # Pojok: proporsional, gunakan rata-rata perubahan X dan Y
                            scale = (dist((anchor[0], anchor[1]), pos) / dist((anchor[0], anchor[1]), handle)) if dist((anchor[0], anchor[1]), handle) != 0 else 1
                            fx = fy = scale
                        r_x = (orig_end[0] - cx) * fx
                        r_y = (orig_end[1] - cy) * fy
                        selected_object.end = (int(cx + r_x), int(cy + r_y))
                    elif selected_object.mode == "GARIS":
                        # --- Perbaikan scaling garis di pojok: update end sesuai drag, anchor tetap ---
                        if scale_axis is None:
                            # Pojok: geser end ke posisi mouse, start tetap di anchor
                            if anchor == orig_start:
                                selected_object.start = anchor
                                selected_object.end = pos
                            else:
                                selected_object.start = pos
                                selected_object.end = anchor
                        else:
                            # Sisi: scaling seperti biasa
                            if scale_axis == 'x':
                                fx = (new_vec[0] / orig_vec[0]) if orig_vec[0] != 0 else 1
                                fy = 1
                            elif scale_axis == 'y':
                                fx = 1
                                fy = (new_vec[1] / orig_vec[1]) if orig_vec[1] != 0 else 1
                            else:
                                fx = (new_vec[0] / orig_vec[0]) if orig_vec[0] != 0 else 1
                                fy = (new_vec[1] / orig_vec[1]) if orig_vec[1] != 0 else 1
                            selected_object.start = (
                                int(anchor[0] + (orig_start[0] - anchor[0]) * fx),
                                int(anchor[1] + (orig_start[1] - anchor[1]) * fy)
                            )
                            selected_object.end = (
                                int(anchor[0] + (orig_end[0] - anchor[0]) * fx),
                                int(anchor[1] + (orig_end[1] - anchor[1]) * fy)
                            )
                    else:
                        if scale_axis == 'x':
                            fx = (new_vec[0] / orig_vec[0]) if orig_vec[0] != 0 else 1
                            fy = 1
                        elif scale_axis == 'y':
                            fx = 1
                            fy = (new_vec[1] / orig_vec[1]) if orig_vec[1] != 0 else 1
                        else:
                            fx = (new_vec[0] / orig_vec[0]) if orig_vec[0] != 0 else 1
                            fy = (new_vec[1] / orig_vec[1]) if orig_vec[1] != 0 else 1
                        if fx > 0.05 and fy > 0.05:
                            selected_object.start = (
                                int(anchor[0] + (orig_start[0] - anchor[0]) * fx),
                                int(anchor[1] + (orig_start[1] - anchor[1]) * fy)
                            )
                            selected_object.end = (
                                int(anchor[0] + (orig_end[0] - anchor[0]) * fx),
                                int(anchor[1] + (orig_end[1] - anchor[1]) * fy)
                            )
                    drag_start = pos
                    canvas.fill((255,255,255))
                    draw_all_objects(canvas, selected_obj=selected_object)

        # --- CLIPPING LOGIC ---
        if clipping_requested and window_rect:
            xmin, ymin = window_rect.left, window_rect.top
            xmax, ymax = window_rect.right, window_rect.bottom
            new_objects = []
            for obj in objects:
                if obj.mode == "GARIS":
                    x0, y0 = obj.start
                    x1, y1 = obj.end
                    clipped = cohen_sutherland_clip(xmin, ymin, xmax, ymax, x0, y0, x1, y1)
                    if clipped:
                        obj.start, obj.end = clipped
                        new_objects.append(obj)
                elif obj.mode == "PERSEGI":
                    # Clipping persegi: potong ke window
                    x0, y0 = obj.start
                    x1, y1 = obj.end
                    left = max(min(x0, x1), xmin)
                    right = min(max(x0, x1), xmax)
                    top = max(min(y0, y1), ymin)
                    bottom = min(max(y0, y1), ymax)
                    if left < right and top < bottom:
                        obj.start = (left, top)
                        obj.end = (right, bottom)
                        new_objects.append(obj)
                elif obj.mode == "LINGKARAN":
                    # Clipping lingkaran: crop ke window (bounding box)
                    cx, cy = obj.start
                    r = int(math.hypot(obj.end[0] - cx, obj.end[1] - cy))
                    # Bounding box lingkaran
                    left = max(cx - r, xmin)
                    right = min(cx + r, xmax)
                    top = max(cy - r, ymin)
                    bottom = min(cy + r, ymax)
                    # Jika masih ada area tersisa
                    if left < right and top < bottom:
                        # Buat lingkaran baru dengan bounding box hasil clipping
                        # Ambil center baru dan radius baru (fit dalam window)
                        new_cx = max(min(cx, xmax), xmin)
                        new_cy = max(min(cy, ymax), ymin)
                        new_r = min(right - left, bottom - top) // 2
                        if new_r > 0:
                            obj.start = (new_cx, new_cy)
                            obj.end = (new_cx + new_r, new_cy)
                            new_objects.append(obj)
                elif obj.mode == "ELIPS":
                    # Clipping elips: crop ke window (bounding box)
                    x0, y0 = obj.start
                    x1, y1 = obj.end
                    left = max(min(x0, x1), xmin)
                    right = min(max(x0, x1), xmax)
                    top = max(min(y0, y1), ymin)
                    bottom = min(max(y0, y1), ymax)
                    if left < right and top < bottom:
                        obj.start = (left, top)
                        obj.end = (right, bottom)
                        new_objects.append(obj)
                else:
                    # Titik: hapus jika di luar window
                    if window_rect.collidepoint(obj.start):
                        new_objects.append(obj)
            objects[:] = new_objects
            clipping_requested = False
            selected_object = None

        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)

asyncio.run(main())
if __name__ == "__main__":
    pass



