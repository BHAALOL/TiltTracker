Voici les besoin de base du Projet.

Je souhaite que se système de ranking en ARAM Uniquement soit opérable depuis discord via des webhook et/ou un bot. 
Les utilisateurs pourront s'inscrire avec une commande puis afficher le classement et quelques autre options que l'ont verra plus tard
Quand un joueur finira ça game elle sera traité par le système de notation, puis les resultats seront envoyer sur discord dans un channel spécifique.
Pour faire ça on utilisera python (Pour l'instant je ne veux pas de code je veux juste une explication de comment tu compte faire).
Il va falloir stocker l'historique des parties dans une base de donnée celle ci pourra etre déployé via docker si besoin.
Je veux pas que se soit qu'un seul fichier qui gère tout je veux un script python pour chaque étape : 
- Inscription des joueurs via le bot discord (Avec une vérification si le nom du joueur existe bien)
- Récupération de la partie via les API RiotGame puis insertion dans la base de donnée
- Traitement de la partie affectation la note pour le joueurs et ajout de cette note dans la BDD
- Publication des résultat sur discord.
tout ces script seront appeller sur un fichier principal "main.py"
pour éviter de mettre des donnée confidentielle en dur dans le script il faudra utiliser un fichier .env (Clé API, connexion a la BDD,API discord etc...)
Evidement je veux que les scripts soit assez verbeux pour trouvé des problème facilement si il y en a.
Fait moi un petit récap et dit moi comment je dois m'y prendre dans quel ordre ? détaille bien tes explications.

Voici l'architecture du projet : 
.
├── docker-compose.yml
├── docs
│   ├── assets
│   ├── CONFIGURATION.md
│   ├── CONTRIBUTING.md
│   └── USAGE.md
├── LICENSE
├── logs
│   ├── 2024-10-29-__main__.log
│   ├── 2024-10-29-tilttracker.modules.discord_bot.log
│   └── 2024-10-29-tilttracker.utils.database.log
├── main.py
├── README.md
├── requirements.txt
├── setup.py
├── tests
│   ├── __init__.py
│   ├── integration
│   │   └── __init__.py
│   └── unit
│       └── __init__.py
└── tilttracker
    ├── __init__.py
    ├── modules
    │   ├── discord_bot.py
    │   ├── discord_publisher.py
    │   ├── game_processor.py
    │   ├── __init__.py
    │   ├── __pycache__
    │   │   ├── discord_bot.cpython-311.pyc
    │   │   ├── __init__.cpython-311.pyc
    │   │   └── riot_api.cpython-311.pyc
    │   └── riot_api.py
    ├── __pycache__
    │   └── __init__.cpython-311.pyc
    └── utils
        ├── database.py
        ├── __init__.py
        ├── logger.py
        └── __pycache__

Voici l'explication de l'archi : 

TiltTracker/
├── main.py                     # Point d'entrée, initialisation du bot
├── requirements.txt            # Dépendances du projet
├── tilttracker/
│   ├── modules/
│   │   ├── discord_bot.py     # Gestion du bot Discord et commandes
│   │   ├── riot_api.py        # Interface avec l'API Riot Games
│   │   ├── game_processor.py  # Traitement des données de partie
│   │   └── discord_publisher.py# Publication des messages Discord
│   └── utils/
│       ├── database.py        # Gestion de la base de données
│       └── logger.py          # Configuration des logs
└── tests/                     # Tests unitaires et d'intégration

Descriptions courtes:
- main.py: Configure et lance le bot
- discord_bot.py: Commandes et interactions Discord
- riot_api.py: Gestion des appels API Riot
- game_processor.py: Analyse des parties
- discord_publisher.py: Formatage et envoi des messages
- database.py: Interactions BDD
- logger.py: Système de logging

 
Dans la base de donnée il me faudra comme donnée : 

Dégat Total infligé aux championa
Dégat subis
Dégat réduis sur soi 
score de controle de foule
KILL 
DEATH 
ASSIST 
Le champion joué 
Toutes ses donnée seront récupéré via L'API riot game avec le script riot_api.py