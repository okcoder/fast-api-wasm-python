#!/usr/bin/env bash
set -euo pipefail

PACKAGE="@micropython/micropython-webassembly-pyscript"
VERSION="1.28.0-6"
DEST_DIR="vendor/micropython-wasm"
TMP_DIR="$(mktemp -d)"

cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

mkdir -p "$DEST_DIR"

npm pack "${PACKAGE}@${VERSION}" --pack-destination "$TMP_DIR" >/dev/null
TARBALL="$(find "$TMP_DIR" -maxdepth 1 -name '*.tgz' | head -n 1)"

tar -xzf "$TARBALL" -C "$TMP_DIR"
cp "$TMP_DIR/package/micropython.wasm" "$DEST_DIR/micropython.wasm"
cp "$TMP_DIR/package/micropython.mjs" "$DEST_DIR/micropython.mjs"
cp "$TMP_DIR/package/package.json" "$DEST_DIR/package.json"

cat <<EOF
MicroPython WASM runtime prepared:
  ${DEST_DIR}/micropython.wasm
  ${DEST_DIR}/micropython.mjs

Use:
  export MICROPYTHON_WASM=${DEST_DIR}/micropython.wasm
EOF
