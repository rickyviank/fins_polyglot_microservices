import pino from "pino";

export const logger = pino({
  name: "customer-profile-service",
  level: process.env.LOG_LEVEL ?? "info",
});
