import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import DictCursor

class DBManager:
    def __init__(self):
        # Chargement des variables d'environnement
        load_dotenv()
        
        # Connexion à la base de données
        self.connection = psycopg2.connect(
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT")
        )

    def show_last_matches(self, limit=5):
        """Affiche les derniers matches avec leurs informations"""
        with self.connection.cursor(cursor_factory=DictCursor) as cursor:
            cursor.execute("""
                SELECT 
                    m.id,
                    m.match_id,
                    p.summoner_name,
                    p.tag_line,
                    pm.champion_name,
                    pm.kills,
                    pm.deaths,
                    pm.assists,
                    pm.win,
                    pm.score
                FROM matches m
                JOIN player_matches pm ON m.id = pm.match_id
                JOIN players p ON p.id = pm.player_id
                ORDER BY m.created_at DESC
                LIMIT %s
            """, (limit,))
            
            matches = cursor.fetchall()
            
            print("\n=== Derniers matches ===")
            for match in matches:
                print(f"\nID: {match['id']} | Match Riot: {match['match_id']}")
                print(f"Joueur: {match['summoner_name']}#{match['tag_line']}")
                print(f"Champion: {match['champion_name']}")
                print(f"KDA: {match['kills']}/{match['deaths']}/{match['assists']}")
                print(f"Résultat: {'Victoire' if match['win'] else 'Défaite'}")
                print(f"Score: {match['score']}")
                print("-" * 50)

    def delete_match(self, match_id: int):
        """Supprime un match spécifique par son ID en base de données"""
        try:
            with self.connection.cursor() as cursor:
                # Supprime d'abord les performances des joueurs
                cursor.execute("DELETE FROM player_matches WHERE match_id = %s", (match_id,))
                # Puis supprime le match
                cursor.execute("DELETE FROM matches WHERE id = %s", (match_id,))
                
            self.connection.commit()
            print(f"\n✅ Match ID {match_id} supprimé avec succès")
            
        except Exception as e:
            self.connection.rollback()
            print(f"\n❌ Erreur lors de la suppression du match {match_id}: {e}")

    def show_menu(self):
        """Affiche le menu principal"""
        while True:
            print("\n=== Menu de gestion de la base de données ===")
            print("1. Voir les derniers matches")
            print("2. Supprimer un match par ID")
            print("3. Quitter")
            
            choice = input("\nChoix (1-3): ")
            
            if choice == "1":
                limit = input("Nombre de matches à afficher (défaut: 5): ")
                limit = int(limit) if limit.isdigit() else 5
                self.show_last_matches(limit)
            
            elif choice == "2":
                match_id = input("ID du match à supprimer: ")
                if match_id.isdigit():
                    confirmation = input(f"Êtes-vous sûr de vouloir supprimer le match {match_id} ? (o/n): ")
                    if confirmation.lower() == 'o':
                        self.delete_match(int(match_id))
                else:
                    print("ID invalide")
            
            elif choice == "3":
                print("\nAu revoir!")
                break
            
            else:
                print("\nChoix invalide")

    def close(self):
        """Ferme la connexion à la base de données"""
        if self.connection:
            self.connection.close()
            print("\nConnexion à la base de données fermée")

if __name__ == "__main__":
    try:
        db_manager = DBManager()
        db_manager.show_menu()
    except Exception as e:
        print(f"\nErreur : {e}")
    finally:
        db_manager.close()