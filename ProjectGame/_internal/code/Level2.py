import sys
import math
import random
import pygame
import code.Settings as Settings
import code.Score    as Score

from code.Player    import Player
from code.Enemy     import Enemy
from code.BossSnake import BossSnake, FLOOR_Y as BOSS_FLOOR_Y
from code.Const     import WIND_WIDHT, WIND_HEIGHT, GROUND_Y
from code.Level     import (CAT_FRAME_W, CAT_FRAME_H, CAT_Y,
                            _CAT_IDLE_FRAMES, _load_cat,
                            _draw_bubble, _show_phase_banner, _Particle,
                            _FloatText, _make_life_gain_surf)

LOOP_W        = WIND_WIDHT          # 576
OUTDOOR_LOOPS = 6
OUTDOOR_WORLD = OUTDOOR_LOOPS * LOOP_W   # 3456
MAX_CAMERA_X  = OUTDOOR_WORLD - LOOP_W  # 2880

WAVE_TRIGGERS = [300, 900, 1600]
WAVE_CONFIGS  = [
    [('warrior', 620), ('spearman', 740), ('archer', 860), ('archer', 980)],
    [('warrior', 620), ('spearman', 740), ('archer', 860), ('archer', 980), ('archer', 1100)],
    [('warrior', 620), ('warrior',  740), ('spearman', 860), ('archer', 980), ('archer', 1100)],
]
_WAVE_LABELS = ['Onda 1', 'Onda 2', 'Onda 3']

# Durante a onda: câmera trava para o player alcançar o inimigo mais distante
WAVE_MAX_CAM = [
    WAVE_TRIGGERS[i] + max(off for _, off in WAVE_CONFIGS[i]) - 90
    for i in range(3)
]  # = [1190, 1910, 2610]

# Entre ondas: limite cresce progressivamente conforme ondas são limpas
_WAVE_ADVANCE_LIMITS = [
    WAVE_TRIGGERS[0] + 300,   # antes de qualquer onda: 600
    WAVE_TRIGGERS[1] + 300,   # após limpar onda 1: 1200
    WAVE_TRIGGERS[2] + 300,   # após limpar onda 2: 1900
]

# Boss room
BOSS_CAM_X        = OUTDOOR_WORLD
BOSS_START_X      = OUTDOOR_WORLD + 400
CAT_BOSS_SCREEN_X = 510

_MIAU_INTERVAL = 360
_MIAU_DURATION = 120


