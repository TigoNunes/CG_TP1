# step09_retas_que_plotam_pontos.py
"""
Etapa 09 — Ferramenta de retas que também plota pontos.

Fluxo:
1) Clique 1: cria Ponto A (plota e rotula)
2) Clique 2: cria Ponto B (plota e rotula) e rasteriza a reta A->B
3) repetição: próximo clique reinicia sequência (novo A)

UI:
- Botões: DDA, Bresenham, Limpar
- Grade centrada; origem (0,0) no centro; X→direita, Y→cima
- Coordenadas dos pontos em azul
"""

import sys
import logging
from pprint import pformat
import pygame as pg

# Configurações de logging
LOG_LEVEL = logging.INFO  # defina logging.DEBUG para mais detalhes

def configurar_logging():
    logger = logging.getLogger("TP1")
    logger.setLevel(LOG_LEVEL)
    logger.handlers.clear()
    fmt = logging.Formatter(fmt="%(asctime)s | %(levelname)s | %(message)s", datefmt="%H:%M:%S")
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)
    ch.setLevel(LOG_LEVEL)
    logger.addHandler(ch)
    fh = logging.FileHandler("tp1.log", mode="w", encoding="utf-8")
    fh.setFormatter(fmt)
    fh.setLevel(LOG_LEVEL)
    logger.addHandler(fh)
    return logger

log = configurar_logging()

def dump_estado(pontos_mundo, retas_mundo, algoritmo, ponto_A):
    log.info(
        "ESTADO | algoritmo=%s | ponto_A=%s | #pontos=%d | #retas=%d\npontos=%s\nretas=%s",
        algoritmo,
        ponto_A,
        len(pontos_mundo),
        len(retas_mundo),
        pformat(pontos_mundo),
        pformat(retas_mundo),
    )

# ... aqui permanecem as configurações (tamanhos, cores, etc.) ...

def inicializar():
    pg.init()
    pg.display.set_caption("TP1 CG — Etapa 09: Retas que plotam pontos (DDA/Bresenham)")
    tela = pg.display.set_mode((LARGURA, ALTURA))
    relogio = pg.time.Clock()
    fonte = pg.font.Font(None, TAM_FONTE)
    log.info("Pygame inicializado | janela=%dx%d", LARGURA, ALTURA)
    return tela, relogio, fonte 

# -------------------------
# Configurações
# -------------------------
LARGURA, ALTURA = 1000, 650
COR_FUNDO = (255, 255, 255)

PASSO_GRADE = 25
COR_GRADE = (225, 225, 225)
COR_EIXOS = (120, 120, 120)
COR_CENTRO = (180, 60, 60)

COR_RETA = (0, 0, 0)
COR_PREVIA = (120, 120, 120)

COR_PONTO = (0, 0, 0)
COR_TEXTO = (0, 0, 255)
RAIO_PONTO = 3
DESLOC_TEXTO = (8, -12)

ALTURA_PAINEL = 44
COR_PAINEL = (245, 245, 245)
COR_BORDA_BOTAO = (180, 180, 180)
COR_BOTAO = (230, 230, 230)
COR_BOTAO_ATIVO = (200, 220, 255)
TAM_FONTE = 16

ALGO_DDA = "DDA"
ALGO_BRES = "BRESENHAM"

ESP_GUIA = 1  # espessura da linha de prévia (apenas guia visual)

# -------------------------
# Inicialização
# -------------------------
def inicializar():
    pg.init()
    pg.display.set_caption("TP1 CG — Etapa 09: Retas que plotam pontos (DDA/Bresenham)")
    tela = pg.display.set_mode((LARGURA, ALTURA))
    relogio = pg.time.Clock()
    fonte = pg.font.Font(None, TAM_FONTE)
    return tela, relogio, fonte

# -------------------------
# Coordenadas
# -------------------------
def mundo_para_tela(x, y):
    cx, cy = LARGURA // 2, ALTURA // 2
    return int(round(cx + x)), int(round(cy - y))

def tela_para_mundo(sx, sy):
    cx, cy = LARGURA // 2, ALTURA // 2
    return sx - cx, cy - sy

