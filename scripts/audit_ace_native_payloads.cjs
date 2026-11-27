// Evidence-only: parse published and source JS with the pinned TypeScript compiler.
// Do not execute a theme, snippet or worker.
"use strict";
const fs = require("node:fs");
const path = require("node:path");
const crypto = require("node:crypto");
const assert = require("node:assert/strict");
const [source, work, output] = process.argv.slice(2);
const ts = require(path.join(work, "typescript/lib/typescript.js"));
assert.equal(ts.version, "5.9.2");
const report = JSON.parse(fs.readFileSync(output, "utf8"));
const read = (root, name) => fs.readFileSync(path.join(root, name), "utf8");
const hash = data => crypto.createHash("sha256").update(data).digest("hex");
const parse = raw => {
    const file = ts.createSourceFile("evidence.js", raw, ts.ScriptTarget.Latest, true, ts.ScriptKind.JS);
    assert.equal(file.parseDiagnostics.length, 0, "Invalid JavaScript input");
    return file;
};
const printer = ts.createPrinter({removeComments: true, newLine: ts.NewLineKind.LineFeed});
const canonical = raw => printer.printFile(parse(raw));
const options = {
    newLine: "lf", downlevelIteration: true, suppressExcessPropertyErrors: true,
    module: ts.ModuleKind.CommonJS, removeComments: false,
    sourceMap: false, inlineSourceMap: false, target: "ES5"
};
const transpile = raw => ts.transpileModule(raw, {compilerOptions: options, fileName: ""}).outputText;
function modules(raw) {
    const file = parse(raw), result = new Map();
    function visit(node) {
        if (ts.isCallExpression(node) && ts.isPropertyAccessExpression(node.expression) &&
            node.expression.expression.getText(file) === "ace" &&
            node.expression.name.text === "define" && node.arguments.length === 3 &&
            ts.isStringLiteral(node.arguments[0]) && ts.isFunctionExpression(node.arguments[2])) {
            const id = node.arguments[0].text, fn = node.arguments[2];
            assert(!result.has(id), "Duplicate Ace module: " + id);
            result.set(id, {body: fn.body.getText(file).slice(1, -1), fn, file});
            return; // never confuse nested code with top-level published definitions
        }
        ts.forEachChild(node, visit);
    }
    visit(file);
    return result;
}
function literal(node) {
    if (ts.isStringLiteral(node) || ts.isNoSubstitutionTemplateLiteral(node)) return node.text;
    if (ts.isNumericLiteral(node)) return Number(node.text);
    if (node.kind === ts.SyntaxKind.TrueKeyword) return true;
    if (node.kind === ts.SyntaxKind.FalseKeyword) return false;
    if (node.kind === ts.SyntaxKind.NullKeyword) return null;
    if (ts.isArrayLiteralExpression(node)) return node.elements.map(literal);
    if (ts.isObjectLiteralExpression(node)) {
        const value = Object.create(null);
        for (const item of node.properties) {
            assert(ts.isPropertyAssignment(item) && (ts.isIdentifier(item.name) ||
                ts.isStringLiteral(item.name) || ts.isNumericLiteral(item.name)), "Nonliteral property");
            assert(!Object.hasOwn(value, item.name.text), "Duplicate literal property");
            value[item.name.text] = literal(item.initializer);
        }
        return value;
    }
    throw new Error("Nonliteral data expression: " + ts.SyntaxKind[node.kind]);
}
function dataAssignments(raw, exported, moduleName) {
    const file = parse(raw), result = {};
    for (const stmt of file.statements) {
        if (!ts.isExpressionStatement(stmt)) continue;
        // Minified expressions can group assignments in comma expressions.
        function visit(expr) {
            if (!ts.isBinaryExpression(expr)) return;
            if (expr.operatorToken.kind === ts.SyntaxKind.CommaToken) {
                visit(expr.left); visit(expr.right); return;
            }
            if (expr.operatorToken.kind !== ts.SyntaxKind.EqualsToken || !ts.isPropertyAccessExpression(expr.left)) return;
            const recv = expr.left.expression.getText(file), key = expr.left.name.text;
            let label = null;
            if (recv === moduleName && key === "exports") label = "module.exports";
            if (recv === exported && ["snippetText", "snippets"].includes(key)) label = key;
            if (!label) return;
            try {
                assert(!Object.hasOwn(result, label), "Duplicate data assignment");
                result[label] = {kind: "static", value: literal(expr.right)};
            } catch (err) {
                result[label] = {kind: "dynamic-or-unhandled", reason: err.message};
            }
        }
        visit(stmt.expression);
    }
    return result;
}
function payload(mod) {
    const params = mod.fn.parameters.map(p => p.name.getText(mod.file));
    return dataAssignments(mod.body, params[1], params[2]);
}
function staticComparison(src, plain, mini) {
    const keys = Object.keys(src).filter(key => src[key].kind === "static");
    return keys.map(key => {
        const value = src[key].value, actual = JSON.stringify(value);
        const p = plain[key], m = mini[key];
        return {key, source_sha256: hash(actual), length: actual.length,
            unminified_equal: p?.kind === "static" && JSON.stringify(p.value) === actual,
            minified_equal: m?.kind === "static" && JSON.stringify(m.value) === actual};
    });
}
function stub(name) {
    return canonical('; (function() { ace.require([' + JSON.stringify("ace/snippets/" + name) +
        '], function(m) { if (typeof module == "object" && typeof exports == "object" && module) { module.exports = m; } }); })();');
}
function native() {
    const bootstrap = read(source, "lib/ace/worker/worker.js");
    const raw = read(path.join(work, "plain"), "worker-base.js");
    const suffix = raw.slice(bootstrap.length);
    const prefix = raw.startsWith(bootstrap);
    const mapped = modules(raw), expected = Object.keys(report.native_sources);
    // Only expected top-level definitions are allowed after the exact bootstrap.
    const rest = parse(suffix);
    const top = rest.statements.map(stmt => {
        if (!ts.isExpressionStatement(stmt) || !ts.isCallExpression(stmt.expression)) return null;
        const expr = stmt.expression;
        return expr.expression.getText(rest) === "ace.define" && ts.isStringLiteral(expr.arguments[0]) ?
            expr.arguments[0].text : null;
    });
    const rows = expected.map(id => {
        const filename = report.native_sources[id], src = read(source, filename), mod = mapped.get(id);
        assert(mod, "Native module missing: " + id);
        let compiled;
        if (filename.startsWith("lib/ace/worker/")) {
            const file = parse(src), call = file.statements[0].expression;
            assert(ts.isCallExpression(call) && call.expression.getText(file) === "define" &&
                   call.arguments.length === 1 && ts.isFunctionExpression(call.arguments[0]));
            compiled = call.arguments[0].body.getText(file).slice(1, -1);
        } else compiled = transpile(src);
        const left = canonical(compiled), right = canonical(mod.body);
        return {module: id, source: filename, source_ast_sha256: hash(left),
            published_ast_sha256: hash(right), ast_equal: left === right};
    });
    const exactModuleClosure = JSON.stringify([...mapped.keys()].sort()) === JSON.stringify(expected.sort()) &&
        JSON.stringify(top) === JSON.stringify([...mapped.keys()]);
    return {bootstrap_exact_prefix: prefix, bootstrap_sha256: hash(bootstrap),
        exact_module_closure: exactModuleClosure, top_level_modules: top, modules: rows,
        all_source_relations_match: prefix && exactModuleClosure && rows.every(r => r.ast_equal)};
}
function asset(row) {
    const name = row.file, plain = read(path.join(work, "plain"), name), mini = read(path.join(work, "mini"), name);
    const isTheme = name.startsWith("theme-");
    const basename = isTheme ? name.slice(6, -3) : name.slice(9, -3);
    const dir = isTheme ? "theme" : "snippets";
    const base = "ace/" + dir + "/" + basename;
    const p = modules(plain), m = modules(mini);
    const info = {...row, category: dir, name: basename, published_modules: [...p.keys()],
                  minified_modules: [...m.keys()], source_files: [], payloads: []};
    if (!p.size && !m.size && !isTheme) {
        info.status = canonical(plain) === stub(basename) && canonical(mini) === stub(basename) ?
            "exact-generated-empty-stub" : "unresolved-empty-or-loader";
        return info;
    }
    for (const id of p.keys()) {
        const file = "src/" + id.slice(4) + ".js";
        const exists = Object.hasOwn(report.sources, file);
        const item = {module: id, source: file, source_present: exists, minified_module_present: m.has(id)};
        if (exists) {
            const raw = read(source, file);
            item.unminified_ast_equal = canonical(transpile(raw)) === canonical(p.get(id).body);
            if (m.has(id)) {
                item.payloads = staticComparison(dataAssignments(raw, "exports", "module"), payload(p.get(id)), payload(m.get(id)));
                info.payloads.push(...item.payloads.map(v => ({module: id, ...v})));
            }
        }
        info.source_files.push(item);
    }
    info.status = "source-review-required";
    if (JSON.stringify([...p.keys()].sort()) === JSON.stringify([...m.keys()].sort()) &&
        p.has(base) && info.source_files.every(x => x.source_present && x.minified_module_present) &&
        info.payloads.length && info.payloads.every(x => x.unminified_equal && x.minified_equal))
        info.status = "static-payload-equal";
    return info;
}
try {
    report.native = native();
    report.theme_snippet_assets = report.assets.filter(a => a.file !== "worker-base.js").map(asset);
    report.status = report.native.all_source_relations_match ? "native-source-mapped-payload-review-open" : "native-source-mismatch";
    console.log("Native module relations:", report.native.modules.filter(m => m.ast_equal).length, "/", report.native.modules.length);
    const stats = {};
    for (const row of report.theme_snippet_assets) {
        const key = row.category + ":" + row.status;
        stats[key] = (stats[key] || 0) + 1;
    }
    report.theme_snippet_summary = stats;
    console.log("Theme/snippet payload evidence:", stats);
} catch (err) {
    report.status = "research-blocked";
    report.error = err.stack;
    throw err;
} finally {
    fs.writeFileSync(output, JSON.stringify(report, null, 2) + "\n");
}
if (report.status !== "native-source-mapped-payload-review-open") process.exitCode = 1;
