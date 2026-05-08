# Somfy Venetian Blinds for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![Version](https://img.shields.io/github/v/release/anakinch75/somfy-venetian-ha)](https://github.com/anakinch75/somfy-venetian-ha/releases)
[![Tests](https://github.com/anakinch75/somfy-venetian-ha/actions/workflows/tests.yml/badge.svg)](https://github.com/anakinch75/somfy-venetian-ha/actions/workflows/tests.yml)

Intégration Home Assistant pour les stores à lamelles Somfy via TaHoma Switch, avec contrôle complet de l'inclinaison des lamelles — fonctionnalité absente de l'intégration Overkiz officielle.

## Pourquoi cette intégration ?

L'intégration officielle **Overkiz** de Home Assistant ne supporte pas le widget `DynamicExteriorVenetianBlind` et n'expose pas l'état `core:SlateOrientationState`. Cette intégration comble ce manque pour les stores à lamelles io-homecontrol Somfy.

## Fonctionnalités

- Contrôle de la position (montée/descente)
- Contrôle de l'inclinaison des lamelles (`tilt_position`)
- Commande combinée position + inclinaison (`setClosureAndOrientation`)
- Bouton Stop
- Position mémorisée (My)
- Polling automatique toutes les 30 secondes

## Appareils supportés

- Widget `DynamicExteriorVenetianBlind` / UI Class `ExteriorVenetianBlind`
- Via TaHoma Switch (io-homecontrol)
- Testé en Suisse avec compte Somfy Europe

## Prérequis

- Home Assistant 2023.1+
- HACS installé
- Compte Somfy (mysciosomfy.com)
- TaHoma Switch connecté et appairé

## Installation via HACS

1. Dans HACS → **Intégrations** → menu ⋮ → **Dépôts personnalisés**
2. URL : `https://github.com/anakinch75/somfy-venetian-ha`
3. Catégorie : **Intégration**
4. Cliquez **Ajouter**
5. Recherchez "Somfy Venetian" et installez
6. Redémarrez Home Assistant

## Configuration

1. **Paramètres** → **Appareils et services** → **Ajouter une intégration**
2. Recherchez **Somfy Venetian Blinds**
3. Entrez votre email et mot de passe du compte Somfy
4. Sélectionnez votre région (Europe par défaut)

## Entités créées

Une entité `cover` par store détecté, nommée d'après le label dans l'app TaHoma.

| Attribut | Description | Valeurs |
|----------|-------------|---------|
| `current_cover_position` | Position du store | 0 = fermé, 100 = ouvert |
| `current_cover_tilt_position` | Inclinaison des lamelles | 0 = vertical (fermé), 100 = horizontal (ouvert) |
| `is_closed` | Store fermé ? | booléen |

## Mapping d'inclinaison

L'API Somfy utilise `core:SlateOrientationState` avec des valeurs 0–100 :

| Somfy | HA `tilt_position` | Position physique |
|-------|--------------------|-------------------|
| 0 | 100 | Lamelles horizontales (max lumière) |
| 50 | 50 | Lamelles à 45° |
| 100 | 0 | Lamelles verticales (occultant) |

## Services disponibles

| Service | Description |
|---------|-------------|
| `cover.open_cover` | Monte le store complètement |
| `cover.close_cover` | Descend le store complètement |
| `cover.stop_cover` | Arrête le mouvement |
| `cover.set_cover_position` | Position précise (0–100) |
| `cover.set_cover_tilt_position` | Inclinaison précise (0–100) |

## Exemples d'automatisation

```yaml
# Lamelles à 45° le matin
automation:
  - alias: "Stores matin"
    trigger:
      platform: time
      at: "07:30:00"
    action:
      - service: cover.set_cover_tilt_position
        target:
          entity_id: cover.salon
        data:
          tilt_position: 50

# Fermeture complète le soir
  - alias: "Stores soir"
    trigger:
      platform: sun
      event: sunset
    action:
      - service: cover.close_cover
        target:
          area_id: salon
```

## Changelog

### v1.0.8
- Ajout de 29 tests unitaires (mappings, pending state, commandes combinées)
- GitHub Actions : tests lancés automatiquement à chaque push
- Badge de statut des tests dans le README

### v1.0.7
- Correction fuite de session réseau au redémarrage/reconnexion
- Annulation propre de la boucle événementielle au déchargement de l'intégration
- Verrou contre la double-connexion simultanée
- `open`/`close` affichent maintenant la position cible pendant le mouvement
- `stop` vide immédiatement le pending pour afficher la vraie position
- `is_opening`/`is_closing` correctement implémentés (animation HA correcte)

### v1.0.6
- Correction définitive de l'effet de recalage en fin de mouvement : le slider affiche la valeur cible pendant tout le déplacement, et bascule sur la valeur réelle uniquement une fois le store arrêté

### v1.0.5
- Correction commandes combinées position+inclinaison : les valeurs en attente sont mémorisées pour éviter les conflits entre commandes rapprochées

### v1.0.4
- Refactoring majeur : remplacement du polling par une boucle événementielle (`fetch_events()` toutes les 2s)
- Les états se mettent à jour en temps réel pendant le mouvement des stores
- Suppression de tout état optimiste — le code est maintenant propre et simple

### v1.0.3
- Correction affichage pendant le mouvement : l'état optimiste est conservé tant que le store bouge
- Suppression du refresh immédiat pendant les commandes de mouvement

### v1.0.2
- Correction mise à jour des états : `get_devices(refresh=True)` pour forcer le rechargement
- Ajout des mises à jour optimistes : HA reflète immédiatement la commande sans attendre le poll
- Meilleure gestion des erreurs de commande avec logs détaillés

### v1.0.1
- Correction du mapping d'inclinaison : l'API Somfy attend 0–100 (et non -90 à 0)

### v1.0.0
- Version initiale : position + inclinaison des lamelles
