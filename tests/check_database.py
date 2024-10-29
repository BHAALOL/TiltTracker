# tests/check_database.py
import logging
from tilttracker.utils.database import Database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_database():
    db = Database()
    try:
        with db.connection.cursor() as cursor:
            # Vérifier la table players
            cursor.execute("SELECT * FROM players")
            players = cursor.fetchall()
            logger.info(f"Nombre de joueurs dans la base: {len(players)}")
            for player in players:
                logger.info(f"Joueur: {player}")

            # Vérifier la table matches
            cursor.execute("SELECT COUNT(*) FROM matches")
            matches_count = cursor.fetchone()[0]
            logger.info(f"Nombre de parties dans la base: {matches_count}")

            # Vérifier la table player_matches
            cursor.execute("""
                SELECT m.match_id, p.summoner_name, pm.kills, pm.deaths, pm.assists
                FROM player_matches pm
                JOIN players p ON p.id = pm.player_id
                JOIN matches m ON m.id = pm.match_id
                ORDER BY m.created_at DESC
                LIMIT 5
            """)
            recent_matches = cursor.fetchall()
            logger.info("5 dernières performances:")
            for match in recent_matches:
                logger.info(f"Match {match[0]} - {match[1]}: {match[2]}/{match[3]}/{match[4]}")

    except Exception as e:
        logger.error(f"Erreur lors de la vérification de la base de données: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_database()