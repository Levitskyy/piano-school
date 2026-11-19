FROM node:22-alpine AS base

RUN npm install -g pnpm@9.2.0

WORKDIR /repo

FROM base AS deps

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml ./
COPY apps/web/package.json apps/web/package.json

RUN pnpm install --frozen-lockfile --filter web...

FROM deps AS build

COPY apps/web apps/web
RUN pnpm --filter web build

FROM base AS runner

ENV NODE_ENV=production

COPY --from=build /repo /repo

EXPOSE 3000

CMD ["pnpm", "--filter", "web", "start"]
