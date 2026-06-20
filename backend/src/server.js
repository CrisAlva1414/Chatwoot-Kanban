require('dotenv').config();

const express = require('express');
const helmet = require('helmet');
const cors = require('cors');
const rateLimit = require('express-rate-limit');
const path = require('path');

const { requirePluginKey } = require('./auth');
const { listConversationsForPipeline, updateConversationEtapa } = require('./chatwootClient');

const app = express();
const PORT = process.env.PORT || 3000;

// Lista de etapas válidas — mantener sincronizada con el custom attribute en Chatwoot.
const ETAPAS_VALIDAS = [
  'Prospección',
  'Contactado',
  'Cotización enviada',
  'Negociación',
  'Ganado',
  'Perdido',
];

// --- Seguridad de cabeceras ---
app.use(
  helmet({
    contentSecurityPolicy: {
      directives: {
        defaultSrc: ["'self'"],
        // frame-ancestors controla quién puede embeber este sitio en un iframe.
        // Restringir solo al dominio de tu instancia de Chatwoot.
        frameAncestors: [process.env.CHATWOOT_FRAME_ANCESTOR || 'https://app.chatwoot.com'],
        scriptSrc: ["'self'"],
        styleSrc: ["'self'", "'unsafe-inline'"],
        connectSrc: ["'self'"],
        imgSrc: ["'self'", 'data:'],
      },
    },
    // No queremos X-Frame-Options DENY (helmet por defecto es más permisivo si hay CSP,
    // pero lo dejamos explícito vía frameguard desactivado a favor de frame-ancestors).
    frameguard: false,
  })
);

// CORS: solo el propio dominio de Chatwoot puede llamar a la API desde el navegador.
app.use(
  cors({
    origin: process.env.CHATWOOT_FRAME_ANCESTOR || 'https://app.chatwoot.com',
    methods: ['GET', 'POST'],
  })
);

app.use(express.json({ limit: '100kb' }));

// Rate limit general — evita abuso/escaneo del endpoint.
app.use(
  '/api/',
  rateLimit({
    windowMs: 60 * 1000,
    max: 60,
    standardHeaders: true,
    legacyHeaders: false,
  })
);

// --- Healthcheck (sin auth, para Docker/orquestador) ---
app.get('/health', (req, res) => res.json({ status: 'ok' }));

// --- Frontend estático (el HTML del kanban) ---
app.use(express.static(path.join(__dirname, '..', '..', 'frontend')));

// --- API protegida ---
const apiRouter = express.Router();
apiRouter.use(requirePluginKey);

apiRouter.get('/conversations', async (req, res) => {
  try {
    const conversations = await listConversationsForPipeline();
    res.json({ etapas: ETAPAS_VALIDAS, conversations });
  } catch (err) {
    console.error('[kanban] Error listando conversaciones:', err.message);
    res.status(502).json({ error: 'No se pudo obtener datos de Chatwoot' });
  }
});

apiRouter.post('/conversations/:id/etapa', async (req, res) => {
  const { id } = req.params;
  const { etapa } = req.body || {};

  if (!ETAPAS_VALIDAS.includes(etapa)) {
    return res.status(400).json({ error: `Etapa inválida. Debe ser una de: ${ETAPAS_VALIDAS.join(', ')}` });
  }
  if (!/^\d+$/.test(id)) {
    return res.status(400).json({ error: 'ID de conversación inválido' });
  }

  try {
    await updateConversationEtapa(id, etapa);
    res.json({ ok: true });
  } catch (err) {
    console.error('[kanban] Error actualizando etapa:', err.message);
    res.status(502).json({ error: 'No se pudo actualizar la etapa en Chatwoot' });
  }
});

app.use('/api/kanban', apiRouter);

// --- Manejo de errores genérico (no filtrar detalles internos) ---
app.use((err, req, res, next) => {
  console.error('[kanban] Error no manejado:', err);
  res.status(500).json({ error: 'Error interno' });
});

app.listen(PORT, () => {
  console.log(`Kanban plugin backend escuchando en puerto ${PORT}`);
});
