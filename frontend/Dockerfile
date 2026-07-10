FROM node:22-slim AS builder
WORKDIR /srv
COPY package.json package-lock.json* ./
RUN npm ci || npm install
COPY . .
RUN npm run build

FROM node:22-slim
WORKDIR /srv
ENV NODE_ENV=production
COPY --from=builder /srv/.next/standalone ./
COPY --from=builder /srv/.next/static ./.next/static
# Required for Next.js standalone: static files in /public are NOT bundled automatically
COPY --from=builder /srv/public ./public
EXPOSE 3000
CMD ["node", "server.js"]
