# main_oop.py
"""
TP1 CG — Versão OOP com painel lateral e abas.

- Canvas à esquerda (origem no centro, grade e eixos)
- Painel à direita com abas:
    Retas      : desenha retas com DDA ou Bresenham (selecionável)
    Circunf.   : placeholder para circunferências
    Polígonos  : placeholder para polígonos
    Transform. : placeholder para seleções/transformações

Principais mudanças:
- Usa classes Ponto e Reta do módulo entities.py.
- Cada clique no canvas cria um Ponto. Na aba Retas, dois cliques consecutivos criam Ponto A e Ponto B e geram uma Reta(A,B,algoritmo).
- As retas são desenhadas chamando reta.draw(), que escolhe DDA ou Bresenham internamente.
"""

import sys
import logging
from pprint import pformat
import pygame as pg

# Importa as classes definidas em entities.py
from entities import Ponto, Reta, Circunferencia, Poligono

# =========================
# LOGGING
# =========================
LOG_LEVEL = logging.INFO  # use logging.DEBUG para mais detalhes

def configurar_logging():
    logger = logging.getLogger("TP1_OOP")
    logger.setLevel(LOG_LEVEL)
    logger.handlers.clear()
    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s", "%H:%M:%S")
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(LOG_LEVEL); ch.setFormatter(fmt)
    fh = logging.FileHandler("tp1_oop.log", mode="w", encoding="utf-8")
    fh.setLevel(LOG_LEVEL); fh.setFormatter(fmt)
    logger.addHandler(ch); logger.addHandler(fh)
    return logger

log = configurar_logging()

def dump_estado(pontos, retas, algoritmo, ponto_A, aba):
    log.info(
        "ESTADO | aba=%s | algoritmo=%s | ponto_A=%s | #pontos=%d | #retas=%d\npontos=%s\nretas=%s",
        aba, algoritmo, ponto_A, len(pontos), len(retas),
        pformat([p.as_tuple() for p in pontos]),
        pformat([ (r.p1.as_tuple(), r.p2.as_tuple(), r.algoritmo) for r in retas ])
    )

# =========================
# CONSTANTES DE JANELA / UI
# =========================
LARGURA_TOTAL, ALTURA = 1200, 700   # janela total
LARGURA_PAINEL = 320                # painel lateral (direita)
LARGURA_CANVAS = LARGURA_TOTAL - LARGURA_PAINEL

# Cores gerais
COR_FUNDO = (255, 255, 255)
COR_PAINEL_BG = (245, 245, 245)
COR_PAINEL_BORDA = (200, 200, 200)
COR_TAB_ATIVA = (200, 220, 255)
COR_TAB_INATIVA = (230, 230, 230)
COR_BOTAO = (230, 230, 230)
COR_BOTAO_ATIVO = (200, 220, 255)
COR_BORDA = (180, 180, 180)

# Canvas (grade/eixos)
PASSO_GRADE = 25
COR_GRADE = (225, 225, 225)
COR_EIXOS = (120, 120, 120)
COR_CENTRO = (180, 60, 60)

# Texto / pontos / retas
COR_PONTO = (0, 0, 0)
COR_TEXTO = (0, 0, 255)
RAIO_PONTO = 3
DESLOC_TEXTO = (8, -12)
COR_RETA = (0, 0, 0)
COR_PREVIA = (120, 120, 120)

# Tipografia
TAM_FONTE = 16

# Abas e algoritmos
ABA_RETAS = "RETAS"
ABA_CIRC = "CIRCUNF"
ABA_POLI = "POLIGONOS"
ABA_TRANSF = "TRANSFORM"

ALGO_DDA = "DDA"
ALGO_BRES = "BRESENHAM"

ESP_GUIA = 1  # espessura da linha de prévia

# =========================
# INICIALIZAÇÃO
# =========================
def inicializar():
    pg.init()
    pg.display.set_caption("TP1 CG — OOP com painel lateral e abas")
    tela = pg.display.set_mode((LARGURA_TOTAL, ALTURA))
    relogio = pg.time.Clock()
    fonte = pg.font.Font(None, TAM_FONTE)
    log.info("Pygame OK | janela=%dx%d | canvas=%dx%d | painel=%dx%d",
             LARGURA_TOTAL, ALTURA, LARGURA_CANVAS, ALTURA, LARGURA_PAINEL, ALTURA)
    return tela, relogio, fonte

