#!/usr/bin/env bash
set -euo pipefail

# --- config ---
CUDA_KEYRING_DEB="cuda-keyring_1.1-1_all.deb"
CUDA_KEYRING_URL="https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2404/x86_64/${CUDA_KEYRING_DEB}"
CUDA_PKG="cuda-toolkit-12-9"
NVIDIA_DRIVER_PKG="nvidia-open"   # Open GPU kernel modules
# ---------------

log() { echo -e "\033[1;34m[INFO]\033[0m $*"; }
warn() { echo -e "\033[1;33m[WARN]\033[0m $*"; }
err() { echo -e "\033[1;31m[ERR ]\033[0m $*" >&2; }

require_root() {
  if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
    err "Please run as root (sudo)."
    exit 1
  fi
}

has_cmd() { command -v "$1" >/dev/null 2>&1; }

get_nvcc_version() {
  if has_cmd nvcc; then
    # Expected: "Cuda compilation tools, release 12.9, V12.9.123"
    nvcc --version | awk -F'release ' '/release/{print $2}' | awk -F',' '{print $1}' | xargs
  else
    echo ""
  fi
}

get_cuda_file_version() {
  # /usr/local/cuda/version.txt often contains: "CUDA Version 13.0.0"
  if [[ -f /usr/local/cuda/version.txt ]]; then
    awk '/CUDA Version/{print $3}' /usr/local/cuda/version.txt | xargs
  else
    echo ""
  fi
}

is_cuda_13_installed() {
  local nvcc_v file_v dpkg_v
  nvcc_v="$(get_nvcc_version || true)"
  file_v="$(get_cuda_file_version || true)"
  dpkg_v="$(dpkg -l | awk '/cuda-toolkit-/ {print $2"="$3}' | grep -E "^cuda-toolkit-13-" || true)"

  if [[ "$nvcc_v" =~ ^13(\.|$) ]]; then return 0; fi
  if [[ "$file_v" =~ ^13(\.|$) ]]; then return 0; fi
  if [[ -n "$dpkg_v" ]]; then return 0; fi
  return 1
}

purge_cuda_and_driver() {
  log "Purging CUDA (common libs/tools) ..."
  apt-get -y --purge remove "*cuda*" "*cublas*" "*cufft*" "*cufile*" "*curand*" \
    "*cusolver*" "*cusparse*" "*gds-tools*" "*npp*" "*nvjpeg*" "nsight*" "*nvvm*" || true

  log "Purging NVIDIA driver and controls ..."
  apt-get -y --purge remove "*nvidia*" "libxnvctrl*" || true

  log "Autoremoving leftover packages ..."
  apt-get -y autoremove || true

  log "Cleaning apt caches ..."
  apt-get clean
}

install_cuda_12_9() {
  log "Ensuring NVIDIA CUDA APT repo keyring is installed ..."
  tmpdir="$(mktemp -d)"
  pushd "$tmpdir" >/dev/null

  if [[ ! -f "${CUDA_KEYRING_DEB}" ]]; then
    wget -q --show-progress "${CUDA_KEYRING_URL}"
  fi

  dpkg -i "${CUDA_KEYRING_DEB}"
  popd >/dev/null
  rm -rf "$tmpdir"

  log "apt-get update ..."
  apt-get update

  log "Installing ${CUDA_PKG} ..."
  apt-get -y install "${CUDA_PKG}"

  log "Installing NVIDIA driver (${NVIDIA_DRIVER_PKG}) ..."
  apt-get -y install "${NVIDIA_DRIVER_PKG}"

  # Optional: hold to avoid accidental upgrade to 13.x later
  if has_cmd apt-mark; then
    log "Holding ${CUDA_PKG} to prevent accidental upgrades ..."
    apt-mark hold "${CUDA_PKG}" || true
  fi
}

verify_install() {
  local ok=1

  echo
  log "Verification:"
  if has_cmd nvidia-smi; then
    echo "---- nvidia-smi ----"
    nvidia-smi || true
  else
    warn "nvidia-smi not found (a reboot is often required after installing the driver)."
    ok=0
  fi

  if has_cmd nvcc; then
    echo "---- nvcc --version ----"
    nvcc --version || true
    local nvcc_v
    nvcc_v="$(get_nvcc_version)"
    if [[ "$nvcc_v" == "12.9"* ]]; then
      log "nvcc reports CUDA ${nvcc_v} ✅"
    else
      err "nvcc is not reporting 12.9 (got '${nvcc_v:-not found}')."
      ok=0
    fi
  else
    warn "nvcc not found."
    ok=0
  fi

  echo
  if [[ $ok -eq 1 ]]; then
    log "✅ CUDA 12.9 toolchain appears installed correctly."
    log "If nvidia-smi shows driver issues, reboot the system: sudo reboot"
    return 0
  else
    err "Verification failed. A reboot may be required. If issues persist, re-run this script after reboot."
    return 1
  fi
}

main() {
  require_root

  log "Detecting if CUDA 13.x is installed ..."
  if is_cuda_13_installed; then
    log "CUDA 13 detected. Proceeding to purge it before installing 12.9."
    purge_cuda_and_driver
  else
    log "CUDA 13 NOT detected. Skipping purge step requested for CUDA 13 only."
  fi

  install_cuda_12_9

  log "Verification step (driver may require reboot to be fully active) ..."
  verify_install
}

main "$@"
