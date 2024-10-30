# game_data/calc_classe/base_calculator.py
from abc import ABC, abstractmethod
from typing import Dict

class BaseCalculator(ABC):
    def __init__(self):
        self.win_multipliers = {
            90: 2.5,  # >90% - Exceptionnel
            75: 2.0,  # 75-90% - Très bon
            60: 1.5,  # 60-75% - Bon
            45: 1.0,  # 45-60% - Moyen
            30: 0.5,  # 30-45% - Faible
            0: 0.2    # <30% - Très faible
        }

        self.lose_multipliers = {
            90: 3.0,  # >90% - Exceptionnel
            75: 2.0,  # 75-90% - Très bon
            60: 1.0,  # 60-75% - Bon
            45: 0.5,  # 45-60% - Moyen
            30: 0.3,  # 30-45% - Faible
            0: 0.1    # <30% - Très faible
        }

    def get_multiplier(self, percentage: float, is_win: bool) -> float:
        """Détermine le multiplicateur basé sur le pourcentage de performance"""
        multipliers = self.win_multipliers if is_win else self.lose_multipliers
        
        for threshold, mult in sorted(multipliers.items(), reverse=True):
            if percentage >= threshold:
                return mult
        return multipliers[0]

    def calculate_final_score(self, base_score: float, is_win: bool) -> int:
        """Calcule le score final avec la formule générale"""
        base = 15 if is_win else -15
        multiplier = self.get_multiplier(base_score, is_win)
        return int(base + (base * multiplier))

    @abstractmethod
    def calculate_base_score(self, stats: Dict) -> float:
        """Calcule le score de base selon la classe"""
        pass