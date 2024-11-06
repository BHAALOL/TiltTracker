from tilttracker.utils.database import Database

def clear_matches():
    db = Database()
    try:
        with db.connection.cursor() as cursor:
            # Supprimer d'abord les performances des joueurs
            cursor.execute("DELETE FROM player_matches;")
            
            # Ensuite supprimer les matches
            cursor.execute("DELETE FROM matches;")
            
            # Valider les changements
            db.connection.commit()
            print("Matches supprimés avec succès!")
            
    except Exception as e:
        print(f"Erreur lors de la suppression: {e}")
        db.connection.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    clear_matches()