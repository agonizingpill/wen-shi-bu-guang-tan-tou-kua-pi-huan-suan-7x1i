import {login} from '../api/workspace.js';
import {inlineError, handle, formData} from '../utils/form.js';
import {setSession} from '../store.js';

export function showLogin(root, render) {
  root.innerHTML = `<main class="login-layout">
    <section class="cover" aria-labelledby="login-title">
      <span class="stem cover-stem" aria-hidden="true">❧</span>
      <p class="label">鹿栖育苗温室</p><h1 id="login-title">补光基准台</h1>
      <p>用同秒基准读数校准新批探头，让值班人员沿用同一条补光记录。</p>
      <div class="cover-tape" aria-hidden="true"></div>
    </section>
    <section class="login-panel">
      <h2>值班入口</h2>
      <form id="login-form">
        <label>用户名<input name="username" autocomplete="username" placeholder="yu" required></label>
        <label>密码<input name="password" type="password" autocomplete="current-password" required></label>
        <button type="submit">进入温室工作台</button>
        ${inlineError}
      </form>
      <p class="fine-print">演示账号 yu 采样、tang 签发、lin 查阅</p>
    </section>
  </main>`;
  handle(root.querySelector('#login-form'), async form => {
    const data = formData(form);
    setSession(await login(data.username, data.password));
    if (location.hash !== '#probes') location.hash = 'probes';
    else render();
  });
}
