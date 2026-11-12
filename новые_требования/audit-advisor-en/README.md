# Audit Advisor — English self-hosted edition

7 standards, 325 questions and 650 US/England examples. Package date: 5 November 2026.

## Contents

- frontend/tilda-t123.txt — one T123 block; configure your server address first.
- frontend/tilda-t123.template.html — template containing one __SET_HOSTING_URL__ placeholder.
- server/ — ready-to-upload JavaScript, questionnaire JSON and a standalone check page.
- source/ — complete editable source for this English edition and its build tools.
- server-config/ — Nginx and Apache header examples.
- configure.py — URL setup using standard Python, without Node.js or additional Python packages.

The application runs in the visitor’s browser. The server serves static files. No database, PHP application, Node.js service or Firebase SDK is required at runtime. Answers stay in the visitor’s browser. Node.js is only needed to rebuild the source.

## Installation

1. Upload the **contents of server/** to a dedicated public HTTPS directory. Keep the rest of the package outside the public document root.
2. Configure CORS and cache headers using server-config/. Serve .js with a JavaScript MIME type and .json as application/json. Missing JSON must return 404 rather than an HTML fallback.
3. From the extracted package root, substitute the real public directory URL and run:

```sh
python3 configure.py https://YOUR_DOMAIN/PUBLIC_DIRECTORY/
```

Use the directory containing audit-advisor.js, not an index.html file URL. The URL must include the actual directory path and end with a slash.

4. Copy all of frontend/tilda-t123.txt into one T123 block on your English Tilda page, set its language to English and publish.
5. Open the published page, select one standard and check that its first question loads.

Without Python, replace the single __SET_HOSTING_URL__ in frontend/tilda-t123.txt manually with the same HTTPS directory URL. Until configured, the block explicitly asks for the hosting address.

server/index.html locates its assets relative to itself and can be checked immediately after upload. It retains noindex because the primary installation is the Tilda block. The Russian and English packages can use separate directories on the same server. Point each T123 at its own directory; do not put two application blocks on one page.

## Editing and rebuilding

Edit source/content/interface.en.json and source/content/standards/*.json. The named fields heading, description, examples and condition identify the question text. Answer labels are in answerPresets; per-question labels are in answers.overrides. Find a question by standard ID plus question ID. Preserve IDs, answer values, answerVersion, weights, sections and applicability for wording-only edits; update contentRevision instead. Keep the original US and England examples and jurisdiction distinctions.

```sh
cd source
npm install
npm run check:content
npm run build
```

The build updates ../server/ and ../frontend/ using ../hosting.json. Upload the updated server files after content edits. Replace T123 too after changes to the static introduction, styling or loader. On Apache use server/.htaccess where supported; server-config/nginx-headers.conf is a snippet for the existing Nginx configuration. Your server’s HTTPS and document-root settings remain in its existing configuration.

Documents use Available / Not available; working practices use Yes / Partly / No. Not sure remains a saved follow-up answer: the affected stage and overall score are withheld until it is resolved. Not applicable and No events remain conditional. This package preserves the approved assessment; no new criteria were introduced.

Questionnaire basis, terms, regional notes and source links remain in JSON. PACKAGE.json identifies this build and the JavaScript hash. Your own server address is intentionally unset; configure it before embedding the block.
