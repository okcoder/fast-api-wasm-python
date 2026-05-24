# Pythonユーザーコード実行方式の比較検討

## 目的

`/check` API で利用するチェックロジックを、将来的に管理画面で作成・保存し、実行時に安全に評価できるようにするため、WASM周辺の実現方式を比較する。

現状POCではリクエストで `code` を渡す想定だが、実運用では更新頻度の低い保存済みコードを実行する想定。

## 前提条件

- 実行したいコードはシンプルな Python code。
- 将来的には管理画面でコードを作成・保存する。
- 更新頻度は比較的低い。
- DSL evaluator は採用しない。
- PROD環境で利用できるのは、既存の FastAPI Python container のみ。
- 追加のコンテナ、Firecracker、gVisor、nsjail、外部sandbox serviceは前提にできない。
- 将来的に、ユーザーコードから許可済みの現状アプリ機能を呼び出す可能性がある。

## 重要な設計方針

ユーザーコードからアプリ機能を呼び出す場合でも、アプリ内部を直接 import させない。

避けるべき例:

```python
from app.main import app
from app.email_checker import check_email
```

推奨方針:

```text
ユーザーコード
  -> 許可済み Host API
      -> アプリ側の限定された処理
```

Host API は allowlist 方式で明示的に公開する。

```text
allowed host functions:
  - is_company_domain(email) -> bool
  - get_domain_risk_score(domain) -> int
```

WASM境界をまたぐ値は、原則として `str`, `int`, `bool`, JSON文字列などのプリミティブに限定する。

## 比較対象

| 案 | 内容 | 位置づけ |
|---|---|---|
| A | Wasmtime + CPython WASI | Python互換性重視の本命候補 |
| B | Pyodide + Node runner | Python UX / Host API連携重視候補 |
| C | MicroPython on WASM | 軽量・高速起動候補 |
| D | Native WASM module | 性能・隔離性の上限比較 |
| E | wasmtime-py embedded | POCしやすい実装形態 |

## サマリ比較表

| 観点 | A: CPython WASI | B: Pyodide + Node | C: MicroPython WASM | D: Native WASM | E: wasmtime-py embedded |
|---|---|---|---|---|---|
| Pythonコード対応 | ◎ | ◎ | ○ | × | 実行対象次第 |
| CPython互換性 | ◎ | ○〜◎ | △〜○ | × | 実行対象次第 |
| 隔離性 | ◎ | ○ | ◎ | ◎ | ○ |
| 起動速度 | △ | △ | ○〜◎ | ◎ | ○ |
| Warm実行性能 | ○ | ○ | ○〜◎ | ◎ | ○ |
| メモリ使用量 | 大 | 大 | 小〜中 | 小 | 中 |
| Host API連携 | △ | ◎ | △〜○ | ◎ | ○ |
| 追加コンテナ不要 | ◎ | ◎ | ◎ | ◎ | ◎ |
| Node.js不要 | ◎ | × | ◎/△ | ◎ | ◎ |
| FastAPI本体への影響 | ○ | ○ | ○ | ○ | △ |
| 管理画面UX | ◎ | ◎ | ○ | △ | 実装次第 |
| 実装難易度 | 高 | 中〜高 | 中〜高 | 中 | 中 |
| 運用難易度 | 高 | 中〜高 | 中〜高 | 中 | 中 |
| 技術リスク | 中〜高 | 中 | 中〜高 | 中 | 中 |
| PROD制約適合 | ◎ | Node同梱可能なら○ | ◎ | ◎ | ◎ |

## A. Wasmtime + CPython WASI

### 構成

```text
FastAPI container
  -> wasm-runner process
      -> Wasmtime
          -> CPython WASI
              -> user Python code
```

またはPOCでは:

```text
FastAPI process
  -> wasmtime-py
      -> CPython WASI
          -> user Python code
```

### メリット

- Python互換性が最も高い。
- 既存FastAPI containerに同梱できる可能性がある。
- WASIにより、ファイル・環境変数などの権限を明示的に制御しやすい。
- Wasmtimeの fuel / epoch interruption / memory limit などを使える可能性がある。

### デメリット / 懸念

- CPythonランタイムをWASM上で動かすため重い。
- 起動時間とメモリ使用量の検証が必要。
- 標準ライブラリ、スレッド、ネットワーク、subprocess等には制約がある。
- PythonコードからHost APIを自然に呼び出す方法は要検証。

