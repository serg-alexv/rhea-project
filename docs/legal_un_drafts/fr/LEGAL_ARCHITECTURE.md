# LEGAL ARCHITECTURE (Brouillon)

## 1) Objet
Cette architecture sépare les régimes juridiques par type d’artefact afin de garder le projet ouvert, réutilisable et gouvernable en tant qu’expérience à but non lucratif.

## 2) Modèle en couches
- Couche A — Code Open Core : `Apache-2.0` (ou `MIT` pour certains modules).
- Couche B — Données, contenus, supports pédagogiques : `CC BY-NC 4.0` par défaut, sauf mention contraire.
- Couche C — Actifs de marque (noms, logos, identité visuelle) : couverts par la politique de marque.
- Couche D — Services hébergés et opérations : régis par Terms/Privacy/Security.

## 3) Règles par défaut
- SPDX par défaut pour le code : `Apache-2.0`.
- Exemples et documentation : `CC BY 4.0`, sauf marquage explicite `CC BY-NC 4.0`.
- Les licences tierces sont conservées et attribuées dans `NOTICE` et les manifestes.

## 4) Garde-fous
- Aucun secret dans les dépôts publics.
- Aucune relicence de code tiers sans droits.
- Chaque artefact distribuable doit déclarer un identifiant SPDX.
- Le CI doit échouer en cas d’échec des contrôles de licence.

## 5) Lien avec la gouvernance
Les changements juridiques exigent :
- une RFC,
- une revue maintainer,
- une approbation steward,
- une entrée de changelog juridique.

## 6) Avertissement
Document de travail du projet, à valider par un conseiller juridique qualifié avant adoption formelle.
