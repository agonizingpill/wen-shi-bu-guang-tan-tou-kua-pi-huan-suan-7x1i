import {escape, clock} from '../utils/format.js';
import {modes, states} from '../constants.js';

export const status = id => `<span class="state state-${escape(id)}">${escape(states[id] || id)}</span>`;
export const empty = text => `<p class="empty">${escape(text)}</p>`;
export const modeOptions = () => Object.entries(modes).map(([name, label]) =>
  `<option value="${name}">${escape(label)}</option>`).join('');

export const plotHeader = (eyebrow, name, detail) =>
  `<header class="workspace-heading"><p class="label">${escape(eyebrow)}</p><h1>${escape(name)}</h1><p>${escape(detail)}</p></header>`;

export function probeOptions(probes, selected) {
  return probes.map(p => `<option value="${p.id}" ${p.id === selected ? 'selected' : ''}>${escape(p.code)} · ${escape(p.bay)}</option>`).join('');
}

export function calibrationCaption(calibration, probes) {
  const code = probes.find(probe => probe.id === calibration.probe_id)?.code;
  return `${code || '—'} · ${clock(calibration.start_minute)}–${clock(calibration.end_minute)}`;
}
