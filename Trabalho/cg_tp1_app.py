import sys
import math
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
import pygame as pg # type: ignore
import numpy as np # type: ignore

# =============================
# Configurações gerais da janela
# =============================
W, H = 1200, 720
PANEL_W = 280     # largura do painel lateral
CANVAS_W = W - PANEL_W
CANVAS_H = H
FPS = 60

BG = (18, 18, 20)
PANEL_BG = (28, 28, 32)
TEXT = (230, 230, 235)
GRID = (44, 44, 48)
PIX = (240, 240, 240)
SEL_RECT = (100, 200, 255)
HILITE = (255, 180, 0)
OK = (90, 210, 120)
BAD = (230, 90, 90)

# =============================
# Utilidades matemáticas (2D homogêneo)
# =============================
def mat_identity():
    return np.eye(3, dtype=float)

def mat_translate(tx, ty):
    M = np.eye(3, dtype=float)
    M[0, 2] = tx
    M[1, 2] = ty
    return M

def mat_scale(sx, sy):
    M = np.eye(3, dtype=float)
    M[0, 0] = sx
    M[1, 1] = sy
    return M

def mat_rotate_deg(theta):
    t = math.radians(theta)
    c, s = math.cos(t), math.sin(t)
    M = np.eye(3, dtype=float)
    M[0, 0] = c
    M[0, 1] = -s
    M[1, 0] = s
    M[1, 1] = c
    return M

def apply_T(M, p):
    v = np.array([p[0], p[1], 1.0], dtype=float)
    r = M @ v
    return (float(r[0]), float(r[1]))

def centroid_pts(pts: List[Tuple[float, float]]) -> Tuple[float, float]:
    if not pts:
        return (0.0, 0.0)
    x = sum(p[0] for p in pts) / len(pts)
    y = sum(p[1] for p in pts) / len(pts)
    return (x, y)

def T_about_point(M, T, pivot):
    px, py = pivot
    return mat_translate(px, py) @ T @ mat_translate(-px, -py) @ M

# =============================
# Estruturas de dados
# =============================
@dataclass
class Entity:
    selected: bool = False

    def get_points(self) -> List[Tuple[float, float]]:
        return []

    def apply_transform(self, M: np.ndarray):
        pass

@dataclass
class Point(Entity):
    p: Tuple[float, float] = (0.0, 0.0)

    def get_points(self):
        return [self.p]

    def apply_transform(self, M):
        self.p = apply_T(M, self.p)

@dataclass
class Line(Entity):
    a: Tuple[float, float] = (0.0, 0.0)
    b: Tuple[float, float] = (0.0, 0.0)

    def get_points(self):
        return [self.a, self.b]

    def apply_transform(self, M):
        self.a = apply_T(M, self.a)
        self.b = apply_T(M, self.b)

@dataclass
class Polygon(Entity):
    verts: List[Tuple[float, float]] = field(default_factory=list)

    def get_points(self):
        return list(self.verts)

    def apply_transform(self, M):
        self.verts = [apply_T(M, p) for p in self.verts]

# =============================
# Rasterização (retas e circunferência)
# =============================
def put_pixel(surface, x, y, color=PIX):
    if 0 <= x < CANVAS_W and 0 <= y < CANVAS_H:
        surface.set_at((int(x), int(y)), color)

def draw_line_dda(surface, p0, p1, color=PIX):
    x0, y0 = p0
    x1, y1 = p1
    dx = x1 - x0
    dy = y1 - y0
    steps = int(max(abs(dx), abs(dy)))
    if steps == 0:
        put_pixel(surface, round(x0), round(y0), color)
        return
    x_inc = dx / steps
    y_inc = dy / steps
    x, y = x0, y0
    for _ in range(steps + 1):
        put_pixel(surface, round(x), round(y), color)
        x += x_inc
        y += y_inc

