# game_data/calc_classe/new_calculator.py

from typing import Dict
from .champion_class_config import ChampionClass, ChampionClassConfig

class MatchScoreCalculator:
    def __init__(self, champion_class: ChampionClass):
        """
        Initialise le calculateur avec la classe du champion
        
        Args:
            champion_class: ChampionClass.DPS ou ChampionClass.TANK
        """
        self.champion_class = champion_class
        self.coefficients = ChampionClassConfig.get_coefficients(champion_class)

    def calculate_performance_score(self, stats: Dict) -> float:
        """
        Calcule le score de performance selon la classe du champion
        
        Args:
            stats: Statistiques du joueur
            
        Returns:
            Score de performance qui servira à classer le joueur
        """
        # Calcul du Kill Participation (KP)
        kills_assists = stats['kills'] + stats['assists']
        team_kills = stats['team_kills'] if stats['team_kills'] > 0 else 1
        kill_participation = (kills_assists / team_kills) * 100
        
        # Dégâts aux champions
        damage_score = stats['total_damage_dealt_to_champions']
        
        # Dégâts absorbés et mitigés
        tank_score = stats['total_damage_taken'] + stats['damage_self_mitigated']
        
        # Score d'utilité (CC + vision)
        utility_score = stats['total_time_crowd_control_dealt'] + (stats['vision_score'] * 100)

        # Calculer le score selon la classe
        if self.champion_class == ChampionClass.TANK:
            return (
                (tank_score * 0.5) +          # 50% tank
                (kill_participation * 0.3) +   # 30% participation
                (damage_score * 0.2)          # 20% dégâts
            )
        else:  # DPS
            return (
                (damage_score * 0.6) +        # 60% dégâts
                (kill_participation * 0.3) +   # 30% participation
                (utility_score * 0.1)         # 10% utility
            )

    def calculate_score(self, stats: Dict, rank_in_team: int, is_victory: bool) -> int:
        """
        Calcule le score final en fonction du rang dans l'équipe et du résultat
        """
        # Points selon le rang et la victoire/défaite
        victory_points = {
            1: 400,   # 1er
            2: 300,   # 2ème
            3: 200,   # 3ème
            4: 100,   # 4ème
            5: -100   # 5ème
        }

        defeat_points = {
            1: 100,    # 1er
            2: -100,   # 2ème
            3: -200,   # 3ème
            4: -300,   # 4ème
            5: -400    # 5ème
        }

        points_table = victory_points if is_victory else defeat_points
        return points_table.get(rank_in_team, 0)