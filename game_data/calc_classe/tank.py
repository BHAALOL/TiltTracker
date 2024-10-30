# game_data/calc_classe/tank.py
from typing import Dict
from .base_calculator import BaseCalculator

class TankCalculator(BaseCalculator):
    def calculate_base_score(self, stats: Dict) -> float:
        """
        Calcule le score pour un TANK
        Score_Base = (Tank_Score × 0.6) + (KP × 0.3) + (Damage × 0.1)
        """
        # Calcul du Tank Score
        tank_score = (stats['total_damage_taken'] + stats['damage_self_mitigated']) / 2
        
        # Calcul du Kill Participation
        team_kills = stats['team_kills']
        kp = ((stats['kills'] + stats['assists']) / team_kills * 100) if team_kills > 0 else 0
        
        # Dégâts aux champions
        damage = stats['total_damage_dealt_to_champions']

        # Normalisation des scores sur 100
        max_tank_score = 100000  # Valeur à ajuster selon les données réelles
        max_damage = 50000       # Valeur à ajuster selon les données réelles

        normalized_tank_score = min((tank_score / max_tank_score) * 100, 100)
        normalized_damage = min((damage / max_damage) * 100, 100)

        # Calcul du score final
        return (
            (normalized_tank_score * 0.6) +
            (kp * 0.3) +
            (normalized_damage * 0.1)
        )