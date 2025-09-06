import sys
import logging
from pprint import pformat
import pygame as pg
from entities import Ponto, Reta, Circunferencia, Poligono
# (opcional) base para futuras transformações: from transformacoes import Translacao, Escala, Rotacao

# -------------------------
# Configuração de logging
# -------------------------
LOG_LEVEL = logging.INFO
def configurar_logging():
    logger = logging.getLogger("TP1_OOP_FULL")
    logger.setLevel(LOG_LEVEL)
    logger.handlers.clear()
    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s", "%H:%M:%S")
    ch = logging.StreamHandler(sys.stdout); ch.setLevel(LOG_LEVEL); ch.setFormatter(fmt)
    fh = logging.FileHandler("tp1_oop_full.log", mode="w", encoding="utf-8")
    fh.setLevel(LOG_LEVEL); fh.setFormatter(fmt)
    logger.addHandler(ch); logger.addHandler(fh)
    return logger

log = configurar_logging()

# -------------------------
# Constantes de UI
# -------------------------
LARGURA_TOTAL, ALTURA = 1200, 700
LARGURA_PAINEL = 320
LARGURA_CANVAS = LARGURA_TOTAL - LARGURA_PAINEL

COR_FUNDO = (255,255,255)
COR_PAINEL_BG = (245,245,245)
COR_PAINEL_BORDA = (200,200,200)
COR_TAB_ATIVA = (200,220,255)
COR_TAB_INATIVA = (230,230,230)
COR_BOTAO = (230,230,230)
COR_BOTAO_ATIVO = (200,220,255)
COR_BORDA = (180,180,180)

PASSO_GRADE = 25
COR_GRADE = (225,225,225)
COR_EIXOS = (120,120,120)
COR_CENTRO = (180,60,60)

COR_PONTO = (0,0,0)
COR_TEXTO = (0,0,255)
RAIO_PONTO = 3
DESLOC_TEXTO = (8,-12)

COR_RETA = (0,0,0)
COR_PREVIA = (120,120,120)
COR_CIRC = (0,0,0)
COR_POLI = (0,0,0)

# Destaques de seleção (Transformações)
COR_SEL_BORDA = (30,144,255)        # azul "dodger blue"
COR_SEL_FILL  = (30,144,255,60)     # com alpha
COR_PONTO_SEL = (0,128,255)         # ponto selecionado

TAM_FONTE = 16

ABA_RETAS  = "RETAS"
ABA_CIRC   = "CIRCUNF"
ABA_POLI   = "POLIGONOS"
ABA_TRANSF = "TRANSFORM"

ALGO_DDA  = "DDA"
ALGO_BRES = "BRESENHAM"

ESP_GUIA = 1  # espessura de guias/linhas de prévia

# -------------------------
# Inicialização / conversões
# -------------------------
def inicializar():
    pg.init()
    pg.display.set_caption("TP1 CG — OOP completo")
    tela = pg.display.set_mode((LARGURA_TOTAL, ALTURA))
    relogio = pg.time.Clock()
    fonte = pg.font.Font(None, TAM_FONTE)
    log.info("Pygame inicializado: %dx%d", LARGURA_TOTAL, ALTURA)
    return tela, relogio, fonte

def mundo_para_tela(x,y):
    cx, cy = LARGURA_CANVAS//2, ALTURA//2
    return int(cx + x), int(cy - y)

def tela_para_mundo(sx,sy):
    cx, cy = LARGURA_CANVAS//2, ALTURA//2
    return sx - cx, cy - sy

