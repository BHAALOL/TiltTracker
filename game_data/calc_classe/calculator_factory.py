# game_data/calc_classe/calculator_factory.py
import json
import os
from typing import Dict, List

from .tank import TankCalculator
from .fighter import FighterCalculator
from .assassin import AssassinCalculator
from .marksman import MarksmanCalculator
from .mage import MageCalculator
from .support_tank import SupportTankCalculator
from .support_mage import SupportMageCalculator

class CalculatorFactory:
    def __init__(self):
        self.champions_data = self._load_champions_data()
        self.calculators = {
            'TANK': TankCalculator(),
            'FIGHTER': FighterCalculator(),
            'ASSASSIN': AssassinCalculator(),
            'MARKSMAN': MarksmanCalculator(),
            'MAGE': MageCalculator(),
            'SUPPORT_TANK': SupportTankCalculator(),
            'SUPPORT_MAGE': SupportMageCalculator()
        }

    def _load_champions_data(self) -> Dict:
        """Charge les données des champions depuis le fichier JSON"""
        json_path = os.path.join(os.path.dirname(__file__), '..', 'champions.json')
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)['data']

    def get_champion_class(self, champion_id: str) -> str:
        """Détermine la classe d'un champion à partir de son ID"""
        # Trouver le champion par son ID
        champion_data = None
        for champ in self.champions_data.values():
            if champ['key'] == str(champion_id):
                champion_data = champ
                break

        if not champion_data:
            raise ValueError(f"Champion ID {champion_id} non trouvé")

        tags = champion_data['tags']

        # Logique de détermination de la classe prioritaire
        if 'Marksman' in tags:
            return 'MARKSMAN'
        elif 'Assassin' in tags:
            return 'ASSASSIN'
        elif 'Support' in tags:
            if 'Tank' in tags:
                return 'SUPPORT_TANK'
            return 'SUPPORT_MAGE'
        elif 'Tank' in tags:
            return 'TANK'
        elif 'Fighter' in tags:
            return 'FIGHTER'
        elif 'Mage' in tags:
            return 'MAGE'
        else:
            return 'FIGHTER'  # Par défaut

    def get_calculator(self, champion_id: str):
        """Retourne le calculateur approprié pour un champion"""
        champion_class = self.get_champion_class(champion_id)
        return self.calculators[champion_class]