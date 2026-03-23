# EnvSync

![CI](https://github.com/MahmoudEzzat8824/EnvSync/actions/workflows/test.yml/badge.svg)
![License](https://img.shields.io/github/license/MahmoudEzzat8824/EnvSync)
![Stars](https://img.shields.io/github/stars/MahmoudEzzat8824/EnvSync)

Catch configuration bugs before they reach production.

EnvSync is a lightweight CLI tool that detects configuration drift across environments (dev, staging, production) by comparing:

- `.env` files
- Kubernetes ConfigMaps and Secrets (`.yml` / `.yaml`)
- Source code references to environment variables across your workspace

Prevent issues like:

- "Works on staging but not production"
- Missing environment variables
- Misconfigured secrets
- Silent config drift in Kubernetes

Built for developers, DevOps engineers, and startups shipping fast.

## Real-World Failures EnvSync Prevents

- Missing `DATABASE_URL` in production leading to downtime
- Wrong API endpoint causing broken integrations
- Misconfigured secrets creating security risks
- Drifted Kubernetes configs causing unpredictable behavior

These issues are responsible for a large percentage of production incidents.
EnvSync catches them before they happen.

## Terminal Demo

![alt text](media/image.png)

![alt text](media/image-1.png)

It reports:

- Missing keys
- Extra keys
- Different values
- Consistent values
- Discovered runtime env variable references by language patterns

For secret keys, comparisons are made using SHA256 digests in memory and raw secret values are never printed in the report.

## Requirements

- Python 3.11+

## Quick Start

```bash
pip install envsync
docker pull envsync/cli:latest
```

## Usage

### Terminal Report

```bash
.venv/bin/envsync compare --env examples/dev.env --env examples/staging.env --env examples/prod.env
```

### Discovery Engine

```bash
.venv/bin/envsync discover .
```

### Discovery + Template Generation

```bash
.venv/bin/envsync discover . --generate-template
```

### JSON Output

```bash
.venv/bin/envsync compare --env examples/dev.env --env examples/staging.env --env examples/prod.env --json
```

## Example Output

```text
EnvSync Drift Report
====================
Environments: dev, staging, prod
Total keys discovered: 3

Missing Keys
------------
dev: None
staging: REDIS_URL
prod: REDIS_URL

Extra Keys
----------
dev: REDIS_URL
staging: None
prod: None

Different Values
----------------
- API_BASE_URL

Consistent Values
-----------------
- JWT_SECRET [secret]
```

## Why EnvSync?

Most teams rely on manual checks or assumptions when managing environment configs.

EnvSync gives you:

- Instant drift detection across environments
- Safe secret comparison (no leaks)
- Fast CLI integration into CI/CD
- Workspace-wide discovery of env variable usage
- Automatic `.env.template` generation from real code usage
- Extensible architecture (Terraform, Helm coming soon)

Stop guessing. Know exactly what is different.

## Why Not Just Use Manual Checks?

Manual checks are:

- Error-prone
- Not scalable
- Not CI/CD friendly

EnvSync is:

- Automated
- Consistent
- CI/CD enforced

Stop relying on human memory for critical configs.

## CI/CD Integration (GitHub Actions)

```yaml
- name: Check config drift
  run: envsync compare --env examples/dev.env --env examples/prod.env --fail-on-drift
```

If drift exists, the command exits non-zero and fails the workflow immediately.

## Input Types

- `.env` files are parsed as plain key/value pairs.
- `.yml` / `.yaml` files are parsed for Kubernetes:
  - `ConfigMap.data`
  - `ConfigMap.binaryData`
  - `Secret.stringData`
  - `Secret.data` (base64 decoded)
- Source files are recursively scanned to detect env variable calls in:
  - Python: `os.getenv("VAR")`, `os.environ.get("VAR")`, `os.environ["VAR"]`, `Config("VAR")`
  - Node.js / TypeScript: `process.env.VAR`, `process.env["VAR"]`
  - Go: `os.Getenv("VAR")`
  - PHP: `getenv('VAR')`, `$_ENV['VAR']`

## Discovery Engine Details

`envsync discover [PATH]` scans a target path (default `.`) and reports:

- Environment variable name
- Number of references found
- Primary file extension where it appears most

The scanner automatically ignores noisy directories such as:

- `node_modules`
- `.git`
- `venv` / `.venv`
- `__pycache__`
- `build`
- `dist`

When `--generate-template` is provided, EnvSync writes discovered keys into `.env.template` in the target directory, for example:

```dotenv
DB_URL=
API_KEY=
JWT_SECRET=
```

## Development Commands

```bash
make install-dev
make test
make run-help
```

## Roadmap

- [x] `.env` comparison
- [x] Kubernetes ConfigMaps and Secrets
- [x] Terminal and JSON reporting
- [x] Workspace discovery engine for environment variable usage
- [x] Automatic `.env.template` generation
- [ ] Drift history tracking
- [ ] Slack and email alerts
- [ ] Terraform state comparison
- [ ] Hosted dashboard (EnvSync Cloud)

## Support and Feedback

If this tool helps you, please star the repo and share feedback.

Early users will get access to EnvSync Cloud for free.

## EnvSync Cloud Early Access

EnvSync Cloud is currently in development.

Teams using early access are already:

- Reducing config-related incidents
- Tracking drift across multiple services
- Automating compliance checks

Join the early access list:

- [Insert link to Google Form / Typeform here (Collect Name, Email, and Company Size)]