# -------------------------
# Canvas: grade e eixos
# -------------------------
def desenhar_canvas(tela):
    tela.fill(COR_FUNDO, rect=pg.Rect(0, 0, LARGURA_CANVAS, ALTURA))
    cx, cy = LARGURA_CANVAS//2, ALTURA//2
    # Grade vertical
    x = cx
    while x < LARGURA_CANVAS:
        pg.draw.line(tela, COR_GRADE, (x,0),(x,ALTURA),1); x += PASSO_GRADE
    x = cx
    while x >= 0:
        pg.draw.line(tela, COR_GRADE, (x,0),(x,ALTURA),1); x -= PASSO_GRADE
    # Grade horizontal
    y = cy
    while y < ALTURA:
        pg.draw.line(tela, COR_GRADE, (0,y),(LARGURA_CANVAS,y),1); y += PASSO_GRADE
    y = cy
    while y >= 0:
        pg.draw.line(tela, COR_GRADE, (0,y),(LARGURA_CANVAS,y),1); y -= PASSO_GRADE
    # Eixos
    pg.draw.line(tela, COR_EIXOS, (0,cy),(LARGURA_CANVAS,cy),2)
    pg.draw.line(tela, COR_EIXOS, (cx,0),(cx,ALTURA),2)
    pg.draw.circle(tela, COR_CENTRO, (cx,cy),3)

# -------------------------
# Painel lateral
# -------------------------
def desenhar_painel(tela, fonte, aba, algo):
    painel_rect = pg.Rect(LARGURA_CANVAS, 0, LARGURA_PAINEL, ALTURA)
    pg.draw.rect(tela, COR_PAINEL_BG, painel_rect)
    pg.draw.line(tela, COR_PAINEL_BORDA, (LARGURA_CANVAS,0),(LARGURA_CANVAS,ALTURA),1)

    # Abas
    tabs = [(ABA_RETAS,"Retas"),(ABA_CIRC,"Circunf."),(ABA_POLI,"Polígonos"),(ABA_TRANSF,"Transform.")]
    tab_rects={}
    pad=10; tab_w=LARGURA_PAINEL-pad*2; tab_h=34; y=pad
    for key,label in tabs:
        r=pg.Rect(LARGURA_CANVAS+pad,y,tab_w,tab_h)
        cor=COR_TAB_ATIVA if key==aba else COR_TAB_INATIVA
        pg.draw.rect(tela, cor, r, border_radius=8)
        pg.draw.rect(tela, COR_BORDA, r, 1, border_radius=8)
        surf=fonte.render(label,True,(0,0,0))
        tela.blit(surf, surf.get_rect(center=r.center))
        tab_rects[key]=r; y+=tab_h+6

    # Conteúdo
    ctrl_rects={}
    content_x=LARGURA_CANVAS+pad
    content_y=y+6
    tela.blit(fonte.render(f"Opções — {aba.title()}",True,(0,0,0)), (content_x,content_y))
    cy=content_y+28
    btn_w=150; btn_h=36

    if aba==ABA_RETAS:
        r_dda=pg.Rect(content_x,cy,btn_w,btn_h)
        r_bres=pg.Rect(content_x+btn_w+12,cy,btn_w,btn_h)
        pg.draw.rect(tela, COR_BOTAO_ATIVO if algo==ALGO_DDA else COR_BOTAO, r_dda, border_radius=8)
        pg.draw.rect(tela, COR_BOTAO_ATIVO if algo==ALGO_BRES else COR_BOTAO, r_bres, border_radius=8)
        pg.draw.rect(tela, COR_BORDA, r_dda,1,border_radius=8)
        pg.draw.rect(tela, COR_BORDA, r_bres,1,border_radius=8)
        tela.blit(fonte.render("DDA",True,(0,0,0)), fonte.render("DDA",True,(0,0,0)).get_rect(center=r_dda.center))
        tela.blit(fonte.render("Bresenham",True,(0,0,0)), fonte.render("Bresenham",True,(0,0,0)).get_rect(center=r_bres.center))
        cy+=btn_h+12
        r_limpar=pg.Rect(content_x,cy,btn_w,btn_h)
        pg.draw.rect(tela, COR_BOTAO, r_limpar, border_radius=8)
        pg.draw.rect(tela, COR_BORDA, r_limpar,1,border_radius=8)
        tela.blit(fonte.render("Limpar",True,(0,0,0)), fonte.render("Limpar",True,(0,0,0)).get_rect(center=r_limpar.center))
        ctrl_rects={"DDA":r_dda,"BRES":r_bres,"LIMPAR":r_limpar}

    elif aba==ABA_CIRC:
        r_limpar=pg.Rect(content_x,cy,btn_w,btn_h)
        pg.draw.rect(tela, COR_BOTAO, r_limpar, border_radius=8)
        pg.draw.rect(tela, COR_BORDA, r_limpar,1,border_radius=8)
        tela.blit(fonte.render("Limpar",True,(0,0,0)), fonte.render("Limpar",True,(0,0,0)).get_rect(center=r_limpar.center))
        ctrl_rects={"LIMPAR":r_limpar}
        _texto_multilinha(tela, fonte, [
            "Clique 1: centro",
            "Clique 2: raio",
            "Bresenham para círculos."
        ], content_x, cy+btn_h+16)

    elif aba==ABA_POLI:
        r_limpar=pg.Rect(content_x,cy,btn_w,btn_h)
        pg.draw.rect(tela, COR_BOTAO, r_limpar, border_radius=8)
        pg.draw.rect(tela, COR_BORDA, r_limpar,1,border_radius=8)
        tela.blit(fonte.render("Limpar",True,(0,0,0)), fonte.render("Limpar",True,(0,0,0)).get_rect(center=r_limpar.center))
        ctrl_rects={"LIMPAR":r_limpar}
        _texto_multilinha(tela, fonte, [
            "Clique esquerdo: adiciona vértice",
            "Clique direito: finaliza polígono (ABERTO)",
            "Arestas com algoritmo atual"
        ], content_x, cy+btn_h+16)

    elif aba==ABA_TRANSF:
        r_limpar=pg.Rect(content_x,cy,btn_w,btn_h)
        pg.draw.rect(tela, COR_BOTAO, r_limpar, border_radius=8)
        pg.draw.rect(tela, COR_BORDA, r_limpar,1,border_radius=8)
        tela.blit(fonte.render("Limpar",True,(0,0,0)), fonte.render("Limpar",True,(0,0,0)).get_rect(center=r_limpar.center))
        ctrl_rects={"LIMPAR":r_limpar}
        _texto_multilinha(tela, fonte, [
            "TRANSFORMAÇÕES:",
            "- Arraste com botão esquerdo para selecionar pontos",
            "- Solte para concluir a seleção",
            "- (após isso, aplique translação/rotação/escala)"
        ], content_x, cy+btn_h+16)

    return tab_rects, ctrl_rects

