# POC結果: MicroPython on WASM

元ブランチ: `poc/micropython-wasm`

## ステータス

部分実装済み。ただし、ランタイム取得が課題として残っている。

このブランチには `app/micropython_wasm_checker.py` が含まれており、`MICROPYTHON_WASM=/path/to/micropython.wasm` を設定すると、指定した MicroPython WASI/WASM ランタイムを実行できる。
安定していてバージョン固定されたサーバーサイド向け MicroPython WASI アーティファクトは、このリポジトリには追加していない。そのため、デフォルトのテスト環境では `/check` は従来のチェッカーへフォールバックする。

## 試したこと

- Wasmtime ベースのランナーの骨組みを追加。
- ルール実行用に、一時ディレクトリだけを preopen する構成を追加。
- 軽量化の目標を表すため、fuel と CPython より小さいメモリ上限 `16 MiB` を設定。

## 次の作業

1. 利用する MicroPython WASM/WASI ビルド元を決め、チェックサムを固定する。
2. `/sandbox/rule.py` を実行するための CLI 呼び出し仕様を確認する。
3. 想定するユーザールールに対して、利用可能な Python サブセットの互換性を検証する。
4. ランタイムが利用できる環境向けの統合テストと、レイテンシ・メモリのベンチマークを追加する。

## サンドボックス / 制限

- タイムアウト方針: Wasmtime fuel は設定済み。本番では subprocess の wall-clock タイムアウトを追加するべき。
- メモリ上限: `Store.set_limits(memory_size=16 MiB)` を設定済み。
- ファイルシステム: `/sandbox` のみ preopen。
- Host API allowlist: 未解決。MicroPython 互換のホスト呼び出しには、明示的な import/stdio プロトコルまたは生成済みバインディングが必要になる可能性が高い。

## OSSレビュー

| OSS | ライセンス | メンテナンス | セキュリティ | 適合性 |
|---|---|---|---|---|
| MicroPython | MIT | 成熟したプロジェクト。ただし WASM/WASI のデプロイ手順は、ブラウザ/デモ向けビルドほど標準化されていない | 小さいランタイムと標準ライブラリ面により攻撃面を減らせる可能性があるが、アーティファクトの出所は固定する必要がある | CPython 互換性が不要な単純なルールには適している |
| wasmtime / wasmtime-py | Apache-2.0 WITH LLVM-exception | Bytecode Alliance により活発にメンテナンスされている | 強いサンドボックスモデルを持ち、fuel と store limits をサポートする | WASI 互換の MicroPython バイナリ向けランタイム層として適している |

## 所見

MicroPython は起動時間とメモリ面では有望なままだが、ランタイムのパッケージングと互換性検証が主要なブロッカーである。
