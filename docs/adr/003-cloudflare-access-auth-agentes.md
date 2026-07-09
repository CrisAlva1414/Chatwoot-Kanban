# ADR-003 — Cloudflare Access como capa de autenticación de agentes

| Campo | Valor |
|---|---|
| **Estado** | Aceptado |
| **Fecha** | 2026-07-09 |
| **Proyecto** | kanban.ruki-bot.com |
| **Decidido por** | Sesión de factibilidad técnica inicial |

---

## Contexto

La aplicación (`kanban.ruki-bot.com`) debe ser accesible públicamente a nivel de red (expuesta via Cloudflare Proxy/Tunnel igual que el resto de servicios de ruki-bot.com), pero no debe permitir acceso a ningún agente no autorizado. El equipo es pequeño (menos de 10 personas) y todos tienen correo `@i-labs.cl` (Hostinger, no Google Workspace ni Microsoft 365).

Se evaluaron tres opciones:

1. **Login propio** (tabla de `agentes` con `password_hash`, sesión propia): funcional, pero requiere construir y mantener flujo de auth, recuperación de contraseñas, y gestión de sesiones.
2. **OAuth con Google** (gratuito): descartado porque no hay Google Workspace corporativo. Usarlo con Gmail personal mezcla identidad personal con la empresa y pierde control de revocación centralizado.
3. **Cloudflare Access con OTP por email**: el proveedor de auth se pone delante de la aplicación a nivel de DNS. Cloudflare envía un OTP al correo `@i-labs.cl` del agente; si es válido, emite un JWT firmado que llega al backend via header `Cf-Access-Jwt-Assertion`.

## Decisión

Usar **Cloudflare Access** con política de acceso restringida al dominio `@i-labs.cl`, autenticación por One-Time PIN enviado al correo corporativo (compatible con Hostinger, no requiere Workspace).

## Fundamento técnico

- Cloudflare Access pasa al backend el JWT del agente autenticado via header `Cf-Access-Jwt-Assertion` (firmado con las claves públicas de Cloudflare, verificables en `https://{team}.cloudflareaccess.com/cdn-cgi/access/certs`).
- El header `Cf-Access-Authenticated-User-Email` provee el email del agente sin necesidad de decodificar el JWT manualmente en cada endpoint.
- Ambos headers son verificables criptográficamente — a diferencia del `postMessage` del Dashboard App, esto sí puede usarse como credencial real.
- Revocar acceso = eliminar al agente de la política en el panel de Cloudflare. No requiere tocar código ni base de datos.

## Consecuencias

- El backend debe validar el JWT de Cloudflare en cada request antes de procesar nada. Las claves públicas se cachean localmente y se rotan según el endpoint de JWKS de Cloudflare.
- La tabla `agentes` en la BD propia **no necesita `password_hash` ni manejo de sesión**. Solo mantiene el mapeo `email → nombre + chatwoot_agent_id` para enriquecer el audit log con nombres legibles.
- Cloudflare Access no resuelve roles dentro de la app. Para el MVP (modelo de pool rotativo donde cualquier agente tiene los mismos permisos), esto no es limitante. Si en el futuro se requieren roles diferenciados, se implementa en la capa de aplicación propia.
- Variables de entorno requeridas: `CF_ACCESS_TEAM_DOMAIN`, `CF_ACCESS_AUD` (audience tag del Access Application).

## Tabla de agentes resultante (mínima)

```sql
CREATE TABLE agentes (
  id                SERIAL PRIMARY KEY,
  email             TEXT NOT NULL UNIQUE,   -- fuente: header Cloudflare Access
  nombre            TEXT NOT NULL,
  chatwoot_agent_id INTEGER,                -- vínculo opcional al id de agente en Chatwoot
  activo            BOOLEAN NOT NULL DEFAULT true
);
```

## Alternativas descartadas

- **Login propio con password:** descartado por overhead de mantenimiento desproporcionado para un equipo de menos de 10 personas sin SSO corporativo.
- **OAuth Google con cuentas personales:** descartado por mezclar identidad personal/corporativa y perder revocación centralizada.
- **Sin auth (confiar en la oscuridad de la URL):** descartado. La URL pública sin protección expone datos reales de leads a cualquiera que la conozca.
