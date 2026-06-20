const fetch = require('node-fetch');

const BASE_URL = (process.env.CHATWOOT_BASE_URL || '').replace(/\/+$/, '');
const ACCOUNT_ID = process.env.CHATWOOT_ACCOUNT_ID;
const API_TOKEN = process.env.CHATWOOT_API_TOKEN;
const ETAPA_ATTRIBUTE_KEY = process.env.CHATWOOT_ETAPA_ATTRIBUTE_KEY || 'etapa_del_embudo';

function assertConfigured() {
  if (!BASE_URL || !ACCOUNT_ID || !API_TOKEN) {
    throw new Error(
      'Faltan variables de entorno: CHATWOOT_BASE_URL, CHATWOOT_ACCOUNT_ID o CHATWOOT_API_TOKEN'
    );
  }
}

async function chatwootRequest(path, options = {}) {
  assertConfigured();
  const url = `${BASE_URL}/api/v1/accounts/${ACCOUNT_ID}${path}`;

  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      api_access_token: API_TOKEN,
      ...(options.headers || {}),
    },
  });

  if (!response.ok) {
    const body = await response.text().catch(() => '');
    throw new Error(`Chatwoot API ${response.status}: ${body}`);
  }

  // Algunas respuestas (ej. PATCH de custom attributes) vienen vacías.
  const text = await response.text();
  return text ? JSON.parse(text) : null;
}

/**
 * Trae las conversaciones abiertas/pendientes con su custom_attribute "Etapa".
 * Chatwoot pagina de a 25; para un pipeline manejable iteramos hasta unas pocas páginas.
 */
async function listConversationsForPipeline({ maxPages = 8 } = {}) {
  const all = [];
  for (let page = 1; page <= maxPages; page += 1) {
    const data = await chatwootRequest(`/conversations?status=all&page=${page}`);
    const items = data?.data?.payload || data?.payload || [];
    if (items.length === 0) break;
    all.push(...items);
    if (items.length < 25) break; // última página
  }

  return all.map((conversation) => ({
    id: conversation.id,
    contactName: conversation.meta?.sender?.name || 'Sin nombre',
    contactEmail: conversation.meta?.sender?.email || null,
    inboxId: conversation.inbox_id,
    etapa: conversation.custom_attributes?.[ETAPA_ATTRIBUTE_KEY] || 'Prospección',
    labels: conversation.labels || [],
    updatedAt: conversation.timestamp || conversation.last_activity_at || null,
    chatwootUrl: `${BASE_URL}/app/accounts/${ACCOUNT_ID}/conversations/${conversation.id}`,
  }));
}

/**
 * Actualiza la etapa (custom attribute a nivel conversación) de una conversación.
 */
async function updateConversationEtapa(conversationId, nuevaEtapa) {
  return chatwootRequest(`/conversations/${conversationId}/custom_attributes`, {
    method: 'POST',
    body: JSON.stringify({
      custom_attributes: {
        [ETAPA_ATTRIBUTE_KEY]: nuevaEtapa,
      },
    }),
  });
}

module.exports = {
  listConversationsForPipeline,
  updateConversationEtapa,
};
