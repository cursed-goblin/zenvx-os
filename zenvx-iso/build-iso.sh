#!/usr/bin/env bash
# build-iso.sh - native ISO build on a Debian/Ubuntu host.
# For Fedora or other distros, use Dockerfile.build instead.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
ISO_DIR="${SCRIPT_DIR}"
AGENT_SRC="${PROJECT_ROOT}/zenvx-os"

if [ "$(id -u)" -ne 0 ]; then
	echo "This build must run as root (it uses debootstrap and mounts). Re-running with sudo..."
	exec sudo -E bash "$0" "$@"
fi

echo "==> Checking for live-build"
if ! command -v lb >/dev/null 2>&1; then
	echo "installing live-build toolchain..."
	apt-get update
	apt-get install -y live-build debootstrap squashfs-tools xorriso \
		grub-efi-amd64-bin grub-pc-bin mtools dosfstools syslinux isolinux rsync
fi

echo "==> Embedding ZenvX agent source into ISO chroot includes"
mkdir -p "${ISO_DIR}/config/includes.chroot/opt/zenvx"
rsync -a \
	--exclude '__pycache__' \
	--exclude '*.pyc' \
	--exclude '.pytest_cache' \
	--exclude 'models' \
	--exclude 'tests' \
	"${AGENT_SRC}/" "${ISO_DIR}/config/includes.chroot/opt/zenvx/"

cd "${ISO_DIR}"

echo "==> Making control scripts and hooks executable"
chmod +x auto/config auto/build auto/clean
find config/hooks -type f -exec chmod +x {} +
find config/includes.chroot/usr/local/bin -type f -exec chmod +x {} +

echo "==> Configuring live-build"
bash auto/config

echo "==> Building ISO (this can take 20-60 minutes)"
bash auto/build

ISO_FILE="$(ls -1 zenvx-os*.iso 2>/dev/null | head -n1 || true)"
if [ -z "${ISO_FILE}" ]; then
	ISO_FILE="$(ls -1 *.iso 2>/dev/null | head -n1 || true)"
fi

if [ -n "${ISO_FILE}" ]; then
	sha256sum "${ISO_FILE}" > "${ISO_FILE}.sha256"
	echo "==> Done. ISO: ${ISO_FILE}"
	echo "==> Checksum: ${ISO_FILE}.sha256"
else
	echo "!! Build finished but no .iso was found. Check zenvx-build.log"
	exit 1
fi
