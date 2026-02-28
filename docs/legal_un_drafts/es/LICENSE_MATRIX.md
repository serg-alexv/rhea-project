# LICENSE MATRIX (Borrador)

## 1) Mapeo artefacto-licencia
- Código fuente central: `Apache-2.0`.
- Módulos utilitarios seleccionados: `MIT` (solo si está marcado).
- Documentación: `CC BY 4.0` (o `CC BY-NC 4.0` para material restringido).
- Datasets/contenido de investigación: licencia declarada en cada ficha.
- Marca/logos/nombres: política de marca, no licencia open source.

## 2) Licencias de terceros permitidas (allowlist)
- `MIT`, `Apache-2.0`, `BSD-2-Clause`, `BSD-3-Clause`, `ISC`, `MPL-2.0`.

## 3) Restringidas / revisión obligatoria
- `GPL-*`, `AGPL-*`, `LGPL-*`, `SSPL-*`, licencias no comerciales o personalizadas.
- Dependencias sin SPDX claro.

## 4) Controles de cumplimiento
- Escaneo SPDX automático en CI.
- Actualización obligatoria de `NOTICE` y atribuciones en release.
- Si falla la política, se bloquea merge/release.

## 5) Excepciones
Excepciones requieren aprobación escrita de maintainer + steward y registro de decisión.
