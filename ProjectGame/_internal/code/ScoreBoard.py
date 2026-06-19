import sys
import pygame
from code.Const import WIND_WIDHT, WIND_HEIGHT
from code.Score import get_top_scores
from code.Player import Player


class ScoreBoard:
    def __init__(self, window):
        self.window = window
        try:
            raw = pygame.image.load('./assets/records.png').convert()
            self._bg = pygame.transform.scale(raw, (WIND_WIDHT, WIND_HEIGHT))
        except Exception:
            self._bg = None

        self._overlay = Player.build_screen_overlay(WIND_WIDHT, WIND_HEIGHT)

    def _draw_scene(self, dim, scores, f_lg, f_xs, f_sm):
        if self._bg:
            self.window.blit(self._bg, (0, 0))
        else:
            self.window.fill((10, 6, 4))
        self.window.blit(dim, (0, 0))

        # title
        for dx, dy, col in ((2, 2, (0, 0, 0)), (0, 0, (255, 220, 50))):
            t = f_lg.render('High Scores', True, col)
            self.window.blit(t, t.get_rect(center=(WIND_WIDHT // 2 + dx, 26 + dy)))
        pygame.draw.rect(self.window, (110, 78, 22), (18, 46, WIND_WIDHT - 36, 2))

        if not scores:
            msg = f_sm.render('No scores yet — go fight!', True, (160, 150, 130))
            self.window.blit(msg, msg.get_rect(center=(WIND_WIDHT // 2, WIND_HEIGHT // 2)))
        else:
            cols_x = [22, 65, 185, 310, 438]
            for text, x in zip(('#', 'Score', 'Difficulty', 'Date', 'Time'), cols_x):
                self.window.blit(f_xs.render(text, True, (190, 148, 30)), (x, 56))
            pygame.draw.rect(self.window, (80, 58, 14), (18, 73, WIND_WIDHT - 36, 1))

            for i, (score, diff, date) in enumerate(scores):
                y = 80 + i * 21
                col = (255, 215, 50) if i == 0 else (200, 195, 178)
                if i % 2 == 0:
                    hl = pygame.Surface((WIND_WIDHT - 36, 20), pygame.SRCALPHA)
                    hl.fill((255, 255, 255, 10))
                    self.window.blit(hl, (18, y))
                date_part = date[:10] if date else ''
                time_part = date[11:16] if date and len(date) > 10 else ''
                for text, x in zip(
                    (f'{i+1}.', str(score), diff.upper(), date_part, time_part),
                    cols_x
                ):
                    self.window.blit(f_xs.render(text, True, col), (x, y + 1))

        hint = f_xs.render('Esc / Enter  →  back to menu', True, (70, 62, 50))
        self.window.blit(hint, hint.get_rect(center=(WIND_WIDHT // 2, WIND_HEIGHT - 9)))
        self.window.blit(self._overlay, (0, 0))

    def run(self):
        clock = pygame.time.Clock()
        f_lg  = pygame.font.Font('./assets/font/Cardinal.ttf', 36)
        f_sm  = pygame.font.Font('./assets/font/Cardinal.ttf', 22)
        f_xs  = pygame.font.Font('./assets/font/Cardinal.ttf', 17)

        scores = get_top_scores(10)

        dim  = pygame.Surface((WIND_WIDHT, WIND_HEIGHT), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 155))
        fade = pygame.Surface((WIND_WIDHT, WIND_HEIGHT))
        fade.fill((0, 0, 0))

        # ── fade in desde preto ───────────────────────────────────
        for alpha in range(255, -1, -8):
            clock.tick(60)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
            self._draw_scene(dim, scores, f_lg, f_xs, f_sm)
            fade.set_alpha(alpha)
            self.window.blit(fade, (0, 0))
            pygame.display.flip()

        # ── loop principal ────────────────────────────────────────
        while True:
            clock.tick(60)
            self._draw_scene(dim, scores, f_lg, f_xs, f_sm)
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                        # ── fade out para preto antes de voltar ───
                        for alpha in range(0, 256, 8):
                            clock.tick(60)
                            self._draw_scene(dim, scores, f_lg, f_xs, f_sm)
                            fade.set_alpha(alpha)
                            self.window.blit(fade, (0, 0))
                            pygame.display.flip()
                        return
