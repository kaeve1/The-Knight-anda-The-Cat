import sys
import math
import random
import pygame
import code.Settings as Settings
import code.Score    as Score

from code.Player import Player
from code.Enemy import Enemy
from code.Const import WIND_WIDHT, WIND_HEIGHT, GROUND_Y

LOOPS = 6
LOOP_W = WIND_WIDHT                        # 576
CAT_WORLD_X = LOOPS * LOOP_W + 200        # 3656
MAX_CAMERA_X = CAT_WORLD_X - 50           # 3606
CAT_FRAME_W = 48
CAT_FRAME_H = 48
CAT_Y = 253   # player visual feet = GROUND_Y+61 = 301; cat 48px → 301-48 = 253

WAVE_TRIGGERS = [500, 1600, 2700]

WAVE_CONFIGS = [
    [('warrior', 620), ('spearman', 740), ('archer', 860)],
    [('warrior', 620), ('spearman', 740), ('archer', 860), ('archer', 980)],
    [('warrior', 620), ('warrior', 740), ('spearman', 860), ('archer', 980)],
]

# Camera limit per wave: rightmost enemy spawn - 100 (player can reach/attack it)
WAVE_MAX_CAM = [
    WAVE_TRIGGERS[i] + max(off for _, off in WAVE_CONFIGS[i]) - 100
    for i in range(3)
]

_WAVE_LABELS = ['Onda 1', 'Onda 2', 'Onda 3']

_CAT_IDLE_FRAMES = 4
_CAT_WALK_FRAMES = 6


def _load_cat(path, count, flip=False):
    sheet = pygame.image.load(path).convert_alpha()
    frames = [sheet.subsurface((i * CAT_FRAME_W, 0, CAT_FRAME_W, CAT_FRAME_H)).copy()
              for i in range(count)]
    if flip:
        frames = [pygame.transform.flip(f, True, False) for f in frames]
    return frames


