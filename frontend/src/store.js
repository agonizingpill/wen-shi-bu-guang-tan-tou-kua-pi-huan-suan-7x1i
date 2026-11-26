import {workspace} from './api/workspace.js';

const key = 'luxury-light-session';
let session = JSON.parse(sessionStorage.getItem(key) || 'null');
let notice = '';

export function setSession(value) {
  session = value;
  if (value) sessionStorage.setItem(key, JSON.stringify(value));
  else sessionStorage.removeItem(key);
}

export const profile = () => session?.profile;
export const api = () => workspace(session?.access_token);
export const notify = message => { notice = message; };

export function takeNotice() {
  const message = notice;
  notice = '';
  return message;
}
