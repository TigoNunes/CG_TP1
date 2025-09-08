import sys
import logging
import pygame as pg
from entities import Ponto, Reta, Circunferencia, Poligono
from transformacoes import Translacao, Rotacao, Escala

# -------------------------
# Logging
# -------------------------
LOG_LEVEL = logging.INFO

def configurar_logging():
    """
    Configura o sistema de logging para registrar eventos importantes.
    Loga tanto no console quanto em arquivo, evitando spam.
    """
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
# UI Consts
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
ESCALA = PASSO_GRADE * 1.0  # 1 unidade = 1 célula
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

# Seleção
COR_SEL_BORDA = (30,144,255)
COR_SEL_FILL  = (30,144,255,60)
COR_PONTO_SEL = (0,128,255)

# Modal
COR_MODAL_BG = (250,250,255)
COR_MODAL_BORDA = (100,120,160)
COR_INPUT_BG = (255,255,255)
COR_INPUT_BORDA = (100,100,100)
COR_BTN_OK = (180,240,200)
COR_BTN_CANCEL = (240,200,200)
COR_DIM = (0,0,0,90)

TAM_FONTE = 16

ABA_RETAS  = "RETAS"
ABA_CIRC   = "CIRCUNF"
ABA_POLI   = "POLIGONOS"
ABA_TRANSF = "TRANSFORM"

ALGO_DDA  = "DDA"
ALGO_BRES = "BRESENHAM"

ESP_GUIA = 1

# -------------------------
# Inicialização / conversões
# -------------------------

def inicializar():
    """
    Inicializa o pygame, configura a janela principal e fontes.
    Retorna a tela, relógio e fonte padrão.
    """
    pg.init()
    pg.display.set_caption("TP1 CG — OOP completo")
    tela = pg.display.set_mode((LARGURA_TOTAL, ALTURA))
    relogio = pg.time.Clock()
    fonte = pg.font.Font(None, TAM_FONTE)
    log.info("Pygame inicializado: %dx%d", LARGURA_TOTAL, ALTURA)
    return tela, relogio, fonte


def mundo_para_tela(x, y):
    """
    Converte coordenadas do mundo lógico para coordenadas de tela (pixels).
    """
    cx, cy = LARGURA_CANVAS//2, ALTURA//2
    return int(cx + x * ESCALA), int(cy - y * ESCALA)


def tela_para_mundo(sx, sy):
    """
    Converte coordenadas de tela (pixels) para o sistema de coordenadas do mundo lógico.
    """
    cx, cy = LARGURA_CANVAS//2, ALTURA//2
    return (sx - cx) / ESCALA, (cy - sy) / ESCALA

# -------------------------
# Canvas
# -------------------------

def desenhar_canvas(tela):
    """
    Desenha o fundo do canvas, grade, eixos e centro.
    """
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
    # Centro
    pg.draw.circle(tela, COR_CENTRO, (cx,cy),3)

