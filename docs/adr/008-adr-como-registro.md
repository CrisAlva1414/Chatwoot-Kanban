# ADR-008: ADR como registro de decisiones

- **Fecha:** 2026-07-09
- **Estado:** Aceptado

## Contexto

El proyecto crecerá en sesiones múltiples con semanas de diferencia. Sin un
registro explícito, el LLM pierde contexto y repite discusiones.

## Decisión

Registrar cada decisión técnica como un archivo ADR numerado en `docs/adr/`.
Seguimos el formato de Michael Nygard (contexto → decisión → consecuencias).

## Consecuencias

- Cada sesión debe revisar si hay ADRs nuevos o cambios que registrar.
- Un ADR no se borra; si cambia, se marca como "Suplantado" y se crea uno nuevo.
- Las decisiones pequeñas (librerías, tools) no requieren ADR, basta con la
  sesión. Los ADRs son para decisiones con impacto duradero.
