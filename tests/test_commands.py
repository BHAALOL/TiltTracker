# tests/test_commands.py
import logging
from tilttracker.utils.database import Database
from tilttracker.modules.discord_publisher import DiscordPublisher
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CommandTester:
    def __init__(self):
        self.db = Database()
        self.discord_publisher = DiscordPublisher()
        self.test_summoner = "GuigZer"
        self.test_tag = "1101"

    async def test_stats_command(self):
        """Test de la commande /stats"""
        logger.info("=== Test de la commande /stats ===")
        try:
            # Test stats globales
            stats = await self.db.get_player_stats(self.test_summoner, self.test_tag)
            if stats:
                logger.info("✅ Stats globales récupérées:")
                logger.info(f"Total parties: {stats['total_games']}")
                logger.info(f"Victoires/Défaites: {stats['wins']}/{stats['losses']}")
                logger.info(f"Winrate: {stats['winrate']:.1f}%")
                logger.info(f"KDA: {stats['avg_kills']:.1f}/{stats['avg_deaths']:.1f}/{stats['avg_assists']:.1f}")
                
                # Vérification des champions
                if 'top_champions' in stats:
                    logger.info("✅ Champions les plus joués récupérés")
                    for champ in stats['top_champions']:
                        logger.info(f"- {champ['champion_name']}: {champ['games']} parties")
            else:
                logger.error("❌ Échec de la récupération des stats")
            
            return bool(stats)
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du test de /stats: {e}")
            return False

    async def test_leaderboard_command(self):
        """Test de la commande /leaderboard"""
        logger.info("\n=== Test de la commande /leaderboard ===")
        try:
            leaderboard = await self.db.get_leaderboard(limit=10)
            if leaderboard:
                logger.info("✅ Leaderboard récupéré:")
                for i, player in enumerate(leaderboard, 1):
                    logger.info(
                        f"{i}. {player['summoner_name']}#{player['tag_line']} - "
                        f"Score: {player['total_score']} - "
                        f"WR: {player['winrate']:.1f}%"
                    )
            else:
                logger.error("❌ Échec de la récupération du leaderboard")
            
            return bool(leaderboard)
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du test de /leaderboard: {e}")
            return False

    async def test_lastgame_command(self):
        """Test de la commande /lastgame"""
        logger.info("\n=== Test de la commande /lastgame ===")
        try:
            last_game = await self.db.get_last_game(self.test_summoner, self.test_tag)
            if last_game:
                logger.info("✅ Dernière partie récupérée:")
                logger.info(f"Champion: {last_game['player_stats']['champion_name']}")
                logger.info(f"KDA: {last_game['player_stats']['kills']}/"
                          f"{last_game['player_stats']['deaths']}/"
                          f"{last_game['player_stats']['assists']}")
                logger.info(f"Résultat: {'Victoire' if last_game['player_stats']['win'] else 'Défaite'}")
                logger.info(f"Score: {last_game['score_info']['final_score']}")
            else:
                logger.error("❌ Échec de la récupération de la dernière partie")
            
            return bool(last_game)
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du test de /lastgame: {e}")
            return False

    async def test_database_integrity(self):
        """Vérification de l'intégrité de la base de données"""
        logger.info("\n=== Vérification de l'intégrité des données ===")
        try:
            with self.db.connection.cursor() as cursor:
                # Vérifier la table players
                cursor.execute("SELECT COUNT(*) FROM players")
                players_count = cursor.fetchone()[0]
                logger.info(f"Nombre de joueurs enregistrés: {players_count}")

                # Vérifier la table matches
                cursor.execute("SELECT COUNT(*) FROM matches")
                matches_count = cursor.fetchone()[0]
                logger.info(f"Nombre de parties enregistrées: {matches_count}")

                # Vérifier la table player_matches
                cursor.execute("SELECT COUNT(*) FROM player_matches")
                performances_count = cursor.fetchone()[0]
                logger.info(f"Nombre de performances enregistrées: {performances_count}")

                # Vérifier les scores
                cursor.execute("SELECT COUNT(*) FROM player_matches WHERE score IS NOT NULL")
                scores_count = cursor.fetchone()[0]
                logger.info(f"Nombre de parties avec score: {scores_count}")

                return True

        except Exception as e:
            logger.error(f"❌ Erreur lors de la vérification de la base de données: {e}")
            return False

    async def run_all_tests(self):
        """Exécute tous les tests"""
        try:
            logger.info("🏁 Début des tests des commandes")
            
            # Test de la base de données
            db_ok = await self.test_database_integrity()
            
            # Test des commandes
            stats_ok = await self.test_stats_command()
            leaderboard_ok = await self.test_leaderboard_command()
            lastgame_ok = await self.test_lastgame_command()
            
            # Résumé
            logger.info("\n=== Résumé des tests ===")
            logger.info(f"Base de données: {'✅' if db_ok else '❌'}")
            logger.info(f"Commande /stats: {'✅' if stats_ok else '❌'}")
            logger.info(f"Commande /leaderboard: {'✅' if leaderboard_ok else '❌'}")
            logger.info(f"Commande /lastgame: {'✅' if lastgame_ok else '❌'}")
            
            all_ok = db_ok and stats_ok and leaderboard_ok and lastgame_ok
            logger.info(f"\nRésultat final: {'✅ Tous les tests ont réussi' if all_ok else '❌ Certains tests ont échoué'}")
            
            return all_ok
            
        except Exception as e:
            logger.error(f"❌ Erreur lors des tests: {e}")
            return False
        finally:
            self.db.close()

if __name__ == "__main__":
    import asyncio
    
    tester = CommandTester()
    result = asyncio.run(tester.run_all_tests())
    
    if not result:
        logger.error("Des erreurs sont survenues pendant les tests")
        exit(1)