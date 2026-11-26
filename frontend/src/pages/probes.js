import {plotHeader, status, empty} from '../components/common.js';
import {escape} from '../utils/format.js';
import {formData, handle, inlineError} from '../utils/form.js';
import {api, notify, profile} from '../store.js';

export async function showProbes(root, context) {
  const probes = await api().probes();
  const canMount = profile().role === 'supervisor';
  root.innerHTML = `${plotHeader('安装台账', '探头标本', '核对安装高度、生产批次和指定基准表，再开始采样。')}
    <div class="desk">
      <section class="specimen-list" aria-label="探头安装点">
        ${probes.map(p => `<article class="specimen">
          <div class="tag"><span class="hole"></span><strong>${escape(p.code)}</strong><small>${escape(p.batch)}</small></div>
          <div class="specimen-details"><h2>${escape(p.bay)}</h2>
            <dl><div><dt>安装高度</dt><dd>${p.mount_cm} cm</dd></div><div><dt>指定基准表</dt><dd>${escape(p.reference_serial)}</dd></div></dl>
            ${status(p.enabled ? '启用' : '暂停')} <a href="#segments?probe=${p.id}">查看见证段</a>
            ${canMount && p.enabled ? `<details><summary>暂停采集</summary><form data-suspend="${p.id}"><p>暂停后，历史交接仍可查阅。</p><button type="submit">确认暂停</button>${inlineError}</form></details>` : ''}
          </div>
        </article>`).join('') || empty('登记首支探头，随后进入亮暗见证采样。')}
      </section>
      ${canMount ? `<aside class="paper-form"><h2>新安装标签</h2><form id="mount-form">
       <label>探头编号<input name="code" placeholder="EQ-215" required></label>
       <label>棚区与架位<input name="bay" placeholder="东棚 · 三号扦插台" required></label>
       <label>生产批次<input name="batch" placeholder="LX-26C" required></label>
       <label>指定基准表<input name="reference_serial" placeholder="REF-072" required></label>
       <label>安装高度（cm）<input type="number" name="mount_cm" min="15" max="300" value="85" required></label>
       <button type="submit">封存安装标签</button>${inlineError}</form></aside>` : `<aside class="margin-note"><h2>采样前对号</h2><p>基准表序列号需与探头标本一致。班长确认安装位后，采样岗才登记亮暗见证。</p></aside>`}
    </div>`;
  handle(root.querySelector('#mount-form'), async form => {
    const row = await api().mount(formData(form, ['mount_cm']));
    notify(`已登记探头 ${row.code}。`);
    context.refresh();
  });
  for (const form of root.querySelectorAll('[data-suspend]')) {
    handle(form, async () => {
      const row = await api().suspend(form.dataset.suspend);
      notify(`已暂停探头 ${row.code}。`);
      context.refresh();
    });
  }
}
