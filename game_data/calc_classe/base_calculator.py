from abc import ABC, abstractmethod
from typing import Dict

class BaseCalculator(ABC):
    # Points attribués selon le rang et la victoire/défaite
    VICTORY_POINTS = {
        1: 400,   # 1er
        2: 300,   # 2ème
        3: 200,   # 3ème
        4: 100,   # 4ème
        5: -100   # 5ème
    }

    DEFEAT_POINTS = {
        1: 100,    # 1er
        2: -100,   # 2ème
        3: -200,   # 3ème
        4: -300,   # 4ème
        5: -400    # 5ème
    }

    def calculate_score(self, stats: Dict, rank_in_team: int, is_victory: bool) -> int:
        """
        Calcule le score final en fonction du rang dans l'équipe et du résultat
        
        Args:
            stats: Statistiques du joueur
            rank_in_team: Position du joueur dans l'équipe (1-5)
            is_victory: True si victoire, False si défaite
        
        Returns:
            Points attribués selon le classement
        """
        points_table = self.VICTORY_POINTS if is_victory else self.DEFEAT_POINTS
        return points_table.get(rank_in_team, 0)

    @abstractmethod
    def calculate_performance_score(self, stats: Dict) -> float:
        """
        Calcule le score de performance qui servira à classer les joueurs
        Cette méthode doit être implémentée par chaque classe spécifique
        
        Args:
            stats: Statistiques du joueur
            
        Returns:
            Score de performance (plus il est élevé, meilleur est le classement)
        """
        pass