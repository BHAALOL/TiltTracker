# tilttracker/modules/discord_publisher.py
import logging
import discord
from discord.webhook import SyncWebhook
from discord import Embed, Colour
import os
from typing import Dict
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class DiscordPublisher:
    def __init__(self):
        load_dotenv()
        self.webhook_url = os.getenv('DISCORD_WEBHOOK_URL')
        if not self.webhook_url:
            raise ValueError("DISCORD_WEBHOOK_URL non trouvée dans les variables d'environnement")
        
        self.webhook = SyncWebhook.from_url(self.webhook_url)
        logger.info("Discord Publisher initialisé avec succès")

    def create_match_embed(self, player_stats: Dict, match_stats: Dict, score_info: Dict) -> Embed:
        """Crée un embed Discord pour une partie."""
        # Déterminer la couleur selon la victoire/défaite
        color = Colour.green() if player_stats['win'] else Colour.red()
        
        # Créer l'embed
        embed = Embed(
            title=f"{player_stats['summoner_name']}#{player_stats['tag_line']} - {player_stats['champion_name']} {'✅' if player_stats['win'] else '❌'}",
            color=color
        )

        # Ajouter l'image du champion
        champion_image_url = f"https://ddragon.leagueoflegends.com/cdn/14.21.1/img/champion/{player_stats['champion_name']}.png"
        embed.set_thumbnail(url=champion_image_url)

        # Stats KDA
        kda = f"{player_stats['kills']}/{player_stats['deaths']}/{player_stats['assists']}"
        kda_ratio = (player_stats['kills'] + player_stats['assists']) / max(1, player_stats['deaths'])
        embed.add_field(
            name="KDA",
            value=f"{kda} ({kda_ratio:.2f})",
            inline=True
        )

        # Dégâts
        dmg_formatted = "{:,}".format(player_stats['total_damage_dealt_to_champions']).replace(',', ' ')
        embed.add_field(
            name="Dégâts aux champions",
            value=dmg_formatted,
            inline=True
        )

        # Dégâts subis
        tank_dmg = "{:,}".format(player_stats['total_damage_taken']).replace(',', ' ')
        embed.add_field(
            name="Dégâts subis",
            value=tank_dmg,
            inline=True
        )

        # Score et Points
        points = score_info['final_score']
        points_str = f"+{points}" if points > 0 else str(points)
        embed.add_field(
            name="Score de performance",
            value=f"{score_info['base_score']:.1f}%",
            inline=True)

        # Nouveau champ pour les points totaux
        # Formatage du changement de points
        change_str = f"(+{score_info['score_change']})" if score_info['score_change'] > 0 else f"({score_info['score_change']})"
        embed.add_field(
            name="Points",
            value=f"{points_str}\n"
                f"Total: {score_info['total_score']} {change_str}",
            inline=True)


        # Footer avec la durée de la partie
        match_duration = match_stats.get('game_duration', 0) // 60
        embed.set_footer(text=f"Durée de la partie: {match_duration} minutes")

        return embed

    def create_performance_message(self, score_info: Dict) -> str:
        """
        Crée un message d'analyse de la performance.
        """
        performance = score_info['base_score']
        if performance >= 90:
            return "🌟 Performance exceptionnelle! Continue comme ça!"
        elif performance >= 75:
            return "💪 Très belle performance!"
        elif performance >= 60:
            return "👍 Bonne performance."
        elif performance >= 45:
            return "😐 Performance moyenne."
        elif performance >= 30:
            return "😕 Performance en dessous de la moyenne."
        else:
            return "😢 Performance difficile. Ne te décourage pas!"

    async def publish_match_result(self, player_stats: Dict, match_stats: Dict, score_info: Dict):
        """Publie les résultats d'une partie sur Discord."""
        try:
            # Debug logs détaillés
            logger.info("=== Début de la publication Discord ===")
            logger.info(f"Publication pour: {player_stats.get('summoner_name')}#{player_stats.get('tag_line')}")
            logger.info(f"Match ID: {match_stats.get('match_id')}")
            logger.info(f"Champion: {player_stats.get('champion_name')}")
            logger.info(f"Score: {score_info.get('final_score')}")
            
            # Vérification des clés requises
            required_keys = ['summoner_name', 'tag_line', 'champion_name', 'kills', 'deaths', 'assists']
            missing_keys = [key for key in required_keys if key not in player_stats]
            if missing_keys:
                logger.error(f"Clés manquantes dans player_stats: {missing_keys}")
                logger.error(f"Données player_stats complètes: {player_stats}")
                raise ValueError(f"Données joueur incomplètes. Clés manquantes: {missing_keys}")
                
            # Créer l'embed
            embed = self.create_match_embed(player_stats, match_stats, score_info)
            
            # Tentative d'envoi
            logger.info("Tentative d'envoi au webhook Discord...")
            self.webhook.send(
                embed=embed,
                username="TiltTracker",
                avatar_url="https://ddragon.leagueoflegends.com/cdn/14.21.1/img/profileicon/4408.png"
            )
            
            logger.info(f"Résultats publiés avec succès pour {player_stats['champion_name']}")
            logger.info("=== Fin de la publication Discord ===")
            
        except Exception as e:
            logger.error(f"Erreur lors de la publication sur Discord: {e}")
            logger.error(f"Données player_stats: {player_stats}")
            logger.error(f"Données match_stats: {match_stats}")
            logger.error(f"Données score_info: {score_info}")
            raise

    def publish_match_result_sync(self, player_stats: Dict, match_stats: Dict, score_info: Dict):
        """
        Version synchrone de la publication (pour les tests).
        """
        try:
            import requests
            
            # Créer l'embed
            embed = self.create_match_embed(player_stats, match_stats, score_info)
            message = self.create_performance_message(score_info)
            
            # Convertir l'embed en format webhook Discord
            webhook_data = {
                "content": message,
                "embeds": [embed.to_dict()],
                "username": "TiltTracker"
            }
            
            # Envoyer à Discord
            response = requests.post(self.webhook_url, json=webhook_data)
            response.raise_for_status()
            
            logger.info(f"Résultats publiés avec succès pour {player_stats['champion_name']}")
            
        except Exception as e:
            logger.error(f"Erreur lors de la publication sur Discord: {e}")
            raise