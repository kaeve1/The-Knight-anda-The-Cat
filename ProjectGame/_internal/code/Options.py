import sys
import pygame
import code.Settings as Settings
from code.Const import WIND_WIDHT, WIND_HEIGHT


_INFO = {
    'cat': [
        '7 lives  |  Damage capped at 1  |  +1 heart/wave',
    ],
    'knight': [
        '3 lives  |  Full damage  |  Heal only at boss room',
    ],
}

_NAMES  = ['cat', 'knight']
_LABELS = ['Cat  (Easy)', 'Knight  (Hard)']
_ACTIVE = [(255, 200, 50), (200, 80, 80)]
_DIMMED = [(120, 100, 30), (100, 40, 40)]

_CONTROLS = [
    ('A / D',     'Move'),
    ('W / Space', 'Jump'),
    ('Left Click',  'Attack'),
    ('Right Click', 'Defend'),
]


class Options:
    def __init__(self, window):
        self.window   = window
        self._sel     = _NAMES.index(Settings.DIFFICULTY)
        raw = pygame.image.load('./assets/options.png').convert()
        self._bg = pygame.transform.scale(raw, (WIND_WIDHT, WIND_HEIGHT))
        from code.Player import Player
        self._overlay = Player.build_screen_overlay(WIND_WIDHT, WIND_HEIGHT)

    def run(self):
        clock   = pygame.time.Clock()
        f_lg    = pygame.font.Font('./assets/font/Cardinal.ttf', 40)
        f_sm    = pygame.font.Font('./assets/font/Cardinal.ttf', 26)
        f_xs    = pygame.font.Font('./assets/font/Cardinal.ttf', 18)

        while True:
            clock.tick(60)

            # ── background ───────────────────────────────────────
            self.window.blit(self._bg, (0, 0))

            # title
            for dx, dy, col in [(2, 2, (0,0,0)), (0, 0, (255, 220, 50))]:
                t = f_lg.render('Difficulty', True, col)
                self.window.blit(t, t.get_rect(center=(WIND_WIDHT // 2 + dx, 35 + dy)))

            # divider
            pygame.draw.rect(self.window, (100, 70, 20),
                             (40, 56, WIND_WIDHT - 80, 2))

            # difficulty options
            for i, label in enumerate(_LABELS):
                col = _ACTIVE[i] if i == self._sel else _DIMMED[i]
                prefix = '► ' if i == self._sel else '  '
                s  = f_sm.render(prefix + label, True, col)
                sh = f_sm.render(prefix + label, True, (0, 0, 0))
                r  = s.get_rect(center=(WIND_WIDHT // 2, 82 + i * 36))
                self.window.blit(sh, (r.x + 2, r.y + 2))
                self.window.blit(s,  r)

            # info box (single line)
            line    = _INFO[_NAMES[self._sel]][0]
            box_x   = 40
            box_y   = 162
            box_w   = WIND_WIDHT - 80
            box_h   = 28
            pygame.draw.rect(self.window, (0, 0, 0),     (box_x + 2, box_y + 2, box_w, box_h))
            pygame.draw.rect(self.window, (20, 14, 8),   (box_x, box_y, box_w, box_h))
            pygame.draw.rect(self.window, (80, 55, 20),  (box_x, box_y, box_w, box_h), 1)
            s = f_xs.render(line, True, (180, 180, 160))
            self.window.blit(s, s.get_rect(center=(WIND_WIDHT // 2, box_y + box_h // 2)))

            # ── controls section ─────────────────────────────────
            for dx, dy, col in [(2, 2, (0, 0, 0)), (0, 0, (255, 220, 50))]:
                t = f_lg.render('Controls', True, col)
                self.window.blit(t, t.get_rect(center=(WIND_WIDHT // 2 + dx, 212 + dy)))

            pygame.draw.rect(self.window, (100, 70, 20),
                             (40, 232, WIND_WIDHT - 80, 2))

            cx   = WIND_WIDHT // 4        # key column center
            cx2  = WIND_WIDHT * 3 // 4   # action column center
            col_header = (140, 110, 50)
            sh_key = f_xs.render('Key', True, (0, 0, 0))
            s_key  = f_xs.render('Key', True, col_header)
            sh_act = f_xs.render('Action', True, (0, 0, 0))
            s_act  = f_xs.render('Action', True, col_header)
            rk = s_key.get_rect(center=(cx, 246))
            ra = s_act.get_rect(center=(cx2, 246))
            self.window.blit(sh_key, (rk.x + 1, rk.y + 1))
            self.window.blit(s_key, rk)
            self.window.blit(sh_act, (ra.x + 1, ra.y + 1))
            self.window.blit(s_act, ra)

            pygame.draw.line(self.window, (60, 45, 15),
                             (WIND_WIDHT // 2, 238), (WIND_WIDHT // 2, 314))

            for row, (key, action) in enumerate(_CONTROLS):
                y = 262 + row * 16
                sk  = f_xs.render(key,    True, (220, 200, 120))
                sa  = f_xs.render(action, True, (180, 180, 160))
                self.window.blit(sk, sk.get_rect(center=(cx,  y)))
                self.window.blit(sa, sa.get_rect(center=(cx2, y)))

            # hint
            hint = f_xs.render('↑↓ select    Enter confirm    Esc back',
                                True, (80, 80, 80))
            self.window.blit(hint, hint.get_rect(center=(WIND_WIDHT // 2, WIND_HEIGHT - 6)))

            self.window.blit(self._overlay, (0, 0))
            pygame.display.flip()

            # ── events ───────────────────────────────────────────
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_UP, pygame.K_DOWN):
                        self._sel = 1 - self._sel
                    elif event.key == pygame.K_RETURN:
                        Settings.DIFFICULTY = _NAMES[self._sel]
                        return
                    elif event.key == pygame.K_ESCAPE:
                        return
