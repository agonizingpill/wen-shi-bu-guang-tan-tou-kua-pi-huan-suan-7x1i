import {calibrationCaption, empty, modeOptions, plotHeader, probeOptions, status} from '../components/common.js';
import {knotPlot} from '../components/chart.js';
import {modes, referenceDay, releaseDay} from '../constants.js';
import {escape, minute, round} from '../utils/format.js';
import {formData, handle, inlineError} from '../utils/form.js';
import {api, notify, profile} from '../store.js';

function renderVersion(row, probes, role) {
  if (!row) return empty('等待采样岗提交第一个拟合窗口。');
  const model = row.model;
  return `<article class="calibration-sheet" data-version="${row.id}">
    <header><div><p class="label">${escape(calibrationCaption(row, probes))}</p>
    <h2>${escape(row.version)}</h2></div>${status(row.state)}</header>
    <dl class="release-overview"><div><dt>基准采样日</dt><dd>${escape(row.reference_day)}</dd></div>
      <div><dt>生效日期</dt><dd>${escape(row.release_day)}</dd></div><div><dt>档位</dt><dd>${escape(modes[row.mode])}</dd></div></dl>
    <p>${escape(row.explanation || '已入队，点击刷新候选查看最新结果。')}</p>
    ${model ? `<p class="results">留出 ${model.validation_count} 点 MAE <strong>${round(model.mae_raw_lux)} → ${round(model.mae_adjusted_lux)} lx</strong></p>
      <p>训练 ${model.train_count} 点 · 来自见证段 ${row.segment_ids.join('、')}</p>${knotPlot(model)}` : ''}
    ${row.state === 'ready' && role === 'supervisor' ? `<form id="publish-form">
      <button type="submit">签发并切换现行版本</button>${inlineError}</form>` : ''}
  </article>`;
}

export async function showCalibrations(root, context) {
  const [probes, versions] = await Promise.all([api().probes(), api().versions()]);
  const role = profile().role;
  const selected = versions.find(row => row.id === Number(context.query.get('version'))) || versions[0];
  root.innerHTML = `${plotHeader('系数版本库', '分位换算', '检查连续见证覆盖和留出误差，再把候选签发到补光早班。')}
    <div class="calibration-desk">
      <section class="version-rail" aria-label="拟合候选档案">
      <button type="button" class="secondary" id="refresh-versions">刷新候选</button>
      ${versions.map(row => `<a class="version-tab ${row === selected ? 'selected' : ''}" href="#calibrations?version=${row.id}">
       <strong>${escape(row.version)}</strong>${status(row.state)}
       <small>${escape(calibrationCaption(row, probes))}</small></a>`).join('')}
      </section>
      <section>${renderVersion(selected, probes, role)}</section>
      ${role === 'technician' && probes.length ? `<aside class="paper-form"><h2>申报换算窗口</h2>
        <form id="fit-form">
          <label>探头<select name="probe_id">${probeOptions(probes)}</select></label>
          <label>亮暗档<select name="mode">${modeOptions()}</select></label>
          <label>基准采样日<input name="reference_day" type="date" required value="${referenceDay}"></label>
          <label>生效日<input name="release_day" type="date" required value="${releaseDay}"></label>
          <div class="two"><label>起点<input name="start_minute" type="time" value="06:00" step="600" required></label>
          <label>终点<input name="end_minute" type="time" value="06:30" step="600" required></label></div>
          <button type="submit">排队拟合分位表</button>${inlineError}</form></aside>` : ''}
    </div>`;
  root.querySelector('#refresh-versions').addEventListener('click', context.refresh);
  handle(root.querySelector('#fit-form'), async form => {
    const data = formData(form, ['probe_id']);
    data.start_minute = minute(data.start_minute);
    data.end_minute = minute(data.end_minute);
    const row = await api().fit(data);
    notify(`已提交 ${row.version}。完成后回到候选栏查看结果。`);
    location.hash = `calibrations?version=${row.id}`;
  });
  handle(root.querySelector('#publish-form'), async () => {
    const row = await api().publish(selected.id);
    notify(`已签发 ${row.version}。`);
    context.refresh();
  });
}
