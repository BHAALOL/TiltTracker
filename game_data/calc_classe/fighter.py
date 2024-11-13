from typing import Dict
from .base_calculator import BaseCalculator

class FighterCalculator(BaseCalculator):
    def calculate_performance_score(self, stats: Dict) -> float:
        """
        Calcule le score de performance pour un FIGHTER
        Score = (Dégâts × 0.4) + (Kill Participation × 0.3) + (Dégâts absorbés × 0.3)
        
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
        
        # Dégâts absorbés
        tank_score = stats['total_damage_taken'] + stats['damage_self_mitigated']
        
        # Score final
        return (
            (damage_score * 0.4) +        # 40% dégâts
            (kill_participation * 0.3) +   # 30% participation
            (tank_score * 0.3)            # 30% résistance
        )