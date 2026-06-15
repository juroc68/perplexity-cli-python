# Perplexity CLI Python

Client Python en ligne de commande pour interroger l'API Sonar de Perplexity
depuis un terminal. Il prend en charge les requêtes ponctuelles, les
conversations interactives, l'affichage progressif des réponses et les
citations retournées par l'API.

> [!NOTE]
> Ce projet est une intégration indépendante. Il n'est ni maintenu, ni affilié,
> ni officiellement approuvé par Perplexity AI.

## Fonctionnalités

- requête unique depuis la ligne de commande ;
- session interactive avec conservation du contexte ;
- réponses en streaming, désactivables avec `--no-stream` ;
- affichage des sources fournies par l'API ;
- sélection du modèle Sonar ;
- aucune dépendance Python à l'exécution.

## Prérequis

- Python 3.10 ou une version ultérieure ;
- une clé d'API Perplexity.

La clé peut être créée depuis la
[console Perplexity](https://console.perplexity.ai/).

## Installation

Depuis la racine du dépôt :

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e .
```

Vérifiez ensuite que la commande est disponible :

```bash
pplx-python --version
pplx-python --help
```

## Configuration

Définissez la clé d'API dans la variable d'environnement
`PERPLEXITY_API_KEY` :

```bash
export PERPLEXITY_API_KEY="pplx-votre-cle"
```

Le modèle par défaut est `sonar`. La variable `PERPLEXITY_MODEL` permet d'en
choisir un autre sans ajouter l'option `--model` à chaque commande :

```bash
export PERPLEXITY_MODEL="sonar-pro"
```

Ne placez pas de clé réelle dans un fichier suivi par Git.

## Utilisation

### Requête ponctuelle

Passez la question directement en argument :

```bash
pplx-python "Quelles sont les principales nouveautés de Python 3.13 ?"
```

Exemples avec des options supplémentaires :

```bash
pplx-python --model sonar-pro "Compare PostgreSQL et SQLite"
pplx-python --no-stream "Explique le protocole HTTP"
pplx-python --no-citations "Résume les principes de REST"
pplx-python --system "Réponds de manière concise." "Qu'est-ce qu'un CDN ?"
```

### Mode interactif

Lancez la commande sans question pour ouvrir une conversation :

```bash
pplx-python
```

Commandes disponibles pendant la session :

| Commande | Description |
| --- | --- |
| `/help` | Affiche la liste des commandes |
| `/clear` | Efface l'historique de la conversation |
| `/model <nom>` | Change de modèle pour les requêtes suivantes |
| `/exit` ou `/quit` | Ferme la session |

### Modèles pris en charge

- `sonar`
- `sonar-pro`
- `sonar-reasoning-pro`
- `sonar-deep-research`

La disponibilité des modèles dépend de l'accès associé à la clé d'API.

### Options principales

```text
-m, --model MODEL       modèle Sonar à utiliser
-s, --system MESSAGE    instruction système
--no-stream             attend la réponse complète avant de l'afficher
--no-citations          masque la liste des URL sources
--timeout SECONDS       délai maximal de la requête réseau (60 par défaut)
--version               affiche la version du client
```

La commande `pplx-python --help` fournit la liste de référence des options.

## Sécurité

Le client :

- transmet la clé d'API dans l'en-tête HTTP `Authorization` ;
- refuse les endpoints qui n'utilisent pas HTTPS ;
- limite chaque réponse à 10 Mio ;
- supprime les séquences de contrôle avant l'affichage dans le terminal ;
- applique un délai maximal configurable aux appels réseau.

Une question passée comme argument peut être enregistrée dans l'historique du
shell. Utilisez le mode interactif lorsque le contenu de la question ne doit
pas y apparaître.

## Développement

Le projet utilise uniquement la bibliothèque standard de Python à l'exécution.
Les tests unitaires simulent les réponses HTTP et n'effectuent aucun appel à
l'API Perplexity.

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q src tests
```

## Licence

Ce projet est distribué sous licence MIT.

Perplexity et Sonar sont des marques ou noms de produits appartenant à leurs
propriétaires respectifs.
