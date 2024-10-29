# tests/test_riot_api.py
import os
import sys
import logging
from pathlib import Path
from tilttracker.modules.riot_api import RiotAPI

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_riot_api():
    try:
        # Initialisation de l'API
        api = RiotAPI()
        logger.info("API Riot initialisée avec succès")

        # Test avec un compte spécifique (à modifier avec un compte valide)
        summoner_name = "GuigZer"  # À remplacer par un vrai nom d'invocateur
        tag_line = "1101"

        # Test 1: Vérification de l'existence du compte
        logger.info(f"Test 1: Vérification du compte {summoner_name}#{tag_line}")
        if api.is_valid_summoner(summoner_name, tag_line):
            logger.info("✅ Compte trouvé")
            
            # Test 2: Récupération du PUUID
            puuid = api.get_puuid(summoner_name, tag_line)
            logger.info(f"✅ PUUID récupéré: {puuid}")
            
            # Test 3: Récupération des parties ARAM récentes
            matches = api.get_recent_aram_matches(puuid, count=5)
            logger.info(f"✅ {len(matches)} parties ARAM trouvées")
            
            if matches:
                # Test 4: Récupération des détails d'une partie
                match_details = api.get_match_details(matches[0])
                if match_details:
                    logger.info(f"✅ Détails de la partie récupérés: {match_details}")
                    
                    # Test 5: Récupération des stats du joueur
                    player_stats = api.get_player_match_stats(matches[0], puuid)
                    if player_stats:
                        logger.info(f"✅ Stats du joueur récupérées: {player_stats}")
                    else:
                        logger.error("❌ Échec de la récupération des stats du joueur")
                else:
                    logger.error("❌ Échec de la récupération des détails de la partie")
        else:
            logger.error(f"❌ Compte {summoner_name}#{tag_line} non trouvé")
            
    except Exception as e:
        logger.error(f"❌ Erreur lors des tests: {e}")
        return False

    return True

if __name__ == "__main__":
    if test_riot_api():
        print("\n✅ Tous les tests ont réussi")
    else:
        print("\n❌ Certains tests ont échoué")