def draw_line_bresenham(surface, p0, p1, color=PIX):
    x0, y0 = map(int, map(round, p0))
    x1, y1 = map(int, map(round, p1))
    steep = abs(y1 - y0) > abs(x1 - x0)
    if steep:
        x0, y0 = y0, x0
        x1, y1 = y1, x1
    if x0 > x1:
        x0, x1 = x1, x0
        y0, y1 = y1, y0
    dx = x1 - x0
    dy = abs(y1 - y0)
    err = dx // 2
    ystep = 1 if y0 < y1 else -1
    y = y0
    for x in range(x0, x1 + 1):
        if steep:
            put_pixel(surface, y, x, color)
        else:
            put_pixel(surface, x, y, color)
        err -= dy
        if err < 0:
            y += ystep
            err += dx

def draw_circle_bresenham(surface, center, radius, color=PIX):
    cx, cy = map(int, map(round, center))
    x = 0
    y = int(round(radius))
    d = 3 - 2 * radius
    while y >= x:
        for px, py in [
            (cx + x, cy + y),
            (cx - x, cy + y),
            (cx + x, cy - y),
            (cx - x, cy - y),
            (cx + y, cy + x),
            (cx - y, cy + x),
            (cx + y, cy - x),
            (cx - y, cy - x),
        ]:
            put_pixel(surface, px, py, color)
        x += 1
        if d > 0:
            y -= 1
            d = d + 4 * (x - y) + 10
        else:
            d = d + 4 * x + 6

# =============================
# Recorte de linhas (Cohen-Sutherland / Liang-Barsky)
# =============================
INSIDE, LEFT, RIGHT, BOTTOM, TOP = 0, 1, 2, 4, 8

def _region_code(x, y, xmin, ymin, xmax, ymax):
    code = INSIDE
    if x < xmin:
        code |= LEFT
    elif x > xmax:
        code |= RIGHT
    if y < ymin:  # topo da tela
        code |= TOP
    elif y > ymax:
        code |= BOTTOM
    return code

def cohen_sutherland_clip(p0, p1, rect):
    xmin, ymin, xmax, ymax = rect
    x0, y0 = p0
    x1, y1 = p1
    code0 = _region_code(x0, y0, xmin, ymin, xmax, ymax)
    code1 = _region_code(x1, y1, xmin, ymin, xmax, ymax)
    accept = False
    while True:
        if not (code0 | code1):
            accept = True
            break
        elif code0 & code1:
            break
        else:
            outcode = code0 if code0 else code1
            if outcode & TOP:
                x = x0 + (x1 - x0) * (ymin - y0) / (y1 - y0)
                y = ymin
            elif outcode & BOTTOM:
                x = x0 + (x1 - x0) * (ymax - y0) / (y1 - y0)
                y = ymax
            elif outcode & RIGHT:
                y = y0 + (y1 - y0) * (xmax - x0) / (x1 - x0)
                x = xmax
            else:  # LEFT
                y = y0 + (y1 - y0) * (xmin - x0) / (x1 - x0)
                x = xmin
            if outcode == code0:
                x0, y0 = x, y
                code0 = _region_code(x0, y0, xmin, ymin, xmax, ymax)
            else:
                x1, y1 = x, y
                code1 = _region_code(x1, y1, xmin, ymin, xmax, ymax)
    if accept:
        return (x0, y0), (x1, y1)
    return None

def liang_barsky_clip(p0, p1, rect):
    xmin, ymin, xmax, ymax = rect
    x0, y0 = p0
    x1, y1 = p1
    dx, dy = x1 - x0, y1 - y0
    p = [-dx, dx, -dy, dy]
    q = [x0 - xmin, xmax - x0, y0 - ymin, ymax - y0]
    u1, u2 = 0.0, 1.0
    for pi, qi in zip(p, q):
        if pi == 0:
            if qi < 0:
                return None
        else:
            r = -qi / pi
            if pi < 0:
                if r > u2:
                    return None
                if r > u1:
                    u1 = r
            else:
                if r < u1:
                    return None
                if r < u2:
                    u2 = r
    nx0, ny0 = x0 + u1 * dx, y0 + u1 * dy
    nx1, ny1 = x0 + u2 * dx, y0 + u2 * dy
    return (nx0, ny0), (nx1, ny1)

