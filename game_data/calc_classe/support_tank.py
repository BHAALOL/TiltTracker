# game_data/calc_classe/support_tank.py
from typing import Dict
from .base_calculator import BaseCalculator

class SupportTankCalculator(BaseCalculator):
    def calculate_base_score(self, stats: Dict) -> float:
        """
        Calcule le score pour un SUPPORT TANK
        Score_Base = (Tank_Score × 0.4) + (KP × 0.4) + (Utility × 0.2)
        """
        # Calcul du Tank Score
        tank_score = (stats['total_damage_taken'] + stats['damage_self_mitigated']) / 2
        
        # Calcul du Kill Participation (accent sur les assists)
        team_kills = stats['team_kills']
        kp = ((stats['kills'] * 0.5 + stats['assists']) / team_kills * 100) if team_kills > 0 else 0
        
        # Calcul du score d'utilité (heal + shield)
        utility = stats.get('total_heal', 0) + stats.get('total_shield', 0)

        # Normalisation des scores sur 100
        max_tank_score = 70000   # Valeur adaptée aux supports tanks
        max_utility = 20000      # Valeur à ajuster selon les données réelles

        normalized_tank_score = min((tank_score / max_tank_score) * 100, 100)
        normalized_utility = min((utility / max_utility) * 100, 100)

        # Calcul du score final
        return (
            (normalized_tank_score * 0.4) +
            (kp * 0.4) +
            (normalized_utility * 0.2)
        )