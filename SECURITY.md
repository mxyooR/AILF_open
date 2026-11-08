# Security and public data

This is a public engineering prototype. Security checks reduce accidental disclosure; they do not certify the application for production use.

## Credentials

- Run `python scripts/setup_env.py` to generate unique local credentials. Never commit the resulting `.env`.
- The backend requires explicit JWT, developer and database credentials. Debug mode and default account seeding are disabled by default.
- Environment files, private key files, database exports, uploads, model weights and local tooling directories are excluded from Git. Docker also excludes local credentials and weights from build contexts.
- Login responses, tokens and authorization header values must not be written to browser logs.
- Async task results require a per-task `poll_token` sent in `X-Task-Token`. Only its SHA-256 digest is stored, and polling does not extend state expiry. Treat the token as a bearer credential: keep it in memory, use HTTPS outside local development, and exclude this header from proxy or tracing logs. A task credential does not replace authorization for business operations.
- Review screenshots and generated datasets as well as code. Public identifiers use `DEMO-…` or non-routable `000…` fixtures, and example emails use reserved example domains. Replace these with local data when testing real validation rules.
- The public demo starts speech recognition only after an explicit click. Browser speech recognition may send audio to the browser provider; text and preset buttons are available without microphone access. The demo does not download a local speech model or persist transcripts.

## Before publishing

```bash
python scripts/check_public_repo.py
python scripts/check_public_repo.py --staged
```

The staged check reads the actual Git index blobs. The scanner reports locations and rule names, never matched values. It checks common provider keys, signed JWTs, private keys, selected personal identifiers, local paths and private file types. Manual review is still needed for images, unusual credential formats and contextual personal data.

`python scripts/check_public_repo.py --history` scans historical text blobs for credential patterns. Two expired JWTs were found in legacy test scripts in the original history (expiry dates: 2025-07-30 and 2025-08-04). Current scripts read a local `AILF_TEST_ACCESS_TOKEN` instead. The original commits containing those fixtures remain unchanged; the history scan continues to report them.

If a real credential is ever exposed, revoke or rotate it at the provider, then coordinate removal from Git history. Deleting it from the latest version alone does not revoke it.

## Reporting

Use the repository's private vulnerability reporting feature when available. Do not post real credentials, account details, database dumps or unredacted logs in public issues.