# =========================
# CONVERSÃO DE COORDENADAS (Canvas)
# =========================
def mundo_para_tela(x, y):
    """Converte um ponto do mundo (origem no centro do canvas, y para cima) para coordenadas de tela."""
    cx, cy = LARGURA_CANVAS // 2, ALTURA // 2
    sx = cx + x
    sy = cy - y
    return int(round(sx)), int(round(sy))

def tela_para_mundo(sx, sy):
    """Converte coordenadas de tela (mouse) para o sistema centrado do canvas."""
    cx, cy = LARGURA_CANVAS // 2, ALTURA // 2
    x = sx - cx
    y = cy - sy
    return x, y

# =========================
# DESENHO DO CANVAS E DO PAINEL
# =========================
def desenhar_canvas(tela):
    """Desenha a área do canvas com grade e eixos."""
    canvas_rect = pg.Rect(0, 0, LARGURA_CANVAS, ALTURA)
    pg.draw.rect(tela, COR_FUNDO, canvas_rect)

    cx, cy = LARGURA_CANVAS // 2, ALTURA // 2

    # Grade vertical
    x = cx
    while x < LARGURA_CANVAS:
        pg.draw.line(tela, COR_GRADE, (x, 0), (x, ALTURA), 1)
        x += PASSO_GRADE
    x = cx
    while x >= 0:
        pg.draw.line(tela, COR_GRADE, (x, 0), (x, ALTURA), 1)
        x -= PASSO_GRADE

    # Grade horizontal
    y = cy
    while y < ALTURA:
        pg.draw.line(tela, COR_GRADE, (0, y), (LARGURA_CANVAS, y), 1)
        y += PASSO_GRADE
    y = cy
    while y >= 0:
        pg.draw.line(tela, COR_GRADE, (0, y), (LARGURA_CANVAS, y), 1)
        y -= PASSO_GRADE

    # Eixos
    pg.draw.line(tela, COR_EIXOS, (0, cy), (LARGURA_CANVAS, cy), 2)
    pg.draw.line(tela, COR_EIXOS, (cx, 0), (cx, ALTURA), 2)

    # Ponto central
    pg.draw.circle(tela, COR_CENTRO, (cx, cy), 3)