# -------------------------
# Painel lateral
# -------------------------
def desenhar_painel(tela, fonte, aba, algo):
    """
    Desenha o painel lateral com abas, botões e controles de acordo com a aba ativa.
    Retorna os retângulos das abas e controles para detecção de clique.
    """
    painel_rect = pg.Rect(LARGURA_CANVAS, 0, LARGURA_PAINEL, ALTURA)
    pg.draw.rect(tela, COR_PAINEL_BG, painel_rect)
    pg.draw.line(tela, COR_PAINEL_BORDA, (LARGURA_CANVAS,0),(LARGURA_CANVAS,ALTURA),1)

    tabs = [(ABA_RETAS,"Retas"),(ABA_CIRC,"Circunf."),(ABA_POLI,"Polígonos"),(ABA_TRANSF,"Transform.")]
    tab_rects={}
    pad=10; tab_w=LARGURA_PAINEL-pad*2; tab_h=34; y=pad
    for key,label in tabs:
        r=pg.Rect(LARGURA_CANVAS+pad,y,tab_w,tab_h)
        cor=COR_TAB_ATIVA if key==aba else COR_TAB_INATIVA
        pg.draw.rect(tela, cor, r, border_radius=8)
        pg.draw.rect(tela, COR_BORDA, r, 1, border_radius=8)
        surf=pg.font.Font(None, TAM_FONTE).render(label,True,(0,0,0))
        tela.blit(surf, surf.get_rect(center=r.center))
        tab_rects[key]=r; y+=tab_h+6

    ctrl_rects={}
    content_x=LARGURA_CANVAS+pad
    content_y=y+6
    tela.blit(pg.font.Font(None, TAM_FONTE).render(f"Opções — {aba.title()}",True,(0,0,0)), (content_x,content_y))
    cy=content_y+28
    btn_w=150; btn_h=36

    if aba==ABA_RETAS:
        r_dda=pg.Rect(content_x,cy,btn_w,btn_h)
        r_bres=pg.Rect(content_x+btn_w+12,cy,btn_w,btn_h)
        pg.draw.rect(tela, COR_BOTAO_ATIVO if algo==ALGO_DDA else COR_BOTAO, r_dda, border_radius=8)
        pg.draw.rect(tela, COR_BOTAO_ATIVO if algo==ALGO_BRES else COR_BOTAO, r_bres, border_radius=8)
        pg.draw.rect(tela, COR_BORDA, r_dda,1,border_radius=8)
        pg.draw.rect(tela, COR_BORDA, r_bres,1,border_radius=8)
        tela.blit(pg.font.Font(None, TAM_FONTE).render("DDA",True,(0,0,0)), pg.font.Font(None, TAM_FONTE).render("DDA",True,(0,0,0)).get_rect(center=r_dda.center))
        tela.blit(pg.font.Font(None, TAM_FONTE).render("Bresenham",True,(0,0,0)), pg.font.Font(None, TAM_FONTE).render("Bresenham",True,(0,0,0)).get_rect(center=r_bres.center))
        cy+=btn_h+12
        r_limpar=pg.Rect(content_x,cy,btn_w,btn_h)
        pg.draw.rect(tela, COR_BOTAO, r_limpar, border_radius=8)
        pg.draw.rect(tela, COR_BORDA, r_limpar,1,border_radius=8)
        tela.blit(pg.font.Font(None, TAM_FONTE).render("Limpar",True,(0,0,0)), pg.font.Font(None, TAM_FONTE).render("Limpar",True,(0,0,0)).get_rect(center=r_limpar.center))
        ctrl_rects={"DDA":r_dda,"BRES":r_bres,"LIMPAR":r_limpar}

    elif aba==ABA_CIRC:
        r_limpar=pg.Rect(content_x,cy,btn_w,btn_h)
        pg.draw.rect(tela, COR_BOTAO, r_limpar, border_radius=8)
        pg.draw.rect(tela, COR_BORDA, r_limpar,1,border_radius=8)
        tela.blit(pg.font.Font(None, TAM_FONTE).render("Limpar",True,(0,0,0)), pg.font.Font(None, TAM_FONTE).render("Limpar",True,(0,0,0)).get_rect(center=r_limpar.center))
        ctrl_rects={"LIMPAR":r_limpar}

    elif aba==ABA_POLI:
        r_limpar=pg.Rect(content_x,cy,btn_w,btn_h)
        pg.draw.rect(tela, COR_BOTAO, r_limpar, border_radius=8)
        pg.draw.rect(tela, COR_BORDA, r_limpar,1,border_radius=8)
        tela.blit(pg.font.Font(None, TAM_FONTE).render("Limpar",True,(0,0,0)), pg.font.Font(None, TAM_FONTE).render("Limpar",True,(0,0,0)).get_rect(center=r_limpar.center))
        ctrl_rects={"LIMPAR":r_limpar}

    elif aba==ABA_TRANSF:
        r_limpar=pg.Rect(content_x,cy,btn_w,btn_h)
        pg.draw.rect(tela, COR_BOTAO, r_limpar, border_radius=8)
        pg.draw.rect(tela, COR_BORDA, r_limpar,1,border_radius=8)
        tela.blit(pg.font.Font(None, TAM_FONTE).render("Limpar",True,(0,0,0)), pg.font.Font(None, TAM_FONTE).render("Limpar",True,(0,0,0)).get_rect(center=r_limpar.center))
        ctrl_rects={"LIMPAR":r_limpar}
        _texto_multilinha(tela, pg.font.Font(None, TAM_FONTE), [
            "TRANSFORMAÇÕES:",
            "- Arraste com botão esquerdo p/ selecionar",
            "- Só objetos totalmente incluídos serão transformados",
            "- Preencha floats (ponto ou vírgula) e clique OK"
        ], content_x, cy+btn_h+16)

    return tab_rects, ctrl_rects

