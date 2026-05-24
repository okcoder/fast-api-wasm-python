# POC結果: Pyodide + Node runner

## ステータス

Pyodide + Node runner 構成で動作確認済み。

このブランチでは、FastAPI が Node.js subprocess を起動し、その中で Pyodide をロードしてユーザーPython codeを実行する。

```text
FastAPI
  -> app/pyodide_node_checker.py
      -> Node subprocess
          -> runners/pyodide_check_runner.mjs
              -> Pyodide
                  -> user Python code
```

主要ファイル:

- `app/pyodide_node_checker.py`
- `runners/pyodide_check_runner.mjs`
- `tests/test_pyodide_node_checker.py`
- `package.json`
- `package-lock.json`

## Runtime / 依存準備手順

このPOCでは Node.js と npm package `pyodide` が必要。

初回セットアップ時に以下を実行する。

```bash
npm install
```

これにより `package-lock.json` に基づいて `node_modules/` が作成される。

```text
node_modules/
```

`node_modules/` はGitにコミットしない。プロジェクト準備時に `npm install` で取得する。

動作確認:

```bash
poetry run pytest -q
```

## リクエスト仕様

`POST /check` の `code` はPython code。

現状のdefault ruleは以下のような処理を行う。

```python
result = ("@" in email) and (code == "001") and is_company_domain(email)
```

現在の実装では、`code` は「任意Python code」として `user_code` に渡せるが、APIのdefault経路では `request.code` は既存テスト互換の値として使われている。

将来的には他ブランチと同様に、`request.code` 自体を以下のようなPython codeとして扱う形に揃える必要がある。

```python
def check(email):
    return "@" in email
```

## Host API連携

この案の大きな特徴は、PyodideのJS bridgeを利用してHost APIを自然に公開できる点。

現在のPOCでは、Node runner側で以下のHost APIをJS関数として定義している。

```javascript
globalThis.__hostApi = {
  isCompanyDomain(value) {
    const domain = String(value).split("@").pop().toLowerCase();
    return domain === "example.com";
  },
};
```

Pyodide側ではPython関数として利用できる。

```python
from js import __hostApi

def is_company_domain(email):
    return bool(__hostApi.isCompanyDomain(email))
```

ユーザーコード例:

```python
result = email.endswith("@example.com") and code == "ABC" and is_company_domain(email)
```

## 動作確認結果

`npm install` 実行後に確認済み。

```text
{"email": "user@example.com", "code": "001"} -> OK
{"email": "example.com", "code": "001"} -> NG
{"email": "user@example.com", "code": "999"} -> NG
```

テスト結果:

```text
10 passed
```

## Sandbox / 制限

- 実行境界は Node.js subprocess。
- Python code は Pyodide 上で実行される。
- Python wrapper側で `subprocess.run(..., timeout=...)` によりwall-clock timeoutを設定。
- Nodeは `--max-old-space-size=128` 付きで起動し、粗いheap上限を設定。
- Host API allowlist として `is_company_domain` のみを公開。
- FastAPI本体プロセス内で直接 `exec` / `eval` しない。

ただし、以下は今後の検証が必要。

- stdout/stderrサイズ制限
- Pyodide runtimeの初期化コスト
- node_modules / Pyodide asset のイメージサイズ影響
- production FastAPI containerにNode.jsを同梱できるか
- hostile-code test
  - 無限ループ
  - メモリ大量確保
  - file / network access 試行

## OSSレビュー

| OSS | License | Maintenance | Security | Fit |
|---|---|---|---|---|
| Pyodide | MPL-2.0 | Pyodide communityにより活発にメンテナンスされている | WASM上のPython runtime。Node subprocess timeout、明示的なbridge制限と組み合わせる必要がある | Python UX と Host API bridge の相性が良い。ただしruntime assetが大きい |
| Node.js | MIT-style / mixed notices | LTS/current releaseが継続的に提供されている成熟runtime | subprocess hardening と依存管理が必要 | 既存FastAPI containerに同梱できるなら利用可能 |

## 所感

Pyodide + Node runner は、Python互換性とHost API連携の自然さが強み。

特に将来要件である、ユーザーコードから許可済みアプリ機能を呼び出す用途では有力。

一方で、主な懸念は以下。

- Pyodide startup latency
- node_modules / Pyodide asset によるイメージサイズ増加
- Node.js を production container に含められるか
- sandboxとしての追加hardeningが必要

## 次の課題

1. `request.code` をPython codeとして扱う仕様に他ブランチと揃える。
2. Host API allowlistの設計を整理する。
3. stdout/stderrサイズ制限を追加する。
4. hostile-code testを追加する。
5. cold/warm latency とメモリ使用量を計測する。
6. production containerでNode.js / Pyodide同梱が許容できるか確認する。
