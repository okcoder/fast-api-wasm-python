#!/usr/bin/env bash
set -euo pipefail

VERSION="3.13.13"
WASI_SDK="24"
BASE_URL="https://github.com/brettcannon/cpython-wasi-build/releases/download/v${VERSION}"
ARCHIVE="python-${VERSION}-wasi_sdk-${WASI_SDK}.zip"
DEST_DIR="vendor/wasmtime-embedded-python"
TMP_DIR="$(mktemp -d)"

cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

mkdir -p "$DEST_DIR"

python - <<PY
import urllib.request
url = "${BASE_URL}/${ARCHIVE}"
out = "${TMP_DIR}/${ARCHIVE}"
urllib.request.urlretrieve(url, out)
print(out)
PY

unzip -q "${TMP_DIR}/${ARCHIVE}" -d "$DEST_DIR"

cat <<EOF
wasmtime-py embedded CPython WASI runtime prepared:
  ${DEST_DIR}/python.wasm
  ${DEST_DIR}/lib/python3.13

Use:
  export WASMTIME_EMBEDDED_PYTHON_WASM=${DEST_DIR}/python.wasm
EOF
