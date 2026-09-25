import fs from "node:fs";
import path from "node:path";

const publicDir = fs.existsSync(path.resolve(".output", "public"))
  ? path.resolve(".output", "public")
  : path.resolve("Frontend", ".output", "public");
const assetsDir = path.join(publicDir, "assets");
const indexPath = path.join(publicDir, "index.html");

if (fs.existsSync(publicDir)) {
  const assets = fs.existsSync(assetsDir) ? fs.readdirSync(assetsDir) : [];
  const css = assets.find((f) => f.endsWith(".css"));
  const js = assets.find((f) => f.startsWith("index") && f.endsWith(".js"));

  const html = `<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Korda — Personal Kanban</title>
    <meta name="description" content="A focused personal Kanban board for organizing tasks from idea to done." />
    ${css ? `<link rel="stylesheet" href="/assets/${css}" />` : ""}
    <link rel="icon" href="/favicon.ico" type="image/x-icon" />
  </head>
  <body>
    <div id="root"></div>
    <script>
      window.$_TSR = window.$_TSR || {
        buffer: [],
        router: { matches: [] },
        h: () => {}
      };
    </script>
    ${js ? `<script type="module" src="/assets/${js}"></script>` : ""}
  </body>
</html>
`;

  fs.writeFileSync(indexPath, html, "utf-8");
  console.log(`Generated static entry: ${indexPath}`);
}