# ── Partícula de hit ──────────────────────────────────────────────
class _Particle:
    def __init__(self, x, y, color):
        angle = random.uniform(0, math.tau)
        speed = random.uniform(1.5, 4.5)
        self.x   = float(x)
        self.y   = float(y)
        self.vx  = math.cos(angle) * speed
        self.vy  = math.sin(angle) * speed - 1.5
        self.life = random.randint(14, 22)
        self.max_life = self.life
        self.color = color

    def update(self):
        self.x  += self.vx
        self.y  += self.vy
        self.vy += 0.3
        self.life -= 1

    def draw(self, surface):
        size = max(1, self.life * 3 // self.max_life)
        pygame.draw.rect(surface, self.color, (int(self.x), int(self.y), size, size))


# ── Texto flutuante +♥ ───────────────────────────────────────────
class _FloatText:
    def __init__(self, surf, x, y):
        self._surf    = surf
        self.x        = float(x)
        self.y        = float(y)
        self.life     = 80
        self.max_life = 80

    def update(self):
        self.y   -= 1.0
        self.life -= 1

    def draw(self, surface):
        a   = int(255 * self.life / self.max_life)
        tmp = self._surf.copy()
        tmp.set_alpha(a)
        surface.blit(tmp, (int(self.x), int(self.y)))


def _make_life_gain_surf(font):
    """Cria surface '+♥' pixel-art para animação de ganho de vida."""
    plus_s = font.render('+', True, (0, 0, 0))
    plus   = font.render('+', True, (255, 80, 100))
    ph     = plus.get_height()
    pw     = plus.get_width()
    _hrows = [
        [(1,4),(7,4)], [(0,5),(6,5)], [(0,11)], [(0,11)],
        [(1,9)], [(2,7)], [(3,5)], [(4,3)], [(5,1)],
    ]
    hw, hh = 12, 9
    surf = pygame.Surface((pw + 6 + hw + 1, ph + 1), pygame.SRCALPHA)
    # shadow "+"
    surf.blit(plus_s, (2, 2))
    # "+"
    surf.blit(plus, (0, 0))
    hx = pw + 6
    hy = (ph - hh) // 2 + 1
    # sombra do coração
    for r, runs in enumerate(_hrows):
        for lx, w in runs:
            pygame.draw.rect(surf, (80, 0, 0), (hx + lx + 1, hy + r + 1, w, 1))
    # coração
    for r, runs in enumerate(_hrows):
        for lx, w in runs:
            pygame.draw.rect(surf, (255, 80, 100), (hx + lx, hy + r, w, 1))
    # highlight
    pygame.draw.rect(surf, (255, 160, 180), (hx + 1, hy, 2, 1))
    pygame.draw.rect(surf, (255, 160, 180), (hx + 7, hy, 2, 1))
    return surf


# ── Bolão de diálogo pixel-art ────────────────────────────────────
def _draw_bubble(surface, font, text, cx, top, text_color=(20, 20, 20),
                 bg=(255, 255, 230), border=(0, 0, 0)):
    txt  = font.render(text, True, text_color)
    pad  = 7
    bw   = txt.get_width()  + pad * 2
    bh   = txt.get_height() + pad * 2
    bx   = max(4, min(cx - bw // 2, WIND_WIDHT - bw - 4))
    by   = top - bh - 14

    # sombra pixel
    pygame.draw.rect(surface, (0, 0, 0),  (bx + 3, by + 3, bw, bh))
    # fundo
    pygame.draw.rect(surface, bg,         (bx, by, bw, bh))
    # borda 2px
    pygame.draw.rect(surface, border,     (bx, by, bw, bh), 2)
    # inner highlight (1px, canto sup-esq)
    pygame.draw.line(surface, (255, 255, 255), (bx + 2, by + 1), (bx + bw - 3, by + 1))
    pygame.draw.line(surface, (255, 255, 255), (bx + 1, by + 2), (bx + 1, by + bh - 3))

    # rabo pixel (triângulo feito de rects)
    tail_x = min(max(cx, bx + 10), bx + bw - 10)
    for row, w in enumerate([6, 4, 2, 2, 1]):
        rx = tail_x - w // 2
        ry = by + bh + row
        pygame.draw.rect(surface, bg,     (rx, ry, w, 1))
        pygame.draw.rect(surface, border, (rx, ry, 1, 1))
        pygame.draw.rect(surface, border, (rx + w - 1, ry, 1, 1))

    surface.blit(txt, (bx + pad, by + pad))


# ── Banner de fase cinemático ─────────────────────────────────────
def _show_phase_banner(window, clock, font, text):
    bar_h   = WIND_HEIGHT // 3 + 4
    mid     = WIND_HEIGHT // 2
    surf    = font.render(text, True, (255, 220, 50))
    shadow  = font.render(text, True, (0, 0, 0))
    rect    = surf.get_rect(center=(WIND_WIDHT // 2, mid))

    # Slide in (50 frames)
    for t in range(50):
        clock.tick(60)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
        p = (t / 49) ** 0.5         # ease out
        top_y = int(-bar_h + (mid - bar_h // 2 + bar_h) * p)
        bot_y = int(WIND_HEIGHT + (mid + bar_h // 2 - WIND_HEIGHT) * p)
        window.fill((0, 0, 0))
        pygame.draw.rect(window, (18, 12, 8), (0, top_y, WIND_WIDHT, bar_h))
        pygame.draw.rect(window, (18, 12, 8), (0, bot_y, WIND_WIDHT, bar_h))
        # gold line seam
        pygame.draw.rect(window, (180, 140, 20), (0, top_y + bar_h - 2, WIND_WIDHT, 2))
        pygame.draw.rect(window, (180, 140, 20), (0, bot_y, WIND_WIDHT, 2))
        pygame.display.flip()

    # Hold + text bounce in (70 frames)
    for t in range(70):
        clock.tick(60)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
        # bounce: overshoot at t=20, settle at t=40
        if t < 30:
            scale = t / 29
            dy = int((1 - scale) * 18 * math.sin(scale * math.pi))
        else:
            dy = 0
        window.fill((0, 0, 0))
        pygame.draw.rect(window, (18, 12, 8), (0, mid - bar_h // 2, WIND_WIDHT, bar_h))
        pygame.draw.rect(window, (180, 140, 20), (0, mid - bar_h // 2, WIND_WIDHT, 2))
        pygame.draw.rect(window, (180, 140, 20), (0, mid + bar_h // 2 - 2, WIND_WIDHT, 2))
        window.blit(shadow, (rect.x + 2, rect.y + 2 + dy))
        window.blit(surf,   (rect.x,     rect.y + dy))
        pygame.display.flip()

    # Slide out (35 frames)
    for t in range(35):
        clock.tick(60)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
        p = (t / 34) ** 2
        top_y = int(mid - bar_h // 2 - bar_h * p * 1.8)
        bot_y = int(mid + bar_h // 2 + (WIND_HEIGHT - mid - bar_h // 2) * p * 1.8)
        window.fill((0, 0, 0))
        pygame.draw.rect(window, (18, 12, 8), (0, top_y, WIND_WIDHT, bar_h))
        pygame.draw.rect(window, (18, 12, 8), (0, bot_y, WIND_WIDHT, bar_h))
        pygame.draw.rect(window, (180, 140, 20), (0, top_y + bar_h - 2, WIND_WIDHT, 2))
        pygame.draw.rect(window, (180, 140, 20), (0, bot_y, WIND_WIDHT, 2))
        pygame.display.flip()


class Level:
    def __init__(self, window, name, menu_option):
        self.window = window
        self.name = name
        self.menu_option = menu_option

        self.bg_surfaces = [
            pygame.image.load(f'./assets/level1bg{i}.png').convert_alpha()
            for i in range(1, 8)
        ]

        self.player = Player('Player1', (10, GROUND_Y))

        self.cat_anim_idle = _load_cat('./assets/cat/IDLE.png', _CAT_IDLE_FRAMES)
        self.cat_anim_walk = _load_cat('./assets/cat/WALK.png', _CAT_WALK_FRAMES)
        self.cat_frame_idx = 0.0
        self.cat_world_x = float(CAT_WORLD_X)
        self.cat_walking = False
        self._cat_offscreen = False
        self.cat_surf = self.cat_anim_idle[0]

        self.camera_x = 0

        self.enemies = []
        self.wave_triggered = [False, False, False]
        self.wave_active = False
        self.wave_lock_x = 0
        self.current_wave_idx = -1
        self.wave_banner_timer = 0

        self.bubble_text = ''
        self.bubble_timer = 0

        self._cat_greeted = False
        self._cat_touched = False
        self._ending = False
        self._ending_timer = 0

        self._particles   = []
        self._float_texts = []

        # Pre-built screen overlay (scanlines + borda) — criado uma vez
        self._screen_overlay = Player.build_screen_overlay(WIND_WIDHT, WIND_HEIGHT)

    # ── Onda ────────────────────────────────────────────────────

    def _spawn_wave(self, wave_idx):
        trigger_x = WAVE_TRIGGERS[wave_idx]
        self.enemies = [
            Enemy(etype, trigger_x + offset)
            for etype, offset in WAVE_CONFIGS[wave_idx]
        ]
        self.wave_active = True
        self.wave_lock_x = self.camera_x
        self.current_wave_idx = wave_idx
        self.wave_banner_timer = 120

    def _check_wave_cleared(self):
        if self.wave_active and not any(e.alive for e in self.enemies):
            self.wave_active = False
            self.enemies.clear()
            if Settings.DIFFICULTY == 'cat':
                self.player.hp = min(self.player.MAX_HP, self.player.hp + 1)

    # ── Partículas ───────────────────────────────────────────────

    def _spawn_hit_particles(self, screen_x, screen_y, color=(255, 200, 60)):
        for _ in range(6):
            self._particles.append(_Particle(screen_x, screen_y, color))

    # ── Loop principal ───────────────────────────────────────────

    def run(self):
        pygame.mixer_music.load('./assets/music/Fase1.mp3')
        pygame.mixer_music.play(-1)

        clock    = pygame.time.Clock()
        font     = pygame.font.Font('./assets/font/Cardinal.ttf', 48)
        font_sm  = pygame.font.Font('./assets/font/Cardinal.ttf', 28)
        font_bub = pygame.font.Font('./assets/font/Cardinal.ttf', 20)
        _life_surf = _make_life_gain_surf(font_bub)
        death_timer = 0

        fade_surf = pygame.Surface((WIND_WIDHT, WIND_HEIGHT))
        fade_surf.fill((0, 0, 0))

        _ENDING_BUBBLE_DUR = 300
        _ENDING_FADE_DUR   = 90

        # ── BANNER FASE 1 ────────────────────────────────────────
        _show_phase_banner(self.window, clock, font, 'Fase 1')

        # ── INTRO ───────────────────────────────────────────────
        intro_timer = 0
        while intro_timer < 220:
            clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                    intro_timer = 220
            intro_timer += 1
            self.player.move()
            self.window.fill((0, 0, 0))
            tile_x = -(self.camera_x % LOOP_W)
            for surf in self.bg_surfaces:
                self.window.blit(surf, (tile_x, 0))
                self.window.blit(surf, (tile_x + LOOP_W, 0))
            self.window.blit(self.player.surf, self.player.rect)
            _draw_bubble(self.window, font_bub, "I need to find my cat",
                         self.player.rect.centerx, self.player.rect.top)
            self.player.draw_hud(self.window)
            self.window.blit(self._screen_overlay, (0, 0))
            pygame.display.flip()

        # ── JOGO ────────────────────────────────────────────────
        while True:
            clock.tick(60)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if not self._ending:
                    self.player.handle_event(event)

            if not self._ending:
                self.player.move()

            # Câmera
            if not self._ending:
                if self.player.direction == 1:
                    new_cam = self.camera_x + self.player.speed
                    if self.wave_active:
                        new_cam = min(new_cam, WAVE_MAX_CAM[self.current_wave_idx])
                    self.camera_x = min(new_cam, MAX_CAMERA_X)
                elif self.player.direction == -1:
                    self.camera_x = max(self.camera_x - self.player.speed, 0)

            # Spawn de ondas
            if not self.wave_active and not self._ending:
                for i, trigger in enumerate(WAVE_TRIGGERS):
                    if not self.wave_triggered[i] and self.camera_x >= trigger:
                        self.wave_triggered[i] = True
                        self._spawn_wave(i)
                        break

            # Atualiza inimigos
            player_world_x = self.camera_x + self.player.rect.centerx
            atk_rect = self.player.attack_world_rect(self.camera_x)

            for enemy in self.enemies:
                if not enemy.alive:
                    continue
                deals_damage = enemy.update(player_world_x)
                if deals_damage:
                    self.player.take_damage(1)
                player_world_rect = pygame.Rect(
                    self.camera_x + self.player.rect.x + 18,
                    self.player.rect.top + 10,
                    self.player.rect.width - 36,
                    self.player.rect.height - 20,
                )
                for proj in enemy.projectiles:
                    if proj.alive and proj.world_rect().colliderect(player_world_rect):
                        proj.alive = False
                        self.player.take_damage(1)
                if atk_rect is not None:
                    eid = id(enemy)
                    if eid not in self.player._atk_hit_enemies:
                        if atk_rect.colliderect(enemy.world_hitbox()):
                            self.player._atk_hit_enemies.add(eid)
                            enemy.take_damage(1)
                            gained = Score.add_points(random.randint(10, 30), self.player)
                            if gained:
                                lx = self.player.rect.centerx - _life_surf.get_width() // 2
                                ly = self.player.rect.top - 16
                                self._float_texts.append(_FloatText(_life_surf, lx, ly))
                            ex = int(enemy.world_x - self.camera_x)
                            ey = enemy._FLOOR_Y + 20
                            self._spawn_hit_particles(ex, ey)

            self.enemies = [e for e in self.enemies if e.alive or e.dead]
            self._check_wave_cleared()

            if self.wave_banner_timer > 0:
                self.wave_banner_timer -= 1

            # Partículas + textos flutuantes
            for p in self._particles:
                p.update()
            self._particles = [p for p in self._particles if p.life > 0]
            for ft in self._float_texts:
                ft.update()
            self._float_texts = [ft for ft in self._float_texts if ft.life > 0]

            # ── Gato ─────────────────────────────────────────────
            cat_anim = self.cat_anim_walk if self.cat_walking else self.cat_anim_idle
            cat_anim_speed = 0.25 if self.cat_walking else 0.08
            self.cat_frame_idx = (self.cat_frame_idx + cat_anim_speed) % len(cat_anim)
            self.cat_surf = cat_anim[int(self.cat_frame_idx)]

            if self.cat_walking:
                self.cat_world_x += 2.0

            cat_screen_x = self.cat_world_x - self.camera_x

            if self.cat_walking and not self._cat_offscreen:
                if cat_screen_x > WIND_WIDHT + CAT_FRAME_W:
                    self._cat_offscreen = True
                    self._ending        = True
                    self.bubble_text    = "uff... here we go again.."
                    self.bubble_timer   = _ENDING_BUBBLE_DUR

            if not self._cat_greeted and cat_screen_x < WIND_WIDHT:
                self._cat_greeted = True
                self.bubble_text  = "finally, here you are"
                self.bubble_timer = 180

            all_waves_done = all(self.wave_triggered) and not self.wave_active
            if all_waves_done and not self._cat_touched and not self.cat_walking:
                pw_rect  = pygame.Rect(
                    int(self.camera_x + self.player.rect.x), self.player.rect.top,
                    self.player.rect.width, self.player.rect.height,
                )
                cat_rect = pygame.Rect(int(self.cat_world_x), CAT_Y, CAT_FRAME_W, CAT_FRAME_H)
                if pw_rect.colliderect(cat_rect):
                    self._cat_touched = True
                    self.cat_walking  = True
                    self.cat_frame_idx = 0.0
                    self.bubble_text  = ''
                    self.bubble_timer = 0

            if self.bubble_timer > 0 and not self._ending:
                self.bubble_timer -= 1

            if self._ending:
                self._ending_timer += 1

            # ── DESENHO ──────────────────────────────────────────
            self.window.fill((0, 0, 0))

            tile_x = -(self.camera_x % LOOP_W)
            for surf in self.bg_surfaces:
                self.window.blit(surf, (tile_x, 0))
                self.window.blit(surf, (tile_x + LOOP_W, 0))

            if -CAT_FRAME_W < cat_screen_x < WIND_WIDHT + CAT_FRAME_W:
                self.window.blit(self.cat_surf, (int(cat_screen_x), CAT_Y))

            for enemy in self.enemies:
                enemy.draw(self.window, self.camera_x)

            # Partículas e textos flutuantes
            for p in self._particles:
                p.draw(self.window)
            for ft in self._float_texts:
                ft.draw(self.window)

            self.window.blit(self.player.surf, self.player.rect)
            self.player.draw_hud(self.window)
            # Score display
            sc = font_bub.render(str(Score.get_score()), True, (255, 215, 50))
            sc_sh = font_bub.render(str(Score.get_score()), True, (0, 0, 0))
            self.window.blit(sc_sh, (6, 28))
            self.window.blit(sc,    (5, 27))

            # Balão de fala
            show_bubble = (self.bubble_timer > 0) or (self._ending and self._ending_timer <= _ENDING_BUBBLE_DUR)
            if show_bubble and self.bubble_text:
                _draw_bubble(self.window, font_bub, self.bubble_text,
                             self.player.rect.centerx, self.player.rect.top)

            # ── Banner cinemático de entrada da onda (primeiros 15 frames) ──
            if self.wave_banner_timer > 0 and self.current_wave_idx >= 0:
                # slide in nas primeiras 15 frames (timer 120→105), some depois
                if self.wave_banner_timer > 105:
                    progress = (120 - self.wave_banner_timer) / 15.0
                    ty = int(-32 * (1.0 - progress))
                else:
                    ty = 0
                alpha = min(255, self.wave_banner_timer * 4)
                txt    = font_sm.render(_WAVE_LABELS[self.current_wave_idx], True, (255, 220, 50))
                shadow = font_sm.render(_WAVE_LABELS[self.current_wave_idx], True, (0, 0, 0))
                txt.set_alpha(alpha); shadow.set_alpha(alpha)
                r = txt.get_rect(center=(WIND_WIDHT // 2, 24 + ty))
                self.window.blit(shadow, (r.x + 2, r.y + 2))
                self.window.blit(txt, r)
                if alpha > 80:
                    pygame.draw.rect(self.window, (180, 140, 20),
                                     (0, r.bottom + 2, WIND_WIDHT, 1))

            # ── Contador persistente de onda no canto superior direito ──
            if self.wave_active and self.current_wave_idx >= 0:
                count_str = f'Onda {self.current_wave_idx + 1}/3'
                ct  = font_sm.render(count_str, True, (255, 220, 50))
                csh = font_sm.render(count_str, True, (0, 0, 0))
                cr  = ct.get_rect(topright=(WIND_WIDHT - 6, 5))
                self.window.blit(csh, (cr.x + 2, cr.y + 2))
                self.window.blit(ct, cr)

            if self.wave_active:
                # Barra pulsante no topo (intensidade varia com o tempo)
                pulse = int(abs(math.sin(pygame.time.get_ticks() * 0.008)) * 80 + 140)
                pygame.draw.rect(self.window, (pulse, 0, 0), (0, 0, WIND_WIDHT, 3))

            # Overlay scanlines + borda
            self.window.blit(self._screen_overlay, (0, 0))

            # Fade de saída para fase 2
            if self._ending and self._ending_timer > _ENDING_BUBBLE_DUR:
                progress = self._ending_timer - _ENDING_BUBBLE_DUR
                a = min(255, progress * 255 // _ENDING_FADE_DUR)
                fade_surf.set_alpha(a)
                self.window.blit(fade_surf, (0, 0))
                if self._ending_timer >= _ENDING_BUBBLE_DUR + _ENDING_FADE_DUR:
                    pygame.display.flip()
                    return "level2"

            # Game Over
            if self.player.dead:
                death_timer += 1
                if death_timer >= 120:
                    text = font.render("GAME OVER", True, (200, 0, 0))
                    shadow = font.render("GAME OVER", True, (0, 0, 0))
                    r = text.get_rect(center=(WIND_WIDHT // 2, WIND_HEIGHT // 2))
                    self.window.blit(shadow, (r.x + 3, r.y + 3))
                    self.window.blit(text, r)
                if death_timer >= 300:
                    pygame.display.flip()
                    return "game_over"

            pygame.display.flip()
