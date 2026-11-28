#!/usr/bin/env node
// R5.4c research only. Not a grammar parser, provenance proof or release gate.
// No network unless --fetch explicitly supplied. Inputs are never vendored.
import { createHash } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import { join } from 'node:path';
import assert from 'node:assert/strict';

// id, repository, commit, path, Git blob SHA-1, expected production occurrences
const pins = [
  [
    "parser",
    "wcandillon/xqlint",
    "900d74d9fda1c2758af045ae6e970af969a43ae4",
    "lib/XQueryParser.ebnf",
    "d189eeeb83972c985d18c64791a5fbec520fce95",
    335
  ],
  [
    "xquery",
    "wcandillon/xqlint",
    "1778846ed8e707780d791fd3ffb41feccdf9de04",
    "lib/lexers/XQueryTokenizer.ebnf",
    "d6514598ccf8d385e6baf70319745410630a5c79",
    67
  ],
  [
    "jsoniq",
    "wcandillon/xqlint",
    "1778846ed8e707780d791fd3ffb41feccdf9de04",
    "lib/lexers/JSONiqTokenizer.ebnf",
    "eff1da00eda14040b50cb2891ea2bcd0f9ba4385",
    70
  ],
  [
    "xq30",
    "GuntherRademacher/rex-parser-generator",
    "52f3bcc355cbfab7692733d79c38c16441fc4eec",
    "docs/sample-grammars/XQuery-30.ebnf",
    "d150e236b136798fba374695f0fb324c12f4a4e5",
    233
  ],
  [
    "update10",
    "GuntherRademacher/rex-parser-generator",
    "52f3bcc355cbfab7692733d79c38c16441fc4eec",
    "docs/sample-grammars/XQuery-Update-10.ebnf",
    "4e6db8e125c35d8d1cad6b9146e8e12adc6bba82",
    184
  ],
  [
    "update30",
    "GuntherRademacher/rex-parser-generator",
    "52f3bcc355cbfab7692733d79c38c16441fc4eec",
    "docs/sample-grammars/XQuery-Update-30.ebnf",
    "a2dd561aecca1ac205bfaaf44ab6edd79f48e7a9",
    246
  ],
  [
    "xml",
    "GuntherRademacher/rex-parser-generator",
    "52f3bcc355cbfab7692733d79c38c16441fc4eec",
    "docs/sample-grammars/XML.ebnf",
    "93f6c8e2424af3a792b13a32e3675663f4499fcb",
    65
  ],
  [
    "json",
    "GuntherRademacher/rex-parser-generator",
    "52f3bcc355cbfab7692733d79c38c16441fc4eec",
    "docs/sample-grammars/JSON.ebnf",
    "232b33ed32a7dfe4884874abcfd83d665f4bfadd",
    16
  ],
  [
    "rfc7159",
    "GuntherRademacher/rex-parser-generator",
    "52f3bcc355cbfab7692733d79c38c16441fc4eec",
    "docs/sample-grammars/RFC-7159.ebnf",
    "c3f1b9490aa37732fd154389c174875a6630429d",
    33
  ],
  [
    "jsoniq-spec",
    "28msec/JSONiq",
    "11c9a66bd3ebe196c6af52b7252ae03c25c6dfd3",
    "JSONiqExtensionToXQuery/en-US/Chapter-Grammar.xml",
    "a322910117bac5dd6ed4d9a6a9a6214438ea8be1",
    16
  ]
];
const expected = [[[228,185],[180,124],[238,195],[9,2],[0,0],[1,1]],[[46,20],[41,18],[46,20],[10,2],[0,0],[1,1]],[[46,19],[41,17],[46,19],[10,2],[0,0],[1,1]]];
const targets = ['xq30','update10','update30','xml','json','rfc7159'];
function parse(s,indented=false){const re=indented?/^[ \t]*([A-Za-z_][\w.-]*(?:\^[\w.-]+)?)\s*(?:\r?\n[ \t]*)?::=[ \t]*/gm:/^([A-Za-z_][\w.-]*(?:\^[\w.-]+)?)\s*(?:\r?\n[ \t]*)?::=[ \t]*/gm;const m=[...s.matchAll(re)];return m.map((x,i)=>[x[1],s.slice(x.index+x[0].length,i+1<m.length?m[i+1].index:s.length).split(/^\s*(?:<\?|\S+\s+(?:<<|\\\\))/m)[0].replace(/\/\*[^]*?\*\//g,"").trim().replace(/\s+/g," ")])}
function compare(a,b){return [a.filter(([n])=>b.some(([m])=>n===m)).length,a.filter(([n,r])=>b.some(([m,s])=>n===m&&r===s)).length]}

const args=process.argv.slice(2);
if (args.length===1 && args[0]==='--pins') {
  console.log(JSON.stringify(pins,null,2));
} else {
  const remote=args.length===1 && args[0]==='--fetch';
  const local=args.length===2 && args[0]==='--input-dir';
  if (!remote && !local) throw Error('Usage: node scripts/research_xqlint_grammar.mjs --pins | --fetch | --input-dir DIR');
  const parsed={};
  const sources=[];
  for (const [id,repo,commit,path,blob,count] of pins) {
    let bytes;
    if (remote) {
      const url='https://raw.githubusercontent.com/'+repo+'/'+commit+'/'+path;
      const response=await fetch(url,{redirect:'error',signal:AbortSignal.timeout(30000)});
      if (!response.ok) throw Error(id+': HTTP '+response.status);
      bytes=Buffer.from(await response.arrayBuffer());
    } else {
      bytes=await readFile(join(args[1],id));
    }
    const actual=createHash('sha1').update('blob '+bytes.length+'\0').update(bytes).digest('hex');
    assert.equal(actual,blob,id+': unexpected Git blob');
    let s=new TextDecoder('utf-8',{fatal:true}).decode(bytes);
    if(id==='jsoniq-spec'){
      const m=s.match(/<programlisting>([\s\S]*?)<\/programlisting>/);
      if(!m)throw Error('Missing JSONiq grammar listing');
      s=m[1];
    }
    parsed[id]=parse(s,id==='jsoniq-spec');
    assert.equal(parsed[id].length,count,id+': occurrence count');
    sources.push({id,repo,commit,path,blob,occurrences:count});
  }
  const comparisons=['parser','xquery','jsoniq'].map(id=>targets.map(t=>compare(parsed[id],parsed[t])));
  const spec=[compare(parsed['jsoniq-spec'],parsed.parser),compare(parsed['jsoniq-spec'],parsed.jsoniq)];
  assert.deepEqual(comparisons,expected);
  assert.deepEqual(spec,[[16,9],[0,0]]);
  const exact=parsed['jsoniq-spec'].filter(([n,r])=>parsed.parser.some(([m,s])=>n===m&&r===s)).map(([n])=>n);
  assert.deepEqual(exact,['ObjectConstructor','PairConstructor','ArrayConstructor','JSONAppendExpr','JSONTest','StructuredItemTest','JSONItemTest','JSONObjectTest','JSONArrayTest']);
  console.log(JSON.stringify({status:'comparison-reproduced-not-provenance-clearance',method:'heuristic occurrence comparison; pairs are [same name, same name and normalized RHS]; no one-to-one matching',sources,rows:['parser','xquery','jsoniq'],targets,comparisons,jsoniqSpec:{targets:['parser','jsoniq'],comparisons:spec,exactParserNames:exact}},null,2));
}