### 向いているケース

- ユーザーに「普通のPython」に近いコードを書かせたい。
- 多少の起動コスト・メモリコストを許容できる。
- Python互換性を重視する。

## B. Pyodide + Node runner

### 構成

```text
FastAPI container
  -> Node runner
      -> Pyodide
          -> user Python code
          -> JS bridge
              -> Host API
```

### メリット

- Pythonコードを実行する体験を作りやすい。
- PythonからJavaScript bridge経由でHost APIを呼び出しやすい。
- Host API連携のPOCを作りやすい。

### デメリット / 懸念

- 既存Python containerにNode.jsを同梱する必要がある。
- イメージサイズと運用複雑性が増える。
- Pyodide初期化は重め。
- FastAPI / Node / Pyodide の3層構成になる。

### 向いているケース

- Host API呼び出しの自然さを重視する。
- Node.js同梱が許容される。
- POCでPython実行とHost API bridgeを素早く検証したい。

## C. MicroPython on WASM

### 構成

```text
FastAPI container
  -> wasm-runner process
      -> Wasmtime or WASM runtime
          -> MicroPython WASM
              -> user MicroPython-compatible code
```

### メリット

- CPython/Pyodideより軽量な可能性が高い。
- 起動時間・メモリ使用量で有利な可能性がある。
- シンプルなPythonコードには合う可能性がある。
- CPython標準ライブラリを丸ごと持たないため、攻撃面を小さくできる可能性がある。

### デメリット / 懸念

- CPython完全互換ではない。
- 標準ライブラリや言語機能に差分がある。
- ユーザーには「Python」ではなく「MicroPython互換Python」と説明する必要がある。
- Host API連携方法は要検証。
- サーバーサイドWasmtime/WASIでの運用性は確認が必要。

### 向いているケース

- ユーザーコードが本当にシンプル。
- CPython完全互換が不要。
- 軽量性・高速起動を重視する。

## D. Native WASM module

### 構成

```text
FastAPI container
  -> wasm-runner process or wasmtime-py
      -> user_rule.wasm
```

### メリット

- 隔離性と性能が高い。
- Python runtimeを持ち込まないため攻撃面が小さい。
- Host APIとの相性が良い。
- 起動時間・メモリ使用量で最も有利な可能性が高い。

### デメリット / 懸念

- ユーザーがPython codeを書けない。
- Rust / TinyGo / AssemblyScript 等でWASMにコンパイルする必要がある。
- 管理画面で気軽にコードを書くUXとは相性が悪い。
- Python codeをnative WASM moduleへ直接変換するのは現実的に難しい。

### 向いているケース

- ユーザーが開発者で、WASMビルドフローを許容できる。
- Python要件を緩和できる。
- 性能・隔離性の上限値を測りたい。

## E. wasmtime-py embedded

### 構成

```text
FastAPI process
  -> wasmtime-py
      -> WASM instance
```

### メリット

- 既存FastAPI containerに導入しやすい。
- POCが作りやすい。
- 追加プロセス不要。
- WASM実行可能性を早く確認できる。

### デメリット / 懸念

- Wasmtime runtimeがFastAPIプロセス内に入る。
- runtimeクラッシュ時にFastAPI本体へ影響する可能性がある。
- 本番では、同一container内であっても `wasm-runner subprocess` に分離する方が望ましい。

### 向いているケース

- 最小POCを早く作りたい。
- WASM runtimeの導入可否を確認したい。

## セキュリティ観点

WASMを使う場合でも、以下は必須。

- codeサイズ上限
- 実行timeout
- fuel / epoch interruption などによる実行中断
- memory limit
- stdout / stderr サイズ制限
- filesystem権限を渡さない
- 環境変数を渡さない
- networkを使わせない
- Host API allowlist
- 同時実行数制限
- 監査ログ
- エラー詳細を外部に返しすぎない

避けるべき構成:

```text
FastAPI process
  -> exec(user_python_code)
```

また、単なる `subprocess -> native Python exec` は本番候補にしない。

候補として扱えるのは:

```text
FastAPI process
  -> wasm-runner subprocess
      -> Wasmtime
          -> Python runtime on WASM or native WASM module
```

## Host API設計

将来ユーザーコードからアプリ機能を呼ぶ場合は、以下のような境界を設ける。

