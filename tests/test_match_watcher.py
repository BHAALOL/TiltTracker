# tests/test_match_watcher.py
import logging
from tilttracker.modules.match_watcher import MatchWatcher

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_watcher():
    """Test le watcher avec un court intervalle"""
    try:
        # Créer le watcher avec un court intervalle pour le test
        watcher = MatchWatcher(check_interval=60)  # 60 secondes
        
        logger.info("Test du watcher pendant 2 minutes...")
        
        # Démarrer le watcher
        watcher.start()
        
        return True
    except Exception as e:
        logger.error(f"Erreur lors du test: {e}")
        return False

if __name__ == "__main__":
    logger.info("🏁 Début du test du Match Watcher")
    test_watcher()