# POC結果: Wasmtime + CPython WASI

元ブランチ: `poc/wasmtime-cpython-wasi`

## ステータス

部分実装済み。ただし、ランタイムのパッケージングが課題として残っている。

このブランチには `app/cpython_wasi_checker.py` が含まれており、`CPYTHON_WASI_WASM=/path/to/python.wasm` を指定すると CPython WASI の `python.wasm` を実行できる。
この環境では、チェックサム固定済みの CPython WASI バイナリを安全にリポジトリへコミットしていない。そのため、`/check` は従来のチェッカーへフォールバックし、構造化された結果内でランタイム不足を報告する。

## 試したこと

- `wasmtime-py` と WASI ランナーの骨組みを追加。
- 入力ファイルとルールファイル向けに、一時ディレクトリ `/sandbox` のみを preopen する構成を追加。
- `wasmtime.Store` に fuel とメモリ上限を設定。
- 現在の CPython WASI 配布状況を確認。Python.org の議論では、公式の小さく安定した vendoring 向けアーティファクトではなく、非公式の `brettcannon/cpython-wasi-build` リリースが参照されていた。

## 次の作業

1. 特定の CPython WASI リリースアーティファクトとチェックサムを fetch スクリプトで固定する。
2. ランタイムと標準ライブラリ用に、git 管理外のキャッシュディレクトリを追加する。
3. `argv`、`PYTHONPATH`、標準ライブラリ配置、stdout JSON プロトコルを確認する。
4. ランタイムが利用可能な場合に実行する、フォールバックなしの統合テストを追加する。

## サンドボックス / 制限

- タイムアウト方針: Wasmtime fuel は設定済み。本番では epoch interruption または subprocess の wall-clock タイムアウトを追加する。
- メモリ上限: `Store.set_limits(memory_size=64 MiB)` を設定済み。
- ファイルシステム: 一時的な `/sandbox` ディレクトリのみ preopen。
- Host API allowlist: 自然な Python 呼び出しとしては未解決。JSON/stdio プロトコルまたは WASI import ブリッジを評価するべき。

## OSSレビュー

| OSS | ライセンス | メンテナンス | セキュリティ | 適合性 |
|---|---|---|---|---|
| CPython WASI | Python Software Foundation License | WASI サポートは存在するが、バイナリ配布はまだ発展途上 | 明示的な preopen の下で WASI 実行できる。標準ライブラリ面は追加レビューが必要 | Python 互換性の最有力候補だが、パッケージングと起動コストのリスクが最も高い |
| wasmtime / wasmtime-py | Apache-2.0 WITH LLVM-exception | Bytecode Alliance により活発にメンテナンスされている | 強いサンドボックスモデルを持ち、fuel と store limits をサポートする | パッケージングを固定できれば、CPython WASI 向けランタイム層として適している |

## 参照した情報

- Python.org discussion: WASI releases for CPython 3.11.9 and 3.12.10.
- 上記議論から参照されていた、非公式の `brettcannon/cpython-wasi-build` リリース。
