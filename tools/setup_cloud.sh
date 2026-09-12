#!/usr/bin/env bash
# Installs Blender + Godot into the cloud session (idempotent).
# Run once per fresh container:  bash tools/setup_cloud.sh
set -euo pipefail

BLENDER_VER="${BLENDER_VER:-5.1.2}"
GODOT_VER="${GODOT_VER:-4.5}"
TMP="${TMPDIR:-/tmp}/game99-setup"; mkdir -p "$TMP"

# --- Mesa software OpenGL so headless EEVEE / Godot work without a GPU ---
if ! ldconfig -p | grep -q libEGL.so.1; then
  apt-get update -qq
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq \
    libegl1 libgl1 libgl1-mesa-dri libglu1-mesa libxi6 libxxf86vm1 \
    libxfixes3 libxrender1 libxkbcommon0 libsm6 mesa-utils unzip xz-utils
fi

# --- Blender (official portable Linux build) ---
if [ ! -x /opt/blender/blender ]; then
  MAJOR="${BLENDER_VER%.*}"
  curl -sS -L -o "$TMP/blender.tar.xz" \
    "https://download.blender.org/release/Blender${MAJOR}/blender-${BLENDER_VER}-linux-x64.tar.xz"
  mkdir -p /opt/blender
  tar -xJf "$TMP/blender.tar.xz" -C /opt/blender --strip-components=1
fi

# --- Godot (official headless-capable Linux build) ---
if [ ! -x /opt/godot/godot ]; then
  curl -sS -L -o "$TMP/godot.zip" \
    "https://github.com/godotengine/godot/releases/download/${GODOT_VER}-stable/Godot_v${GODOT_VER}-stable_linux.x86_64.zip"
  mkdir -p /opt/godot
  unzip -oq "$TMP/godot.zip" -d /opt/godot
  mv "/opt/godot/Godot_v${GODOT_VER}-stable_linux.x86_64" /opt/godot/godot
  chmod +x /opt/godot/godot
fi

ln -sf /opt/blender/blender /usr/local/bin/blender
ln -sf /opt/godot/godot /usr/local/bin/godot
echo "Blender: $(blender --version | head -1)"
echo "Godot:   $(godot --version)"
