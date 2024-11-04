from abc import ABC, abstractmethod
from typing import Dict

class BaseCalculator(ABC):
    def calculate_final_score(self, base_score: float, win: bool) -> int:
        """
        Calcule le score final en fonction du KDA et de la victoire/défaite
        Score final = 15 * KDA * (1 ou -1 selon victoire/défaite)
        """
        # Pour debug
        print(f"KDA reçu (base_score): {base_score}")
        
        # Calcul des points (positifs pour une victoire, négatifs pour une défaite)
        multiplier = 1 if win else -1
        score = round(15 * base_score * multiplier)
        
        # Pour debug
        print(f"Score calculé: {score}")
        
        return score

    @abstractmethod
    def calculate_base_score(self, stats: Dict) -> float:
        """
        Calcule le KDA: (Kills + Assists) / Deaths
        """
        kills = stats['kills']
        deaths = stats['deaths']
        assists = stats['assists']
        
        # Pour debug
        print(f"Kills: {kills}, Deaths: {deaths}, Assists: {assists}")
        
        # Éviter division par zéro
        kda = (kills + assists) / max(deaths, 1)
        
        # Pour debug
        print(f"KDA calculé: {kda}")
        
        return kda