def _texto_multilinha(tela, fonte, linhas, x, y, dy=20):
    """
    Renderiza múltiplas linhas de texto na tela, útil para instruções.
    """
    for ln in linhas:
        surf=fonte.render(ln,True,(0,0,0))
        tela.blit(surf,(x,y)); y+=dy

# -------------------------
# InputBox (float, vírgula/ponto)
# -------------------------
class InputBox:
    """
    Caixa de entrada para valores numéricos (float), aceita ponto ou vírgula.
    """
    def __init__(self, x, y, w, h, text="0"):
        self.rect = pg.Rect(x,y,w,h)
        self.text = text
        self.active = False
        self.font = pg.font.Font(None, TAM_FONTE)

    def draw(self, tela):
        pg.draw.rect(tela, COR_INPUT_BG, self.rect)
        pg.draw.rect(tela, COR_INPUT_BORDA, self.rect, 2 if self.active else 1)
        surf = self.font.render(self.text, True, (0,0,0))
        tela.blit(surf, (self.rect.x+6, self.rect.y+8))

    def handle_event(self, ev):
        if ev.type == pg.MOUSEBUTTONDOWN and ev.button == 1:
            self.active = self.rect.collidepoint(ev.pos)
        elif ev.type == pg.KEYDOWN and self.active:
            if ev.key == pg.K_BACKSPACE:
                self.text = self.text[:-1] if self.text else ""
            elif ev.key in (pg.K_RETURN, pg.K_KP_ENTER):
                self.active = False
            else:
                ch = ev.unicode
                if self._can_insert(ch):
                    if ch == '-' and len(self.text) == 0:
                        self.text += ch
                    elif ch in ('.', ','):
                        if ('.' not in self.text) and (',' not in self.text):
                            self.text += ch
                    elif ch.isdigit():
                        self.text += ch
            if self.text == "-":
                pass

    def value(self, default=0.0):
        try:
            txt = self.text.strip()
            if txt in ("", "-", ".", "-.", ",", "-,"):
                return default
            txt = txt.replace(',', '.')
            return float(txt)
        except Exception:
            return default

    def _can_insert(self, ch):
        return (ch.isdigit() or ch in ['-','.',','])

# -------------------------
# Desenho entidades
# -------------------------
def desenhar_pontos(tela, fonte, pontos):
    """
    Desenha todos os pontos na tela, com rótulo.
    """
    for p in pontos:
        p.draw(tela, mundo_para_tela, radius=RAIO_PONTO, color=COR_PONTO, font=fonte, label_color=COR_TEXTO)

def desenhar_pontos_selecionados(tela, selecionados):
    """
    Destaca pontos selecionados com cor diferente.
    """
    for p in selecionados:
        sx, sy = mundo_para_tela(p.x, p.y)
        pg.draw.circle(tela, COR_PONTO_SEL, (sx, sy), RAIO_PONTO + 2)

def desenhar_retas(tela, retas):
    """
    Desenha todas as retas na tela.
    """
    for r in retas:
        r.draw(tela, mundo_para_tela, color=COR_RETA)

def desenhar_circs(tela, circs):
    """
    Desenha todas as circunferências na tela.
    """
    for c in circs:
        c.draw(tela, mundo_para_tela, color=COR_CIRC)

def desenhar_poligonos(tela, poligonos):
    """
    Desenha todos os polígonos na tela.
    """
    for poly in poligonos:
        poly.draw(tela, mundo_para_tela, color=COR_POLI)

def desenhar_previa_poligono(tela, vertices, pos_mouse, algo):
    """
    Desenha a prévia do polígono enquanto o usuário está adicionando vértices.
    """
    if not vertices: return
    for i in range(len(vertices)-1):
        Reta(vertices[i], vertices[i+1], algo).draw(tela, mundo_para_tela, color=COR_PREVIA)
    last=vertices[-1]
    ax, ay = mundo_para_tela(last.x, last.y)
    mx, my = pos_mouse
    if mx>=LARGURA_CANVAS: mx=LARGURA_CANVAS-1
    pg.draw.line(tela, COR_PREVIA, (ax,ay),(mx,my),ESP_GUIA)

def desenhar_retangulo_selec(tela, rect_screen):
    """
    Desenha o retângulo de seleção translúcido durante seleção de pontos.
    """
    if rect_screen is None: return
    r = rect_screen.copy(); r.normalize()
    dim = pg.Surface((LARGURA_CANVAS, ALTURA), pg.SRCALPHA); dim.fill(COR_DIM); tela.blit(dim, (0,0))
    fill_surf = pg.Surface((max(r.w,1), max(r.h,1)), pg.SRCALPHA); fill_surf.fill(COR_SEL_FILL)
    tela.blit(fill_surf, r.topleft)
    pg.draw.rect(tela, COR_SEL_BORDA, r, width=2)

