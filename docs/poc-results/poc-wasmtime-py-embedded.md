# POC結果: wasmtime-py embedded

元ブランチ: `poc/wasmtime-py-embedded`

## ステータス

実装済み。FastAPI は in-process で `wasmtime-py` を呼び出し、埋め込みの WAT モジュールを実行する。
このモジュールは、将来の allowlist 方式の Host API を模擬するために、明示的なホスト関数 `host.is_company_domain(domain_id)` を1つ import する。

## サンドボックス / 制限

- タイムアウト方針: Wasmtime fuel は有効化済み。wall-clock キャンセルには epoch interruption を重ねられる。
- メモリ上限: `Store.set_limits(memory_size=128 KiB)` を設定済み。
- Host API allowlist: ホスト import は明示的に構築される。ユーザー/WASM コードは任意の Python モジュールを import できない。

## OSSレビュー

| OSS | ライセンス | メンテナンス | セキュリティ | 適合性 |
|---|---|---|---|---|
| wasmtime / wasmtime-py | Apache-2.0 WITH LLVM-exception | Bytecode Alliance により活発にメンテナンスされている | 強い WASM サンドボックスを持ち、fuel とリソース上限をサポートする | 既存の Python コンテナ内で素早く POC するには非常に適している。本番では FastAPI プロセスへの影響範囲を減らすため、subprocess 分離を検討するべき |

## 所見

この方式は既存の Python コンテナ内に収まるため、運用上は単純である。
主なリスクは FastAPI プロセス内にランタイムを埋め込む点であり、本番では別ランナー process の方が安全である。
