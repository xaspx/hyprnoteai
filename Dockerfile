# https://pnpm.io/docker#example-3-build-on-cicd
FROM node:20-slim AS web-base
ENV PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"
RUN npm install -g corepack@latest
RUN corepack enable

FROM web-base AS web-builder
ARG VITE_CLERK_PUBLISHABLE_KEY
ARG VITE_SENTRY_DSN
COPY . /app
WORKDIR /app
RUN --mount=type=cache,id=pnpm,target=/pnpm/store pnpm install --frozen-lockfile
RUN pnpm -F ui build
RUN VITE_CLERK_PUBLISHABLE_KEY=$VITE_CLERK_PUBLISHABLE_KEY VITE_SENTRY_DSN=$VITE_SENTRY_DSN pnpm --filter @hypr/app build

FROM rust:1.86.0 AS rust-builder
WORKDIR /app

RUN apt-get update && apt-get install -y \
    pkg-config \
    cmake \
    build-essential \
    protobuf-compiler \
    libasound2-dev

COPY . .
RUN cargo build --release --package app

FROM debian:bookworm-slim AS runtime
RUN apt-get update && apt-get install -y ca-certificates libasound2 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY --from=web-builder /app/apps/app/dist ./static
COPY --from=rust-builder /app/target/release/app ./app
ENV APP_STATIC_DIR="./static"
ENTRYPOINT ["./app"]