def desenhar_painel(tela, fonte, aba_atual, algoritmo):
    """
    Desenha o painel lateral (direito) com as abas e os controles da aba ativa.
    Retorna:
      - dict com rects das abas
      - dict com rects dos controles da aba atual
    """
    painel_rect = pg.Rect(LARGURA_CANVAS, 0, LARGURA_PAINEL, ALTURA)
    pg.draw.rect(tela, COR_PAINEL_BG, painel_rect)
    pg.draw.line(tela, COR_PAINEL_BORDA, (LARGURA_CANVAS, 0), (LARGURA_CANVAS, ALTURA), 1)

    # Abas
    tabs = [
        (ABA_RETAS, "Retas"),
        (ABA_CIRC, "Circunf."),
        (ABA_POLI, "Polígonos"),
        (ABA_TRANSF, "Transform.")
    ]
    tab_rects = {}
    pad = 10
    tab_w = (LARGURA_PAINEL - pad*2)
    tab_h = 34
    y = pad

    for key, label in tabs:
        r = pg.Rect(LARGURA_CANVAS + pad, y, tab_w, tab_h)
        cor = COR_TAB_ATIVA if key == aba_atual else COR_TAB_INATIVA
        pg.draw.rect(tela, cor, r, border_radius=8)
        pg.draw.rect(tela, COR_BORDA, r, 1, border_radius=8)
        surf = fonte.render(label, True, (0, 0, 0))
        tela.blit(surf, surf.get_rect(center=r.center))
        tab_rects[key] = r
        y += tab_h + 6

    # Conteúdo da aba ativa
    controls_rects = {}
    content_area = pg.Rect(LARGURA_CANVAS + pad, y + 6, tab_w, ALTURA - (y + 6) - pad)
    titulo = fonte.render(f"Opções — {aba_atual.title()}", True, (0, 0, 0))
    tela.blit(titulo, (content_area.x, content_area.y))

    cy = content_area.y + 28
    btn_w, btn_h = 150, 36

    if aba_atual == ABA_RETAS:
        # Botão DDA
        r_dda = pg.Rect(content_area.x, cy, btn_w, btn_h)
        pg.draw.rect(tela, COR_BOTAO_ATIVO if algoritmo == ALGO_DDA else COR_BOTAO, r_dda, border_radius=8)
        pg.draw.rect(tela, COR_BORDA, r_dda, 1, border_radius=8)
        txt = fonte.render("DDA", True, (0, 0, 0))
        tela.blit(txt, txt.get_rect(center=r_dda.center))

        # Botão Bresenham
        r_bres = pg.Rect(content_area.x + btn_w + 12, cy, btn_w, btn_h)
        pg.draw.rect(tela, COR_BOTAO_ATIVO if algoritmo == ALGO_BRES else COR_BOTAO, r_bres, border_radius=8)
        pg.draw.rect(tela, COR_BORDA, r_bres, 1, border_radius=8)
        txt = fonte.render("Bresenham", True, (0, 0, 0))
        tela.blit(txt, txt.get_rect(center=r_bres.center))

        # Botão Limpar
        cy += btn_h + 12
        r_limpar = pg.Rect(content_area.x, cy, btn_w, btn_h)
        pg.draw.rect(tela, COR_BOTAO, r_limpar, border_radius=8)
        pg.draw.rect(tela, COR_BORDA, r_limpar, 1, border_radius=8)
        txt = fonte.render("Limpar", True, (0, 0, 0))
        tela.blit(txt, txt.get_rect(center=r_limpar.center))

        controls_rects["DDA"] = r_dda
        controls_rects["BRES"] = r_bres
        controls_rects["LIMPAR"] = r_limpar

    elif aba_atual == ABA_CIRC:
        _texto_multilinha(tela, fonte, [
            "Aba Circunf. (em breve)",
            "Clique 1: centro",
            "Clique 2: raio",
            "Desenho pelo algoritmo Midpoint Circle."
        ], content_area.x, cy)

    elif aba_atual == ABA_POLI:
        _texto_multilinha(tela, fonte, [
            "Aba Polígonos (em breve)",
            "Clique sucessivos: vértices",
            "Finalizar: clique especial ou botão",
            "Arestas rasterizadas com DDA/Bres."
        ], content_area.x, cy)

    elif aba_atual == ABA_TRANSF:
        _texto_multilinha(tela, fonte, [
            "Aba Transform. (em breve)",
            "Selecionar entidades e aplicar",
            "Translação, rotação, escala",
            "Reta só seleciona se os 2 pontos estiverem selecionados."
        ], content_area.x, cy)

    return tab_rects, controls_rects

def _texto_multilinha(tela, fonte, linhas, x, y_inicial, dy=20):
    """Desenha várias linhas de texto em sequência."""
    y = y_inicial
    for s in linhas:
        surf = fonte.render(s, True, (0, 0, 0))
        tela.blit(surf, (x, y))
        y += dy

# =========================
# DESENHO DAS ENTIDADES
# =========================
def desenhar_pontos(tela, fonte, pontos):
    """Percorre a lista de objetos Ponto e desenha cada um."""
    for ponto in pontos:
        # Removemos 'label=True' — basta passar a fonte para desenhar as coordenadas
        ponto.draw(tela, mundo_para_tela, radius=RAIO_PONTO, color=COR_PONTO,
                   font=fonte, label_color=COR_TEXTO)

def desenhar_retas(tela, retas):
    """Percorre a lista de objetos Reta e desenha cada um usando seu algoritmo."""
    for reta in retas:
        reta.draw(tela, mundo_para_tela, color=COR_RETA)

def desenhar_previa(tela, ponto_A, pos_mouse):
    """Desenha a linha de prévia entre Ponto A e a posição atual do mouse no canvas."""
    if ponto_A is None or pos_mouse is None:
        return
    ax, ay = mundo_para_tela(ponto_A.x, ponto_A.y)
    mx, my = pos_mouse
    # Evita cruzar para o painel
    if mx >= LARGURA_CANVAS:
        mx = LARGURA_CANVAS - 1
    pg.draw.line(tela, COR_PREVIA, (ax, ay), (mx, my), ESP_GUIA)

