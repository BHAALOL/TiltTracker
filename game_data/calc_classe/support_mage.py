from typing import Dict
from .base_calculator import BaseCalculator

class SupportMageCalculator(BaseCalculator):
    def calculate_performance_score(self, stats: Dict) -> float:
        """
        Calcule le score de performance pour un SUPPORT MAGE
        Score = (Kill Participation × 0.4) + (Utility × 0.4) + (Dégâts × 0.2)
        
        Args:
            stats: Dictionnaire contenant les statistiques du joueur
            
        Returns:
            Score de performance qui servira à classer le joueur
        """
        # Calcul du Kill Participation (KP)
        kills_assists = stats['kills'] + stats['assists']
        team_kills = stats['team_kills'] if stats['team_kills'] > 0 else 1
        kill_participation = (kills_assists / team_kills) * 100
        
        # Score d'utilité (CC + vision)
        utility_score = stats['total_time_crowd_control_dealt']
        
        # Dégâts aux champions
        damage_score = stats['total_damage_dealt_to_champions']
        
        # Score final
        return (
            (kill_participation * 0.4) +   # 40% participation
            (utility_score * 0.4) +        # 40% utility
            (damage_score * 0.2)          # 20% dégâts
        )