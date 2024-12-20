# game_data/calc_classe/marksman.py
from typing import Dict
from .base_calculator import BaseCalculator

class MarksmanCalculator(BaseCalculator):
    def calculate_base_score(self, stats: Dict) -> float:
        """
        Calcule le score pour un MARKSMAN
        Score_Base = (Damage × 0.7) + (KP × 0.3)
        """
        # Calcul du Kill Participation
        team_kills = stats['team_kills']
        kp = ((stats['kills'] + stats['assists']) / team_kills * 100) if team_kills > 0 else 0
        
        # Dégâts aux champions
        damage = stats['total_damage_dealt_to_champions']

        # Normalisation des dégâts sur 100
        max_damage = 65000  # Valeur plus élevée pour les MARKSMAN
        normalized_damage = min((damage / max_damage) * 100, 100)

        # Calcul du score final
        return (normalized_damage * 0.7) + (kp * 0.3)