def _texto_multilinha(tela, fonte, linhas, x, y, dy=20):
    for ln in linhas:
        surf=fonte.render(ln,True,(0,0,0))
        tela.blit(surf,(x,y)); y+=dy

# -------------------------
# Desenho de entidades e previews
# -------------------------
def desenhar_pontos(tela, fonte, pontos):
    for p in pontos:
        p.draw(tela, mundo_para_tela, radius=RAIO_PONTO, color=COR_PONTO, font=fonte, label_color=COR_TEXTO)

def desenhar_pontos_selecionados(tela, fonte, selecionados):
    # destaca os pontos selecionados (raio maior e cor diferente)
    for p in selecionados:
        sx, sy = mundo_para_tela(p.x, p.y)
        pg.draw.circle(tela, COR_PONTO_SEL, (sx, sy), RAIO_PONTO + 2)

def desenhar_retas(tela, retas):
    for r in retas:
        r.draw(tela, mundo_para_tela, color=COR_RETA)

def desenhar_circs(tela, circs):
    for c in circs:
        c.draw(tela, mundo_para_tela, color=COR_CIRC)

def desenhar_poligonos(tela, poligonos):
    for poly in poligonos:
        poly.draw(tela, mundo_para_tela, color=COR_POLI)

def desenhar_previa_poligono(tela, vertices, pos_mouse, algo):
    if not vertices:
        return
    for i in range(len(vertices)-1):
        edge=Reta(vertices[i], vertices[i+1], algo)
        edge.draw(tela, mundo_para_tela, color=COR_PREVIA)
    last=vertices[-1]
    ax, ay = mundo_para_tela(last.x, last.y)
    mx, my = pos_mouse
    if mx>=LARGURA_CANVAS: mx=LARGURA_CANVAS-1
    pg.draw.line(tela, COR_PREVIA, (ax,ay),(mx,my),ESP_GUIA)

