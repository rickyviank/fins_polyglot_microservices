FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json tsconfig.json ./
COPY src ./src
COPY templates ./templates
RUN npm install --no-audit --no-fund && npm run build

FROM node:20-alpine
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/templates ./templates
COPY package.json ./
ENV NODE_ENV=production
EXPOSE 8087
CMD ["node", "dist/index.js"]
