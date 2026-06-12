# Building ZenvX OS on GitHub Actions

The workflow [`build-iso.yml`](workflows/build-iso.yml) builds the live ISO
entirely on a GitHub-hosted Ubuntu runner — no local Linux machine required.

## How it runs

| Trigger | What happens |
|---|---|
| Push to `main`/`master` (touching `zenvx-iso/`, `zenvx-os/`, or the workflow) | Builds the ISO and uploads it as a **workflow artifact** |
| Pull request touching those paths | Builds the ISO to verify it still compiles (artifact uploaded) |
| Push a tag like `v1.0.0` | Builds the ISO **and** publishes a **GitHub Release** with the `.iso` + `.sha256` attached |
| Manual "Run workflow" (workflow_dispatch) | Builds on demand; optionally pass a `release_tag` to also cut a release |

## Getting the ISO

1. Open the **Actions** tab of the repo.
2. Click the latest **Build ZenvX OS ISO** run.
3. Download the artifact named `zenvx-os-<version>-amd64.iso` (includes the
   `.sha256` checksum).

For tagged builds, the ISO is also attached to the matching **Release** under
the repo's Releases page — a permanent, directly downloadable link.

## Notes

- The runner installs `live-build` and its dependencies, frees disk space
  (live-build needs several GB), then runs `sudo lb config && sudo lb build`
  inside `zenvx-iso/`.
- A full build takes roughly 20–40 minutes; the job timeout is 120 minutes.
- `permissions: contents: write` lets the workflow publish releases. No extra
  secrets are needed — the built-in `GITHUB_TOKEN` is sufficient.
- If a build fails, the `build.log` is uploaded as an artifact for debugging.