# -------------------------
# Grade / eixos
# -------------------------
def desenhar_grade(tela):
    tela.fill(COR_FUNDO)
    cx, cy = LARGURA // 2, ALTURA // 2

    x = cx
    while x < LARGURA:
        pg.draw.line(tela, COR_GRADE, (x, 0), (x, ALTURA), 1); x += PASSO_GRADE
    x = cx
    while x >= 0:
        pg.draw.line(tela, COR_GRADE, (x, 0), (x, ALTURA), 1); x -= PASSO_GRADE

    y = cy
    while y < ALTURA:
        pg.draw.line(tela, COR_GRADE, (0, y), (LARGURA, y), 1); y += PASSO_GRADE
    y = cy
    while y >= 0:
        pg.draw.line(tela, COR_GRADE, (0, y), (LARGURA, y), 1); y -= PASSO_GRADE

    pg.draw.line(tela, COR_EIXOS, (0, cy), (LARGURA, cy), 2)   # eixo X
    pg.draw.line(tela, COR_EIXOS, (cx, 0), (cx, ALTURA), 2)    # eixo Y
    pg.draw.circle(tela, COR_CENTRO, (cx, cy), 3)

# -------------------------
# UI
# -------------------------
def desenhar_painel(tela, fonte, algoritmo):
    pad_x, pad_y = 10, 8
    w, h = 120, 28

    barra = pg.Rect(0, 0, LARGURA, ALTURA_PAINEL)
    pg.draw.rect(tela, COR_PAINEL, barra)

    r_dda = pg.Rect(pad_x, pad_y, w, h)
    pg.draw.rect(tela, COR_BOTAO_ATIVO if algoritmo == ALGO_DDA else COR_BOTAO, r_dda, border_radius=6)
    pg.draw.rect(tela, COR_BORDA_BOTAO, r_dda, 1, border_radius=6)
    tela.blit(fonte.render("DDA", True, (0,0,0)), r_dda.move(10,5).topleft)

    r_bres = pg.Rect(r_dda.right + 10, pad_y, w, h)
    pg.draw.rect(tela, COR_BOTAO_ATIVO if algoritmo == ALGO_BRES else COR_BOTAO, r_bres, border_radius=6)
    pg.draw.rect(tela, COR_BORDA_BOTAO, r_bres, 1, border_radius=6)
    tela.blit(fonte.render("Bresenham", True, (0,0,0)), r_bres.move(10,5).topleft)

    r_limpar = pg.Rect(r_bres.right + 20, pad_y, w, h)
    pg.draw.rect(tela, COR_BOTAO, r_limpar, border_radius=6)
    pg.draw.rect(tela, COR_BORDA_BOTAO, r_limpar, 1, border_radius=6)
    tela.blit(fonte.render("Limpar", True, (0,0,0)), r_limpar.move(10,5).topleft)

    return r_dda, r_bres, r_limpar

# -------------------------
# Rasterização (pixel a pixel)
# -------------------------
def put_pixel(tela, x, y, cor):
    if 0 <= x < LARGURA and 0 <= y < ALTURA:
        tela.set_at((int(x), int(y)), cor)

def reta_dda(tela, x0, y0, x1, y1, cor):
    x0, y0 = float(x0), float(y0)
    x1, y1 = float(x1), float(y1)
    dx, dy = x1 - x0, y1 - y0
    passos = int(max(abs(dx), abs(dy)))
    if passos == 0:
        put_pixel(tela, round(x0), round(y0), cor); return
    inc_x, inc_y = dx / passos, dy / passos
    x, y = x0, y0
    for _ in range(passos + 1):
        put_pixel(tela, round(x), round(y), cor)
        x += inc_x; y += inc_y

def reta_bresenham(tela, x0, y0, x1, y1, cor):
    x0, y0 = int(round(x0)), int(round(y0))
    x1, y1 = int(round(x1)), int(round(y1))
    steep = abs(y1 - y0) > abs(x1 - x0)
    if steep: x0, y0, x1, y1 = y0, x0, y1, x1
    if x0 > x1: x0, x1, y0, y1 = x1, x0, y1, y0
    dx, dy = x1 - x0, abs(y1 - y0)
    err = dx // 2
    ystep = 1 if y0 < y1 else -1
    y = y0
    for x in range(x0, x1 + 1):
        if steep: put_pixel(tela, y, x, cor)
        else:     put_pixel(tela, x, y, cor)
        err -= dy
        if err < 0: y += ystep; err += dx

