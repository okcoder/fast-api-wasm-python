# POC結果: Native WASM module

元ブランチ: `poc/native-wasm-module`

## ステータス

実装済み。`/check` は `wasmtime-py` 経由で埋め込みのネイティブ WASM モジュールを呼び出す。
この POC ではプリミティブ値 `email_has_at` と `code_is_001` を WASM に渡し、`OK`/`NG` を返す。

## サンドボックス / 制限

- タイムアウト方針: Wasmtime fuel は有効化済み。wall-clock 締め切りには epoch interruption を追加できる。
- メモリ上限: インスタンスに対して `Store.set_limits(memory_size=64 KiB)` を設定済み。
- Host API allowlist: 現時点ではホスト関数を import していない。将来の Host API は、明示的な import としてのみ追加するべき。

## OSSレビュー

| OSS | ライセンス | メンテナンス | セキュリティ | 適合性 |
|---|---|---|---|---|
| wasmtime / wasmtime-py | Apache-2.0 WITH LLVM-exception | Bytecode Alliance により活発にメンテナンスされている | 強いサンドボックスモデルを持ち、fuel と store limits を利用できる | ネイティブ WASM の分離と性能のベースラインとして非常に適しているが、Python でルールを書く UX は満たせない |

## 所見

これは最速かつ最小のベースラインだが、ルールを WASM にコンパイルするか、固定 ABI で表現する必要がある。
分離と性能の上限比較として有用である。
