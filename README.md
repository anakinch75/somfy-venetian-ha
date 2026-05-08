# Somfy Venetian Blinds for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

Intégration Home Assistant pour les stores à lamelles Somfy via TaHoma Switch, avec contrôle complet de l'inclinaison des lamelles.

## Fonctionnalités

- Contrôle de la position (montée/descente)
- Contrôle de l'inclinaison des lamelles (`tilt_position`)
- Commande combinée position + inclinaison
- Bouton Stop
- Position mémorisée (My)
- Polling automatique toutes les 30 secondes

## Appareils supportés

- `ExteriorVenetianBlind` via TaHoma Switch
- Testé avec stores io-homecontrol Somfy en Suisse

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

## Entités créées

Pour chaque store détecté, une entité `cover` est créée avec :

| Attribut | Description |
|----------|-------------|
| `current_cover_position` | Position (0=fermé, 100=ouvert) |
| `current_cover_tilt_position` | Inclinaison lamelles (0=fermé, 100=horizontal) |

## Services disponibles

- `cover.set_cover_position` — position seule
- `cover.set_cover_tilt_position` — inclinaison seule
- `cover.open_cover` / `cover.close_cover` / `cover.stop_cover`

## Exemple d'automatisation

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
```
