# LEGAL ARCHITECTURE (Borrador)

## 1) Propósito
Esta arquitectura separa los regímenes legales por tipo de artefacto para mantener el proyecto abierto, reutilizable y gobernable como experimento sin fines de lucro.

## 2) Modelo por capas
- Capa A — Código Open Core: `Apache-2.0` (o `MIT` para módulos específicos).
- Capa B — Datos, contenido y materiales educativos: por defecto `CC BY-NC 4.0`, salvo indicación contraria.
- Capa C — Activos de marca (nombres, logos, identidad visual): cubiertos por la política de marca.
- Capa D — Servicios alojados y operaciones: regidos por Terms/Privacy/Security.

## 3) Reglas por defecto
- SPDX por defecto para código del repositorio: `Apache-2.0`.
- Ejemplos y documentación: `CC BY 4.0`, salvo marcado explícito `CC BY-NC 4.0`.
- Las licencias de terceros se conservan y se atribuyen en `NOTICE` y manifiestos.

## 4) Controles
- No subir secretos a repositorios públicos.
- No relicenciar código de terceros sin derechos.
- Todo artefacto distribuible debe declarar SPDX.
- CI debe fallar si fallan los chequeos de licencia.

## 5) Vínculo con gobernanza
Cambios legales requieren:
- RFC,
- revisión de maintainers,
- aprobación de stewards,
- registro en changelog legal.

## 6) Aviso
Documento de borrador del proyecto; requiere revisión legal profesional antes de adopción formal.
