import pygame
import code.Settings as Settings
from code.Entity import Entity
from code.Const import GROUND_Y

FRAME_W = 96
FRAME_H = 84
GRAVITY = 0.6
JUMP_VEL = -11


def _load_sheet(path, count):
    sheet = pygame.image.load(path).convert_alpha()
    return [sheet.subsurface((i * FRAME_W, 0, FRAME_W, FRAME_H)) for i in range(count)]


class Player(Entity):
    # MAX_HP is set per-instance from Settings in __init__
    _ANIM_SPEED = {
        'idle': 0.12, 'walk': 0.15, 'jump': 0.2,
        'attack1': 0.2, 'attack2': 0.25,
        'hurt': 0.28, 'death': 0.1,
        'defend': 0.18,
    }

    def __init__(self, name, position):
        self.MAX_HP = Settings.CAT_MAX_HP if Settings.DIFFICULTY == 'cat' else Settings.KNIGHT_MAX_HP
        self.name = name
        self.speed = 5
        self.direction = 0
        self.facing_right = True

        self.anim = {
            'idle':    _load_sheet('./assets/knight/caminhando/IDLE.png', 7),
            'walk':    _load_sheet('./assets/knight/caminhando/WALK.png', 8),
            'attack1': _load_sheet('./assets/knight/ATTACK 1.png', 6),
            'attack2': _load_sheet('./assets/knight/ATTACK 2.png', 5),
            'hurt':    _load_sheet('./assets/knight/HURT.png', 4),
            'death':   _load_sheet('./assets/knight/DEATH.png', 12),
            'jump':    _load_sheet('./assets/knight/JUMP.png', 5),
            'defend':  _load_sheet('./assets/knight/DEFEND.png', 6),
        }

        self.state = 'idle'
        self.frame_index = 0.0
        self.frames = self.anim['idle']
        self.surf = self.frames[0]
        self.rect = self.surf.get_rect(left=position[0], top=position[1])

        self.vel_y = 0.0
        self.on_ground = True
        self.hp = self.MAX_HP
        self.dead = False
        self._locked = False
        self.defending = False
        self.invincible_frames = 0
        self._atk_hit_enemies = set()
        self.forced_direction = 0   # when != 0, overrides keyboard input in move()

    def _set_state(self, state):
        if self.state != state:
            self.state = state
            self.frame_index = 0.0
            self.frames = self.anim[state]

    def take_damage(self, amount):
        """Retorna True se o dano foi aplicado, False se bloqueado/imune."""
        if self.dead or self.invincible_frames > 0 or self.defending:
            return False
        if Settings.DIFFICULTY == 'cat':
            amount = 1
        self.invincible_frames = 50
        self.hp = max(0, self.hp - amount)
        if self.hp == 0:
            self.dead = True
            self._locked = True
            self._set_state('death')
        elif self.state not in ('hurt', 'death'):
            self._locked = True
            self._set_state('hurt')
        return True

    def handle_event(self, event):
        if self.dead:
            return
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_w, pygame.K_SPACE) and self.on_ground and not self._locked:
                self.vel_y = JUMP_VEL
                self.on_ground = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self._locked:
                return
            if event.button == 1:
                self._locked = True
                self._set_state('attack1')
            elif event.button == 3 and self.on_ground:
                self._locked = True
                self.defending = True
                self._set_state('defend')

    def _animate(self):
        speed = self._ANIM_SPEED.get(self.state, 0.15)
        self.frame_index += speed

        if self.frame_index >= len(self.frames):
            if self.state == 'death':
                self.frame_index = len(self.frames) - 1
            elif self.state in ('attack1', 'attack2', 'hurt', 'defend'):
                if self.state == 'defend':
                    self.defending = False
                self._locked = False
                self._set_state('jump' if not self.on_ground else 'idle')
                self.frame_index = 0.0
            else:
                self.frame_index = 0.0

        frame = self.frames[int(self.frame_index)]
        if not self.facing_right:
            frame = pygame.transform.flip(frame, True, False)
        self.surf = frame

    def move(self):
        if self.dead:
            self._animate()
            return

        keys = pygame.key.get_pressed()

        # forced_direction overrides keyboard (used for auto-walk sequences)
        self.direction = 0
        if self.forced_direction != 0:
            self.direction = self.forced_direction
            if not self._locked:
                self.facing_right = self.forced_direction > 0
        elif keys[pygame.K_a]:
            self.direction = -1
            if not self._locked:
                self.facing_right = False
        elif keys[pygame.K_d]:
            self.direction = 1
            if not self._locked:
                self.facing_right = True

        # Gravity + vertical movement
        self.vel_y += GRAVITY
        self.rect.top += int(self.vel_y)

        if self.rect.top >= GROUND_Y:
            self.rect.top = GROUND_Y
            self.vel_y = 0.0
            self.on_ground = True

        if self.invincible_frames > 0:
            self.invincible_frames -= 1

        # Reset hit-set when attack animation ends
        if self.state not in ('attack1', 'attack2'):
            self._atk_hit_enemies.clear()

        # State selection when not locked
        if not self._locked:
            if not self.on_ground:
                self._set_state('jump')
            elif self.direction != 0:
                self._set_state('walk')
            else:
                self._set_state('idle')

        self._animate()

    def attack_world_rect(self, camera_x):
        """Retorna Rect no espaço do mundo durante frames ativos do ataque, ou None."""
        if self.state not in ('attack1', 'attack2'):
            return None
        # Frames ativos: 1 em diante (evita hit instantâneo no frame 0)
        if int(self.frame_index) < 1:
            return None
        cx = camera_x + self.rect.centerx
        reach = 80
        if self.facing_right:
            return pygame.Rect(cx + 8, self.rect.top + 10, reach, self.rect.height - 20)
        else:
            return pygame.Rect(cx - 8 - reach, self.rect.top + 10, reach, self.rect.height - 20)

    # Bitmask pixel heart 16×14 (row = list of (left, width) runs)
    _HEART_ROWS = [
        [(1,4),(7,4)],   # .####..####.  row 0
        [(0,5),(6,5)],   # #####.#####   row 1
        [(0,11)],        # ###########   row 2
        [(0,11)],        # ###########   row 3
        [(1,9)],         # .#########.   row 4
        [(2,7)],         # ..#######..   row 5
        [(3,5)],         # ...#####...   row 6
        [(4,3)],         # ....###....   row 7
        [(5,1)],         # .....#.....   row 8
    ]

    def draw_hud(self, surface):
        total_w = self.MAX_HP * 20 + 6
        # dark frame
        pygame.draw.rect(surface, (0, 0, 0),    (3, 3, total_w + 2, 22))
        pygame.draw.rect(surface, (25, 15, 8),  (4, 4, total_w,     20))
        pygame.draw.rect(surface, (90, 60, 25), (4, 4, total_w,     20), 1)

        for i in range(self.MAX_HP):
            filled = i < self.hp
            c  = (230, 40,  40) if filled else (75, 35, 35)
            hi = (255, 130, 130) if filled else (100, 60, 60)
            x, y = 7 + i * 20, 7
            for r, runs in enumerate(self._HEART_ROWS):
                for lx, w in runs:
                    pygame.draw.rect(surface, c, (x + lx, y + r, w, 1))
            # single-pixel highlight
            if filled:
                pygame.draw.rect(surface, hi, (x + 1, y, 2, 1))
                pygame.draw.rect(surface, hi, (x + 7, y, 2, 1))

    @staticmethod
    def build_screen_overlay(width, height):
        """Cria surface SRCALPHA com scanlines + borda pixel-art. Chame uma vez."""
        surf = pygame.Surface((width, height), pygame.SRCALPHA)
        # Scanlines: linha preta semi-transparente a cada 2px
        for y in range(0, height, 2):
            pygame.draw.rect(surf, (0, 0, 0, 28), (0, y, width, 1))
        # Borda sólida 2px (estilo CRT/TV)
        pygame.draw.rect(surf, (0, 0, 0, 180), (0, 0, width, 2))
        pygame.draw.rect(surf, (0, 0, 0, 180), (0, height - 2, width, 2))
        pygame.draw.rect(surf, (0, 0, 0, 180), (0, 0, 2, height))
        pygame.draw.rect(surf, (0, 0, 0, 180), (width - 2, 0, 2, height))
        return surf
