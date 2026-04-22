## What's new

### Optional JavaScript runtime support

Youtube-dl GUI now supports JavaScript runtimes for sites that require yt-dlp's EJS solver (used for certain obfuscated video sources).

The app automatically detects a suitable runtime on your system, checking in this order: **Deno → Bun → Node.js → QuickJS**. If none are found, it falls back to a bundled QuickJS binary included with the app.

The installer includes an optional **Install QuickJS JavaScript runtime** component. It is skipped automatically if a compatible runtime is already on your PATH — you only get the bundled binary if you actually need it.

No configuration is required. Runtime detection happens at download time.  
> **But it is recommended to manually redownload the installer or install your own JS runtime**
