---
name: "tailscale-links"
description: "Use whenever you are about to give the user a link to something running on this computer (a dev server, preview, review page, dashboard, local report). Never send localhost, 127.0.0.1 or a LAN IP; publish it with tailscale serve, open the Tailscale link yourself to check it works, then send it."
---

# Tailscale Links

The user works across several computers and a phone. `localhost` only means something on this machine, so a link that uses it is useless to them. Every link to something running here is a Tailscale link, and you have opened it before they do.

## Steps

1. **Get this machine's name.**
   ```bash
   tailscale status --json | python3 -c "import sys,json; print(json.load(sys.stdin)['Self']['DNSName'].rstrip('.'))"
   ```
   Not `Running`, or no `tailscale` binary: stop and say so. Do not fall back to localhost.

2. **Publish it.** Use the same port outside as inside, so two previews never collide. Run it with a short timeout (20 s): without Serve enabled the command waits forever.
   ```bash
   tailscale serve --bg --https=<port> http://127.0.0.1:<port>
   ```
   - `Serve is not enabled on your tailnet` plus a `login.tailscale.com` link: stop. Enabling it is a tailnet admin setting and the user's to change. Give them that link, and kill any `tailscale serve` process you left waiting.
   - HTTPS port refused: use 8443 or 10000, or 443 if free.
   - Target is HTTPS with a self-signed cert: `https+insecure://127.0.0.1:<port>`.
   - Check `tailscale serve status` first; do not overwrite a mapping you did not make.

3. **Open it yourself.** The link is `https://<DNSName>:<port>/<path>`.
   - `curl -sS -m 15 -o /dev/null -w "%{http_code}" <link>` must print 200 (or the page's normal redirect). Then confirm the body is the thing you meant to publish, not an error page.
   - For anything visual, also load it in the browser tool and look.
   - 403 or "blocked host" from a dev server (Vite `allowedHosts`, webpack `allowedHosts`, Next `allowedDevOrigins`): add the DNSName to the server's allow list. That is a small config change; say you made it.
   - It must work through the Tailscale hostname, not only on localhost. If it does not, say what you saw. Do not send a link you have not opened.

4. **Send it.** Only the Tailscale link, as a clickable URL. One line on what it is. Do not mention the localhost address.

## Rules

- `tailscale serve` is tailnet-only. Never use `tailscale funnel`: it puts the page on the public internet.
- Links in files you write (reports, READMEs, review pages) get the same treatment when they are meant for the user to click.
- When you stop the underlying server, remove the mapping: `tailscale serve --https=<port> off`.
- A preview that exits when your command ends needs to be started in the background first. Publish only once it answers on 127.0.0.1.
- Say what you did not verify: for example, "opened from this Mac only, not from your phone".
