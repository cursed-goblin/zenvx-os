# ZenvX OS

**Privacy-first. Local AI. Your machine.**

ZenvX OS is a Debian 12 (Bookworm) live ISO that boots straight into a
terminal and runs a fully local AI agent (the *ZenvX Agent*) from RAM. No
desktop environment, no cloud calls for inference — the language model runs on
your own CPU/GPU. An optional installer copies the system permanently to disk.

---

## Repository layout

```
zenvx-project/
├─ zenvx-iso/                     # live-build project that produces the ISO
│  ├─ auto/{config,build,clean}   # live-build automation scripts
│  ├─ config/
│  │  ├─ package-lists/zenvx.list.chroot
│  │  ├─ hooks/live/              # chroot hooks (install deps, copy agent, cleanup)
│  │  └─ includes.chroot/         # files baked into the image
│  │     ├─ etc/                  # systemd units, skel/.bashrc, motd, sudoers, profile.d
│  │     └─ usr/                  # /usr/local/bin tools, plymouth theme, grub theme, config
│  ├─ Dockerfile.build            # build the ISO from any Docker host (e.g. Fedora)
│  └─ build-iso.sh                # one-shot build wrapper
└─ zenvx-os/                      # the Python agent (copied to /opt/zenvx in the image)
   ├─ agent_integrated.py         # main ReAct loop / entrypoint
   ├─ inference/                  # llm engine, memory, cache, recovery, streaming, ...
   ├─ tools/                      # executor, permissions, web, ecommerce, payment, ...
   ├─ monitoring/                 # metrics, log rotation, live dashboard
   └─ requirements.txt
```

---

## Building the ISO

The ISO must be built on a Linux host with `live-build` (or via the included
Docker container, which works on Fedora/macOS/any Docker host). Building needs
root/privileged access and roughly 8 GB of free disk; it takes ~20–60 minutes
and produces an ~800 MB `zenvx-os.iso`.

### Option A — native Debian/Ubuntu host

```bash
sudo apt-get update
sudo apt-get install -y live-build
cd zenvx-iso
sudo lb config        # reads auto/config
sudo lb build         # produces zenvx-os.iso
```

### Option B — Docker (recommended on Fedora)

```bash
cd zenvx-iso
./build-iso.sh        # builds the image and runs the privileged build container
```

The resulting `zenvx-os.iso` is a hybrid BIOS+UEFI image. Flash it with:

```bash
sudo dd if=zenvx-os.iso of=/dev/sdX bs=4M status=progress oflag=sync
```

---

## First boot

1. GRUB shows **Live (RAM)**, **Live (safe graphics)**, and **Install to Disk**.
2. The live system auto-logs in as user `zenvx` on tty1.
3. `zenvx-firstboot` runs once: it detects hardware, recommends a Llama model
   tier (1B / 3B / 8B), lets you choose one, and downloads it from Hugging
   Face into `/opt/zenvx/models`.
4. The `zenvx-agent` service starts. Type `zenvx` to chat, `dashboard` for live
   metrics, `logs` to follow logs, or `status` to check the service.

---

## The agent

`agent_integrated.py` runs a ReAct loop (max 5 iterations per turn). Each step
the LLM returns a JSON decision `{thought, action, parameters, confidence}`.
Actions: `search`, `execute`, `recall`, `analyze_screen`, `payment_info`,
`respond`, `done`. Sensitive actions (command execution, web search, screen
capture, payments) are gated behind a permission prompt and written to
`/var/log/zenvx/audit.log`. Payments are **never** auto-executed — ZenvX only
prints manual UPI instructions.

If no model file is present (or `llama-cpp-python` is missing), the engine runs
in a safe mock mode so the system still boots and responds.

---

## Notes

- Secure Boot must be disabled (the image is not signed).
- All Python modules compile cleanly with `python3 -m py_compile`; heavy
  runtime dependencies are imported lazily so the code is importable even when
  they are not installed.
