import {empty, modeOptions, plotHeader, probeOptions, status} from '../components/common.js';
import {pairedPlot} from '../components/chart.js';
import {pairValues, pointEditor} from '../components/pointEditor.js';
import {modes, referenceDay, states} from '../constants.js';
import {clock, escape, minute} from '../utils/format.js';
import {formData, handle, inlineError} from '../utils/form.js';
import {api, notify, profile} from '../store.js';

const stamp = value => (value || '').replace('T', ' ').slice(0, 16);

function recallArchive(recalls) {
  if (!recalls?.length) return '';
  return `<details><summary>撤回留档 · ${recalls.length} 次（原读数与签字留作复核）</summary>
    ${recalls.map(row => `<blockquote>撤回：${escape(row.recall_note)} · ${escape(row.recalled_by)} · ${escape(stamp(row.recalled_at))}<br>
      原签字 ${escape(row.witnessed_by || '—')}：${escape(row.witness_note || '—')}（${row.point_count} 对读数存档）</blockquote>`).join('')}</details>`;
}

function segmentStrip(segment, probe, isSupervisor) {
  return `<article class="segment">
    <header><div><h2>${escape(probe?.code)} · ${clock(segment.start_minute)}</h2>
    <p>${escape(segment.day)} · ${escape(modes[segment.mode])} · ${escape(segment.reference_serial)}</p></div>${status(segment.state)}</header>
    ${pairedPlot(segment.points)}
    <p class="source-file">${escape(segment.source)}</p>
    ${segment.witness_note ? `<blockquote>${escape(segment.witness_note)} ${segment.witnessed_by ? `· ${escape(segment.witnessed_by)}` : ''}</blockquote>` : ''}
    ${recallArchive(segment.recalls)}
    ${isSupervisor && segment.state === 'draft' ? `<form data-witness="${segment.id}">
      <label>班长见证说明<input name="note" required minlength="4" placeholder="基准表同秒配对及架位确认"></label>
      <button type="submit" value="witness">签署见证</button>
      <button type="submit" value="discard" class="secondary">作废重采</button>${inlineError}</form>` : ''}
    ${isSupervisor && segment.state === 'witnessed' ? `<form data-witness="${segment.id}">
      <label>撤回说明<input name="note" required minlength="4" placeholder="基准表与探头对时偏差等复核依据"></label>
      <button type="submit" value="recall" class="secondary">撤回见证</button>${inlineError}</form>` : ''}
  </article>`;
}

export async function showSegments(root, context) {
  const selected = Number(context.query.get('probe')) || undefined;
  const [probes, segments] = await Promise.all([api().probes(), api().segments(selected)]);
  const probe = probes.find(p => p.id === selected) || probes[0];
  const role = profile().role;
  root.innerHTML = `${plotHeader('同秒配对', '亮暗见证', '按十分钟窗查阅同秒读数。班长签字前可作废重采。')}
    <div class="desk">
      <section>
      <label class="filter">过滤安装点<select id="filter-probe"><option value="">全部探头</option>${probeOptions(probes, selected)}</select></label>
      ${segments.map(row => segmentStrip(row, probes.find(p => p.id === row.probe_id), role === 'supervisor')).join('') ||
        empty('当前探头没有采样段。采样岗可从右侧录入同秒配对样本。')}
      </section>
      ${role === 'technician' && probe ? `<aside class="paper-form"><h2>十分钟采样单</h2>
        <form id="capture-form">
        <label>探头<select name="probe_id">${probeOptions(probes, probe.id)}</select></label>
        <div class="two"><label>日期<input name="day" type="date" value="${referenceDay}" required></label>
        <label>档位<select name="mode">${modeOptions()}</select></label></div>
        <div class="two"><label>时段起点<input name="start_minute" type="time" value="06:30" step="600" required></label>
        <label>基准表<input name="reference_serial" value="${escape(probe.reference_serial)}" required></label></div>
        <label>来源文件<input name="source" placeholder="east-1123-high-0630.csv" required></label>
        ${pointEditor()}<button type="submit">登记待见证段</button>${inlineError}</form></aside>` :
        `<aside class="margin-note"><h2>覆盖规则</h2><p>覆盖以同一天、同一探头和同一档位的已见证记录计算。暗档记录不能借给亮档。班长可撤回对时有偏差的见证段，补采见证齐全后原候选自动重算。</p></aside>`}
    </div>`;
  root.querySelector('#filter-probe').addEventListener('change', event => {
    location.hash = event.target.value ? `segments?probe=${event.target.value}` : 'segments';
  });
  const capture = root.querySelector('#capture-form');
  capture?.elements.probe_id.addEventListener('change', event => {
    capture.elements.reference_serial.value = probes.find(p => p.id === Number(event.target.value)).reference_serial;
  });
  handle(capture, async form => {
    const data = formData(form, ['probe_id']);
    delete data.offset_seconds;
    delete data.raw_lux;
    delete data.reference_lux;
    data.start_minute = minute(data.start_minute);
    data.points = pairValues(form);
    const row = await api().capture(data);
    notify(`已登记 ${clock(row.start_minute)} 采样段，等待班长见证。`);
    context.refresh();
  });
  for (const form of root.querySelectorAll('[data-witness]')) {
    form.addEventListener('submit', event => { form.dataset.action = event.submitter.value; });
    handle(form, async () => {
      const row = await api().witness(form.dataset.witness, form.elements.note.value, form.dataset.action);
      notify(`${clock(row.start_minute)} · ${states[row.state] || row.state}`);
      context.refresh();
    });
  }
}
