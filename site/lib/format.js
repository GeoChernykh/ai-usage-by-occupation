// Every value on screen goes through one of these, so a missing metric can only
// ever render as the "not published" chip - never as undefined, NaN or a silent 0.

const MISSING = '<span class="chip">not published</span>';

const ok = v => v !== undefined && v !== null && Number.isFinite(v);

export const chip = () => MISSING;

export function num(v, digits = 2, suffix = '') {
  return ok(v) ? v.toFixed(digits) + suffix : MISSING;
}

export const pct = (v, digits = 2) => num(v, digits, '%');
export const factor = v => num(v, 1, '×');

// Times print the published value rather than a rounded one: 2.05 h and 13.3 min
// are what the release says, and the demo script quotes them.
export function hours(v) {
  return ok(v) ? String(Number(v.toFixed(2))) + ' h' : MISSING;
}

export function minutes(v) {
  return ok(v) ? String(Number(v.toFixed(1))) + ' min' : MISSING;
}

export function monthLabel(iso) {
  const [y, m] = iso.split('-');
  const names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  return names[Number(m) - 1] + ' ' + y;
}

// artifact_code_fix_or_debug_pct -> "Code fix or debug"
export function humanise(metricId) {
  const s = metricId.replace(/^artifact_/, '').replace(/_pct$/, '').replace(/_/g, ' ');
  return s.charAt(0).toUpperCase() + s.slice(1);
}

export const esc = s => String(s).replace(/[&<>"]/g,
  c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

export const SOURCE_LABEL = {
  claude_ai: 'Consumer (Claude apps)',
  '1p_api': 'Enterprise API',
};
