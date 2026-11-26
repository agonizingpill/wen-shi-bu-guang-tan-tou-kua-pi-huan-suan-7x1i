import {escape, round} from '../utils/format.js';

function scales(values) {
  const ceiling = Math.max(100, ...values);
  return [0, 0.25, 0.5, 0.75, 1].map(step => Math.round(ceiling * step));
}

export function pairedPlot(points) {
  const labels = scales(points.flatMap(p => [p.raw_lux, p.reference_lux]));
  const y = value => 140 - value / labels.at(-1) * 112;
  const x = i => 61 + 426 * i / Math.max(points.length - 1, 1);
  const lines = [
    ['raw_lux', 'raw', '探头'], ['reference_lux', 'ref', '基准'],
  ].map(([key, css]) => `<polyline class="${css}" points="${points.map((p, i) => `${x(i)},${y(p[key])}`).join(' ')}"></polyline>`).join('');
  return `<figure class="chart"><svg viewBox="0 0 520 172" role="img" aria-label="同秒配对亮度曲线">
    ${labels.map(value => `<path class="tick" d="M61 ${y(value)}h426"></path><text x="4" y="${y(value) + 4}">${value}</text>`).join('')}
    ${lines}<text x="61" y="163">${points[0]?.offset_seconds ?? 0} 秒</text><text x="449" y="163">${points.at(-1)?.offset_seconds ?? 0} 秒</text>
  </svg><figcaption><span class="legend raw">探头 lx</span><span class="legend ref">基准 lx</span></figcaption></figure>`;
}

export function knotPlot(model) {
  const pairs = model.raw_knots.map((raw, i) => ({raw_lux: raw, reference_lux: model.reference_knots[i], offset_seconds: i + 1}));
  return `<figure class="chart knot-figure"><figcaption>经验分位节点 · ${pairs.length} 个</figcaption>
    <ol>${pairs.map((p, i) => `<li><span>${Math.round(model.probabilities[i] * 100)}%</span>
      <span>${escape(round(p.raw_lux))}</span><span aria-hidden="true">→</span><strong>${escape(round(p.reference_lux))}</strong></li>`).join('')}</ol></figure>`;
}
