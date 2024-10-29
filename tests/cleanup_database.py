# tests/cleanup_database.py
import logging
from tilttracker.utils.database import Database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def cleanup_database():
    db = Database()
    try:
        with db.connection.cursor() as cursor:
            # Supprimer dans l'ordre à cause des contraintes de clé étrangère
            logger.info("Suppression des données des tables...")
            
            cursor.execute("DELETE FROM player_matches")
            cursor.execute("DELETE FROM matches")
            logger.info("Tables matches et player_matches vidées")
            
            # Optionnel : supprimer aussi les joueurs
            # cursor.execute("DELETE FROM players")
            # logger.info("Table players vidée")
            
        db.connection.commit()
        logger.info("Nettoyage terminé avec succès")
        
    except Exception as e:
        logger.error(f"Erreur lors du nettoyage: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    cleanup_database()