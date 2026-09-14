// Case-insensitive substring plus token-prefix match. 746 titles and 2,823 task
// texts is small enough that a scan per keystroke is imperceptible.

function score(haystack, q) {
  const h = haystack.toLowerCase();
  const i = h.indexOf(q);
  if (i === 0) return 3;
  if (i > 0) return h[i - 1] === ' ' ? 2 : 1;
  return 0;
}

export function match(rows, textOf, query, limit = 8) {
  const q = query.trim().toLowerCase();
  if (q.length < 2) return [];
  const hits = [];
  for (const row of rows) {
    const s = score(textOf(row), q);
    if (s) hits.push([s, row.pct || 0, row]);
  }
  hits.sort((a, b) => b[0] - a[0] || b[1] - a[1]);
  return hits.slice(0, limit).map(h => h[2]);
}
