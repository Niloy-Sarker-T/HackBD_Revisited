import { createReadStream, existsSync, statSync } from "node:fs";
import { createServer, request as httpRequest } from "node:http";
import { dirname, extname, join, normalize, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = dirname(fileURLToPath(import.meta.url));
const port = Number(process.env.PORT || 5173);
const backendUrl = new URL(process.env.BACKEND_URL || "http://127.0.0.1:8000");

const mimeTypes = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".svg": "image/svg+xml",
};

function safePath(urlPath) {
  const cleanPath = normalize(decodeURIComponent(urlPath.split("?")[0])).replace(/^(\.\.[/\\])+/, "");
  const filePath = resolve(join(root, cleanPath === "/" ? "index.html" : cleanPath));
  return filePath.startsWith(root) ? filePath : join(root, "index.html");
}

function proxyToBackend(request, response) {
  const targetUrl = new URL(request.url || "/", backendUrl);
  const proxyRequest = httpRequest(
    targetUrl,
    {
      method: request.method,
      headers: {
        ...request.headers,
        host: backendUrl.host,
      },
    },
    (proxyResponse) => {
      response.writeHead(proxyResponse.statusCode || 502, proxyResponse.headers);
      proxyResponse.pipe(response);
    },
  );

  proxyRequest.on("error", () => {
    response.writeHead(502, { "Content-Type": "application/json; charset=utf-8" });
    response.end(
      JSON.stringify({
        detail: `FastAPI backend is not reachable at ${backendUrl.origin}`,
      }),
    );
  });

  request.pipe(proxyRequest);
}

createServer((request, response) => {
  const pathname = new URL(request.url || "/", `http://localhost:${port}`).pathname;
  if (pathname.startsWith("/api/") || pathname === "/health") {
    proxyToBackend(request, response);
    return;
  }

  const filePath = safePath(request.url || "/");
  const finalPath = existsSync(filePath) && statSync(filePath).isFile() ? filePath : join(root, "index.html");
  const ext = extname(finalPath);

  response.writeHead(200, {
    "Content-Type": mimeTypes[ext] || "application/octet-stream",
    "Cache-Control": "no-store",
  });
  createReadStream(finalPath).pipe(response);
}).listen(port, () => {
  console.log(`HackBD frontend running at http://localhost:${port}`);
  console.log(`Proxying /api/* and /health to ${backendUrl.origin}`);
});
