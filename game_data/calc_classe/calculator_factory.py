# game_data/calc_classe/calculator_factory.py

import json
import os
from typing import Dict
from .champion_class_config import ChampionClass
from .new_calculator import MatchScoreCalculator

class CalculatorFactory:
    def __init__(self):
        self.champions_data = self._load_champions_data()

    def _load_champions_data(self) -> Dict:
        """Charge les données des champions depuis le fichier JSON"""
        json_path = os.path.join(os.path.dirname(__file__), '..', 'champions.json')
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)['data']

    def get_champion_class_type(self, champion_id: str) -> ChampionClass:
        """
        Détermine si le champion est un TANK ou un DPS
        """
        # Trouver le champion par son ID
        champion_data = None
        for champ in self.champions_data.values():
            if champ['key'] == str(champion_id):
                champion_data = champ
                break

        if not champion_data:
            raise ValueError(f"Champion ID {champion_id} non trouvé")

        # Vérifier les tags
        return ChampionClass.TANK if "Tank" in champion_data['tags'] else ChampionClass.DPS

    def get_calculator(self, champion_id: str) -> MatchScoreCalculator:
        """
        Retourne le calculateur approprié pour un champion
        """
        champion_class = self.get_champion_class_type(champion_id)
        return MatchScoreCalculator(champion_class)