# -------------------------
# Desenho de entidades
# -------------------------
def desenhar_pontos(tela, fonte, pontos_mundo):
    for (x, y) in pontos_mundo:
        sx, sy = mundo_para_tela(x, y)
        pg.draw.circle(tela, COR_PONTO, (sx, sy), RAIO_PONTO)
        label = fonte.render(f"({x}, {y})", True, COR_TEXTO)
        tela.blit(label, (sx + DESLOC_TEXTO[0], sy + DESLOC_TEXTO[1]))

def desenhar_retas(tela, retas_mundo, algoritmo):
    # log.info("Desenhando reta")
    for (ax, ay), (bx, by) in retas_mundo:
        sx0, sy0 = mundo_para_tela(ax, ay)
        sx1, sy1 = mundo_para_tela(bx, by)
        if algoritmo == ALGO_DDA:
            reta_dda(tela, sx0, sy0, sx1, sy1, COR_RETA)
        else:
            reta_bresenham(tela, sx0, sy0, sx1, sy1, COR_RETA)

def desenhar_previa(tela, ponto_A_mundo, pos_mouse_tela):
    if ponto_A_mundo is None or pos_mouse_tela is None:
        return
    ax, ay = mundo_para_tela(*ponto_A_mundo)
    mx, my = pos_mouse_tela
    if my < ALTURA_PAINEL:  # não desenhar sobre o painel
        my = ALTURA_PAINEL
    pg.draw.line(tela, COR_PREVIA, (ax, ay), (mx, my), ESP_GUIA)

# -------------------------
# Main loop
# -------------------------
def main():
    tela, relogio, fonte = inicializar()

    algoritmo = ALGO_BRES
    pontos_mundo = []   # lista de todos os pontos colocados (x,y)
    retas_mundo = []    # lista de segmentos [((xA,yA),(xB,yB)), ...]
    ponto_A = None      # primeiro ponto aguardando B
    log.info("Aplicação iniciada | algoritmo inicial=%s", algoritmo)
    rodando = True
    
    while rodando:
        # DESENHO
        desenhar_grade(tela)
        r_dda, r_bres, r_limpar = desenhar_painel(tela, fonte, algoritmo)
        desenhar_retas(tela, retas_mundo, algoritmo)
        desenhar_pontos(tela, fonte, pontos_mundo)
        if ponto_A is not None:
            desenhar_previa(tela, ponto_A, pg.mouse.get_pos())

        pg.display.flip()
        relogio.tick(60)

        # EVENTOS
        for ev in pg.event.get():
            if ev.type == pg.QUIT:
                log.info("Evento: QUIT | encerrando aplicação")
                rodando = False

            elif ev.type == pg.MOUSEBUTTONDOWN and ev.button == 1:
                sx, sy = ev.pos
                log.info("Clique | tela=(%d,%d)", sx, sy)

                # Botões
                if r_dda.collidepoint(sx, sy):
                    if algoritmo != ALGO_DDA:
                        algoritmo = ALGO_DDA
                        log.info("Algoritmo alterado para DDA")
                        dump_estado(pontos_mundo, retas_mundo, algoritmo, ponto_A)
                    continue
                if r_bres.collidepoint(sx, sy):
                    if algoritmo != ALGO_BRES:
                        algoritmo = ALGO_BRES
                        log.info("Algoritmo alterado para Bresenham")
                        dump_estado(pontos_mundo, retas_mundo, algoritmo, ponto_A)
                    continue
                if r_limpar.collidepoint(sx, sy):
                    pontos_mundo.clear(); retas_mundo.clear(); ponto_A = None; continue

                # Ignora cliques no painel
                if sy < ALTURA_PAINEL:
                    log.info("Clique descartado (painel)")
                    continue


                # Clique no canvas: cada clique plota ponto; a cada par de cliques cria reta
                x, y = tela_para_mundo(sx, sy)
                log.info("Conversão | mundo=(%d,%d)", x, y)
                pontos_mundo.append((x, y))
                log.info("Ponto criado | aguardando par? %s | ponto=(%d,%d)", ponto_A is not None, x, y)
                if ponto_A is None:
                    ponto_A = (x, y)
                    log.info("Definido Ponto A | A=%s", ponto_A)
                else:
                    ponto_B = (x, y)
                    retas_mundo.append((ponto_A, ponto_B))
                    log.info("Reta criada | A=%s B=%s | algoritmo=%s", ponto_A, ponto_B, algoritmo)
                    ponto_A = None
                    dump_estado(pontos_mundo, retas_mundo, algoritmo, ponto_A)
    pg.quit()
    sys.exit()

if __name__ == "__main__":
    main()
