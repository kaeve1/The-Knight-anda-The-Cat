import pygame
from code.Const import GROUND_Y

ENE_W = 128
ENE_H = 128
DRAW_W = 96   # largura do sprite desenhado
DRAW_H = 84   # mesma altura do player (FRAME_H) → alinha os pés automaticamente

_SHOOT_FRAME = 8   # frame da animação Shot_1 em que o projétil é criado
_MELEE_FRAME = 2   # frame da animação Attack em que o dano é causado

_ANIM_SPEED = {'idle': 0.12, 'walk': 0.15, 'attack': 0.18, 'hurt': 0.3, 'dead': 0.1}

_CFG = {
    'archer': {
        'hp': 1, 'speed': 0.8, 'attack_range': 350, 'cooldown': 160,
        'sheets': {
            'idle':   ('Skeleton_Archer/Idle.png',  7),
            'walk':   ('Skeleton_Archer/Walk.png',  8),
            'attack': ('Skeleton_Archer/Shot_1.png', 15),
            'hurt':   ('Skeleton_Archer/Hurt.png',  2),
            'dead':   ('Skeleton_Archer/Dead.png',  5),
        },
    },
    'spearman': {
        'hp': 2, 'speed': 1.2, 'attack_range': 68, 'cooldown': 90,
        'sheets': {
            'idle':   ('Skeleton_Spearman/Idle.png',     7),
            'walk':   ('Skeleton_Spearman/Walk.png',     7),
            'attack': ('Skeleton_Spearman/Attack_1.png', 4),
            'hurt':   ('Skeleton_Spearman/Hurt.png',     3),
            'dead':   ('Skeleton_Spearman/Dead.png',     5),
        },
    },
    'warrior': {
        'hp': 2, 'speed': 1.6, 'attack_range': 68, 'cooldown': 80,
        'sheets': {
            'idle':   ('Skeleton_Warrior/Idle.png',     7),
            'walk':   ('Skeleton_Warrior/Walk.png',     7),
            'attack': ('Skeleton_Warrior/Attack_1.png', 5),
            'hurt':   ('Skeleton_Warrior/Hurt.png',     2),
            'dead':   ('Skeleton_Warrior/Dead.png',     4),
        },
    },
}


def _load_sheet(path, count):
    sheet = pygame.image.load(path).convert_alpha()
    size = (DRAW_W, DRAW_H)
    return [
        pygame.transform.scale(sheet.subsurface((i * ENE_W, 0, ENE_W, ENE_H)), size)
        for i in range(count)
    ]


class Projectile:
    SPEED = 6

    def __init__(self, world_x, world_y, direction):
        self.world_x = float(world_x)
        self.world_y = float(world_y)
        self.direction = direction
        self.alive = True
        raw = pygame.image.load('./assets/skeleton/Skeleton_Archer/Arrow.png').convert_alpha()
        self.surf = raw if direction == 1 else pygame.transform.flip(raw, True, False)

    def update(self):
        self.world_x += self.SPEED * self.direction
        if not (-300 < self.world_x < 12000):
            self.alive = False

    def draw(self, surface, camera_x):
        sx = int(self.world_x - camera_x) - 24
        sy = int(self.world_y) - 24
        surface.blit(self.surf, (sx, sy))

    def world_rect(self):
        return pygame.Rect(int(self.world_x) - 10, int(self.world_y) - 10, 20, 20)


