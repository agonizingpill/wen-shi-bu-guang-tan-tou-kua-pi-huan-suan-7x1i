const demo = [
  [0, 360, 418], [110, 420, 480], [220, 480, 542],
  [330, 540, 604], [440, 600, 666], [550, 660, 728],
];

export function pointEditor() {
  return `<fieldset class="pair-editor"><legend>基准表配对样本</legend>
    <div class="pair-head" aria-hidden="true"><span>偏移秒</span><span>探头 lx</span><span>基准 lx</span></div>
    ${demo.map(([offset, raw, reference], i) => `<div class="pair-row">
      <input aria-label="样本 ${i + 1} 的偏移秒" type="number" name="offset_seconds" min="0" max="599" value="${offset}" required>
      <input aria-label="样本 ${i + 1} 的探头亮度" type="number" name="raw_lux" min="0" max="100000" step="any" value="${raw}" required>
      <input aria-label="样本 ${i + 1} 的基准亮度" type="number" name="reference_lux" min="0" max="100000" step="any" value="${reference}" required>
    </div>`).join('')}</fieldset>`;
}

export function pairValues(form) {
  return Array.from(form.querySelectorAll('.pair-row'), row =>
    Object.fromEntries(Array.from(row.querySelectorAll('input'), input => [input.name, Number(input.value)])));
}
