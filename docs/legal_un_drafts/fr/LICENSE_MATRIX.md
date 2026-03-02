# LICENSE MATRIX (Brouillon)

## 1) Mapping artefact → licence
- Code source principal : `Apache-2.0`.
- Certains modules utilitaires : `MIT` (uniquement si explicitement marqué).
- Documentation : `CC BY 4.0` (ou `CC BY-NC 4.0` pour contenu restreint).
- Jeux de données / contenu de recherche : licence indiquée par fiche de dataset.
- Marques/logos/noms : politique de marque, pas licence open source.

## 2) Licences tierces autorisées (allowlist)
- `MIT`, `Apache-2.0`, `BSD-2-Clause`, `BSD-3-Clause`, `ISC`, `MPL-2.0`.

## 3) Restreintes / revue obligatoire
- `GPL-*`, `AGPL-*`, `LGPL-*`, `SSPL-*`, licences non commerciales ou personnalisées.
- Dépendances sans identifiant SPDX clair.

## 4) Contrôles de conformité
- Scan SPDX automatique en CI.
- Mise à jour obligatoire de `NOTICE` et des attributions pour release.
- Échec politique => blocage merge/release.

## 5) Exceptions
Les exceptions nécessitent une approbation écrite maintainer + steward et une trace de décision.
