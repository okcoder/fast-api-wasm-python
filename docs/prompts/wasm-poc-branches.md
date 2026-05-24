docs/wasm-python-code-execution-comparison.md の各提案について、提案ごとにGitブランチを作成してPOC実装してください。

対象案:
1. Wasmtime + CPython WASI
2. Pyodide + Node runner
3. MicroPython on WASM
4. Native WASM module
5. wasmtime-py embedded

進め方:
- まず working tree が clean であることを確認してください。
- main ブランチを起点に、提案ごとに以下のブランチを作成してください。
  - poc/wasmtime-cpython-wasi
  - poc/pyodide-node-runner
  - poc/micropython-wasm
  - poc/native-wasm-module
  - poc/wasmtime-py-embedded
- 各ブランチで、その提案に対応するPOC実装を行ってください。
- 実装できた場合はテストを追加し、poetry run pytest -q を実行してください。
- 依存関係や外部ランタイム取得が必要な場合は、可能な範囲で自動的に導入してください。
- 導入したOSSについて、License / Maintenance / Security / Fit の観点をREADMEまたはdocsに記録してください。
- 実装が困難またはブロックされた場合でも作業を止めず、ブランチ内に docs/poc-results/<案名>.md を作成し、原因・試したこと・次の対応を記録してください。
- 各ブランチで必ずコミットしてください。
- force push、git reset --hard、rm -rf など破壊的操作は行わないでください。
- main ブランチには直接実装変更を入れないでください。
- 最後に、作成したブランチ名、コミットID、実装状況、テスト結果、ブロック事項をまとめて報告してください。

重視する観点:
- 既存FastAPI Python container内で完結できるか
- /check API から email, code を受け取って OK/NG を返せるか
- timeout / memory limit / sandbox 制御が可能か
- Host API allowlist の将来拡張が可能か
- 各案の性能・隔離性・運用性を比較できる形にすること

ユーザー確認は極力待たず、可能な限り最後まで進めてください。
