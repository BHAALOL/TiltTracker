from typing import Dict
from .base_calculator import BaseCalculator

class AssassinCalculator(BaseCalculator):
    def calculate_performance_score(self, stats: Dict) -> float:
        """
        Calcule le score de performance pour un ASSASSIN
        Score = (Dégâts × 0.6) + (Kill Participation × 0.3) + (Utility × 0.1)
        
        Args:
            stats: Dictionnaire contenant les statistiques du joueur
            
        Returns:
            Score de performance qui servira à classer le joueur
        """
        # Calcul du Kill Participation (KP)
        kills_assists = stats['kills'] + stats['assists']
        team_kills = stats['team_kills'] if stats['team_kills'] > 0 else 1
        kill_participation = (kills_assists / team_kills) * 100
        
        # Dégâts aux champions
        damage_score = stats['total_damage_dealt_to_champions']
        
        # Score d'utilité (CC score)
        utility_score = stats['total_time_crowd_control_dealt']
        
        # Score final
        return (
            (damage_score * 0.6) +        # 60% dégâts
            (kill_participation * 0.3) +   # 30% participation
            (utility_score * 0.1)         # 10% utility
        )