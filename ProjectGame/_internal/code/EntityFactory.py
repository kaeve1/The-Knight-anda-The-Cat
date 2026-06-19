from unittest import case

from code.Background import Background
from code.Const import WIND_WIDHT, GROUND_Y
from code.Player import Player


class EntityFactory:

    @staticmethod
    def get_entity(entity_name: str, position=(0, 0)):
        match entity_name:
            case "Level1bg":
                list_bg = []

                for i in range(1,8):
                    list_bg.append(Background(f'level1bg{i}', (0, 0)))
                    list_bg.append(Background(f'level1bg{i}', (WIND_WIDHT, 0)))


                return list_bg
            case "Player":
                return Player("Player1", (10, GROUND_Y))

        return []