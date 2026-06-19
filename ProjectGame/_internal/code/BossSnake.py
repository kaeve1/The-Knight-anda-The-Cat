import pygame
import random
from code.Const import GROUND_Y

FRAME_W = 128
FRAME_H = 128
DRAW_W  = 96
DRAW_H  = 96
# player visual feet = GROUND_Y+61 = 301; boss bottom = FLOOR_Y+DRAW_H → 301-96 = 205
FLOOR_Y = 205

_ANIM_SPEED  = {'idle': 0.12, 'walk': 0.14, 'attack': 0.16,
                'special': 0.14, 'hurt': 0.28, 'dead': 0.08}
_MELEE_FRAME   = 8   # frame do attack normal que causa dano
_SPECIAL_FRAME = 3   # frame do special que causa dano
_ATK_COOLDOWN  = 90
_ATK_RANGE     = 100
_IMMUNE        = 120  # 2 s a 60 fps


def _load(path, count):
    sheet = pygame.image.load(path).convert_alpha()
    return [
        pygame.transform.scale(
            sheet.subsurface((i * FRAME_W, 0, FRAME_W, FRAME_H)),
            (DRAW_W, DRAW_H)
        )
        for i in range(count)
    ]


class BossSnake:
    MAX_HP = 10

    def __init__(self, world_x):
        self.world_x = float(world_x)

        # Fase 1: vida vermelha
        self.hp    = self.MAX_HP
        # Fase 2: vida amarela
        self.phase     = 1
        self.phase2_hp = self.MAX_HP

        self.alive = True
        self.dead  = False
        self.facing_right = False
        self._locked = False
        self.frame_index   = 0.0
        self.immune_frames  = 0
        self.attack_cooldown = 0
        self._dmg_dealt = False

        b = './assets/boss/'
        self.anim = {
            'idle':    _load(b + 'Idle.png',     7),
            'walk':    _load(b + 'Walk.png',     13),
            'attack':  _load(b + 'Attack_1.png', 16),
            'special': _load(b + 'Special.png',   5),
            'hurt':    _load(b + 'Hurt.png',      3),
            'dead':    _load(b + 'Dead.png',      3),
        }
        self.state  = 'idle'
        self.frames = self.anim['idle']
        self.surf   = self.frames[0]

    # ── state ───────────────────────────────────────────────────
    def _set_state(self, state):
        if self.state != state:
            self.state = state
            self.frame_index = 0.0
            self.frames = self.anim[state]
            self._dmg_dealt = False

    # ── damage ──────────────────────────────────────────────────
    def take_damage(self):
        if self.dead or self.immune_frames > 0:
            return False
        self.immune_frames = _IMMUNE

        if self.phase == 1:
            self.hp -= 1
            if self.hp <= 0:
                self.hp = 0
                self.phase = 2          # transição para fase 2
                self._locked = False
                self._set_state('idle')
            else:
                self._locked = True
                self._set_state('hurt')
        else:
            self.phase2_hp -= 1
            if self.phase2_hp <= 0:
                self.phase2_hp = 0
                self.dead  = True
                self._locked = True
                self._set_state('dead')
            else:
                self._locked = True
                self._set_state('hurt')
        return True

    # ── animate ─────────────────────────────────────────────────
    def _animate(self):
        self.frame_index += _ANIM_SPEED.get(self.state, 0.15)
        total = len(self.frames)
        if self.frame_index >= total:
            if self.state == 'dead':
                self.frame_index = float(total - 1)
                self.alive = False
            elif self.state in ('hurt', 'attack', 'special'):
                if self.state in ('attack', 'special'):
                    self.attack_cooldown = _ATK_COOLDOWN
                self._locked = False
                self._set_state('idle')
            else:
                self.frame_index = 0.0

        frame = self.frames[int(self.frame_index)]
        if not self.facing_right:
            frame = pygame.transform.flip(frame, True, False)
        self.surf = frame

    # ── update ──────────────────────────────────────────────────
    def update(self, player_world_x):
        """Retorna quantidade de dano causado neste frame (0, 1 ou 2)."""
        if self.immune_frames   > 0: self.immune_frames   -= 1
        if self.attack_cooldown > 0: self.attack_cooldown -= 1

        dx   = player_world_x - self.world_x
        dist = abs(dx)
        self.facing_right = dx > 0

        if not self._locked:
            if dist <= _ATK_RANGE and self.attack_cooldown == 0:
                self._locked = True
                # Fase 2: 40% de chance de usar special
                if self.phase == 2 and random.random() < 0.4:
                    self._set_state('special')
                else:
                    self._set_state('attack')
            elif dist > _ATK_RANGE:
                self.world_x += _ANIM_SPEED['walk'] * (1 if dx > 0 else -1) * 6
                self._set_state('walk')
            else:
                self._set_state('idle')

        damage = 0
        if self.state == 'attack' and not self._dmg_dealt:
            if int(self.frame_index) >= _MELEE_FRAME and dist <= _ATK_RANGE + 30:
                self._dmg_dealt = True
                damage = 1
        elif self.state == 'special' and not self._dmg_dealt:
            if int(self.frame_index) >= _SPECIAL_FRAME and dist <= _ATK_RANGE + 50:
                self._dmg_dealt = True
                damage = 2

        self._animate()
        return damage

    # ── geometry ────────────────────────────────────────────────
    def world_hitbox(self):
        return pygame.Rect(int(self.world_x) - 22, FLOOR_Y + 20, 44, DRAW_H - 28)

    # ── draw ────────────────────────────────────────────────────
    def draw(self, surface, camera_x):
        sx = int(self.world_x - camera_x) - DRAW_W // 2

        # White blink when recently hit
        if self.immune_frames > 60 and (self.immune_frames // 4) % 2 == 0:
            flash = self.surf.copy()
            flash.fill((255, 255, 255), special_flags=pygame.BLEND_RGB_MAX)
            surface.blit(flash, (sx, FLOOR_Y))
        else:
            surface.blit(self.surf, (sx, FLOOR_Y))

        if not self.dead:
            bw = 140
            bx = sx + DRAW_W // 2 - bw // 2
            by = FLOOR_Y - 12
            if self.phase == 1:
                pygame.draw.rect(surface, (60, 0, 0),   (bx, by, bw, 7))
                pygame.draw.rect(surface, (220, 30, 30),
                                 (bx, by, int(bw * self.hp / self.MAX_HP), 7))
            else:
                pygame.draw.rect(surface, (60, 50, 0),  (bx, by, bw, 7))
                pygame.draw.rect(surface, (255, 200, 0),
                                 (bx, by, int(bw * self.phase2_hp / self.MAX_HP), 7))
