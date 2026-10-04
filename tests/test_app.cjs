const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const context = vm.createContext({
  localStorage: { getItem: () => null },
  document: { body: {}, querySelector: () => ({}) },
});
vm.runInContext(fs.readFileSync('app.js', 'utf8').replace(/init\(\);\s*$/, ''), context);
const evaluate = (code) => vm.runInContext(code, context);
assert.equal(evaluate('state.sort'), 'collected');
evaluate(`state.items = [
  {full_name:'old/game', category:'游戏', first_seen_at:'2026-09-01', updated_at:'2026-10-05', stars:100},
  {full_name:'new/game', category:'游戏', first_seen_at:'2026-10-04', updated_at:'2026-10-01', stars:1},
  {full_name:'new/tool', category:'工具', first_seen_at:'2026-10-04', updated_at:'2026-10-02', stars:10}
];`);
assert.equal(evaluate('getFilteredItems().map(x => x.full_name).join(",")'), 'new/tool,new/game,old/game');
evaluate('state.filter = "游戏"');
assert.equal(evaluate('getFilteredItems()[0].full_name'), 'new/game');
evaluate('state.filter = "all"; state.sort = "updated"');
assert.equal(evaluate('getFilteredItems()[0].full_name'), 'old/game');
evaluate('state.sort = "stars"');
assert.equal(evaluate('getFilteredItems()[0].full_name'), 'old/game');
console.log('PASS: default collection order, batch tie-break, category filter, updated and stars sorting');
