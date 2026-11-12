import { serveStatic } from "srvx/static";

const publicFile = serveStatic({ dir: "public" });
export const env = {
  ASSETS: { fetch: request => publicFile(request, () => new Response(null, { status: 404 })) },
};
