import sys
import math
import random
import pygame
from code.Const import WIND_WIDHT, WIND_HEIGHT, MENU_OPTION

# ── Castle layout constants ────────────────────────────────────────
_GY   = 206          # ground y
_CX   = 210          # main wall left
_CY   = 82           # main wall top
_CW   = 156          # main wall width
_CH   = _GY - _CY   # main wall height = 124

_LTX  = _CX - 32    # left tower left   = 178
_LTW  = 46          # tower width
_LTY  = 38          # tower top
_LTH  = _GY - _LTY  # tower height = 168

_RTX  = _CX + _CW - 14  # right tower left = 352
_RTW  = _LTW
_RTY  = _LTY
_RTH  = _LTH

_GW   = 32           # gate width
_GX   = _CX + _CW // 2 - _GW // 2   # gate left = 288-16 = 272

# Torch bracket positions (screen x, y of bracket base)
_TOR_L = (_CX + 38,        _GY - 52)
_TOR_R = (_CX + _CW - 52,  _GY - 52)


class Menu:
    def __init__(self, window):
        self.window      = window
        self.menu_option = 0
        self._t          = 0
        raw = pygame.image.load('./assets/startpixelart.png').convert()
        self._bg = pygame.transform.scale(raw, (WIND_WIDHT, WIND_HEIGHT))
        self._stars      = [
            (random.randint(0, WIND_WIDHT),
             random.randint(2, 130),
             random.choice([1, 1, 1, 2]),
             random.uniform(0, math.tau))
            for _ in range(90)
        ]
        # Reusable glow surface (SRCALPHA, created once)
        self._glow = pygame.Surface((28, 36), pygame.SRCALPHA)

    def run(self):
        pygame.mixer_music.load("./assets/music/Fase1.mp3")
        pygame.mixer_music.play(-1)
        clock = pygame.time.Clock()

        f_title = pygame.font.Font("assets/font/Cardinal.ttf", 52)
        f_sub   = pygame.font.Font("assets/font/Cardinal.ttf", 22)
        f_menu  = pygame.font.Font("assets/font/Cardinal.ttf", 30)

        _COL_SEL = [(80, 200, 255), (80, 210, 100), (255, 200, 50), (230, 80,  80)]
        _COL_DIM = [(32, 80, 110),  (32, 90,  42),  (110, 85, 20), (100, 34,  34)]

        while True:
            clock.tick(60)
            self._t += 1
            t = self._t

            # ── static background ─────────────────────────────
            self.window.blit(self._bg, (0, 0))

            # ── title (gentle bob) ────────────────────────────
            bob = int(3 * math.sin(t * 0.04))
            ty0 = 50 + bob
            for dx, dy, col in [(3, 3, (0, 0, 0)), (0, 0, (255, 228, 60))]:
                s = f_title.render("The Knight", True, col)
                self.window.blit(s, s.get_rect(center=(WIND_WIDHT // 2 + dx, ty0 + dy)))
            for dx, dy, col in [(2, 2, (0, 0, 0)), (0, 0, (220, 142, 22))]:
                s = f_sub.render("and the Cat", True, col)
                self.window.blit(s, s.get_rect(center=(WIND_WIDHT // 2 + dx, ty0 + 43 + dy)))

            # ── menu box ─────────────────────────────────────
            n      = len(MENU_OPTION)
            bh     = n * 38 + 18
            bx     = WIND_WIDHT // 2 - 90
            by     = 134
            bw     = 180

            pygame.draw.rect(self.window, (0, 0, 0),    (bx + 3, by + 3, bw, bh))
            pygame.draw.rect(self.window, (16, 11, 6),  (bx,     by,     bw, bh))
            pygame.draw.rect(self.window, (110, 78, 22),(bx,     by,     bw, bh), 2)
            # pixel corners
            for ox, oy in ((0, 0), (bw - 3, 0), (0, bh - 3), (bw - 3, bh - 3)):
                pygame.draw.rect(self.window, (210, 158, 40), (bx + ox, by + oy, 3, 3))

            for i, opt in enumerate(MENU_OPTION):
                sel = i == self.menu_option
                col = _COL_SEL[i] if sel else _COL_DIM[i]
                iy  = by + 10 + i * 38

                if sel:
                    # pulsing highlight row
                    pa = int(45 + 30 * math.sin(t * 0.1))
                    hl = pygame.Surface((bw - 4, 32), pygame.SRCALPHA)
                    hl.fill((*col, pa))
                    self.window.blit(hl, (bx + 2, iy + 2))
                    # blinking arrow
                    arr = f_menu.render('►', True, col)
                    self.window.blit(arr, arr.get_rect(midright=(bx + 24, iy + 16)))

                sh = f_menu.render(opt, True, (0, 0, 0))
                s  = f_menu.render(opt, True, col)
                r  = s.get_rect(midleft=(bx + 28, iy + 16))
                self.window.blit(sh, (r.x + 2, r.y + 2))
                self.window.blit(s,  r)

            # ── controls hint ─────────────────────────────────
            h = f_sub.render("↑↓  Move    Enter  Select", True, (62, 52, 42))
            self.window.blit(h, h.get_rect(center=(WIND_WIDHT // 2, WIND_HEIGHT - 10)))

            pygame.display.flip()

            # ── events ───────────────────────────────────────
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_DOWN:
                        self.menu_option = (self.menu_option + 1) % n
                    elif event.key == pygame.K_UP:
                        self.menu_option = (self.menu_option - 1) % n
                    elif event.key == pygame.K_RETURN:
                        return MENU_OPTION[self.menu_option]


# ── helpers ───────────────────────────────────────────────────────

def _stone(surf, rx, ry, rw, rh, base, line):
    pygame.draw.rect(surf, base, (rx, ry, rw, rh))
    for row, y in enumerate(range(ry + 8, ry + rh, 12)):
        pygame.draw.rect(surf, line, (rx, y, rw, 1))
        off = 0 if row % 2 == 0 else 10
        for x in range(rx + off, rx + rw, 20):
            pygame.draw.rect(surf, line, (x, y - 6, 1, 12))


def _battlements(surf, bx, by, bw, col):
    for x in range(bx, bx + bw, 12):
        pygame.draw.rect(surf, col, (x, by - 12, 8, 12))


def _build_bg():
    surf = pygame.Surface((WIND_WIDHT, WIND_HEIGHT))

    # Sky gradient (dark indigo → dark grey-blue)
    for y in range(_GY + 30):
        t = y / (_GY + 30)
        pygame.draw.rect(surf, (
            int(6  + t * 14),
            int(5  + t * 12),
            int(28 + t * 30),
        ), (0, y, WIND_WIDHT, 1))

    # Moon
    mx, my = 472, 54
    pygame.draw.circle(surf, (218, 208, 168), (mx, my), 30)
    pygame.draw.circle(surf, (205, 195, 155), (mx, my), 29)
    for cx, cy, cr, cc in (
        (mx - 10, my + 6,  5, (185, 175, 135)),
        (mx + 11, my - 5,  4, (188, 178, 138)),
        (mx + 2,  my + 15, 3, (190, 180, 140)),
    ):
        pygame.draw.circle(surf, cc, (cx, cy), cr)

    # Distant mountains
    mc = (14, 11, 34)
    for bx, peak in ((0,75),(70,95),(160,65),(250,85),(340,78),(430,90),(510,68)):
        pts = [(bx, _GY+10), (bx+60, _GY+10-peak), (bx+120, _GY+10)]
        pygame.draw.polygon(surf, mc, pts)

    # Ground gradient
    for y in range(_GY, WIND_HEIGHT):
        t = (y - _GY) / max(1, WIND_HEIGHT - _GY)
        pygame.draw.rect(surf, (
            int(18 + t * 8),
            int(14 + t * 6),
            int(8  + t * 4),
        ), (0, y, WIND_WIDHT, 1))
    pygame.draw.rect(surf, (48, 38, 24), (0, _GY, WIND_WIDHT, 3))

    # Castle colours
    wc  = (58, 48, 36)   # wall base
    sl  = (44, 37, 28)   # stone line
    dk  = (28, 22, 16)   # dark / gate

    # Left tower
    _stone(surf, _LTX, _LTY, _LTW, _LTH, wc, sl)
    _battlements(surf, _LTX, _LTY, _LTW, wc)
    # LT window
    pygame.draw.rect(surf, (10, 22, 58), (_LTX + 14, _LTY + 28, 14, 22))
    pygame.draw.rect(surf, (75, 52,  8), (_LTX + 15, _LTY + 28, 12,  6))

    # Right tower
    _stone(surf, _RTX, _RTY, _RTW, _RTH, wc, sl)
    _battlements(surf, _RTX, _RTY, _RTW, wc)
    pygame.draw.rect(surf, (10, 22, 58), (_RTX + 14, _RTY + 28, 14, 22))
    pygame.draw.rect(surf, (75, 52,  8), (_RTX + 15, _RTY + 28, 12,  6))

    # Main wall
    _stone(surf, _CX, _CY, _CW, _CH, wc, sl)
    _battlements(surf, _CX, _CY, _CW, wc)
    # Main wall windows
    for wx in (_CX + 28, _CX + _CW - 42):
        pygame.draw.rect(surf, (10, 22, 58), (wx, _CY + 20, 14, 22))
        pygame.draw.rect(surf, (70, 48,  8), (wx +  1, _CY + 20, 12,  6))

    # Gate arch
    gh = 48
    gx, gy = _GX, _GY - gh
    pygame.draw.rect(surf, dk, (gx, gy, _GW, gh))
    # rounded arch top
    r = _GW // 2
    for i in range(r):
        pygame.draw.rect(surf, dk, (gx + i, gy - int((r**2 - (i-r)**2)**0.5), 1, 1))
        pygame.draw.rect(surf, dk, (gx + _GW - 1 - i, gy - int((r**2 - (i-r)**2)**0.5), 1, 1))
    # portcullis grid
    for px in range(gx + 5, gx + _GW, 7):
        pygame.draw.rect(surf, (32, 25, 16), (px, gy + 10, 2, gh - 10))
    for py in range(gy + 16, gy + gh, 10):
        pygame.draw.rect(surf, (32, 25, 16), (gx + 3, py, _GW - 6, 1))

    # Torch brackets (static)
    for tx, ty in (_TOR_L, _TOR_R):
        pygame.draw.rect(surf, (95, 72, 32), (tx, ty, 6, 18))
        pygame.draw.rect(surf, (108, 84, 38), (tx - 3, ty, 12, 5))

    # Trees left
    for tx, th in ((18,62),(44,55),(72,68),(98,50),(124,60)):
        pygame.draw.rect(surf, (40, 26, 12), (tx + 5, _GY - 18, 6, 18))
        for l in range(3):
            lw = 24 - l * 5
            ly = _GY - 20 - th // 3 * (l + 1)
            c  = (10 + l * 6, 44 + l * 10, 12 + l * 4)
            pts = [(tx+8-lw//2, ly+20), (tx+8, ly), (tx+8+lw//2, ly+20)]
            pygame.draw.polygon(surf, c, pts)

    # Trees right
    for tx, th in ((438,60),(462,54),(488,66),(512,50),(536,58),(558,56)):
        pygame.draw.rect(surf, (40, 26, 12), (tx + 5, _GY - 18, 6, 18))
        for l in range(3):
            lw = 24 - l * 5
            ly = _GY - 20 - th // 3 * (l + 1)
            c  = (10 + l * 6, 44 + l * 10, 12 + l * 4)
            pts = [(tx+8-lw//2, ly+20), (tx+8, ly), (tx+8+lw//2, ly+20)]
            pygame.draw.polygon(surf, c, pts)

    # Path to gate
    pygame.draw.polygon(surf, (36, 29, 18), [
        (WIND_WIDHT // 2 - 28, WIND_HEIGHT),
        (WIND_WIDHT // 2 + 28, WIND_HEIGHT),
        (_GX + _GW, _GY + 2),
        (_GX,       _GY + 2),
    ])

    # Subtle ground mist
    fog = pygame.Surface((WIND_WIDHT, 22), pygame.SRCALPHA)
    for fy in range(22):
        a = int(38 * (1 - fy / 22))
        pygame.draw.rect(fog, (185, 200, 225, a), (0, fy, WIND_WIDHT, 1))
    surf.blit(fog, (0, _GY - 6))

    return surf
