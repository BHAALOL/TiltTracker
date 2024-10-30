import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
import logging
from .riot_api import RiotAPI

# Configuration du logger
logger = logging.getLogger(__name__)

class TiltTrackerBot(commands.Bot):
    def __init__(self, riot_api_key: str):
        logger.info("Initialisation du bot TiltTracker...")
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        
        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None
        )
        
        self.riot_api = RiotAPI(riot_api_key)
        self.startup_time = datetime.now()
        logger.info("Bot initialisé avec succès")

    async def setup_hook(self):
        """Appelé avant que le bot ne démarre, configure les commandes"""
        logger.info("Synchronisation des commandes...")
        await self.add_cog(CommandsCog(self))
        await self.tree.sync()
        logger.info("Commandes synchronisées avec succès")

    async def on_ready(self):
        """Événement déclenché quand le bot est prêt"""
        logger.info(f"Bot connecté en tant que {self.user.name}")
        logger.info(f"ID du bot: {self.user.id}")
        logger.info(f"Temps de démarrage: {datetime.now() - self.startup_time}")
        logger.info(f"Latence avec Discord: {round(self.latency * 1000)}ms")
       
        for guild in self.guilds:
            logger.info(f"Connecté au serveur: {guild.name} (ID: {guild.id})")
            logger.info(f"Nombre de membres sur {guild.name}: {guild.member_count}")
        
        try:
            synced = await self.tree.sync()
            logger.info(f'Commandes slash synchronisées : {len(synced)} commandes')
        except Exception as e:
            logger.error(f'Erreur lors de la synchronisation : {e}')

        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="League of Legends players tilt"
            )
        )
        logger.info("Statut du bot mis à jour")