# =========================
# MAIN LOOP
# =========================
def main():
    tela, relogio, fonte = inicializar()

    # Estado
    aba_atual = ABA_RETAS
    algoritmo_atual = ALGO_BRES
    pontos = []  # lista de Ponto
    retas = []   # lista de Reta
    ponto_A = None  # referência para o primeiro ponto (Ponto)

    dump_estado(pontos, retas, algoritmo_atual, ponto_A, aba_atual)

    rodando = True
    while rodando:
        # DESENHO
        desenhar_canvas(tela)
        tab_rects, ctrl_rects = desenhar_painel(tela, fonte, aba_atual, algoritmo_atual)
        desenhar_retas(tela, retas)
        desenhar_pontos(tela, fonte, pontos)
        if aba_atual == ABA_RETAS and ponto_A is not None:
            desenhar_previa(tela, ponto_A, pg.mouse.get_pos())

        pg.display.flip()
        relogio.tick(60)

        # EVENTOS
        for ev in pg.event.get():
            if ev.type == pg.QUIT:
                log.info("QUIT — encerrando")
                rodando = False

            elif ev.type == pg.MOUSEBUTTONDOWN and ev.button == 1:
                sx, sy = ev.pos

                # Clique no PAINEL (lado direito)
                if sx >= LARGURA_CANVAS:
                    # Abas
                    for key, r in tab_rects.items():
                        if r.collidepoint(sx, sy):
                            if key != aba_atual:
                                aba_atual = key
                                log.info("Aba -> %s", aba_atual)
                                dump_estado(pontos, retas, algoritmo_atual, ponto_A, aba_atual)
                            break
                    else:
                        # Controles da aba Retas
                        if aba_atual == ABA_RETAS:
                            r_dda = ctrl_rects.get("DDA")
                            r_bres = ctrl_rects.get("BRES")
                            r_limpar = ctrl_rects.get("LIMPAR")

                            if r_dda and r_dda.collidepoint(sx, sy):
                                if algoritmo_atual != ALGO_DDA:
                                    algoritmo_atual = ALGO_DDA
                                    log.info("Algoritmo -> DDA (para novas retas)")
                                    dump_estado(pontos, retas, algoritmo_atual, ponto_A, aba_atual)
                                continue

                            if r_bres and r_bres.collidepoint(sx, sy):
                                if algoritmo_atual != ALGO_BRES:
                                    algoritmo_atual = ALGO_BRES
                                    log.info("Algoritmo -> Bresenham (para novas retas)")
                                    dump_estado(pontos, retas, algoritmo_atual, ponto_A, aba_atual)
                                continue

                            if r_limpar and r_limpar.collidepoint(sx, sy):
                                log.info("LIMPAR | antes: #pontos=%d #retas=%d", len(pontos), len(retas))
                                pontos.clear(); retas.clear(); ponto_A = None
                                log.info("LIMPAR | depois: #pontos=%d #retas=%d", len(pontos), len(retas))
                                dump_estado(pontos, retas, algoritmo_atual, ponto_A, aba_atual)
                                continue

                    # Clique no painel processado
                    continue

                # Clique no CANVAS (lado esquerdo)
                if aba_atual == ABA_RETAS:
                    x, y = tela_para_mundo(sx, sy)
                    novo_ponto = Ponto(x, y)
                    pontos.append(novo_ponto)
                    log.info("Ponto criado (RETAS) | mundo=(%d,%d)", x, y)

                    if ponto_A is None:
                        ponto_A = novo_ponto
                        log.info("Definido Ponto A: %s", ponto_A.as_tuple())
                    else:
                        ponto_B = novo_ponto
                        nova_reta = Reta(ponto_A, ponto_B, algoritmo_atual)
                        retas.append(nova_reta)
                        log.info("Reta criada A->B | A=%s B=%s | algoritmo=%s",
                                 ponto_A.as_tuple(), ponto_B.as_tuple(), algoritmo_atual)
                        ponto_A = None
                        dump_estado(pontos, retas, algoritmo_atual, ponto_A, aba_atual)

                elif aba_atual == ABA_CIRC:
                    # Placeholder: criação de Circunferência
                    log.info("Clique em canvas na aba CIRCUNF (placeholder): tela=(%d,%d)", sx, sy)

                elif aba_atual == ABA_POLI:
                    # Placeholder: criação de Polígono
                    log.info("Clique em canvas na aba POLIGONOS (placeholder): tela=(%d,%d)", sx, sy)

                elif aba_atual == ABA_TRANSF:
                    # Placeholder: seleção e transformações
                    log.info("Clique em canvas na aba TRANSFORM (placeholder): tela=(%d,%d)", sx, sy)

    pg.quit()
    sys.exit()

if __name__ == "__main__":
    main()
