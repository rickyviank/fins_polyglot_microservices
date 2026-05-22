import { buildServer } from "./server";
import { logger } from "./logger";

const port = Number(process.env.PORT ?? 8000);

const app = buildServer();

app.listen(port, () => {
  logger.info({ port }, "api-gateway listening");
});