def desenhar_retangulo_selec(tela, rect_screen):
    """Desenha um retângulo semi-transparente (preview de seleção)."""
    if rect_screen is None:
        return
    r = rect_screen.copy()
    r.normalize()  # garante largura/altura positivas
    # fill translúcido
    fill_surf = pg.Surface((max(r.w,1), max(r.h,1)), pg.SRCALPHA)
    fill_surf.fill(COR_SEL_FILL)
    tela.blit(fill_surf, r.topleft)
    # borda
    pg.draw.rect(tela, COR_SEL_BORDA, r, width=2)

# -------------------------
# Main
# -------------------------
def main():
    tela, relogio, fonte = inicializar()

    aba  = ABA_RETAS
    algo = ALGO_BRES

    pontos=[]; retas=[]; circs=[]; poligonos=[]
    ponto_A=None; circ_centro=None; poliverts=[]

    # --- Estado de seleção (Transformações)
    selecionando = False                 # se está arrastando o retângulo
    selec_inicio_screen = None           # (sx0, sy0) início do arrasto
    selec_rect_screen = None             # pygame.Rect em coordenadas de tela
    pontos_selecionados = []             # lista de objetos Ponto selecionados

    def limpar_tudo():
        nonlocal pontos, retas, circs, poligonos, ponto_A, circ_centro, poliverts
        nonlocal selecionando, selec_inicio_screen, selec_rect_screen, pontos_selecionados
        pontos.clear(); retas.clear(); circs.clear(); poligonos.clear()
        ponto_A=None; circ_centro=None; poliverts=[]
        selecionando=False; selec_inicio_screen=None; selec_rect_screen=None; pontos_selecionados=[]
        log.info("Canvas limpo")

    rodando=True
    while rodando:
        # --- DESENHO
        desenhar_canvas(tela)
        tab_rects, ctrl_rects = desenhar_painel(tela, fonte, aba, algo)

        # Entidades
        desenhar_poligonos(tela, poligonos)
        desenhar_retas(tela, retas)
        desenhar_circs(tela, circs)
        desenhar_pontos(tela, fonte, pontos)

        # Destaque dos selecionados (sempre por cima)
        if pontos_selecionados:
            desenhar_pontos_selecionados(tela, fonte, pontos_selecionados)

        # Pré-visualizações
        if aba==ABA_POLI:
            desenhar_previa_poligono(tela, poliverts, pg.mouse.get_pos(), algo)

        # Retângulo de seleção (Transformações) enquanto arrasta
        if aba==ABA_TRANSF and selecionando and selec_rect_screen is not None:
            desenhar_retangulo_selec(tela, selec_rect_screen)

        pg.display.flip()
        relogio.tick(60)

        # --- EVENTOS
        for ev in pg.event.get():
            if ev.type==pg.QUIT:
                rodando=False

            elif ev.type==pg.MOUSEBUTTONDOWN:
                sx, sy = ev.pos

                # clique no painel
                if sx>=LARGURA_CANVAS:
                    trocou=False
                    for key,r in tab_rects.items():
                        if r.collidepoint(sx,sy) and key!=aba:
                            # trocar de aba: reset prévias de construção e seleção
                            aba=key; ponto_A=None; circ_centro=None; poliverts=[]
                            selecionando=False; selec_inicio_screen=None; selec_rect_screen=None
                            trocou=True; break
                    if trocou: continue

                    # botões do painel
                    if "LIMPAR" in ctrl_rects and ctrl_rects["LIMPAR"].collidepoint(sx,sy):
                        limpar_tudo(); continue
                    if aba==ABA_RETAS:
                        if "DDA" in ctrl_rects and ctrl_rects["DDA"].collidepoint(sx,sy):
                            algo=ALGO_DDA; continue
                        if "BRES" in ctrl_rects and ctrl_rects["BRES"].collidepoint(sx,sy):
                            algo=ALGO_BRES; continue
                    continue  # painel tratado

                # clique no CANVAS
                # --- Aba Transformações: iniciar seleção retangular com botão esquerdo
                if aba==ABA_TRANSF and ev.button==1:
                    selecionando = True
                    selec_inicio_screen = (sx, sy)
                    selec_rect_screen = pg.Rect(sx, sy, 0, 0)
                    # não cria ponto nesta aba
                    continue

                # Nas demais abas, comportamento normal de construção
                x,y = tela_para_mundo(sx,sy)
                novo_p = Ponto(x,y)

                if ev.button==1:  # esquerdo
                    pontos.append(novo_p)
                    if aba==ABA_RETAS:
                        if ponto_A is None:
                            ponto_A=novo_p
                        else:
                            retas.append(Reta(ponto_A, novo_p, algo))
                            ponto_A=None
                    elif aba==ABA_CIRC:
                        if circ_centro is None:
                            circ_centro=novo_p
                        else:
                            dx=novo_p.x-circ_centro.x; dy=novo_p.y-circ_centro.y
                            raio=int(round((dx*dx+dy*dy)**0.5))
                            circs.append(Circunferencia(circ_centro, raio))
                            circ_centro=None
                    elif aba==ABA_POLI:
                        poliverts.append(novo_p)

                elif ev.button == 3:  # direito: concluir polígono ABERTO
                    if aba == ABA_POLI and len(poliverts) >= 2:
                        novo_poly = Poligono(vertices=poliverts.copy(), fechado=False)
                        poligonos.append(novo_poly)
                        poliverts.clear()
                        log.info("Polígono aberto criado com %d vértices", len(novo_poly.vertices))

            elif ev.type==pg.MOUSEMOTION:
                # atualizar preview do retângulo de seleção enquanto arrasta
                if aba==ABA_TRANSF and selecionando and selec_inicio_screen is not None:
                    sx0, sy0 = selec_inicio_screen
                    sx1, sy1 = ev.pos
                    # clamp para não invadir o painel:
                    if sx1 >= LARGURA_CANVAS: sx1 = LARGURA_CANVAS-1
                    # atualiza rect de seleção
                    left   = min(sx0, sx1)
                    top    = min(sy0, sy1)
                    width  = abs(sx1 - sx0)
                    height = abs(sy1 - sy0)
                    selec_rect_screen.update(left, top, width, height)

            elif ev.type==pg.MOUSEBUTTONUP:
                # finalizar seleção retangular
                if aba==ABA_TRANSF and ev.button==1 and selecionando and selec_rect_screen is not None:
                    selecionando=False
                    # converte para mundo usando cantos do retângulo
                    r = selec_rect_screen.copy(); r.normalize()
                    # atenção: se r invadir painel, já fizemos clamp no motion
                    (xw1, yw1) = tela_para_mundo(r.left,  r.top)
                    (xw2, yw2) = tela_para_mundo(r.right, r.bottom)
                    xmin, xmax = (xw1, xw2) if xw1<=xw2 else (xw2, xw1)
                    ymin, ymax = (yw1, yw2) if yw1<=yw2 else (yw2, yw1)

                    # seleciona apenas Pontos dentro do retângulo
                    pontos_selecionados = [p for p in pontos if (xmin <= p.x <= xmax and ymin <= p.y <= ymax)]
                    log.info("Seleção concluída: %d pontos selecionados", len(pontos_selecionados))

                    # esconde o retângulo após concluir
                    selec_inicio_screen=None
                    selec_rect_screen=None

    pg.quit(); sys.exit()

if __name__ == "__main__":
    main()
