import pino from "pino";

export const logger = pino({
  name: "statement-service",
  level: process.env.LOG_LEVEL ?? "info",
});
