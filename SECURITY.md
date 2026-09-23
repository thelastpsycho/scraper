# Security and deployment

## Immediately rotate exposed credentials

Previous public frontend commits contained a DeepSeek API key and a D-EDGE
password. This PR removes the current frontend copies, **not their Git
history**. Revoke and replace the DeepSeek key, change the affected D-EDGE
password, and invalidate old sessions where supported. Review recent activity,
previous deployments, and logs. Do not commit the replacements.

## Operator authentication

Copy `backend/.env.example` to `backend/.env`, then generate two independent,
random 32+-character strings:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Set `APP_ACCESS_TOKEN` for operator login and a *different*
`APP_SESSION_SECRET` for Flask session signing. Optional
`PMS_USERNAME`, `PMS_PASSWORD`, `DEDGE_USERNAME`, and `DEDGE_PASSWORD`
can also reside on the backend. Never use frontend `VITE_*` variables for
provider credentials: Vite embeds them into browser JavaScript.

Backend API operations are locked if authentication is unconfigured. The
browser uses an HttpOnly, SameSite=Strict session cookie plus an in-memory
CSRF header for writes. Log in on the frontend before using the console.
When serving over HTTPS, set `APP_SECURE_COOKIES=1`.

Flask now binds to `127.0.0.1` by default with its debugger disabled.
For other devices, use an HTTPS reverse proxy, firewall/network controls,
and login. Do not enable the interactive debugger on external interfaces.
Protect the single-operator login against brute-force attempts with network
restrictions or reverse-proxy rate limiting; use organization SSO for
multi-user deployments. A deliberate `ALLOW_INSECURE_LOCAL_DEV=1` mode is
available for loopback-only development. Never enable it behind a publicly
reachable reverse proxy.

## BAR checkpoint recovery

Successful D-EDGE chunks are atomically checkpointed under the ignored
runtime data directory. A retry of an *identical plan* resumes successfully
confirmed chunks. If the allocation plan or selected rooms change, the
system refuses to reuse an unfinished checkpoint. After checking the
D-EDGE extranet, select **Start a fresh BAR batch** on the pipeline page
(or supply `resetCheckpoint: true` to the direct BAR endpoint).

There is one unavoidable uncertainty: if D-EDGE commits a change but its
success response is lost before the checkpoint is recorded, the operator
must check the extranet manually before retrying. These checks and unit tests
do not validate live PMS/D-EDGE browser behavior.
