import { serveStatic } from "srvx/static";

const publicFile = serveStatic({ dir: "public" });
export const env = {
  ASSETS: {
    async fetch(request) {
      const path = new URL(request.url).pathname;
      if (process.env.ARCHIVE_RELEASE && (path === "/__data/cms-snapshot.txt" || /^\/jee-(?:advanced-)?archive\/.+\.bin$/.test(path))) {
        const { archiveResponse } = await import("./archive-db.mjs");
        return archiveResponse(path);
      }
      return publicFile(request, () => new Response(null, { status: 404 }));
    },
  },
};
