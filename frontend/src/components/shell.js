import {roles} from '../constants.js';
import {escape} from '../utils/format.js';

const pages = [
  ['probes', '探头标本'], ['segments', '亮暗见证'],
  ['calibrations', '分位换算'], ['readings', '早班交接'],
];

export function shell(current, operator, notice) {
  const entries = pages.map(([id, label]) =>
    `<a href="#${id}" ${current === id ? 'aria-current="page"' : ''}>${label}</a>`).join('');
  return `<div class="workspace">
    <aside class="rail">
      <a href="#probes" class="brand" aria-label="鹿栖育苗工作台"><span class="stem" aria-hidden="true">❧</span><strong>鹿栖育苗</strong><small>补光基准台</small></a>
      <nav aria-label="工作区">${entries}</nav>
      <footer class="operator"><span>${escape(operator.display_name)}</span><small>${escape(roles[operator.role])}</small>
      <button type="button" id="logout" class="link">退出</button></footer>
    </aside>
    <main id="content">${notice ? `<p class="notice" role="status">${escape(notice)}</p>` : ''}<div id="page"></div></main>
  </div>`;
}
