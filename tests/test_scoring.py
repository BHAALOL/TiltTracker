# tests/test_scoring.py
import logging
import json
import os
from tilttracker.modules.game_processor import GameProcessor
from game_data.calc_classe.calculator_factory import CalculatorFactory

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_champion_classification():
    """Teste la classification des champions"""
    factory = CalculatorFactory()
    test_champions = {
        "266": ("Aatrox", "FIGHTER"),      # Aatrox
        "103": ("Ahri", "MAGE"),           # Ahri
        "84": ("Akali", "ASSASSIN"),       # Akali
        "12": ("Alistar", "SUPPORT_TANK"), # Alistar
        "1": ("Annie", "MAGE"),            # Annie
        "22": ("Ashe", "MARKSMAN"),        # Ashe
    }

    logger.info("=== Test de Classification des Champions ===")
    for champ_id, (champ_name, expected_class) in test_champions.items():
        try:
            actual_class = factory.get_champion_class(champ_id)
            success = actual_class == expected_class
            logger.info(f"Champion: {champ_name} - Attendu: {expected_class} - Obtenu: {actual_class} - {'✅' if success else '❌'}")
        except Exception as e:
            logger.error(f"Erreur pour {champ_name}: {e}")

def test_score_calculation():
    """Teste le calcul des scores pour différents scénarios"""
    processor = GameProcessor()
    
    # Exemple de stats pour différents types de performances
    test_scenarios = [
        {
            "name": "Tank - Bonne performance, Victoire",
            "match_stats": {
                "info": {
                    "participants": [
                        {"teamId": 100, "kills": 5},
                        {"teamId": 100, "kills": 10},
                        {"teamId": 100, "kills": 8},
                    ]
                }
            },
            "player_stats": {
                "champion_id": "12",  # Alistar
                "champion_name": "Alistar",
                "team_id": 100,
                "kills": 2,
                "deaths": 3,
                "assists": 25,
                "total_damage_dealt_to_champions": 15000,
                "total_damage_taken": 45000,
                "damage_self_mitigated": 40000,
                "win": True
            }
        },
        {
            "name": "Marksman - Performance exceptionnelle, Défaite",
            "match_stats": {
                "info": {
                    "participants": [
                        {"teamId": 200, "kills": 12},
                        {"teamId": 200, "kills": 8},
                        {"teamId": 200, "kills": 5},
                    ]
                }
            },
            "player_stats": {
                "champion_id": "22",  # Ashe
                "champion_name": "Ashe",
                "team_id": 200,
                "kills": 15,
                "deaths": 4,
                "assists": 10,
                "total_damage_dealt_to_champions": 45000,
                "total_damage_taken": 20000,
                "damage_self_mitigated": 5000,
                "win": False
            }
        },
        {
            "name": "Mage - Performance moyenne, Victoire",
            "match_stats": {
                "info": {
                    "participants": [
                        {"teamId": 100, "kills": 7},
                        {"teamId": 100, "kills": 9},
                        {"teamId": 100, "kills": 6},
                    ]
                }
            },
            "player_stats": {
                "champion_id": "103",  # Ahri
                "champion_name": "Ahri",
                "team_id": 100,
                "kills": 8,
                "deaths": 6,
                "assists": 12,
                "total_damage_dealt_to_champions": 30000,
                "total_damage_taken": 25000,
                "damage_self_mitigated": 8000,
                "win": True
            }
        }
    ]

    logger.info("\n=== Test de Calcul des Scores ===")
    for scenario in test_scenarios:
        try:
            logger.info(f"\nScénario: {scenario['name']}")
            score, summary = processor.calculate_match_score(
                scenario['match_stats'],
                scenario['player_stats']
            )
            logger.info(f"Résultat:\n{summary}")
        except Exception as e:
            logger.error(f"Erreur dans le scénario {scenario['name']}: {e}")

def test_full_game_processing():
    """Teste le traitement complet d'une partie réelle"""
    processor = GameProcessor()
    
    logger.info("\n=== Test de Traitement Complet ===")
    
    # Test avec votre compte
    summoner_name = "GuigZer"
    tag_line = "1101"
    
    try:
        # Récupération et traitement d'une partie
        logger.info(f"Test avec le compte {summoner_name}#{tag_line}")
        
        # Vérification du joueur
        player_id = processor.ensure_player_exists(summoner_name, tag_line)
        if not player_id:
            logger.error("❌ Échec de la vérification du joueur")
            return False
        
        # Récupération du PUUID
        puuid = processor.riot_api.get_puuid(summoner_name, tag_line)
        if not puuid:
            logger.error("❌ PUUID non trouvé")
            return False
            
        # Récupération des parties récentes
        matches = processor.riot_api.get_recent_aram_matches(puuid, count=1)
        if not matches:
            logger.error("❌ Aucune partie trouvée")
            return False
            
        # Traitement de la dernière partie
        success = processor._process_single_match(matches[0], puuid)
        if success:
            logger.info("✅ Partie traitée avec succès")
        else:
            logger.error("❌ Échec du traitement de la partie")
            
    except Exception as e:
        logger.error(f"❌ Erreur lors du test: {e}")
        return False
    finally:
        processor.close()

    return True

if __name__ == "__main__":
    logger.info("🏁 Début des tests du système de scoring")
    
    try:
        # Test de la classification des champions
        test_champion_classification()
        
        # Test des calculs de score
        test_score_calculation()
        
        # Test du traitement complet
        test_full_game_processing()
        
        logger.info("\n✅ Tests terminés")
    except Exception as e:
        logger.error(f"\n❌ Erreur générale lors des tests: {e}")