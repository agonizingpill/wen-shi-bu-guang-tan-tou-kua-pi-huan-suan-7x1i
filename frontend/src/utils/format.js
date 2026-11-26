export const escape = (text = '') => String(text ?? '')
  .replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;')
  .replaceAll('"', '&quot;').replaceAll("'", '&#39;');

export const clock = minute => [Math.floor(minute / 60), minute % 60]
  .map(value => String(value).padStart(2, '0')).join(':');

export function minute(value) {
  const [hours, mins] = value.split(':').map(Number);
  return hours * 60 + mins;
}

export const round = value => Number(value).toLocaleString('zh-CN', {maximumFractionDigits: 2});
