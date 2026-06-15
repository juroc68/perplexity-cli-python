# Perplexity CLI Python

Client terminal Python pour l'API Sonar de Perplexity. Il propose une question
ponctuelle ou une conversation interactive avec streaming et citations.

Cette version est un client conversationnel. Elle ne lit pas et ne modifie pas
les fichiers du poste comme un agent de développement.

## Pourquoi cette architecture ?

La bibliothèque standard Python suffit pour envoyer une requête HTTPS et lire
le flux SSE de Perplexity. L'absence de dépendance réduit la surface d'attaque
et simplifie l'audit du projet.

Mesures de sécurité incluses :

- endpoint HTTPS obligatoire ;
- délai réseau configurable ;
- réponse limitée à 10 Mio ;
- suppression des séquences de contrôle avant affichage dans le terminal ;
- clé API lue uniquement depuis `PERPLEXITY_API_KEY` ;
- modèle économique `sonar` utilisé par défaut.

## Installation

Un environnement virtuel isole les dépendances de ce projet du reste de la
machine.

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e .
```

Vérification :

```bash
pplx-python --version
pplx-python --help
```

## Configuration

Créez une clé dans le [portail API](https://console.perplexity.ai/) puis
définissez-la uniquement pour le terminal courant :

```bash
export PERPLEXITY_API_KEY="pplx-votre-cle"
```

Piège fréquent : l'abonnement Web ou Enterprise ne rend pas nécessairement les
appels API gratuits. Désactivez le rechargement automatique des crédits pour
éviter une facturation inattendue.

## Utilisation

```bash
pplx-python
pplx-python "Explique le fonctionnement des modèles de langage"
pplx-python --model sonar-pro "Compare Python et JavaScript"
```

Dans le mode interactif :

```text
/help
/clear
/model sonar-pro
/exit
```

Pour une question confidentielle, privilégiez le mode interactif. Une question
passée directement dans la commande peut rester dans l'historique du shell.

## Vérifications

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q src tests
```

Les tests n'effectuent aucun appel réseau et ne consomment aucun crédit API.
