"""
Modulo entities define classes para entidades geometricas 2D usadas no
trabalho de Computacao Grafica. Cada entidade conhece sua geometria e
como desenhar‑se sobre um surface do pygame utilizando as funcoes de
conversao de coordenadas fornecidas externamente. Tambem provem
metodos de transformacao (translacao, rotacao, escala) sobre seus
pontos. Estas classes nao gerenciam eventos de interface ou estado
global; cabera ao loop principal da aplicacao orquestrar a criacao e
transformacao das instancias.

Classes incluidas:
    - Ponto: representa um ponto no plano 2D.
    - Reta: representa um segmento de reta entre dois pontos.
    - Circunferencia: representa uma circunferencia 2D com centro
      e raio.
    - Poligono: representa um poligono simples como uma lista de
      vertices.

Autor: Conversao da versao monolitica para POO.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple, Callable
import math
import pygame as pg


Vec2 = Tuple[int, int]
Color = Tuple[int, int, int]


@dataclass
class Ponto:
    """Representa um ponto 2D no mundo cartesiano.

    O ponto contem coordenadas inteiras (x, y). Ele nao conhece
    nada sobre coordenadas de tela; para desenhar deve ser passada
    uma funcao de conversao mundo->tela.
    """

    x: int
    y: int

    def as_tuple(self) -> Vec2:
        return (self.x, self.y)

    def translate(self, dx: int, dy: int) -> None:
        """Translada o ponto de acordo com dx e dy."""
        self.x += dx
        self.y += dy

    def rotate(self, angle_deg: float, pivot: Vec2 = (0, 0)) -> None:
        """Rota o ponto ao redor de um pivot.

        Args:
            angle_deg: angulo em graus, positivo anti‑horario.
            pivot: par (px, py) centro de rotacao.
        """
        angle_rad = math.radians(angle_deg)
        px, py = pivot
        # translada para origem
        dx = self.x - px
        dy = self.y - py
        # rotacao
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        rx = dx * cos_a - dy * sin_a
        ry = dx * sin_a + dy * cos_a
        # translada de volta
        self.x = int(round(px + rx))
        self.y = int(round(py + ry))

    def scale(self, factor: float, pivot: Vec2 = (0, 0)) -> None:
        """Escala o ponto em torno de um pivot.

        Args:
            factor: fator de escala uniforme.
            pivot: centro de escala.
        """
        px, py = pivot
        self.x = int(round(px + (self.x - px) * factor))
        self.y = int(round(py + (self.y - py) * factor))

    def draw(self, surface: pg.Surface, world_to_screen: Callable[[int, int], Tuple[int, int]],
             radius: int = 3, color: Color = (0, 0, 0), font: pg.font.Font | None = None,
             label_color: Color = (0, 0, 255)) -> None:
        """Desenha o ponto no surface.

        Args:
            surface: surface do pygame onde desenhar.
            world_to_screen: funcao para converter coordenadas do mundo para a tela.
            radius: raio do circulo representando o ponto.
            color: cor do ponto.
            font: fonte para renderizar o rotulo (x,y). Se None, nao desenha rotulo.
            label_color: cor do texto do rotulo.
        """
        sx, sy = world_to_screen(self.x, self.y)
        pg.draw.circle(surface, color, (sx, sy), radius)
        if font:
            text = font.render(f"({self.x}, {self.y})", True, label_color)
            # desloca o texto um pouco para nao sobrepor o ponto
            surface.blit(text, (sx + 8, sy - 12))


@dataclass
class Reta:
    """Representa um segmento de reta entre dois pontos."""

    p1: Ponto
    p2: Ponto
    algoritmo: str = "BRESENHAM"  # 'DDA' ou 'BRESENHAM'

    def translate(self, dx: int, dy: int) -> None:
        self.p1.translate(dx, dy)
        self.p2.translate(dx, dy)

    def rotate(self, angle_deg: float, pivot: Vec2) -> None:
        self.p1.rotate(angle_deg, pivot)
        self.p2.rotate(angle_deg, pivot)

    def scale(self, factor: float, pivot: Vec2) -> None:
        self.p1.scale(factor, pivot)
        self.p2.scale(factor, pivot)

    def draw(self, surface: pg.Surface, world_to_screen: Callable[[int, int], Tuple[int, int]],
             color: Color = (0, 0, 0)) -> None:
        """Rasteriza a reta usando o algoritmo configurado.

        Note: o rasterizador opera em coordenadas de tela, entao convertemos
        os extremos antes de chamar o algoritmo.
        """
        # converte para tela
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
            x += inc_x
            y += inc_y

    @staticmethod
    def _raster_bresenham(surface: pg.Surface, x0: int, y0: int, x1: int, y1: int, color: Color) -> None:
        x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
        steep = abs(y1 - y0) > abs(x1 - x0)
        if steep:
            x0, y0, x1, y1 = y0, x0, y1, x1
        if x0 > x1:
            x0, x1 = x1, x0
            y0, y1 = y1, y0
        dx = x1 - x0
        dy = abs(y1 - y0)
        err = dx // 2
        y_step = 1 if y0 < y1 else -1
        y = y0
        for x in range(x0, x1 + 1):
            if steep:
                if 0 <= y < surface.get_width() and 0 <= x < surface.get_height():
                    surface.set_at((y, x), color)
            else:
                if 0 <= x < surface.get_width() and 0 <= y < surface.get_height():
                    surface.set_at((x, y), color)
            err -= dy
            if err < 0:
                y += y_step
                err += dx


@dataclass
class Circunferencia:
    """Representa uma circunferencia 2D com centro e raio."""

    centro: Ponto
    raio: int

    def translate(self, dx: int, dy: int) -> None:
        self.centro.translate(dx, dy)

    def scale(self, factor: float, pivot: Vec2) -> None:
        """Escala a circunferencia uniformemente em torno de um pivot.

        Note: a escala afeta o raio proporcionalmente.
        """
        # Escala o centro
        self.centro.scale(factor, pivot)
        # Escala o raio
        self.raio = int(round(self.raio * factor))

    def rotate(self, angle_deg: float, pivot: Vec2) -> None:
        self.centro.rotate(angle_deg, pivot)
        # rotacao nao muda o raio

    def draw(self, surface: pg.Surface, world_to_screen: Callable[[int, int], Tuple[int, int]],
             color: Color = (0, 0, 0)) -> None:
        """Desenha a circunferencia usando algoritmo midpoint circle.
        O algoritmo opera em coordenadas de tela."""
        cx, cy = world_to_screen(self.centro.x, self.centro.y)
        r = abs(self.raio)
        x = 0
        y = r
        p = 1 - r

        def plot8(xc, yc, x, y):
            pontos = [
                (xc + x, yc + y), (xc - x, yc + y), (xc + x, yc - y), (xc - x, yc - y),
                (xc + y, yc + x), (xc - y, yc + x), (xc + y, yc - x), (xc - y, yc - x),
            ]
            for px, py in pontos:
                if 0 <= px < surface.get_width() and 0 <= py < surface.get_height():
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


@dataclass
class Poligono:
    """Representa um poligono simples definido por uma lista de vertices."""

    vertices: List[Ponto]
    algoritmo: str = "BRESENHAM"
    fechado: bool = False

    def add_vertice(self, p: Ponto) -> None:
        """Adiciona um vertice ao poligono. Se o poligono estiver fechado,
        este metodo nao faz nada."""
        if not self.fechado:
            self.vertices.append(p)

    def close(self) -> None:
        """Fecha o poligono, conectando o ultimo vertice ao primeiro."""
        self.fechado = True

    def translate(self, dx: int, dy: int) -> None:
        for v in self.vertices:
            v.translate(dx, dy)

    def rotate(self, angle_deg: float, pivot: Vec2) -> None:
        for v in self.vertices:
            v.rotate(angle_deg, pivot)

    def scale(self, factor: float, pivot: Vec2) -> None:
        for v in self.vertices:
            v.scale(factor, pivot)

    def draw(self, surface: pg.Surface, world_to_screen: Callable[[int, int], Tuple[int, int]],
             color: Color = (0, 0, 0)) -> None:
        """Desenha o poligono conectando vertices consecutivos e fechando se necessário."""
        if len(self.vertices) < 2:
            return
        # desenha cada segmento
        for i in range(len(self.vertices) - 1):
            r = Reta(self.vertices[i], self.vertices[i + 1], self.algoritmo)
            r.draw(surface, world_to_screen, color)
        # se fechado, conecta ultimo ao primeiro
        if self.fechado:
            r = Reta(self.vertices[-1], self.vertices[0], self.algoritmo)
            r.draw(surface, world_to_screen, color)
