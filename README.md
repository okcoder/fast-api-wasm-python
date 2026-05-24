# fast-api-wasm-python

Dev Container 内で FastAPI アプリを開発し、同じコンテナ内で Codex CLI を使うための雛形です。

Python と Poetry は mise で管理します。Poetry の仮想環境はプロジェクト直下の `.venv` に作成されます。

## 使い方

1. VS Code / Cursor などでこのフォルダを開く
2. `Dev Containers: Reopen in Container` を実行
3. コンテナ作成後、mise が Python / Poetry をインストールし、`poetry install` で依存関係がインストールされます
4. API を起動

```bash
./scripts/dev.sh
```

- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- health check: http://localhost:8000/health

## 依存関係

依存関係は `pyproject.toml` で管理します。

```bash
poetry add <package>
poetry add --group dev <package>
poetry install
```

仮想環境は `poetry.toml` の設定により `.venv` に作成されます。

## Codex CLI

Dev Container 起動後の `postCreateCommand` で `@openai/codex` をグローバルインストールします。
ホスト側の `~/.codex` をコンテナの `/home/node/.codex` に bind mount するため、既存ログイン情報を利用できます。

確認:

```bash
codex --version
codex
```

未ログインの場合はコンテナ内で Codex CLI のログイン手順を実行してください。

## 開発コマンド

```bash
poetry run pytest
poetry run ruff check .
poetry run black .
```
