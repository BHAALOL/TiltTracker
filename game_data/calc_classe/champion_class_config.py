from enum import Enum
from dataclasses import dataclass

class ChampionClass(Enum):
    """Types de classes de champions"""
    DPS = "DPS"
    TANK = "TANK"

@dataclass
class ClassCoefficients:
    """Coefficients pour chaque classe de champion"""
    rd: float  # Coefficient de dégâts
    rt: float  # Coefficient tank

class ChampionClassConfig:
    """Configuration des coefficients pour chaque classe de champion"""
    
    # Coefficients par classe
    COEFFICIENTS = {
        ChampionClass.DPS: ClassCoefficients(rd=1, rt=1),
        ChampionClass.TANK: ClassCoefficients(rd=1, rt=1)
    }
    
    @staticmethod
    def get_coefficients(champion_class: ChampionClass) -> ClassCoefficients:
        """
        Récupère les coefficients pour une classe de champion donnée
        
        Args:
            champion_class: La classe du champion (DPS ou TANK)
            
        Returns:
            ClassCoefficients contenant rd et rt
            
        Raises:
            ValueError si la classe n'existe pas
        """
        if champion_class not in ChampionClassConfig.COEFFICIENTS:
            raise ValueError(f"Classe de champion non reconnue: {champion_class}")
            
        return ChampionClassConfig.COEFFICIENTS[champion_class]
        
    @staticmethod
    def is_valid_class(champion_class: str) -> bool:
        """Vérifie si une classe est valide"""
        try:
            ChampionClass(champion_class.upper())
            return True
        except ValueError:
            return False