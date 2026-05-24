# POC結果: MicroPython on WASM

## ステータス

MicroPython WebAssembly PyScript npm package を利用したPOC実装済み。

このブランチでは、リクエストの `code` を **Python code** として扱い、MicroPython WASM上で実行する。

主要ファイル:

- `app/micropython_wasm_checker.py`
- `scripts/micropython_wasm_runner.mjs`
- `scripts/prepare_micropython_wasm.sh`
- `tests/test_micropython_wasm_checker.py`

`vendor/micropython-wasm/` 配下のruntime artifactはGitにコミットしない。プロジェクト準備時に取得する。

## Runtime準備手順

Node.js / npm が利用できる環境で以下を実行する。

```bash
./scripts/prepare_micropython_wasm.sh
```

このスクリプトは以下のnpm packageを取得し、必要なファイルだけを `vendor/micropython-wasm/` に配置する。

```text
@micropython/micropython-webassembly-pyscript@1.28.0-6
```

配置されるファイル:

```text
vendor/micropython-wasm/micropython.wasm
vendor/micropython-wasm/micropython.mjs
vendor/micropython-wasm/package.json
```

実行時は環境変数を設定する。

```bash
export MICROPYTHON_WASM=vendor/micropython-wasm/micropython.wasm
```

テスト実行例:

```bash
MICROPYTHON_WASM=vendor/micropython-wasm/micropython.wasm poetry run pytest -q
```

## 重要な発見

取得した `micropython.wasm` は Emscripten/WebAssembly artifact であり、`wasi_snapshot_preview1` のみでWasmtimeから直接instantiateできるplain WASI moduleではなかった。

直接Wasmtime実行では以下のエラーになった。

```text
unknown import: `env::invoke_ii` has not been defined
```

そのため、このPOCでは生成済みの `micropython.mjs` wrapper をNode.jsで実行し、その内部で `micropython.wasm` をロードする。

```text
FastAPI
  -> Python checker
      -> Node subprocess
          -> micropython.mjs
              -> micropython.wasm
                  -> user Python code
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

`MICROPYTHON_WASM=vendor/micropython-wasm/micropython.wasm` を設定した状態で確認済み。

```text
email="user@example.com", code='def check(email): return "@" in email' -> OK
email="example.com", code='def check(email): return "@" in email' -> NG
```

テスト結果:

```text
12 passed
```

## 試したこと

- `@micropython/micropython-webassembly-pyscript@1.28.0-6` をnpmから取得。
- `micropython.wasm`, `micropython.mjs`, `package.json` を `vendor/micropython-wasm/` に配置。
- Node runnerでMicroPythonをロードし、`email` を注入してユーザーPython codeを実行。
- 実行結果をJSONでPython側へ返却。
- 将来WASI互換MicroPython artifactが利用できる場合に備え、Wasmtime/WASI直接実行pathは残した。

## Sandbox / 制限

- 現在の実行境界は「Node subprocess上で動くMicroPython WASM」。
- Python側の `subprocess.run(..., timeout=2.0)` でwall-clock timeoutを設定。
- `loadMicroPython` の `heapsize` は `1 MiB` に設定。
- ユーザーPython codeに対して、意図的なホストファイルシステム公開はしていない。
- ただし、Emscripten JS wrapperとNode.jsは信頼済みruntimeとして扱う必要がある。
- 本番ではstdout/stderrサイズ制限、process-level resource limit、監査ログ追加が必要。

## Host API allowlist

未解決。

ただし、このpackageはJavaScript bridgeを持つため、Host APIの検証余地はある。
将来的には、許可済み関数のみをJS moduleとして登録し、MicroPython側から以下のように呼び出す設計を検討できる。

```python
def check(email):
    return host.is_company_domain(email)
```

Host APIはallowlist方式にし、DB connection、request object、ORM modelなどは渡さない。

## OSSレビュー

| OSS | License | Maintenance | Security | Fit |
|---|---|---|---|---|
| `@micropython/micropython-webassembly-pyscript@1.28.0-6` | MIT | 公式MicroPython WebAssembly/PyScript package。POCではversion pinningする | CPythonより小さいruntime surfaceが期待できる。ただしEmscripten JS wrapperの信頼とartifact provenanceの固定が必要 | シンプルなルールで、MicroPython互換性を許容できるなら有望 |
| Node.js | MIT-style / mixed notices | 成熟したruntime。devcontainerでは利用可能 | 信頼済みwrapper実行基盤。ユーザーコード自体はMicroPython WASM内で実行される | 今回取得したEmscripten artifactの実行に必要 |

## 次の課題

1. stdout/stderrサイズ上限をNode runnerに追加する。
2. hostile-code testを追加する。
   - 無限ループ
   - メモリ大量確保
   - import / file access 試行
3. MicroPython JS module登録によるHost API allowlistを検証する。
4. cold/warm latency とメモリ使用量を計測する。
5. 本番FastAPI containerにNode.js同梱を許容できるか判断する。