# ─────────────────────────────────────────────────────────────────
class Level2:
    def __init__(self, window, name, menu_option):
        self.window      = window
        self.name        = name
        self.menu_option = menu_option

        self.bg_outdoor = [
            pygame.image.load(f'./assets/level2bg{i}.png').convert_alpha()
            for i in range(1, 5)
        ]
        self.bg_casa = [
            pygame.image.load(f'./assets/level2/casa/{i}.png').convert_alpha()
            for i in range(1, 5)
        ]

        # offscreen surfaces removed — blitting direct to window (Level1 style)

        self.cat_idle   = _load_cat('./assets/cat/IDLE.png', _CAT_IDLE_FRAMES)
        self.cat_fidx   = 0.0

        self.player   = Player('Player1', (10, GROUND_Y))
        self.camera_x = 0

        self.enemies          = []
        self.wave_triggered   = [False, False, False]
        self.wave_active      = False
        self.wave_lock_x      = 0
        self.current_wave_idx = -1
        self.wave_banner_timer = 0
        self.waves_cleared    = 0

        self._particles   = []
        self._float_texts = []

        self._screen_overlay = Player.build_screen_overlay(WIND_WIDHT, WIND_HEIGHT)

    # ── helpers de renderização ──────────────────────────────────

    def _draw_outdoor_bg(self, camera_x):
        """Mesmo sistema do Level 1: blit direto no window, tiling via módulo."""
        tile_x = -(camera_x % LOOP_W)
        for surf in self.bg_outdoor:
            self.window.blit(surf, (int(tile_x), 0))
            self.window.blit(surf, (int(tile_x + LOOP_W), 0))

    def _draw_casa_bg(self):
        for surf in self.bg_casa:
            self.window.blit(surf, (0, 0))

    # ── ondas ───────────────────────────────────────────────────

    def _spawn_wave(self, idx):
        trigger_x = WAVE_TRIGGERS[idx]
        self.enemies = [
            Enemy(etype, trigger_x + offset)
            for etype, offset in WAVE_CONFIGS[idx]
        ]
        self.wave_active      = True
        self.wave_lock_x      = self.camera_x
        self.current_wave_idx = idx
        self.wave_banner_timer = 120

    def _check_wave_cleared(self):
        if self.wave_active and not any(e.alive for e in self.enemies):
            self.wave_active = False
            self.enemies.clear()
            self.waves_cleared += 1
            if Settings.DIFFICULTY == 'cat':
                self.player.hp = min(self.player.MAX_HP, self.player.hp + 1)

    # ── partículas ───────────────────────────────────────────────

    def _spawn_hit_particles(self, sx, sy, color=(255, 200, 60)):
        for _ in range(6):
            self._particles.append(_Particle(sx, sy, color))

    # ── FASE 1: outdoor ─────────────────────────────────────────

    def _run_outdoor(self, clock, font, font_sm, font_bub):
        _show_phase_banner(self.window, clock, font, 'Fase 2')
        _life_surf       = _make_life_gain_surf(font_bub)
        post_wave_timer  = 0
        post_wave_active = False   # True após última onda — player anda sozinho
        death_timer      = 0

        while True:
            clock.tick(60)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if not post_wave_active:
                    self.player.handle_event(event)

            self.player.move()

            # Auto-walk para a direita nos 5 s finais (forced_direction → move() usa walk)
            if post_wave_active:
                self.player.forced_direction = 1

            # Câmera progressiva: trava por onda ativa; entre ondas cresce por onda limpa
            if self.player.direction == 1:
                new_cam = self.camera_x + self.player.speed
                if self.wave_active:
                    new_cam = min(new_cam, WAVE_MAX_CAM[self.current_wave_idx])
                elif self.waves_cleared < 3:
                    new_cam = min(new_cam, _WAVE_ADVANCE_LIMITS[self.waves_cleared])
                self.camera_x = new_cam
            elif self.player.direction == -1:
                self.camera_x = max(self.camera_x - self.player.speed, 0)

            if not self.wave_active:
                for i, trigger in enumerate(WAVE_TRIGGERS):
                    if not self.wave_triggered[i] and self.camera_x >= trigger:
                        self.wave_triggered[i] = True
                        self._spawn_wave(i)
                        break

            player_world_x = self.camera_x + self.player.rect.centerx
            atk_rect = self.player.attack_world_rect(self.camera_x)

            for enemy in self.enemies:
                if not enemy.alive:
                    continue
                if enemy.update(player_world_x):
                    self.player.take_damage(1)
                player_world_rect = pygame.Rect(
                    self.camera_x + self.player.rect.x + 18, self.player.rect.top + 10,
                    self.player.rect.width - 36, self.player.rect.height - 20,
                )
                for proj in enemy.projectiles:
                    if proj.alive and proj.world_rect().colliderect(player_world_rect):
                        proj.alive = False
                        self.player.take_damage(1)
                if atk_rect:
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

            for p in self._particles:
                p.update()
            self._particles = [p for p in self._particles if p.life > 0]
            for ft in self._float_texts:
                ft.update()
            self._float_texts = [ft for ft in self._float_texts if ft.life > 0]

            if all(self.wave_triggered) and not self.wave_active:
                if not post_wave_active:
                    post_wave_active = True
                post_wave_timer += 1
                if post_wave_timer >= 300:
                    return

            # ── desenho ─────────────────────────────────────────
            self.window.fill((0, 0, 0))
            self._draw_outdoor_bg(self.camera_x)

            for e in self.enemies:
                e.draw(self.window, self.camera_x)

            for p in self._particles:
                p.draw(self.window)
            for ft in self._float_texts:
                ft.draw(self.window)

            self.window.blit(self.player.surf, self.player.rect)
            self.player.draw_hud(self.window)
            sc = font_bub.render(str(Score.get_score()), True, (255, 215, 50))
            sc_sh = font_bub.render(str(Score.get_score()), True, (0, 0, 0))
            self.window.blit(sc_sh, (6, 28))
            self.window.blit(sc,    (5, 27))

            # ── Banner de entrada de onda (slide in nas primeiras 15 frames) ──
            if self.wave_banner_timer > 0 and self.current_wave_idx >= 0:
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

            # ── Contador persistente no canto superior direito ──
            if self.wave_active and self.current_wave_idx >= 0:
                count_str = f'Onda {self.current_wave_idx + 1}/3'
                ct  = font_sm.render(count_str, True, (255, 220, 50))
                csh = font_sm.render(count_str, True, (0, 0, 0))
                cr  = ct.get_rect(topright=(WIND_WIDHT - 6, 5))
                self.window.blit(csh, (cr.x + 2, cr.y + 2))
                self.window.blit(ct, cr)

            if self.wave_active:
                pulse = int(abs(math.sin(pygame.time.get_ticks() * 0.008)) * 80 + 140)
                pygame.draw.rect(self.window, (pulse, 0, 0), (0, 0, WIND_WIDHT, 3))

            self.window.blit(self._screen_overlay, (0, 0))

            if self.player.dead:
                death_timer += 1
                if death_timer >= 120:
                    go_t  = font.render('GAME OVER', True, (200, 0, 0))
                    go_sh = font.render('GAME OVER', True, (0, 0, 0))
                    r = go_t.get_rect(center=(WIND_WIDHT // 2, WIND_HEIGHT // 2))
                    self.window.blit(go_sh, (r.x + 3, r.y + 3))
                    self.window.blit(go_t,  r)
                if death_timer >= 300:
                    pygame.display.flip()
                    return 'dead'

            pygame.display.flip()

    # ── CUTSCENE ────────────────────────────────────────────────

    def _run_cutscene(self, clock, font):
        fade = pygame.Surface((WIND_WIDHT, WIND_HEIGHT))
        fade.fill((0, 0, 0))
        text   = font.render("after a long walk..", True, (200, 200, 200))
        shadow = font.render("after a long walk..", True, (0, 0, 0))
        tr = text.get_rect(center=(WIND_WIDHT // 2, WIND_HEIGHT // 2))

        for alpha in range(0, 256, 4):
            clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
            fade.set_alpha(alpha)
            self.window.blit(fade, (0, 0))
            pygame.display.flip()

        for _ in range(180):
            clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
            self.window.fill((0, 0, 0))
            self.window.blit(shadow, (tr.x + 2, tr.y + 2))
            self.window.blit(text, tr)
            self.window.blit(self._screen_overlay, (0, 0))
            pygame.display.flip()

        for _ in range(60):
            clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
            self.window.fill((0, 0, 0))
            pygame.display.flip()

    # ── FASE 2: sala do boss ─────────────────────────────────────

    def _run_boss_room(self, clock, font, font_sm, font_bub):
        self.player.hp              = self.player.MAX_HP
        self.player.dead            = False
        self.player._locked         = False
        self.player.invincible_frames = 0
        self.player.forced_direction = 0   # limpa auto-walk da fase anterior
        self.player.rect.left       = 50
        self.player.rect.top        = GROUND_Y

        boss = BossSnake(BOSS_START_X)
        _life_surf = _make_life_gain_surf(font_bub)

        flash_timer = 0
        flash_surf  = pygame.Surface((WIND_WIDHT, WIND_HEIGHT))

        intro_freeze       = True
        intro_freeze_timer = 180

        boss_bubble   = 'SssKNIGHT.. want your CAT back?'
        boss_bubble_t = intro_freeze_timer

        boss_dead_bubble = False

        cat_visible = True
        miau_timer  = 0
        miau_show   = False

        win_triggered = False
        _boss_id      = id(boss)
        death_timer   = 0

        while True:
            clock.tick(60)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if not intro_freeze and not boss_dead_bubble:
                    self.player.handle_event(event)

            if not intro_freeze:
                self.player.move()
                if self.player.direction == 1:
                    self.player.rect.x = min(
                        self.player.rect.x + self.player.speed,
                        WIND_WIDHT - self.player.rect.width
                    )
                elif self.player.direction == -1:
                    self.player.rect.x = max(self.player.rect.x - self.player.speed, 0)

            player_world_x = BOSS_CAM_X + self.player.rect.centerx

            if intro_freeze:
                intro_freeze_timer -= 1
                if intro_freeze_timer <= 0:
                    intro_freeze  = False
                    boss_bubble   = ''
                    boss_bubble_t = 0
            elif boss_bubble_t > 0:
                boss_bubble_t -= 1

            if not intro_freeze and boss.alive and not boss.dead:
                dealt = boss.update(player_world_x)
                if dealt > 0:
                    hit = self.player.take_damage(dealt)
                    if hit:
                        flash_timer = 24

                atk_rect = self.player.attack_world_rect(BOSS_CAM_X)
                if atk_rect and _boss_id not in self.player._atk_hit_enemies:
                    if atk_rect.colliderect(boss.world_hitbox()):
                        self.player._atk_hit_enemies.add(_boss_id)
                        boss.take_damage()
                        gained = Score.add_points(random.randint(10, 30), self.player)
                        if gained:
                            lx = self.player.rect.centerx - _life_surf.get_width() // 2
                            ly = self.player.rect.top - 16
                            self._float_texts.append(_FloatText(_life_surf, lx, ly))
                        # partículas no boss
                        bsx = int(boss.world_x - BOSS_CAM_X)
                        self._spawn_hit_particles(bsx, BOSS_FLOOR_Y + 30, (255, 80, 80))
                        if boss.dead:
                            boss_dead_bubble = True
                            boss_bubble      = 'shhhNOOOOO'
                            boss_bubble_t    = 240

            elif boss.dead and boss.alive:
                boss._animate()

            for p in self._particles:
                p.update()
            self._particles = [p for p in self._particles if p.life > 0]
            for ft in self._float_texts:
                ft.update()
            self._float_texts = [ft for ft in self._float_texts if ft.life > 0]

            if cat_visible:
                miau_timer += 1
                if miau_timer >= _MIAU_INTERVAL:
                    miau_timer = 0
                    miau_show  = True
                if miau_show and miau_timer >= _MIAU_DURATION:
                    miau_show = False

                if not boss.alive:
                    cat_rect = pygame.Rect(CAT_BOSS_SCREEN_X, CAT_Y, CAT_FRAME_W, CAT_FRAME_H)
                    if self.player.rect.colliderect(cat_rect) and not win_triggered:
                        win_triggered = True

            self.cat_fidx = (self.cat_fidx + 0.08) % len(self.cat_idle)

            # ── DESENHO ─────────────────────────────────────────
            self.window.fill((0, 0, 0))
            self._draw_casa_bg()

            boss.draw(self.window, BOSS_CAM_X)

            if cat_visible:
                cat_surf = self.cat_idle[int(self.cat_fidx)]
                self.window.blit(cat_surf, (CAT_BOSS_SCREEN_X, CAT_Y))

            for p in self._particles:
                p.draw(self.window)
            for ft in self._float_texts:
                ft.draw(self.window)

            self.window.blit(self.player.surf, self.player.rect)
            self.player.draw_hud(self.window)
            sc = font_bub.render(str(Score.get_score()), True, (255, 215, 50))
            sc_sh = font_bub.render(str(Score.get_score()), True, (0, 0, 0))
            self.window.blit(sc_sh, (6, 28))
            self.window.blit(sc,    (5, 27))

            if boss_bubble_t > 0 and boss_bubble:
                boss_sx   = int(boss.world_x - BOSS_CAM_X)
                bub_color = (180, 0, 0) if boss_dead_bubble else (200, 0, 0)
                _draw_bubble(self.window, font_bub, boss_bubble,
                             boss_sx, BOSS_FLOOR_Y,
                             text_color=bub_color,
                             bg=(40, 10, 10),
                             border=(160, 0, 0))

            if cat_visible and miau_show:
                cat_cx = CAT_BOSS_SCREEN_X + CAT_FRAME_W // 2
                _draw_bubble(self.window, font_bub, 'miau',
                             cat_cx, CAT_Y)

            if flash_timer > 0:
                flash_color = (220, 0, 0) if (flash_timer // 3) % 2 == 0 else (255, 255, 255)
                flash_surf.fill(flash_color)
                flash_surf.set_alpha(140)
                self.window.blit(flash_surf, (0, 0))
                flash_timer -= 1

            self.window.blit(self._screen_overlay, (0, 0))

            if self.player.dead:
                death_timer += 1
                if death_timer >= 120:
                    go_t  = font.render('GAME OVER', True, (200, 0, 0))
                    go_sh = font.render('GAME OVER', True, (0, 0, 0))
                    r = go_t.get_rect(center=(WIND_WIDHT // 2, WIND_HEIGHT // 2))
                    self.window.blit(go_sh, (r.x + 3, r.y + 3))
                    self.window.blit(go_t,  r)
                if death_timer >= 300:
                    pygame.display.flip()
                    return 'game_over'

            pygame.display.flip()

            if win_triggered:
                self._run_win_screen(clock, font, font_sm)
                return 'win'

    # ── WIN SCREEN ──────────────────────────────────────────────

    def _run_win_screen(self, clock, font, font_sm):
        fade = pygame.Surface((WIND_WIDHT, WIND_HEIGHT))
        fade.fill((0, 0, 0))

        # fade to black
        for alpha in range(0, 256, 4):
            clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
            fade.set_alpha(alpha)
            self.window.blit(fade, (0, 0))
            pygame.display.flip()

        line1  = font.render('The Knight and the cat', True, (255, 220, 50))
        line1b = font.render('are now Happy', True, (255, 220, 50))
        line2  = font_sm.render('"Thank you for playing"', True, (200, 200, 200))
        sh1    = font.render('The Knight and the cat', True, (0, 0, 0))
        sh1b   = font.render('are now Happy', True, (0, 0, 0))
        sh2    = font_sm.render('"Thank you for playing"', True, (0, 0, 0))

        cy = WIND_HEIGHT // 2
        for _ in range(420):
            clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
            self.window.fill((0, 0, 0))
            for surf, sh, y in [
                (line1,  sh1,  cy - 44),
                (line1b, sh1b, cy - 6),
                (line2,  sh2,  cy + 38),
            ]:
                r = surf.get_rect(center=(WIND_WIDHT // 2, y))
                self.window.blit(sh,   (r.x + 2, r.y + 2))
                self.window.blit(surf, r)
            self.window.blit(self._screen_overlay, (0, 0))
            pygame.display.flip()

        # ── fade to black before credits ─────────────────────────
        for alpha in range(0, 256, 4):
            clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
            fade.set_alpha(alpha)
            self.window.blit(fade, (0, 0))
            pygame.display.flip()

        # ── tela de créditos com finalpixelart.png ───────────────
        raw    = pygame.image.load('./assets/finalpixelart.png').convert()
        bg     = pygame.transform.scale(raw, (WIND_WIDHT, WIND_HEIGHT))

        credit_t  = font_sm.render('By Kevin Rosa, Uninter, 2026', True, (255, 220, 50))
        credit_sh = font_sm.render('By Kevin Rosa, Uninter, 2026', True, (0, 0, 0))
        cr = credit_t.get_rect(center=(WIND_WIDHT // 2, WIND_HEIGHT - 28))

        # fade in
        for alpha in range(255, -1, -5):
            clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
            self.window.blit(bg, (0, 0))
            self.window.blit(credit_sh, (cr.x + 2, cr.y + 2))
            self.window.blit(credit_t,  cr)
            self.window.blit(self._screen_overlay, (0, 0))
            fade.set_alpha(alpha)
            self.window.blit(fade, (0, 0))
            pygame.display.flip()

        # hold
        for _ in range(480):
            clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    return
            self.window.blit(bg, (0, 0))
            self.window.blit(credit_sh, (cr.x + 2, cr.y + 2))
            self.window.blit(credit_t,  cr)
            self.window.blit(self._screen_overlay, (0, 0))
            pygame.display.flip()

    # ── ENTRY POINT ─────────────────────────────────────────────

    def run(self):
        pygame.mixer_music.load('./assets/music/Fase2.mp3')
        pygame.mixer_music.play(-1)

        clock    = pygame.time.Clock()
        font     = pygame.font.Font('./assets/font/Cardinal.ttf', 48)
        font_sm  = pygame.font.Font('./assets/font/Cardinal.ttf', 28)
        font_bub = pygame.font.Font('./assets/font/Cardinal.ttf', 18)

        result = self._run_outdoor(clock, font, font_sm, font_bub)
        if result == 'dead':
            return 'game_over'

        self._run_cutscene(clock, font)

        return self._run_boss_room(clock, font, font_sm, font_bub)