class CommandsCog(commands.Cog):
    def __init__(self, bot: TiltTrackerBot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command(self, ctx):
        """Log chaque commande reçue"""
        logger.info(f"Commande reçue - Type: {ctx.command.name} | "
                   f"Auteur: {ctx.author} (ID: {ctx.author.id}) | "
                   f"Serveur: {ctx.guild.name} (ID: {ctx.guild.id}) | "
                   f"Canal: {ctx.channel.name}")

    @commands.Cog.listener()
    async def on_command_completion(self, ctx):
        """Log la completion d'une commande"""
        logger.info(f"Commande terminée avec succès - Type: {ctx.command.name} | "
                   f"Auteur: {ctx.author}")

    @commands.hybrid_command(
        name="ping",
        description="Vérifie la latence du bot"
    )
    async def ping(self, ctx: commands.Context):
        """Ping le bot pour vérifier sa latence"""
        start_time = datetime.now()
        latency = round(self.bot.latency * 1000)
        
        logger.info(f"Commande ping reçue de {ctx.author}")
        message = await ctx.send(f"🏓 Pong! Latence: **{latency}ms**")
        
        end_time = datetime.now()
        response_time = (end_time - start_time).total_seconds() * 1000
        
        logger.info(f"Ping exécuté | Latence: {latency}ms | "
                   f"Temps de réponse: {round(response_time)}ms")

    @commands.hybrid_command(
        name="register",
        description="Enregistre un compte League of Legends"
    )
    @app_commands.describe(
        game_name="Ton nom de jeu LoL",
        tag_line="Ton tag (ex: EUW, NA1, etc.)"
    )
    async def register(self, ctx: commands.Context, game_name: str,tag_line: str):
        start_time = datetime.now()
        logger.info(f"Commande register reçue | "
                   f"Auteur: {ctx.author} | "
                   f"Compte: {game_name}#{tag_line}")
        
        await ctx.defer()
        logger.info(f"Début de la recherche pour {game_name}#{tag_line}")

        try:
            puuid = await self.bot.riot_api.get_puuid(game_name, tag_line)
            if not puuid:
                logger.warning(f"Compte non trouvé: {game_name}#{tag_line}")
                error_embed = discord.Embed(
                    title="❌ Erreur",
                    description=f"Le compte '{game_name}#{tag_line}' n'existe pas.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=error_embed)
                return

            logger.info(f"PUUID trouvé pour {game_name}#{tag_line}")
            account_info = await self.bot.riot_api.get_account_info(puuid)
            
            if not account_info:
                logger.error(f"Échec de récupération des infos pour {game_name}#{tag_line}")
                error_embed = discord.Embed(
                    title="❌ Erreur",
                    description="Erreur lors de la récupération des informations du compte.",
                    color=discord.Color.red()
                )
                await ctx.send(embed=error_embed)
                return

            logger.info(f"Informations récupérées pour {game_name}#{tag_line}")
            
            # Création de l'embed avec les informations du compte
            embed = discord.Embed(
                title="✅ Compte trouvé !",
                description=f"Confirmation des informations pour {game_name}#{tag_line}",
                color=discord.Color.green()
            )
            
            # Ajoute les détails du compte
            embed.add_field(
                name="Niveau d'invocateur", 
                value=str(account_info['summonerLevel']),
                inline=True
            )
            
            # Ajoute les informations de rang si disponibles
            if 'solo_duo' in account_info['ranks']:
                rank_info = account_info['ranks']['solo_duo']
                embed.add_field(
                    name="Rang Solo/Duo",
                    value=f"{rank_info['tier']} {rank_info['rank']} ({rank_info['lp']} LP)",
                    inline=True
                )
                embed.add_field(
                    name="Ratio V/D",
                    value=f"{rank_info['wins']}W/{rank_info['losses']}L",
                    inline=True
                )
            else:
                embed.add_field(
                    name="Rang Solo/Duo",
                    value="Non classé",
                    inline=True
                )
            
            # Ajoute l'icône du compte
            icon_id = account_info['profileIconId']
            embed.set_thumbnail(url=f"http://ddragon.leagueoflegends.com/cdn/13.24.1/img/profileicon/{icon_id}.png")
            
            # Ajoute le footer avec l'auteur de la commande
            embed.set_footer(
                text=f"Demandé par {ctx.author.name}", 
                icon_url=ctx.author.avatar.url if ctx.author.avatar else None
            )
            
            # Envoie l'embed
            await ctx.send(embed=embed)
            logger.info(f"Embed envoyé avec succès pour {game_name}#{tag_line}")
            
            end_time = datetime.now()
            process_time = (end_time - start_time).total_seconds()
            logger.info(f"Commande register terminée | "
                       f"Compte: {game_name}#{tag_line} | "
                       f"Temps total: {process_time:.2f}s")

        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement de {game_name}#{tag_line}: {str(e)}")
            error_embed = discord.Embed(
                title="❌ Erreur",
                description="Une erreur est survenue lors de l'enregistrement. Réessayez plus tard.",
                color=discord.Color.red()
            )
            await ctx.send(embed=error_embed)

    @commands.hybrid_command(
        name="stats",
        description="Affiche les statistiques ARAM d'un joueur"
    )
    @app_commands.describe(
        summoner_name="Nom d'invocateur (optionnel)"
    )
    async def stats(self, ctx: commands.Context, summoner_name: str = None):
        """Affiche les statistiques globales d'un joueur"""
        try:
            await ctx.defer()
            start_time = datetime.now()
            
            # Si aucun nom n'est fourni, utiliser l'ID Discord de l'auteur
            if not summoner_name:
                player = await self.bot.database.get_player_by_discord_id(str(ctx.author.id))
                if not player:
                    await ctx.send("❌ Vous n'êtes pas enregistré. Utilisez `/register` d'abord.")
                    return
                summoner_name = player['summoner_name']
                tag_line = player['tag_line']
                
            # Récupérer les stats depuis la base de données
            stats = await self.get_player_stats(summoner_name, tag_line)
            
            if not stats:
                await ctx.send("❌ Aucune statistique trouvée pour ce joueur.")
                return
                
            # Créer l'embed
            embed = discord.Embed(
                title=f"Statistiques ARAM de {summoner_name}#{tag_line}",
                color=discord.Color.blue()
            )
            
            # Stats générales
            embed.add_field(
                name="📊 Général",
                value=f"Parties jouées: {stats['total_games']}\n"
                      f"Victoires: {stats['wins']}\n"
                      f"Défaites: {stats['losses']}\n"
                      f"Winrate: {stats['winrate']:.1f}%",
                inline=True
            )
            
            # KDA moyen
            embed.add_field(
                name="⚔️ KDA Moyen",
                value=f"Kills: {stats['avg_kills']:.1f}\n"
                      f"Deaths: {stats['avg_deaths']:.1f}\n"
                      f"Assists: {stats['avg_assists']:.1f}\n"
                      f"Ratio: {stats['kda_ratio']:.2f}",
                inline=True
            )
            
            # Champions les plus joués
            if stats['top_champions']:
                champs_str = "\n".join([
                    f"{i+1}. {champ['champion_name']} ({champ['games']} parties, {champ['winrate']:.1f}% WR)"
                    for i, champ in enumerate(stats['top_champions'][:3])
                ])
                embed.add_field(
                    name="🏆 Champions favoris",
                    value=champs_str,
                    inline=False
                )
            
            # Performance
            embed.add_field(
                name="🎯 Performance",
                value=f"Score total: {stats['total_score']}\n"
                      f"Score moyen: {stats['avg_score']:.1f}\n"
                      f"Meilleur score: {stats['best_score']}\n"
                      f"Classement: #{stats['rank']}",
                inline=False
            )
            
            # Footer
            process_time = (datetime.now() - start_time).total_seconds()
            embed.set_footer(text=f"Généré en {process_time:.2f} secondes")
            
            await ctx.send(embed=embed)
            logger.info(f"Stats affichées pour {summoner_name}#{tag_line}")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'affichage des stats: {e}")
            await ctx.send("❌ Une erreur s'est produite lors de la récupération des statistiques.")

    @commands.hybrid_command(
        name="leaderboard",
        description="Affiche le classement ARAM"
    )
    async def leaderboard(self, ctx: commands.Context):
        """Affiche le classement des joueurs"""
        try:
            await ctx.defer()
            start_time = datetime.now()
            
            # Récupérer le top 10
            top_players = await self.get_leaderboard()
            
            if not top_players:
                await ctx.send("❌ Aucun classement disponible pour le moment.")
                return
                
            embed = discord.Embed(
                title="🏆 Classement ARAM",
                description="Top 10 des joueurs",
                color=discord.Color.gold()
            )
            
            for i, player in enumerate(top_players, 1):
                # Emoji pour les trois premiers
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                
                embed.add_field(
                    name=f"{medal} {player['summoner_name']}#{player['tag_line']}",
                    value=f"Score: {player['total_score']:,}\n"
                          f"WR: {player['winrate']:.1f}% ({player['wins']}/{player['total_games']})\n"
                          f"Score moyen: {player['avg_score']:.1f}",
                    inline=False
                )
            
            # Footer
            process_time = (datetime.now() - start_time).total_seconds()
            embed.set_footer(text=f"Généré en {process_time:.2f} secondes")
            
            await ctx.send(embed=embed)
            logger.info("Leaderboard affiché avec succès")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'affichage du leaderboard: {e}")
            await ctx.send("❌ Une erreur s'est produite lors de la récupération du classement.")

    @commands.hybrid_command(
        name="lastgame",
        description="Affiche les détails de la dernière partie ARAM"
    )
    @app_commands.describe(
        summoner_name="Nom d'invocateur (optionnel)"
    )
    async def lastgame(self, ctx: commands.Context, summoner_name: str = None):
        """Affiche les détails de la dernière partie d'un joueur"""
        try:
            await ctx.defer()
            
            # Si aucun nom n'est fourni, utiliser l'ID Discord de l'auteur
            if not summoner_name:
                player = await self.bot.database.get_player_by_discord_id(str(ctx.author.id))
                if not player:
                    await ctx.send("❌ Vous n'êtes pas enregistré. Utilisez `/register` d'abord.")
                    return
                summoner_name = player['summoner_name']
                tag_line = player['tag_line']
                
            # Récupérer la dernière partie
            last_game = await self.get_last_game(summoner_name, tag_line)
            
            if not last_game:
                await ctx.send("❌ Aucune partie récente trouvée.")
                return
                
            embed = self.create_game_embed(last_game)
            await ctx.send(embed=embed)
            logger.info(f"Dernière partie affichée pour {summoner_name}#{tag_line}")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'affichage de la dernière partie: {e}")
            await ctx.send("❌ Une erreur s'est produite lors de la récupération de la dernière partie.")

