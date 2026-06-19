import pygame
from code.Const     import WIND_WIDHT, WIND_HEIGHT, MENU_OPTION
from code.Level     import Level
from code.Level2    import Level2
from code.Menu      import Menu
from code.Options   import Options
from code.ScoreBoard import ScoreBoard
import code.Score   as Score
import code.Settings as Settings


class Game:
    def __init__(self):
        pygame.init()
        self.window = pygame.display.set_mode(size=(WIND_WIDHT, WIND_HEIGHT))

    def run(self):
        while True:
            menu = Menu(self.window)
            menu_return = menu.run()

            if menu_return == MENU_OPTION[0]:           # New Game
                Score.reset()
                level = Level(self.window, "level", menu_return)
                level_return = level.run()
                if level_return == 'level2':
                    level2 = Level2(self.window, 'level2', menu_return)
                    level2.run()
                # Save score regardless of win or loss
                Score.save_score(Score.get_score(), Settings.DIFFICULTY)

            elif menu_return == MENU_OPTION[1]:         # Options
                opts = Options(self.window)
                opts.run()

            elif menu_return == MENU_OPTION[2]:         # Records
                sb = ScoreBoard(self.window)
                sb.run()

            elif menu_return == MENU_OPTION[3]:         # Exit
                pygame.quit()
                quit()