# =============================
# UI: Botões e Numpad
# =============================
@dataclass
class Button:
    rect: pg.Rect
    label: str
    tag: str
    active: bool = False

    def draw(self, surf, font):
        pg.draw.rect(
            surf,
            (60, 60, 66) if not self.active else (90, 110, 160),
            self.rect,
            border_radius=8,
        )
        txt = font.render(self.label, True, TEXT)
        surf.blit(txt, txt.get_rect(center=self.rect.center))

    def hit(self, pos):
        return self.rect.collidepoint(pos)

class Numpad:
    """Numpad on-screen simples para inserir números com clique (inclui ponto e sinal)."""

    def __init__(self, x, y, w=240, h=320):
        self.rect = pg.Rect(x, y, w, h)
        self.value = ""
        self.visible = False
        self.buttons: List[Button] = []
        labels = [
            "7",
            "8",
            "9",
            "4",
            "5",
            "6",
            "1",
            "2",
            "3",
            "+/-",
            "0",
            ".",
            "OK",
            "C",
            "<-",
        ]
        cols = 3
        rows = 5
        bw = (w - 20) // cols
        bh = (h - 50) // rows
        idx = 0
        for r in range(rows):
            for c in range(cols):
                bx = x + 10 + c * bw
                by = y + 40 + r * bh
                self.buttons.append(
                    Button(pg.Rect(bx, by, bw - 8, bh - 8), labels[idx], labels[idx])
                )
                idx += 1

    def open(self, initial=""):
        self.value = initial
        self.visible = True

    def close(self):
        self.visible = False

    def draw(self, surf, font):
        if not self.visible:
            return
        pg.draw.rect(surf, (36, 36, 40), self.rect, border_radius=10)
        title = font.render("Digite valor", True, TEXT)
        surf.blit(title, (self.rect.x + 10, self.rect.y + 10))
        box = pg.Rect(
            self.rect.x + 10,
            self.rect.y + 10 + title.get_height() + 6,
            self.rect.w - 20,
            30,
        )
        pg.draw.rect(surf, (22, 22, 26), box, border_radius=6)
        valtxt = font.render(
            self.value if self.value else " ",
            True,
            OK if self.value else TEXT,
        )
        surf.blit(valtxt, (box.x + 6, box.y + 6))
        for b in self.buttons:
            b.draw(surf, font)

    def handle_click(self, pos) -> Optional[Tuple[str, Optional[float]]]:
        """Retorna (action, number?) quando um botão é clicado. 'OK' retorna número (float)."""
        if not self.visible:
            return None
        for b in self.buttons:
            if b.hit(pos):
                tag = b.tag
                if tag in [str(i) for i in range(10)]:
                    self.value += tag
                elif tag == ".":
                    if "." not in self.value:
                        self.value = self.value + "." if self.value else "0."
                elif tag == "<-":
                    self.value = self.value[:-1]
                elif tag == "C":
                    self.value = ""
                elif tag == "+/-":
                    if self.value.startswith("-"):
                        self.value = self.value[1:]
                    else:
                        self.value = "-" + self.value if self.value else "-"
                elif tag == "OK":
                    try:
                        num = float(self.value)
                        self.close()
                        return ("OK", num)
                    except:
                        self.value = ""
                        return ("ERR", None)
                return (tag, None)
        return None

# =============================
# Estados do app
# =============================
class Mode:
    SELECT = "Selecionar"
    ADD_POINT = "Add Ponto"
    ADD_LINE = "Add Reta"
    ADD_POLY = "Add Políg."
    DRAW_CIRCLE = "Circ Bres."
    TRANSFORM = "Transformar"
    CLIP_WINDOW = "Janela Recorte"


class LineAlgo:
    DDA = "DDA"
    BRES = "Bresenham"


class ClipAlgo:
    COHEN = "Cohen-Suth"
    LIANG = "Liang-Barsky"


