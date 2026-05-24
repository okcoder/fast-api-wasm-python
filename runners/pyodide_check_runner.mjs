import { loadPyodide } from "pyodide";

const input = await new Promise((resolve, reject) => {
  let data = "";
  process.stdin.setEncoding("utf8");
  process.stdin.on("data", (chunk) => (data += chunk));
  process.stdin.on("end", () => {
    try { resolve(JSON.parse(data)); } catch (error) { reject(error); }
  });
});

const pyodide = await loadPyodide();
globalThis.__hostApi = {
  isCompanyDomain(value) {
    const domain = String(value).split("@").pop().toLowerCase();
    return domain === "example.com";
  },
};

pyodide.runPython(`
from js import __hostApi

def is_company_domain(email):
    return bool(__hostApi.isCompanyDomain(email))
`);
pyodide.globals.set("email", input.email);
pyodide.globals.set("code", input.code);
pyodide.globals.set("result", false);

try {
  pyodide.runPython(input.user_code);
  const result = pyodide.globals.get("result");
  console.log(JSON.stringify({ result: result ? "OK" : "NG" }));
} catch (error) {
  console.log(JSON.stringify({ result: "NG", error: String(error.message ?? error) }));
}
