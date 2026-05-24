# POC結果: Wasmtime + CPython WASI

## ステータス

外部から取得した CPython WASI runtime を利用するPOCとして動作確認済み。

このブランチでは、`app/cpython_wasi_checker.py` が `CPYTHON_WASI_WASM=/path/to/python.wasm` で指定された CPython WASI runtime を Wasmtime 上で実行する。

`vendor/cpython-wasi/` 配下のruntime artifactはGitにコミットしない。プロジェクト準備時に取得する。

主要ファイル:

- `app/cpython_wasi_checker.py`
- `scripts/prepare_cpython_wasi.sh`
- `tests/test_cpython_wasi_checker.py`

## Runtime準備手順

以下を実行する。

```bash
./scripts/prepare_cpython_wasi.sh
export CPYTHON_WASI_WASM=vendor/cpython-wasi/python.wasm
```

このスクリプトは以下のartifactを取得する。

```text
https://github.com/brettcannon/cpython-wasi-build/releases/download/v3.13.13/python-3.13.13-wasi_sdk-24.zip
```

配置される主なファイル:

```text
vendor/cpython-wasi/python.wasm
vendor/cpython-wasi/lib/python3.13/
```

テスト実行例:

```bash
CPYTHON_WASI_WASM=vendor/cpython-wasi/python.wasm poetry run pytest -q
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

`CPYTHON_WASI_WASM=vendor/cpython-wasi/python.wasm` を設定した状態で確認済み。

```text
email="user@example.com", code='def check(email): return "@" in email' -> OK
email="example.com", code='def check(email): return "@" in email' -> NG
```

テスト結果:

```text
11 passed
```

## 試したこと

- `wasmtime-py` を利用した WASI runner scaffold を追加。
- `scripts/prepare_cpython_wasi.sh` を追加し、version pinningした CPython WASI runtime を取得できるようにした。
- 入力ファイルとユーザーコード実行用に一時ディレクトリを `/sandbox` としてpreopen。
- CPython標準ライブラリ参照用にruntimeディレクトリを `/runtime` としてpreopen。
- `PYTHONHOME=/runtime` と `PYTHONPATH=/runtime/lib/python3.13` を設定。
- `wasmtime.Store` に fuel と memory limit を設定。
- CPythonの起動コストが高いため、初期POCよりfuelを増やした。

## Sandbox / 制限

- 実行境界は Wasmtime 上の CPython WASI runtime。
- fuel は `50_000_000_000` に設定。
- memory limit は `256 MiB` に設定。
- filesystem は `/sandbox` と `/runtime` のみpreopen。
- `/sandbox` は入力・ユーザーコード実行用の一時ディレクトリ。
- `/runtime` はCPython runtimeと標準ライブラリ用。
- 現時点ではwall-clock timeoutは未実装。productionでは subprocess runner 化、または epoch interruption の追加が必要。
- Host API allowlist は未解決。JSON/stdio protocol または WASI import bridge の検証が必要。

## 重要な所感

CPython WASI は Python互換性が最も高い候補だが、以下のコストが大きい。

- runtime artifact が大きい。
- 起動が重い。
- 標準ライブラリ配置が必要。
- fuel消費が大きい。
- Host API連携の自然な設計はまだ検証が必要。

一方で、通常のPythonコードに近い体験を提供できる点は大きなメリット。

## OSSレビュー

| OSS | License | Maintenance | Security | Fit |
|---|---|---|---|---|
| CPython WASI `v3.13.13` from `brettcannon/cpython-wasi-build` | Python Software Foundation License | 非公式artifactだが、CPython releaseに追随した更新がある | WASI上で実行し、preopenでfilesystem accessを制御できる。ただし標準ライブラリsurfaceの確認が必要 | Python互換性は最も高いが、startup costとpackaging riskが大きい |
| wasmtime / wasmtime-py | Apache-2.0 WITH LLVM-exception | Bytecode Allianceにより活発にメンテナンスされている | sandbox model、fuel、store limitを利用可能 | CPython WASI runtime layerとして有力 |

## 参照情報

- Python.org discussion: WASI releases for CPython 3.11.9 and 3.12.10
- Python.org discussion: Python 3.15.0a8, 3.14.4 and 3.13.13 are now available
- GitHub: `brettcannon/cpython-wasi-build`

## 次の課題

1. `scripts/prepare_cpython_wasi.sh` にchecksum検証を追加する。
2. wall-clock timeoutを追加する。
   - subprocess runner化
   - Wasmtime epoch interruption
3. hostile-code testを追加する。
   - 無限ループ
   - メモリ大量確保
   - import / file access 試行
4. cold/warm latency とメモリ使用量を計測する。
5. Host API allowlist 設計を検証する。
