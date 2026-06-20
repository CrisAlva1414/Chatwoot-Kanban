const crypto = require('crypto');

/**
 * Autenticación del plugin.
 *
 * El secreto (PLUGIN_SECRET) NUNCA llega al navegador.
 * El frontend manda un header "x-plugin-key" que debe coincidir
 * con el secreto configurado en el servidor.
 *
 * Esto es intencionalmente simple (capa 1). Si más adelante se quiere
 * algo más robusto (expiración, multi-usuario, revocación), se puede
 * subir a JWT firmado por sesión sin tocar el resto del backend.
 */
function requirePluginKey(req, res, next) {
  const providedKey = req.headers['x-plugin-key'];
  const expectedKey = process.env.PLUGIN_SECRET;

  if (!expectedKey) {
    // Fail closed: si el servidor no tiene secreto configurado, no se sirve nada.
    return res.status(500).json({ error: 'PLUGIN_SECRET no configurado en el servidor' });
  }

  if (!providedKey) {
    return res.status(401).json({ error: 'Falta el header x-plugin-key' });
  }

  // Comparación en tiempo constante para evitar timing attacks.
  const a = Buffer.from(String(providedKey));
  const b = Buffer.from(String(expectedKey));
  const isValid = a.length === b.length && crypto.timingSafeEqual(a, b);

  if (!isValid) {
    return res.status(403).json({ error: 'x-plugin-key inválida' });
  }

  next();
}

module.exports = { requirePluginKey };
