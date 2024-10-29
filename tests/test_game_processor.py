# tests/test_game_processor.py
import logging
from tilttracker.modules.game_processor import GameProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_game_processor():
    try:
        processor = GameProcessor()
        
        # Test avec votre compte
        summoner_name = "GuigZer"
        tag_line = "1101"
        # Pas de Discord ID pour le test
        
        logger.info(f"Test du traitement des parties pour {summoner_name}#{tag_line}")
        
        # Création/vérification du joueur
        logger.info("Vérification de l'existence du joueur...")
        player_id = processor.ensure_player_exists(summoner_name, tag_line)
        
        if player_id:
            logger.info(f"✅ Joueur trouvé/créé avec l'ID: {player_id}")
            
            # Traitement des parties
            success = processor.process_recent_matches(summoner_name, tag_line)
            if success:
                logger.info("✅ Traitement des parties réussi")
            else:
                logger.error("❌ Échec du traitement des parties")
        else:
            logger.error("❌ Impossible de créer/trouver le joueur")

        processor.close()
        return player_id is not None

    except Exception as e:
        logger.error(f"❌ Erreur lors du test: {e}")
        return False

if __name__ == "__main__":
    if test_game_processor():
        print("\n✅ Test réussi")
    else:
        print("\n❌ Test échoué")