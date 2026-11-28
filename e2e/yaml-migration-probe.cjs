// Bounded compatibility checks against the exact verified npm browser member.
const assert = require('node:assert/strict');
const path = require('node:path');
const yaml = require(path.resolve(process.argv[2]));
assert.equal(typeof yaml.load, 'function');
assert.deepEqual(yaml.load('base: &b {one: 1}\nmerged: {<<: *b, two: 2}\n'),
  {base: {one: 1}, merged: {one: 1, two: 2}});
assert.throws(() => yaml.load('base: &b {}\nmerged: {<<: [*b, *b, *b]}\n',
  {maxTotalMergeKeys: 2}), /maxTotalMergeKeys/);
assert.deepEqual(yaml.load('ordered: !!omap [one: 1, two: 2]'),
  {ordered: [{one: 1}, {two: 2}]});
assert.throws(() => yaml.load('ordered: !!omap [one: 1, one: 2]'));
assert.equal(yaml.load('text: "a\u00a0b"').text, 'a\u00a0b');
assert.equal(yaml.load('text: a\u00a0b').text, 'a\u00a0b');
assert.throws(() => yaml.load('bad: [one, two'));
assert.deepEqual(yaml.loadAll('---\na: 1\n---\nb: 2\n'), [{a:1},{b:2}]);
console.log('Bounded js-yaml migration probes passed.');