# -------------------------
# Helpers seleção por objeto
# -------------------------
def _objetos_como_conjuntos(retas, circs, poligonos):
    """
    Retorna lista de conjuntos de pontos, um por objeto composto (reta, circunf., polígono).
    """
    grupos = []
    for r in retas:
        grupos.append({r.p1, r.p2})
    for c in circs:
        grupos.append({c.centro, c.borda})
    for poly in poligonos:
        grupos.append(set(poly.vertices))
    return grupos

def pontos_transformaveis(pontos_sel, retas, circs, poligonos):
    """
    Aplica a regra: só transforma objetos totalmente selecionados.
    Retorna o conjunto de pontos que podem ser transformados.
    """
    S = set(pontos_sel)
    grupos = _objetos_como_conjuntos(retas, circs, poligonos)

    # união dos grupos totalmente contidos em S
    transform = set()
    for g in grupos:
        if g.issubset(S):
            transform.update(g)

    # Pontos "soltos" (que não pertencem a nenhum objeto composto)
    pontos_participantes = set().union(*grupos) if grupos else set()
    for p in S:
        if p not in pontos_participantes:
            transform.add(p)

    return transform

def centroid(points):
    """
    Calcula o centróide (média das coordenadas) de uma lista de pontos.
    """
    if not points: return (0.0, 0.0)
    sx = sum(p.x for p in points); sy = sum(p.y for p in points); n = len(points)
    return (sx/n, sy/n)

# -------------------------
# Modal de Transformações
# -------------------------
def abrir_menu_transform(posicao_referencia, pontos_transform):
    """
    Cria o estado do modal de transformações (translação, rotação, escala).
    """
    w, h = 420, 220
    x = min(max(10, posicao_referencia[0]), LARGURA_CANVAS - w - 10)
    y = min(max(10, posicao_referencia[1]), ALTURA - h - 10)
    modal_rect = pg.Rect(x, y, w, h)

    gap_y = 34
    start_x = x + 14
    start_y = y + 40
    ib_w, ib_h = 90, 32

    input_dx = InputBox(start_x + 120, start_y, ib_w, ib_h, "0")
    input_dy = InputBox(start_x + 220, start_y, ib_w, ib_h, "0")
    input_ang = InputBox(start_x + 120, start_y + gap_y, ib_w, ib_h, "0")
    input_esc = InputBox(start_x + 120, start_y + 2*gap_y, ib_w, ib_h, "1")

    btn_ok = pg.Rect(x + w - 190, y + h - 50, 80, 34)
    btn_cancel = pg.Rect(x + w - 100, y + h - 50, 80, 34)

    return {
        "rect": modal_rect,
        "inputs": {"dx": input_dx, "dy": input_dy, "ang": input_ang, "esc": input_esc},
        "btn_ok": btn_ok,
        "btn_cancel": btn_cancel,
        "pivoto": centroid(list(pontos_transform)),
        "pontos": list(pontos_transform)
    }

def desenhar_menu_transform(tela, fonte, modal_state):
    """
    Desenha o modal de transformações com campos de entrada e botões.
    """
    r = modal_state["rect"]
    pg.draw.rect(tela, COR_MODAL_BG, r, border_radius=10)
    pg.draw.rect(tela, COR_MODAL_BORDA, r, 2, border_radius=10)

    titulo = fonte.render("Transformações (objetos completos)", True, (0,0,0))
    tela.blit(titulo, (r.x + 14, r.y + 12))

    lbl = fonte.render
    tela.blit(lbl("Translação:", True, (0,0,0)), (r.x+14, r.y+42))
    tela.blit(lbl("dx", True, (0,0,0)), (r.x+100, r.y+48))
    tela.blit(lbl("dy", True, (0,0,0)), (r.x+200, r.y+48))

    tela.blit(lbl("Rotação (graus):", True, (0,0,0)), (r.x+14, r.y+42+34))
    tela.blit(lbl("Escala (fator):", True, (0,0,0)), (r.x+14, r.y+42+68))

    cx, cy = modal_state["pivoto"]
    tela.blit(lbl(f"Pivô: centróide ({cx:.2f}, {cy:.2f})", True, (0,0,0)), (r.x+14, r.y+42+102))

    for ib in modal_state["inputs"].values():
        ib.draw(tela)

    pg.draw.rect(tela, COR_BTN_OK, modal_state["btn_ok"], border_radius=6)
    pg.draw.rect(tela, (0,0,0), modal_state["btn_ok"], 1, border_radius=6)
    ok_s = fonte.render("OK", True, (0,0,0))
    tela.blit(ok_s, ok_s.get_rect(center=modal_state["btn_ok"].center))

    pg.draw.rect(tela, COR_BTN_CANCEL, modal_state["btn_cancel"], border_radius=6)
    pg.draw.rect(tela, (0,0,0), modal_state["btn_cancel"], 1, border_radius=6)
    ca_s = fonte.render("Cancelar", True, (0,0,0))
    tela.blit(ca_s, ca_s.get_rect(center=modal_state["btn_cancel"].center))

