# ---- Build stage: instala dependencias con devDependencies si las hubiera ----
FROM node:20-alpine AS deps
WORKDIR /app
COPY backend/package.json backend/package-lock.json* ./
RUN npm install --omit=dev --no-audit --no-fund

# ---- Runtime stage: imagen final mínima ----
FROM node:20-alpine AS runtime

# Buenas prácticas de seguridad para la imagen:
# - usuario no-root dedicado
# - solo lo necesario copiado (sin .git, sin node_modules de dev, sin .env)
# - tini como init para manejar señales correctamente (kill -TERM, etc.)
RUN apk add --no-cache tini \
  && addgroup -S appgroup \
  && adduser -S appuser -G appgroup

WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY backend/package.json ./
COPY backend/src ./src
COPY frontend ./frontend

# Nunca copiar .env al build; los secretos entran solo en runtime vía --env-file o -e.
# (Ver .dockerignore para lo que queda explícitamente excluido.)

ENV NODE_ENV=production \
    PORT=3000

EXPOSE 3000

USER appuser

# Healthcheck para que Docker/orquestador detecte caídas.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD node -e "require('http').get('http://127.0.0.1:3000/health', r => process.exit(r.statusCode===200?0:1)).on('error', () => process.exit(1))"

ENTRYPOINT ["/sbin/tini", "--"]
CMD ["node", "src/server.js"]
