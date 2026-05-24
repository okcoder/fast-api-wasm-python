import { pathToFileURL } from 'node:url';

const [mjsPath, wasmPath, email, userCode] = process.argv.slice(2);

if (!mjsPath || !wasmPath || email === undefined || userCode === undefined) {
  console.error('usage: node scripts/micropython_wasm_runner.mjs <micropython.mjs> <micropython.wasm> <email> <python_code>');
  process.exit(2);
}

const { loadMicroPython } = await import(pathToFileURL(mjsPath).href);
const stdout = [];
const stderr = [];

try {
  const mp = await loadMicroPython({
    url: pathToFileURL(wasmPath).href,
    heapsize: 1024 * 1024,
    stdout: (line) => stdout.push(String(line)),
    stderr: (line) => stderr.push(String(line)),
  });

  const source = `
email = ${JSON.stringify(email)}
result = False
${userCode}
try:
    result = check(email)
except NameError:
    pass
`;

  mp.runPython(source);
  const result = mp.globals.get('result') ? 'OK' : 'NG';
  process.stdout.write(JSON.stringify({ result, stdout, stderr }));
} catch (error) {
  process.stdout.write(JSON.stringify({
    result: 'NG',
    error: error && error.message ? error.message : String(error),
    stdout,
    stderr,
  }));
  process.exit(1);
}