# =============================
# Aplicação principal
# =============================
class App:
    def __init__(self):
        pg.init()
        pg.display.set_caption(
            "CG TP1 - Canvas, Rasterização, Transformações e Recorte"
        )
        self.screen = pg.display.set_mode((W, H))
        self.clock = pg.time.Clock()
        self.font = pg.font.SysFont("consolas", 16)
        self.big = pg.font.SysFont("consolas", 20, bold=True)

        # Entidades
        self.entities: List[Entity] = []
        self.temp_line_start: Optional[Tuple[int, int]] = None
        self.temp_poly_pts: List[Tuple[int, int]] = []
        self.drawing_poly = False

        # Seleção por retângulo
        self.sel_rect_active = False
        self.sel_start = None
        self.sel_end = None

        # Janela de recorte (retângulo)
        self.clip_window: Optional[pg.Rect] = None
        self.clip_dragging = False
        self.clip_start = None

        # Modos e opções
        self.mode = Mode.ADD_POINT
        self.line_algo = LineAlgo.BRES
        self.clip_algo = ClipAlgo.COHEN

        # Painel de botões
        self.buttons: List[Button] = []
        self._build_buttons()

        # Numpad on-screen
        self.numpad = Numpad(W - 260, 360)

        # Transformação acumulada a aplicar sobre SELEÇÃO
        self.pending_T = mat_identity()

        # Rastrear ação pendente (para translação/rotação/escala)
        self.pending_action = None

    # ---------- UI ----------
    def _build_buttons(self):
        x = CANVAS_W + 10
        y = 10
        w = PANEL_W - 20
        h = 32
        gap = 8

        def add(label, tag, rowinc=True):
            nonlocal y
            b = Button(pg.Rect(x, y, w, h), label, tag)
            self.buttons.append(b)
            if rowinc:
                y += h + gap

        # modos de criação/seleção
        add("Selecionar", Mode.SELECT)
        add("Add Ponto", Mode.ADD_POINT)
        add("Add Reta", Mode.ADD_LINE)
        add("Add Políg.", Mode.ADD_POLY)
        add("Circ Bres.", Mode.DRAW_CIRCLE)
        add("Janela Recorte", Mode.CLIP_WINDOW)
        y += 6
        add("Reta: DDA", "LINE_DDA")
        add("Reta: Bresenham", "LINE_BRES")
        y += 6
        add("Recorte: Cohen-S.", "CLIP_COHEN")
        add("Recorte: Liang-B.", "CLIP_LIANG")
        y += 6
        add("Transladar", "T_TRANSLATE")
        add("Escalar", "T_SCALE")
        add("Rotacionar", "T_ROTATE")
        add("Refletir X", "T_REFLECT_X")
        add("Refletir Y", "T_REFLECT_Y")
        add("Refletir XY", "T_REFLECT_XY")
        add("Aplicar T na seleção", "T_APPLY")
        add("Limpar seleção", "CLEAR_SEL")
        y += 6
        add("Concluir Polígono", "POLY_CLOSE")
        add("Cancelar Polígono", "POLY_CANCEL")
        add("Limpar Tudo", "CLEAR_ALL")

    def set_active_button(self):
        for b in self.buttons:
            b.active = (
                (b.tag == self.mode)
                or (b.tag == "LINE_BRES" and self.line_algo == LineAlgo.BRES)
                or (b.tag == "LINE_DDA" and self.line_algo == LineAlgo.DDA)
                or (b.tag == "CLIP_COHEN" and self.clip_algo == ClipAlgo.COHEN)
                or (b.tag == "CLIP_LIANG" and self.clip_algo == ClipAlgo.LIANG)
            )

    # ---------- Entrada ----------
    def on_mouse_down(self, pos, button):
        # Clique no painel
        if pos[0] >= CANVAS_W:
            for b in self.buttons:
                if b.hit(pos):
                    self._handle_button(b.tag)
                    return
            # Numpad
            npad = self.numpad.handle_click(pos)
            if npad:
                action, number = npad
                if action == "OK" and number is not None and self.pending_action:
                    name = self.pending_action[0]
                    if name == "translate_dx":
                        dx = number
                        self.numpad.open("0")
                        self.pending_action = ("translate_dy", dx)
                    elif name == "translate_dy":
                        dx = self.pending_action[1]
                        dy = number
                        self.pending_T = mat_translate(dx, dy) @ self.pending_T
                        self.pending_action = None
                    elif name == "scale_uniform":
                        s = number
                        self.pending_T = mat_scale(s, s) @ self.pending_T
                        self.pending_action = None
                    elif name == "rotate_deg":
                        ang = number
                        self.pending_T = mat_rotate_deg(ang) @ self.pending_T
                        self.pending_action = None
                return
        # Clique no canvas
        if self.mode == Mode.ADD_POINT:
            self.entities.append(Point(p=pos))
        elif self.mode == Mode.ADD_LINE:
            if self.temp_line_start is None:
                self.temp_line_start = pos
            else:
                self.entities.append(Line(a=self.temp_line_start, b=pos))
                self.temp_line_start = None
        elif self.mode == Mode.ADD_POLY:
            self.drawing_poly = True
            self.temp_poly_pts.append(pos)
        elif self.mode == Mode.SELECT:
            self.sel_rect_active = True
            self.sel_start = pos
            self.sel_end = pos
        elif self.mode == Mode.DRAW_CIRCLE:
            if self.temp_line_start is None:
                self.temp_line_start = pos
            else:
                cx, cy = self.temp_line_start
                r = math.hypot(pos[0] - cx, pos[1] - cy)
                # Guardamos a circunferência como polígono de pixels amostrados
                circ_pts = []
                temp = pg.Surface((CANVAS_W, CANVAS_H))
                temp.fill((0, 0, 0))
                draw_circle_bresenham(temp, (cx, cy), r, color=(255, 255, 255))
                arr = pg.surfarray.array3d(temp)
                for x in range(CANVAS_W):
                    for y in range(CANVAS_H):
                        if arr[x, y, 0] != 0:
                            circ_pts.append((x, y))
                self.entities.append(Polygon(verts=circ_pts))
                self.temp_line_start = None
        elif self.mode == Mode.CLIP_WINDOW:
            self.clip_dragging = True
            self.clip_start = pos
            self.clip_window = pg.Rect(pos[0], pos[1], 1, 1)

    def on_mouse_up(self, pos, button):
        if self.sel_rect_active:
            self.sel_rect_active = False
            self._apply_selection()
        if self.clip_dragging:
            self.clip_dragging = False

    def on_mouse_motion(self, pos, rel, buttons):
        if self.sel_rect_active and self.sel_start:
            self.sel_end = pos
        if self.clip_dragging and self.clip_start:
            x0, y0 = self.clip_start
            x1, y1 = pos
            x = min(x0, x1)
            y = min(y0, y1)
            w = abs(x1 - x0)
            h = abs(y1 - y0)
            self.clip_window = pg.Rect(x, y, w, h)

    # ---------- Ações ----------
    def _handle_button(self, tag):
        if tag in [
            Mode.SELECT,
            Mode.ADD_POINT,
            Mode.ADD_LINE,
            Mode.ADD_POLY,
            Mode.DRAW_CIRCLE,
            Mode.CLIP_WINDOW,
        ]:
            self.mode = tag
        elif tag == "LINE_DDA":
            self.line_algo = LineAlgo.DDA
        elif tag == "LINE_BRES":
            self.line_algo = LineAlgo.BRES
        elif tag == "CLIP_COHEN":
            self.clip_algo = ClipAlgo.COHEN
        elif tag == "CLIP_LIANG":
            self.clip_algo = ClipAlgo.LIANG
        elif tag == "POLY_CLOSE":
            if self.drawing_poly and len(self.temp_poly_pts) >= 3:
                self.entities.append(Polygon(verts=list(self.temp_poly_pts)))
            self.temp_poly_pts.clear()
            self.drawing_poly = False
        elif tag == "POLY_CANCEL":
            self.temp_poly_pts.clear()
            self.drawing_poly = False
        elif tag == "CLEAR_ALL":
            self.entities.clear()
            self.temp_line_start = None
            self.temp_poly_pts.clear()
            self.drawing_poly = False
            self.clip_window = None
        elif tag == "CLEAR_SEL":
            for e in self.entities:
                e.selected = False
        elif tag.startswith("T_"):
            self._begin_transform(tag)
        elif tag == "T_APPLY":
            self._apply_transform_to_selection()
        self.set_active_button()

    def _begin_transform(self, tag):
        # Abrir numpad para solicitar valores dependendo do tipo de transformação
        if tag == "T_TRANSLATE":
            self.numpad.open("0")
            self.pending_action = ("translate_dx",)
        elif tag == "T_SCALE":
            self.numpad.open("1.0")
            self.pending_action = ("scale_uniform",)
        elif tag == "T_ROTATE":
            self.numpad.open("10")
            self.pending_action = ("rotate_deg",)
        elif tag == "T_REFLECT_X":
            self.pending_T = mat_scale(1, -1) @ self.pending_T
        elif tag == "T_REFLECT_Y":
            self.pending_T = mat_scale(-1, 1) @ self.pending_T
        elif tag == "T_REFLECT_XY":
            self.pending_T = mat_scale(-1, -1) @ self.pending_T

    def _apply_transform_to_selection(self):
        if np.allclose(self.pending_T, mat_identity()):
            return
        sel = [e for e in self.entities if e.selected]
        if not sel:
            return
        all_pts = []
        for e in sel:
            all_pts.extend(e.get_points())
        pivot = centroid_pts(all_pts) if all_pts else (0, 0)
        Tpivot = (
            mat_translate(pivot[0], pivot[1])
            @ self.pending_T
            @ mat_translate(-pivot[0], -pivot[1])
        )
        for e in sel:
            e.apply_transform(Tpivot)
        self.pending_T = mat_identity()

    def _apply_selection(self):
        if not (self.sel_start and self.sel_end):
            return
        x0, y0 = self.sel_start
        x1, y1 = self.sel_end
        xmin, xmax = min(x0, x1), max(x0, x1)
        ymin, ymax = min(y0, y1), max(y0, y1)
        rect = pg.Rect(xmin, ymin, xmax - xmin, ymax - ymin)
        for e in self.entities:
            pts = e.get_points()
            if not pts:
                e.selected = False
                continue
            e.selected = any(rect.collidepoint(p) for p in pts)

    # ---------- Desenho ----------
    def draw_panel(self):
        panel = pg.Rect(CANVAS_W, 0, PANEL_W, H)
        pg.draw.rect(self.screen, PANEL_BG, panel)
        title = self.big.render("CG TP1 - Ferramentas", True, TEXT)
        self.screen.blit(title, (CANVAS_W + 10, 8))
        for b in self.buttons:
            b.draw(self.screen, self.font)
        st1 = self.font.render(f"Reta: {self.line_algo}", True, TEXT)
        st2 = self.font.render(f"Recorte: {self.clip_algo}", True, TEXT)
        self.screen.blit(st1, (CANVAS_W + 10, 320))
        self.screen.blit(st2, (CANVAS_W + 10, 340))
        self.numpad.draw(self.screen, self.font)
        info = [
            f"Modo: {self.mode}",
            "Clique e arraste p/ selecionar.",
            "Reta: 2 cliques (A->B).",
            "Polígono: clique n vértices",
            "  e 'Concluir Polígono'.",
            "Círculo: 2 cliques (centro, raio).",
            "Janela de Recorte: arraste p/ criar.",
            "Transformações: abra numpad,",
            "  insira valor e aplique.",
        ]
        yy = H - 9 * 18 - 10
        for s in info:
            self.screen.blit(
                self.font.render(s, True, TEXT), (CANVAS_W + 10, yy)
            )
            yy += 18

    def draw_grid(self):
        for x in range(0, CANVAS_W, 25):
            pg.draw.line(self.screen, GRID, (x, 0), (x, CANVAS_H))
        for y in range(0, CANVAS_H, 25):
            pg.draw.line(self.screen, GRID, (0, y), (CANVAS_W, y))

    def draw_entities(self):
        surf = pg.Surface((CANVAS_W, CANVAS_H))
        surf.fill(BG)
        clip_rect = None
        if self.clip_window and self.clip_window.w > 0 and self.clip_window.h > 0:
            clip_rect = (
                self.clip_window.x,
                self.clip_window.y,
                self.clip_window.right,
                self.clip_window.bottom,
            )
        for e in self.entities:
            col = HILITE if e.selected else PIX
            if isinstance(e, Point):
                put_pixel(surf, int(e.p[0]), int(e.p[1]), col)
            elif isinstance(e, Line):
                p0, p1 = e.a, e.b
                if clip_rect:
                    if self.clip_algo == ClipAlgo.COHEN:
                        clipped = cohen_sutherland_clip(
                            p0, p1, (clip_rect[0], clip_rect[1], clip_rect[2], clip_rect[3])
                        )
                    else:
                        clipped = liang_barsky_clip(
                            p0, p1, (clip_rect[0], clip_rect[1], clip_rect[2], clip_rect[3])
                        )
                    if clipped is None:
                        continue
                    p0, p1 = clipped
                if self.line_algo == LineAlgo.DDA:
                    draw_line_dda(surf, p0, p1, col)
                else:
                    draw_line_bresenham(surf, p0, p1, col)
            elif isinstance(e, Polygon):
                verts = e.verts
                for i in range(len(verts)):
                    p0, p1 = verts[i], verts[(i + 1) % len(verts)]
                    if clip_rect:
                        if self.clip_algo == ClipAlgo.COHEN:
                            clipped = cohen_sutherland_clip(
                                p0,
                                p1,
                                (
                                    clip_rect[0],
                                    clip_rect[1],
                                    clip_rect[2],
                                    clip_rect[3],
                                ),
                            )
                        else:
                            clipped = liang_barsky_clip(
                                p0,
                                p1,
                                (
                                    clip_rect[0],
                                    clip_rect[1],
                                    clip_rect[2],
                                    clip_rect[3],
                                ),
                            )
                        if clipped is None:
                            continue
                        p0, p1 = clipped
                    if self.line_algo == LineAlgo.DDA:
                        draw_line_dda(surf, p0, p1, col)
                    else:
                        draw_line_bresenham(surf, p0, p1, col)
        self.screen.blit(surf, (0, 0))
        if self.temp_line_start and self.mode == Mode.ADD_LINE:
            pg.draw.circle(
                self.screen, (180, 180, 200), self.temp_line_start, 3
            )
        if self.drawing_poly and self.temp_poly_pts:
            for i in range(len(self.temp_poly_pts) - 1):
                pg.draw.line(
                    self.screen,
                    (160, 200, 255),
                    self.temp_poly_pts[i],
                    self.temp_poly_pts[i + 1],
                    1,
                )
            for p in self.temp_poly_pts:
                pg.draw.circle(self.screen, (200, 200, 240), p, 3)
        if (
            self.sel_rect_active
            and self.sel_start
            and self.sel_end
        ):
            x0, y0 = self.sel_start
            x1, y1 = self.sel_end
            rect = pg.Rect(
                min(x0, x1),
                min(y0, y1),
                abs(x1 - x0),
                abs(y1 - y0),
            )
            pg.draw.rect(self.screen, SEL_RECT, rect, 1)
        if self.clip_window and self.clip_window.w > 0 and self.clip_window.h > 0:
            pg.draw.rect(
                self.screen, (120, 160, 255), self.clip_window, 1
            )

    # ---------- Loop principal ----------
    def run(self):
        self.set_active_button()
        running = True
        while running:
            dt = self.clock.tick(FPS)
            for ev in pg.event.get():
                if ev.type == pg.QUIT:
                    running = False
                elif ev.type == pg.MOUSEBUTTONDOWN:
                    self.on_mouse_down(ev.pos, ev.button)
                elif ev.type == pg.MOUSEBUTTONUP:
                    self.on_mouse_up(ev.pos, ev.button)
                elif ev.type == pg.MOUSEMOTION:
                    self.on_mouse_motion(ev.pos, ev.rel, ev.buttons)
            self.draw_grid()
            self.draw_entities()
            self.draw_panel()
            pg.display.flip()
            pg.event.pump()
        pg.quit()
        sys.exit()


if __name__ == "__main__":
    App().run()