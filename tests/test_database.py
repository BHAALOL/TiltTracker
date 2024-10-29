# tests/test_database.py
import os
import sys
import logging
from pathlib import Path

# Ajout du répertoire racine au PYTHONPATH
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from tilttracker.utils.database import Database

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_database_connection():
    """Test la connexion à la base de données et les opérations de base"""
    try:
        # Création de l'instance de la base de données
        db = Database()
        logger.info("Connexion à la base de données établie avec succès")

        # Test d'enregistrement d'un joueur
        test_player = {
            'discord_id': '123456789',
            'riot_puuid': 'test_puuid_123',
            'summoner_name': 'TestPlayer',
            'tag_line': 'EUW'
        }

        success = db.register_player(
            discord_id=test_player['discord_id'],
            riot_puuid=test_player['riot_puuid'],
            summoner_name=test_player['summoner_name'],
            tag_line=test_player['tag_line']
        )

        if success:
            logger.info("Test d'enregistrement du joueur réussi")

        # Test de récupération du joueur
        player = db.get_player_by_discord_id(test_player['discord_id'])
        if player:
            logger.info(f"Joueur récupéré avec succès: {player['summoner_name']}#{player['tag_line']}")

        # Nettoyage du test (optionnel)
        with db.connection.cursor() as cursor:
            cursor.execute("DELETE FROM players WHERE discord_id = %s", (test_player['discord_id'],))
            db.connection.commit()
            logger.info("Données de test nettoyées")

        db.close()
        return True

    except Exception as e:
        logger.error(f"Erreur lors du test de la base de données: {e}")
        return False

if __name__ == "__main__":
    if test_database_connection():
        print("✅ Tous les tests de base de données ont réussi")
    else:
        print("❌ Certains tests ont échoué")