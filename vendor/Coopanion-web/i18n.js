/**
 * The pages' text. Each app language is a module in `i18n/` named for its code (`zh.js`, `en.js`,
 * `zh-Hant.js`), whose default export maps keys to strings; `{name}` marks a value filled in. zh.js and
 * en.js have every key; a key another language's module leaves out reads zh.js for `zh-Hant` and en.js
 * for the rest.
 *
 * The server stamps the app language on `<html lang>` (`zh` as `zh-CN`) when it serves a page; the
 * page awaits `useLanguage()` before drawing, and calls it again when the World's prefs bring
 * another language. The figure frame gets the language from its `init` message.
 */
import zh from './i18n/zh.js';
import en from './i18n/en.js';

let current = 'zh', table = zh, fallback = zh, loads = 0;

/** `<html lang>` for an app language code, and back. */
export const htmlLang = (code) => (code === 'zh' ? 'zh-CN' : code);
const codeOf = (lang) => (!lang || lang === 'zh-CN' ? 'zh' : lang);

/** Loads the text of `code` (by default the language stamped on the page) and marks the page with it. */
export async function useLanguage(code = codeOf(document.documentElement.lang)) {
  const load = ++loads;
  const back = code === 'zh' || code === 'zh-Hant' ? zh : en;
  let own = code === 'zh' ? zh : code === 'en' ? en : null;
  if (!own && /^[a-z]{2,3}(-[A-Za-z0-9]{2,8})*$/.test(code)) {
    try { own = (await import(`./i18n/${code}.js`)).default; } catch { own = null; }
  }
  if (load !== loads) return;
  current = code; fallback = back; table = own ?? back;
  document.documentElement.lang = htmlLang(code);
}

/** The app language the pages show. */
export const language = () => current;

/** The text of `key`, `{name}` filled from `vars`. */
export function t(key, vars) {
  const s = table[key] ?? fallback[key] ?? en[key] ?? key;
  return vars ? s.replace(/\{(\w+)\}/g, (m, k) => (k in vars ? String(vars[k]) : m)) : s;
}

/** A name a figure pack gives per language (`{ zh, en, … }`): the page's, else as `t` falls back, else the first one. */
export function nameIn(names) {
  if (!names) return '';
  const back = current === 'zh' || current === 'zh-Hant' ? 'zh' : 'en';
  return names[current] ?? names[back] ?? names.en ?? names.zh ?? Object.values(names)[0] ?? '';
}

/** Fills the elements under `root` marked `data-i18n` (text), `data-i18n-label` (aria-label) and `data-i18n-title` (title). */
export function applyText(root = document) {
  for (const el of root.querySelectorAll('[data-i18n]')) el.textContent = t(el.dataset.i18n);
  for (const el of root.querySelectorAll('[data-i18n-label]')) el.setAttribute('aria-label', t(el.dataset.i18nLabel));
  for (const el of root.querySelectorAll('[data-i18n-title]')) el.title = t(el.dataset.i18nTitle);
}
