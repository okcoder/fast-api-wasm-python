# POC結果: Pyodide + Node runner

元ブランチ: `poc/pyodide-node-runner`

## ステータス

実装済み。FastAPI は subprocess の Node ランナーを呼び出し、そのランナーが Pyodide をロードして Python ユーザーコードを実行し、`OK`/`NG` の JSON を返す。
デフォルトルールでは `email`、`code`、およびブリッジされた Host API `is_company_domain(email)` を確認する。

## サンドボックス / 制限

- タイムアウト: Python ラッパーは `subprocess.run(..., timeout=...)` を使う。
- メモリ: Node は粗いヒープ上限として `--max-old-space-size=128` 付きで起動する。
- Host API allowlist: JS/Python ブリッジ経由で `is_company_domain` のみを公開している。
- 分離: ランナーは subprocess なので、障害は in-process 実行より閉じ込めやすい。

## OSSレビュー

| OSS | ライセンス | メンテナンス | セキュリティ | 適合性 |
|---|---|---|---|---|
| Pyodide | MPL-2.0 | Pyodide コミュニティにより活発にメンテナンスされている | ブラウザ/WASM の分離モデル。Node では subprocess タイムアウトと明示的なブリッジ制限を組み合わせる | Python UX と Host API ブリッジの適合性は高いが、Node と大きなランタイムアセットが追加される |
| Node.js | MIT | LTS/current リリースが活発にメンテナンスされている | 通常の subprocess ハードニングと依存管理が必要 | 既存コンテナに Node を同梱する運用が許容できるなら採用可能 |

## 所見

Host API 連携は、Python 互換の選択肢の中で最も自然である。
主な欠点は、起動レイテンシ、イメージサイズ、Node/Pyodide 追加による運用複雑性である。