class Enemy:
    # Player feet at GROUND_Y+61=301. Skeleton feet after scale at _FLOOR_Y+83.
    # To align: _FLOOR_Y = 301 - 83 = 218
    _FLOOR_Y = GROUND_Y - 22   # 218

    def __init__(self, enemy_type, world_x):
        cfg = _CFG[enemy_type]
        self.enemy_type = enemy_type
        self.world_x = float(world_x)
        self.facing_right = False
        self.dead = False
        self.alive = True
        self._locked = False
        self.frame_index = 0.0
        self.hp = cfg['hp']
        self.MAX_HP = cfg['hp']
        self.speed = cfg['speed']
        self.attack_range = cfg['attack_range']
        self.attack_cooldown = 0
        self.ATTACK_COOLDOWN = cfg['cooldown']
        self.immune_frames = 0
        self.projectiles = []
        self._shot_fired = False
        self._dmg_dealt = False

        base = './assets/skeleton/'
        self.anim = {
            state: _load_sheet(base + path, count)
            for state, (path, count) in cfg['sheets'].items()
        }
        self.state = 'idle'
        self.frames = self.anim['idle']
        self.surf = self.frames[0]

    def _set_state(self, state):
        if self.state != state:
            self.state = state
            self.frame_index = 0.0
            self.frames = self.anim[state]
            self._shot_fired = False
            self._dmg_dealt = False

    def take_damage(self, amount):
        if self.dead or self.immune_frames > 0:
            return
        self.immune_frames = 20
        self.hp = max(0, self.hp - amount)
        if self.hp == 0:
            self.dead = True
            self._locked = True
            self._set_state('dead')
        elif self.state != 'hurt':
            self._locked = True
            self._set_state('hurt')

    def _animate(self):
        self.frame_index += _ANIM_SPEED.get(self.state, 0.15)
        total = len(self.frames)

        if self.frame_index >= total:
            if self.state == 'dead':
                self.frame_index = float(total - 1)
                self.alive = False
            elif self.state in ('hurt', 'attack'):
                if self.state == 'attack':
                    self.attack_cooldown = self.ATTACK_COOLDOWN
                self._locked = False
                self._set_state('idle')
            else:
                self.frame_index = 0.0

        frame = self.frames[int(self.frame_index)]
        if not self.facing_right:
            frame = pygame.transform.flip(frame, True, False)
        self.surf = frame

    def update(self, player_world_x):
        """Returns True if this enemy deals melee damage this frame."""
        if not self.alive:
            return False

        if self.immune_frames > 0:
            self.immune_frames -= 1
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1

        dx = player_world_x - self.world_x
        dist = abs(dx)
        self.facing_right = dx > 0

        deal_damage = False

        if not self._locked:
            if dist <= self.attack_range and self.attack_cooldown == 0:
                self._locked = True
                self._set_state('attack')
            elif dist > self.attack_range:
                self.world_x += self.speed * (1 if dx > 0 else -1)
                self._set_state('walk')
            else:
                self._set_state('idle')

        # Archer: spawn arrow at _SHOOT_FRAME
        if self.state == 'attack' and self.enemy_type == 'archer':
            if not self._shot_fired and int(self.frame_index) >= _SHOOT_FRAME:
                self._shot_fired = True
                direction = 1 if self.facing_right else -1
                proj = Projectile(
                    self.world_x + 40 * direction,
                    self._FLOOR_Y + DRAW_H // 2 - 10,  # centro vertical do sprite
                    direction,
                )
                self.projectiles.append(proj)

        # Melee: flag damage at _MELEE_FRAME
        if self.state == 'attack' and self.enemy_type != 'archer':
            if not self._dmg_dealt and int(self.frame_index) >= _MELEE_FRAME:
                if dist <= self.attack_range + 20:
                    self._dmg_dealt = True
                    deal_damage = True

        for p in self.projectiles:
            p.update()
        self.projectiles = [p for p in self.projectiles if p.alive]

        self._animate()
        return deal_damage

    def world_hitbox(self):
        return pygame.Rect(int(self.world_x) - 20, self._FLOOR_Y + 18, 40, DRAW_H - 24)

    def draw(self, surface, camera_x):
        if not self.alive:
            return
        sx = int(self.world_x - camera_x) - DRAW_W // 2

        # White blink when recently hit
        if self.immune_frames > 8 and (self.immune_frames // 3) % 2 == 0:
            flash = self.surf.copy()
            flash.fill((255, 255, 255), special_flags=pygame.BLEND_RGB_MAX)
            surface.blit(flash, (sx, self._FLOOR_Y))
        else:
            surface.blit(self.surf, (sx, self._FLOOR_Y))

        for p in self.projectiles:
            p.draw(surface, camera_x)

        if not self.dead and self.MAX_HP > 1:
            bx = sx + DRAW_W // 4
            by = self._FLOOR_Y - 7
            bw = DRAW_W // 2
            pygame.draw.rect(surface, (40, 0, 0),   (bx - 1, by - 1, bw + 2, 6))
            pygame.draw.rect(surface, (80, 0, 0),   (bx, by, bw, 4))
            pygame.draw.rect(surface, (220, 30, 30), (bx, by, int(bw * self.hp / self.MAX_HP), 4))