# -------------------------
# Main
# -------------------------
def main():
    """
    Função principal do programa. Controla o loop de eventos, desenho e lógica de interação.
    """
    tela, relogio, fonte = inicializar()

    aba  = ABA_RETAS
    algo = ALGO_BRES

    pontos=[]; retas=[]; circs=[]; poligonos=[]
    ponto_A=None; circ_centro=None; poliverts=[]

    # Seleção
    selecionando = False
    selec_inicio_screen = None
    selec_rect_screen = None
    pontos_selecionados = []

    # Modal
    modal_open = False
    modal_state = None

    def limpar_tudo():
        """
        Limpa todas as entidades e estados da interface, reiniciando o canvas.
        """
        nonlocal pontos, retas, circs, poligonos, ponto_A, circ_centro, poliverts
        nonlocal selecionando, selec_inicio_screen, selec_rect_screen, pontos_selecionados
        nonlocal modal_open, modal_state
        pontos.clear(); retas.clear(); circs.clear(); poligonos.clear()
        ponto_A=None; circ_centro=None; poliverts=[]
        selecionando=False; selec_inicio_screen=None; selec_rect_screen=None; pontos_selecionados=[]
        modal_open=False; modal_state=None
        log.info("Canvas limpo")

    rodando=True

    while rodando:
        # --- Desenho da interface ---
        desenhar_canvas(tela)
        tab_rects, ctrl_rects = desenhar_painel(tela, fonte, aba, algo)
        desenhar_poligonos(tela, poligonos)
        desenhar_retas(tela, retas)
        desenhar_circs(tela, circs)
        desenhar_pontos(tela, fonte, pontos)
        if pontos_selecionados:
            desenhar_pontos_selecionados(tela, pontos_selecionados)
        if aba==ABA_POLI:
            desenhar_previa_poligono(tela, poliverts, pg.mouse.get_pos(), algo)
        if aba==ABA_TRANSF and selecionando and selec_rect_screen is not None:
            desenhar_retangulo_selec(tela, selec_rect_screen)
        if modal_open and modal_state:
            # Escurece fundo e desenha modal
            dim = pg.Surface((LARGURA_CANVAS, ALTURA), pg.SRCALPHA); dim.fill(COR_DIM); tela.blit(dim, (0,0))
            desenhar_menu_transform(tela, fonte, modal_state)
        pg.display.flip(); relogio.tick(60)


        # --- Loop de eventos ---
        for ev in pg.event.get():
            if ev.type==pg.QUIT:
                rodando=False
                continue

            # Modal consome eventos enquanto aberto
            if modal_open and modal_state:
                for ib in modal_state["inputs"].values():
                    ib.handle_event(ev)

                if ev.type == pg.MOUSEBUTTONDOWN and ev.button == 1:
                    if modal_state["btn_ok"].collidepoint(ev.pos):
                        dx  = modal_state["inputs"]["dx"].value(0.0)
                        dy  = modal_state["inputs"]["dy"].value(0.0)
                        ang = modal_state["inputs"]["ang"].value(0.0)
                        esc = modal_state["inputs"]["esc"].value(1.0)
                        pts = modal_state["pontos"]
                        cx, cy = modal_state["pivoto"]

                        if pts:
                            log.info(f"Aplicando transformações: dx={dx}, dy={dy}, ang={ang}, esc={esc}, n_pontos={len(pts)}")
                            Translacao(pts, dx, dy).aplicar()
                            Rotacao(pts, ang, (cx, cy)).aplicar()
                            Escala(pts, esc, (cx, cy)).aplicar()
                        modal_open=False; modal_state=None

                    elif modal_state["btn_cancel"].collidepoint(ev.pos):
                        modal_open=False; modal_state=None
                    else:
                        # Fecha modal se clicar fora dele (mas dentro do canvas)
                        if not modal_state["rect"].collidepoint(ev.pos) and ev.pos[0] < LARGURA_CANVAS:
                            modal_open=False; modal_state=None
                continue

            # --- UI normal ---
            if ev.type==pg.MOUSEBUTTONDOWN:
                sx, sy = ev.pos

                # Clique no painel lateral
                if sx>=LARGURA_CANVAS:
                    trocou=False
                    for key,r in tab_rects.items():
                        if r.collidepoint(sx,sy) and key!=aba:
                            aba=key; ponto_A=None; circ_centro=None; poliverts=[]
                            selecionando=False; selec_inicio_screen=None; selec_rect_screen=None
                            modal_open=False; modal_state=None
                            trocou=True; break
                    if trocou: continue

                    if "LIMPAR" in ctrl_rects and ctrl_rects["LIMPAR"].collidepoint(sx,sy):
                        limpar_tudo(); continue
                    if aba==ABA_RETAS:
                        if "DDA" in ctrl_rects and ctrl_rects["DDA"].collidepoint(sx,sy):
                            algo=ALGO_DDA; continue
                        if "BRES" in ctrl_rects and ctrl_rects["BRES"].collidepoint(sx,sy):
                            algo=ALGO_BRES; continue
                    continue

                # Clique no canvas
                if aba==ABA_TRANSF and ev.button==1:
                    selecionando = True
                    selec_inicio_screen = (sx, sy)
                    selec_rect_screen = pg.Rect(sx, sy, 0, 0)
                    continue

                x,y = tela_para_mundo(sx,sy)
                novo_p = Ponto(x,y)

                if ev.button==1:
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
                            # segundo clique define ponto de borda
                            circs.append(Circunferencia(circ_centro, novo_p))
                            circ_centro=None
                    elif aba==ABA_POLI:
                        poliverts.append(novo_p)

                elif ev.button == 3:
                    if aba == ABA_POLI and len(poliverts) >= 2:
                        novo_poly = Poligono(vertices=poliverts.copy(), fechado=False)
                        poligonos.append(novo_poly)
                        poliverts.clear()
                        log.info("Polígono aberto criado com %d vértices", len(novo_poly.vertices))

            elif ev.type==pg.MOUSEMOTION:
                # Atualiza retângulo de seleção durante arrasto
                if aba==ABA_TRANSF and selecionando and selec_inicio_screen is not None:
                    sx0, sy0 = selec_inicio_screen
                    sx1, sy1 = ev.pos
                    if sx1 >= LARGURA_CANVAS: sx1 = LARGURA_CANVAS-1
                    left   = min(sx0, sx1)
                    top    = min(sy0, sy1)
                    width  = abs(sx1 - sx0)
                    height = abs(sy1 - sy0)
                    selec_rect_screen.update(left, top, width, height)

            elif ev.type==pg.MOUSEBUTTONUP:
                # Finaliza seleção de pontos para transformação
                if aba==ABA_TRANSF and ev.button==1 and selecionando and selec_rect_screen is not None:
                    selecionando=False
                    r = selec_rect_screen.copy(); r.normalize()
                    (xw1, yw1) = tela_para_mundo(r.left,  r.top)
                    (xw2, yw2) = tela_para_mundo(r.right, r.bottom)
                    xmin, xmax = (xw1, xw2) if xw1<=xw2 else (xw2, xw1)
                    ymin, ymax = (yw1, yw2) if yw1<=yw2 else (yw2, yw1)
                    pontos_selecionados = [p for p in pontos if (xmin <= p.x <= xmax and ymin <= p.y <= ymax)]
                    log.info("Seleção concluída: %d pontos (brutos)", len(pontos_selecionados))
                    selec_inicio_screen=None
                    selec_rect_screen=None

                    # aplica regra: somente objetos completos
                    pts_ok = pontos_transformaveis(pontos_selecionados, retas, circs, poligonos)
                    log.info("Pontos transformáveis (objetos completos): %d", len(pts_ok))

                    if pts_ok:
                        ref_pos = (r.right + 10, r.top)
                        modal_open = True
                        modal_state = abrir_menu_transform(ref_pos, pts_ok)
                    else:
                        log.info("Nenhum objeto completo na seleção — modal não aberto.")

    pg.quit(); sys.exit()

if __name__ == "__main__":
    main()
