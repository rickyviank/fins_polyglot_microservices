import { buildServer } from "./server";
import { logger } from "./logger";

const port = Number(process.env.PORT ?? 8085);

const app = buildServer();

app.listen(port, () => {
  logger.info({ port }, "notification-service listening");
});
