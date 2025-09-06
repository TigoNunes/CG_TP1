"""
Modulo entities define classes para entidades geometricas 2D usadas no
trabalho de Computacao Grafica (TP1). Cada entidade conhece sua geometria e
como desenhar-se sobre um surface do pygame utilizando funcoes de conversao
de coordenadas fornecidas externamente.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple, Callable
import math
import pygame as pg

Vec2 = Tuple[float, float]
Color = Tuple[int, int, int]


# -------------------------
# Ponto
# -------------------------
@dataclass(eq=False)
class Ponto:
    """Representa um ponto 2D no mundo cartesiano."""
    x: float
    y: float

    # >>> Permite usar Ponto em set/dict pela identidade do objeto
    def __hash__(self) -> int:
        return object.__hash__(self)

    def as_tuple(self) -> Tuple[float, float]:
        return (self.x, self.y)

    def translate(self, dx: float, dy: float) -> None:
        self.x += dx
        self.y += dy

    def rotate(self, angle_deg: float, pivot: Vec2 = (0.0, 0.0)) -> None:
        angle_rad = math.radians(angle_deg)
        px, py = pivot
        dx = self.x - px
        dy = self.y - py
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        rx = dx * cos_a - dy * sin_a
        ry = dx * sin_a + dy * cos_a
        self.x = px + rx
        self.y = py + ry

    def scale(self, factor: float, pivot: Vec2 = (0.0, 0.0)) -> None:
        px, py = pivot
        self.x = px + (self.x - px) * factor
        self.y = py + (self.y - py) * factor

    def draw(self, surface: pg.Surface, world_to_screen: Callable[[float, float], Tuple[int, int]],
             radius: int = 3, color: Color = (0, 0, 0), font: pg.font.Font | None = None,
             label_color: Color = (0, 0, 255)) -> None:
        sx, sy = world_to_screen(self.x, self.y)
        pg.draw.circle(surface, color, (sx, sy), radius)
        if font and label_color:
            label = font.render(f"({self.x:.2f}, {self.y:.2f})", True, label_color)
            surface.blit(label, (sx + 8, sy - 12))


# -------------------------
# Reta
# -------------------------
@dataclass
class Reta:
    """Segmento de reta entre dois pontos."""
    p1: Ponto
    p2: Ponto
    algoritmo: str = "BRESENHAM"  # 'DDA' ou 'BRESENHAM'

    def translate(self, dx: float, dy: float) -> None:
        self.p1.translate(dx, dy); self.p2.translate(dx, dy)

    def rotate(self, angle_deg: float, pivot: Vec2) -> None:
        self.p1.rotate(angle_deg, pivot); self.p2.rotate(angle_deg, pivot)

    def scale(self, factor: float, pivot: Vec2) -> None:
        self.p1.scale(factor, pivot); self.p2.scale(factor, pivot)

    def draw(self, surface: pg.Surface, world_to_screen: Callable[[float, float], Tuple[int, int]],
             color: Color = (0, 0, 0)) -> None:
        x0, y0 = world_to_screen(self.p1.x, self.p1.y)
        x1, y1 = world_to_screen(self.p2.x, self.p2.y)
        if self.algoritmo.upper() == "DDA":
            self._raster_dda(surface, x0, y0, x1, y1, color)
        else:
            self._raster_bresenham(surface, x0, y0, x1, y1, color)

    @staticmethod
    def _raster_dda(surface: pg.Surface, x0: int, y0: int, x1: int, y1: int, color: Color) -> None:
        x0_f, y0_f = float(x0), float(y0)
        x1_f, y1_f = float(x1), float(y1)
        dx, dy = x1_f - x0_f, y1_f - y0_f
        steps = int(max(abs(dx), abs(dy)))
        if steps == 0:
            if 0 <= x0 < surface.get_width() and 0 <= y0 < surface.get_height():
                surface.set_at((x0, y0), color)
            return
        inc_x, inc_y = dx / steps, dy / steps
        x, y = x0_f, y0_f
        for _ in range(steps + 1):
            xi, yi = int(round(x)), int(round(y))
            if 0 <= xi < surface.get_width() and 0 <= yi < surface.get_height():
                surface.set_at((xi, yi), color)
            x += inc_x; y += inc_y

    @staticmethod
    def _raster_bresenham(surface: pg.Surface, x0: int, y0: int, x1: int, y1: int, color: Color) -> None:
        x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
        steep = abs(y1 - y0) > abs(x1 - x0)
        if steep: x0, y0, x1, y1 = y0, x0, y1, x1
        if x0 > x1: x0, x1, y0, y1 = x1, x0, y1, y0
        dx = x1 - x0; dy = abs(y1 - y0)
        err = dx // 2; y_step = 1 if y0 < y1 else -1; y = y0
        for x in range(x0, x1 + 1):
            if steep:
                if 0 <= y < surface.get_width() and 0 <= x < surface.get_height():
                    surface.set_at((y, x), color)
            else:
                if 0 <= x < surface.get_width() and 0 <= y < surface.get_height():
                    surface.set_at((x, y), color)
            err -= dy
            if err < 0:
                y += y_step; err += dx


# -------------------------
# Circunferencia (centro + ponto de borda)
# -------------------------
@dataclass
class Circunferencia:
    """Circunferencia definida por centro e um ponto da borda."""
    centro: Ponto
    borda: Ponto  # ponto que define o raio (distância ao centro)

    @property
    def raio(self) -> float:
        """Raio em unidades de mundo (distancia centro-borda)."""
        return math.hypot(self.borda.x - self.centro.x, self.borda.y - self.centro.y)

    def translate(self, dx: float, dy: float) -> None:
        self.centro.translate(dx, dy); self.borda.translate(dx, dy)

    def scale(self, factor: float, pivot: Vec2) -> None:
        self.centro.scale(factor, pivot); self.borda.scale(factor, pivot)

    def rotate(self, angle_deg: float, pivot: Vec2) -> None:
        self.centro.rotate(angle_deg, pivot); self.borda.rotate(angle_deg, pivot)

    def draw(self, surface: pg.Surface, world_to_screen: Callable[[float, float], Tuple[int, int]],
             color: Color = (0, 0, 0)) -> None:
        # Converte centro e borda para tela e calcula raio em pixels
        cx, cy = world_to_screen(self.centro.x, self.centro.y)
        bx, by = world_to_screen(self.borda.x, self.borda.y)
        r = int(round(math.hypot(bx - cx, by - cy)))
        if r <= 0:
            return

        # Bresenham/Midpoint Circle em tela
        x, y = 0, r
        p = 1 - r

        def plot8(xc, yc, x_, y_):
            pts = [(xc + x_, yc + y_), (xc - x_, yc + y_), (xc + x_, yc - y_), (xc - x_, yc - y_),
                   (xc + y_, yc + x_), (xc - y_, yc + x_), (xc + y_, yc - x_), (xc - y_, yc - x_)]
            w, h = surface.get_width(), surface.get_height()
            for px, py in pts:
                if 0 <= px < w and 0 <= py < h:
                    surface.set_at((int(px), int(py)), color)

        plot8(cx, cy, x, y)
        while x < y:
            x += 1
            if p < 0:
                p += 2 * x + 1
            else:
                y -= 1
                p += 2 * (x - y) + 1
            plot8(cx, cy, x, y)


# -------------------------
# Poligono
# -------------------------
@dataclass
class Poligono:
    """Polígono simples definido por lista de vértices."""
    vertices: List[Ponto]
    algoritmo: str = "BRESENHAM"
    fechado: bool = False

    def add_vertice(self, p: Ponto) -> None:
        if not self.fechado:
            self.vertices.append(p)

    def close(self) -> None:
        self.fechado = True

    def translate(self, dx: float, dy: float) -> None:
        for v in self.vertices: v.translate(dx, dy)

    def rotate(self, angle_deg: float, pivot: Vec2) -> None:
        for v in self.vertices: v.rotate(angle_deg, pivot)

    def scale(self, factor: float, pivot: Vec2) -> None:
        for v in self.vertices: v.scale(factor, pivot)

    def draw(self, surface: pg.Surface, world_to_screen: Callable[[float, float], Tuple[int, int]],
             color: Color = (0, 0, 0)) -> None:
        if len(self.vertices) < 2:
            return
        for i in range(len(self.vertices) - 1):
            Reta(self.vertices[i], self.vertices[i + 1], self.algoritmo).draw(surface, world_to_screen, color)
        # Se quiser fechar o poligono:
        # if self.fechado:
        #     Reta(self.vertices[-1], self.vertices[0], self.algoritmo).draw(surface, world_to_screen, color)
