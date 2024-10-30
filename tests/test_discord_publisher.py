# tests/test_discord_publisher.py
import logging
from tilttracker.modules.discord_publisher import DiscordPublisher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_discord_publisher():
    """Test la publication des résultats sur Discord"""
    try:
        publisher = DiscordPublisher()
        
        # Données de test
        player_stats = {
            'summoner_name': 'GuigZer',
            'tag_line': '1101',
            'champion_name': 'Ahri',
            'champion_id': '103',
            'kills': 10,
            'deaths': 5,
            'assists': 15,
            'total_damage_dealt_to_champions': 45000,
            'total_damage_taken': 25000,
            'win': True
        }
        
        match_stats = {
            'game_duration': 1500,  # 25 minutes
            'game_version': '14.21.1',
            'match_id': 'EUW1_1234567'
        }
        
        score_info = {
            'base_score': 85.5,
            'final_score': 25,
            'total_points': 1250
        }
        
        # Publier le message
        logger.info("Test de publication sur Discord...")
        publisher.publish_match_result_sync(player_stats, match_stats, score_info)
        logger.info("✅ Message publié avec succès")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors du test: {e}")
        return False

if __name__ == "__main__":
    if test_discord_publisher():
        print("\n✅ Test réussi")
    else:
        print("\n❌ Test échoué")