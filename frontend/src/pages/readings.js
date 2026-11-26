import {calibrationCaption, empty, modeOptions, plotHeader, probeOptions, status} from '../components/common.js';
import {modes, releaseDay} from '../constants.js';
import {clock, escape, minute, round} from '../utils/format.js';
import {formData, handle, inlineError} from '../utils/form.js';
import {api, notify, profile} from '../store.js';

export async function showReadings(root, context) {
  const [probes, active, readings] = await Promise.all([api().probes(), api().active(), api().readings()]);
  const canConvert = profile().role !== 'viewer';
  root.innerHTML = `${plotHeader('值班用表', '早班交接', '记录经签发的补光读数。每条读数保留当时使用的版本。')}
    <div class="desk">
    <section>
      <div class="active-strip"><h2>现行换算单</h2>${active.map(row => `<p><a href="#calibrations?version=${row.id}">
        ${escape(row.version)}</a> · ${escape(row.release_day)} · ${escape(modes[row.mode])} · ${escape(calibrationCaption(row, probes))} ${status(row.state)}</p>`).join('') || empty('当前未签发任何时段。')}</div>
      <div class="scroll-table"><table><caption>已登记的读数凭证</caption>
      <thead><tr><th>日期和时间</th><th>探头</th><th>探头 lx</th><th>校准 lx</th><th>版本</th></tr></thead>
      <tbody>${readings.map(row => `<tr><td>${escape(row.day)} ${clock(row.minute)}</td>
        <td>${escape(probes.find(p => p.id === row.probe_id)?.code)}</td>
        <td>${round(row.raw_lux)}</td><td><strong>${round(row.adjusted_lux)}</strong></td>
        <td><a href="#calibrations?version=${row.calibration_id}">${escape(row.version)}</a></td></tr>`).join('')}</tbody></table></div>
      ${readings.length ? '' : empty('录入第一个匹配现行窗口的读数后，此表会显示使用的版本。')}
    </section>
    <aside class="paper-form">
      ${canConvert && probes.length ? `<h2>抄录现场读数</h2><form id="convert-form">
        <label>探头<select name="probe_id">${probeOptions(probes)}</select></label>
        <div class="two"><label>日期<input type="date" name="day" value="${releaseDay}" required></label>
        <label>时间<input type="time" name="minute" value="06:12" required></label></div>
        <label>档位<select name="mode">${modeOptions()}</select></label>
        <label>探头原始亮度（lx）<input type="number" name="raw_lux" min="0" max="100000" step="any" value="480" required></label>
        <button type="submit">记入早班交接</button>${inlineError}</form>` : ''}
      <h2>下载今天的交接单</h2>
      <form id="export-form"><label>交接日期<input type="date" name="day" value="${releaseDay}" required></label>
      <button type="submit" class="secondary">导出 CSV</button>${inlineError}</form>
    </aside></div>`;
  handle(root.querySelector('#convert-form'), async form => {
    const data = formData(form, ['probe_id', 'raw_lux']);
    data.minute = minute(data.minute);
    const row = await api().convert(data);
    notify(`已登记 ${clock(row.minute)} · ${round(row.adjusted_lux)} lx。`);
    context.refresh();
  });
  handle(root.querySelector('#export-form'), async form => {
    const {day} = formData(form);
    const url = URL.createObjectURL(await api().export(day));
    const download = document.createElement('a');
    download.href = url;
    download.download = `light-shift-${day}.csv`;
    download.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
}
