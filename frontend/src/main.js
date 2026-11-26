import {shell} from './components/shell.js';
import {showLogin} from './pages/login.js';
import {showProbes} from './pages/probes.js';
import {showSegments} from './pages/segments.js';
import {showCalibrations} from './pages/calibrations.js';
import {showReadings} from './pages/readings.js';
import {notify, profile, setSession, takeNotice} from './store.js';
import {escape} from './utils/format.js';

const root = document.querySelector('#app');
const pages = {probes: showProbes, segments: showSegments, calibrations: showCalibrations, readings: showReadings};

async function show() {
  const [name, query] = location.hash.slice(1).split('?');
  const page = Object.hasOwn(pages, name) ? name : 'probes';
  if (!profile() || name === 'login') {
    showLogin(root, show);
    return;
  }
  root.innerHTML = shell(page, profile(), takeNotice());
  root.querySelector('#logout').addEventListener('click', () => {
    setSession(null);
    location.hash = 'login';
  });
  const content = root.querySelector('#page');
  try {
    await pages[page](content, {query: new URLSearchParams(query), refresh: show});
  } catch (error) {
    if (!content.isConnected) return;
    if (error.status === 401 || error.status === 403) {
      setSession(null);
      notify('请重新登录。');
      location.hash = 'login';
      return;
    }
    content.innerHTML = `<div class="page-error" role="alert"><h1>暂时无法加载</h1><p>${escape(error.message)}</p><button>重新连接</button></div>`;
    content.querySelector('button').addEventListener('click', show);
  }
}

window.addEventListener('hashchange', show);
show();
