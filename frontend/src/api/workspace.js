import {request} from './http.js';

export const login = (username, password) => request('/auth/login', {method: 'POST', data: {username, password}});

export const workspace = token => ({
  profile: () => request('/auth/me', {token}),
  probes: () => request('/probes', {token}),
  mount: data => request('/probes', {token, method: 'POST', data}),
  suspend: id => request(`/probes/${id}/suspend`, {token, method: 'POST'}),
  segments: id => request(`/segments${id ? `?probe_id=${id}` : ''}`, {token}),
  capture: data => request('/segments', {token, method: 'POST', data}),
  witness: (id, note, action) => request(`/segments/${id}/${action}`, {token, method: 'POST', data: {note}}),
  segmentRecalls: id => request(`/segments/${id}/recalls`, {token}),
  versions: id => request(`/calibrations${id ? `?probe_id=${id}` : ''}`, {token}),
  fit: data => request('/calibrations', {token, method: 'POST', data}),
  publish: id => request(`/calibrations/${id}/publish`, {token, method: 'POST'}),
  attempts: id => request(`/calibrations/${id}/attempts`, {token}),
  active: () => request('/calibrations/active', {token}),
  readings: () => request('/readings', {token}),
  convert: data => request('/readings', {token, method: 'POST', data}),
  export: day => request(`/readings/export?day=${encodeURIComponent(day)}`, {token, raw: true}),
});