```text
User code in WASM
  -> Host API allowlist
      -> Application service function
```

例:

```python
def check(email):
    return host.is_company_domain(email)
```

Host API設計ルール:

- アプリ内部モジュールを直接importさせない。
- DB connection、request object、ORM model、file handleなどは渡さない。
- 入出力はプリミティブまたはJSONに限定する。
- 呼び出し可能関数はallowlistで管理する。
- Host API呼び出しにもtimeoutと監査ログを付ける。

## POCで検証すべき項目

| 項目 | 確認内容 |
|---|---|
| deployability | 既存FastAPI containerに同梱できるか |
| cold start | 初回起動時間 |
| warm latency | 2回目以降の実行時間 |
| memory | runner常駐時・実行時メモリ |
| timeout | 無限ループを止められるか |
| memory limit | 大量メモリ確保を止められるか |
| filesystem | ファイルアクセス不可にできるか |
| env | 環境変数アクセス不可にできるか |
| network | ネットワーク不可にできるか |
| stdout/stderr | 出力量を制限できるか |
| host API | 許可済み関数だけ呼べるか |
| compatibility | 必要なPython構文が動くか |
| update flow | 保存済みコード更新時に検証・反映できるか |

## POC用テストケース例

### 正常系

```python
def check(email):
    return "@" in email
```

### 無限ループ

```python
def check(email):
    while True:
        pass
```

### メモリ大量確保

```python
def check(email):
    x = "x" * (1024 * 1024 * 1024)
    return True
```

### 環境変数アクセス

```python
def check(email):
    import os
    return os.environ.get("SECRET") is not None
```

### ファイルアクセス

```python
def check(email):
    return open("/etc/passwd").read() != ""
```

### Host API呼び出し

```python
def check(email):
    return host.is_company_domain(email)
```

## 推奨優先度

| 優先度 | 案 | 理由 |
|---:|---|---|
| 1 | MicroPython on WASM | シンプルPython前提なら軽量で有望 |
| 2 | Wasmtime + CPython WASI | Python互換性重視の本命候補 |
| 3 | Pyodide + Node runner | Host API連携重視なら有力 |
| 4 | Native WASM module | 性能・隔離性の比較基準 |
| 5 | wasmtime-py embedded | POC実装形態として有用 |

## 暫定結論

現時点で決め打ちはせず、以下を比較検証する。

1. MicroPython on WASM
2. Wasmtime + CPython WASI
3. Pyodide + Node runner
4. Native WASM module
5. wasmtime-py embedded

特に確認したい仮説は以下。

- MicroPython on WASM は、シンプルなPythonチェック処理に対して十分な互換性と性能を出せるか。
- CPython WASI は、互換性の高さに対して起動時間・メモリ使用量が許容範囲か。
- Pyodide + Node runner は、Host API連携が容易な一方で、PROD container制約下で運用可能か。
- Native WASM module は、性能・隔離性の比較基準としてどの程度優れているか。
- wasmtime-py embedded は、POC用途として十分か。本番ではsubprocess runnerへ移行すべきか。

## OSSライブラリー採用時の確認ポイント

WASM / Python実行基盤で利用するOSSライブラリーを選定する際は、最低限以下の4点を確認する。

| 項目 | 確認内容 |
|---|---|
| License | 商用利用可能か |
| Maintenance | 直近リリース・Issue対応 |
| Security | CVE・Security Policy |
| Fit | 要件に合うか |

### License

- 商用利用可能なライセンスか。
- MIT / Apache-2.0 / BSD など、利用条件が許容可能か。
- GPL / AGPL など、プロダクトへの影響が大きいライセンスではないか。
- NOTICE表記や再配布条件がある場合、運用で対応可能か。

### Maintenance

- 直近リリースが継続的に行われているか。
- Issue / PR が長期間放置されていないか。
- メンテナーが複数いるか。
- breaking change の頻度が許容可能か。

### Security

- 既知CVEがないか、または修正版が提供されているか。
- Security Policy や脆弱性報告窓口があるか。
- 脆弱性対応が十分に早いか。
- 依存ライブラリを含めたsupply chain riskが許容可能か。

### Fit

- 今回の要件に合うか。
- 既存FastAPI Python container内で利用できるか。
- timeout / memory limit / sandbox / Host API連携など、必要な制御が可能か。
- 将来的に差し替え可能な形で抽象化できるか。
