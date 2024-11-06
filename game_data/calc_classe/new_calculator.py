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
        self.coefficients = ChampionClassConfig.get_coefficients(champion_class)
        
    def calculate_score(self, stats: Dict, is_win: bool) -> int:
        """
        Calcule le score final selon les formules fournies
        
        Args:
            stats: Dictionnaire contenant les statistiques du match
            is_win: True si victoire, False si défaite
            
        Returns:
            Score calculé (positif pour victoire, négatif pour défaite)
        """
        try:
            # Extraction des statistiques
            kills = stats['kills']
            assists = stats['assists']
            deaths = max(1, stats['deaths'])  # Éviter division par zéro
            team_kills = max(1, stats['team_total_kills'])
            damage_dealt = stats['total_damage_dealt_to_champions']
            damage_taken = stats['total_damage_taken']
            team_damage_dealt = max(1, stats['team_total_damage_dealt'])
            team_damage_taken = max(1, stats['team_total_damage_taken'])
            
            # Calcul des ratios
            damage_ratio = (damage_dealt * 100 / team_damage_dealt * self.coefficients.rd)
            tank_ratio = (damage_taken * 100 / team_damage_taken * self.coefficients.rt)
            kda_ratio = (kills + assists) / deaths
            kill_participation = (kills + assists) / team_kills * 100
            
            if is_win:
                # POINT_DPS_WIN = (((DI × 100/TTDI × RD) + (DS × 100/TTDS × RT)) × ((K + A)/D) + ((K + A)/TTKT × 100)) × (15/10)
                return int((((damage_ratio + tank_ratio) * kda_ratio) + kill_participation) * 1.5)
            else:
                # POINT_DPS_LOSS = -(-((DI × 100/TTDI × RD + DS × 100/TTDS × RT) × ((K + A)/D) + ((K + A)/TTKT × 100)) × 15/10 - 500) × (-1)
                base_calc = (((damage_ratio + tank_ratio) * kda_ratio) + kill_participation) * 1.5
                return int(-(-base_calc - 100) * -1)
                
        except Exception as e:
            logger.error(f"Erreur lors du calcul du score: {e}")
            return 0