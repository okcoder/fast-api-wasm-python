# POC結果: wasmtime-py embedded + CPython WASI

## ステータス

request `code` をPython codeとして、FastAPIプロセス内の `wasmtime-py` から CPython WASI runtime に渡して実行するPOCとして動作確認済み。

このブランチの構成:

```text
FastAPI process
  -> wasmtime-py
      -> CPython WASI python.wasm
          -> request.code Python code
```

主要ファイル:

- `app/wasmtime_embedded_checker.py`
- `scripts/prepare_wasmtime_embedded_python.sh`
- `tests/test_wasmtime_embedded_checker.py`

`vendor/wasmtime-embedded-python/` 配下のruntime artifactはGitにコミットしない。プロジェクト準備時に取得する。

## Runtime準備手順

以下を実行する。

```bash
./scripts/prepare_wasmtime_embedded_python.sh
export WASMTIME_EMBEDDED_PYTHON_WASM=vendor/wasmtime-embedded-python/python.wasm
```

このスクリプトは以下のartifactを取得する。

```text
https://github.com/brettcannon/cpython-wasi-build/releases/download/v3.13.13/python-3.13.13-wasi_sdk-24.zip
```

配置される主なファイル:

```text
vendor/wasmtime-embedded-python/python.wasm
vendor/wasmtime-embedded-python/lib/python3.13/
```

テスト実行例:

```bash
WASMTIME_EMBEDDED_PYTHON_WASM=vendor/wasmtime-embedded-python/python.wasm poetry run pytest -q
```

## リクエスト仕様

`POST /check` の `code` はPython code。

推奨インターフェース:

```python
def check(email):
    return "@" in email
```

リクエスト例:

```json
{
  "email": "user@example.com",
  "code": "def check(email):\n    return \"@\" in email"
}
```

POCの利便性のため、`result` 変数を直接設定する形式も許容している。

```python
result = "@" in email
```

## 動作確認結果

`WASMTIME_EMBEDDED_PYTHON_WASM=vendor/wasmtime-embedded-python/python.wasm` を設定した状態で確認済み。

```text
email="user@example.com", code='def check(email): return "@" in email' -> OK
email="example.com", code='def check(email): return "@" in email' -> NG
```

テスト結果:

```text
12 passed
```

## Sandbox / 制限

- 実行境界は FastAPI process 内の `wasmtime-py` + CPython WASI runtime。
- fuel は `50_000_000_000` に設定。
- memory limit は `256 MiB` に設定。
- filesystem は `/sandbox` と `/runtime` のみpreopen。
- `/sandbox` は入力・ユーザーコード実行用の一時ディレクトリ。
- `/runtime` はCPython runtimeと標準ライブラリ用。
- FastAPIプロセス内にWasmtime runtimeを埋め込むため、runtimeクラッシュ時のblast radiusは別process runnerより大きい。
- 現時点ではwall-clock timeoutは未実装。productionでは subprocess runner 化、または epoch interruption の追加が必要。
- Host API allowlist は未実装。

## 重要な所感

この案は、既存FastAPI Python container内で完結しやすく、追加のNode.jsは不要。

一方で、以下が懸念。

- FastAPIプロセス内にWasmtimeを埋め込む。
- CPython WASI runtimeと標準ライブラリが必要。
- CPython startup costが大きい。
- Host API allowlistの自然な設計は未検証。

本番では、同一container内であっても `wasm-runner subprocess` に分離する方が安全。

## OSSレビュー

| OSS | License | Maintenance | Security | Fit |
|---|---|---|---|---|
| CPython WASI `v3.13.13` from `brettcannon/cpython-wasi-build` | Python Software Foundation License | 非公式artifactだが、CPython releaseに追随した更新がある | WASI上で実行し、preopenでfilesystem accessを制御できる。ただし標準ライブラリsurfaceの確認が必要 | Python互換性は高いが、startup costとpackaging riskが大きい |
| wasmtime / wasmtime-py | Apache-2.0 WITH LLVM-exception | Bytecode Allianceにより活発にメンテナンスされている | sandbox model、fuel、store limitを利用可能 | 既存Python container内でのPOCに適している。本番ではprocess分離を検討 |

## 次の課題

1. `scripts/prepare_wasmtime_embedded_python.sh` にchecksum検証を追加する。
2. wall-clock timeoutを追加する。
   - subprocess runner化
   - Wasmtime epoch interruption
3. hostile-code testを追加する。
   - 無限ループ
   - メモリ大量確保
   - import / file access 試行
4. cold/warm latency とメモリ使用量を計測する。
5. Host API allowlist 設計を検証する。
