'use strict';
const $ = (selector) => document.querySelector(selector);
let mode = 'build', busy = false, ready = false, history = [];
const titles = {build: 'Build', explain: 'Explain', debug: 'Debug'};
function setMode(next) {
  mode = next;
  document.querySelectorAll('.mode').forEach(button => {
    const selected = button.dataset.mode === mode;
    button.classList.toggle('active', selected);
    button.setAttribute('aria-pressed', selected);
  });
  $('#mode-title').textContent = $('#composer-mode').textContent = titles[mode];
}
document.querySelectorAll('.mode').forEach(button => button.addEventListener('click', () => {if (!busy) setMode(button.dataset.mode);}));
document.querySelectorAll('[data-prompt]').forEach(button => button.addEventListener('click', () => {
  if (busy) return;
  setMode(button.dataset.targetMode || 'build');
  $('#prompt').value = button.dataset.prompt.replaceAll('\\n', '\n');
  $('#prompt').focus();
}));
function renderMessage(role, content) {
  const article = document.createElement('article');
  article.className = 'message ' + role;
  const heading = document.createElement('div');
  heading.className = 'message-heading';
  heading.textContent = role === 'user' ? 'YOU' : 'FORGE';
  article.append(heading);
  // Never interpret model output as HTML. Only fenced code blocks get special rendering.
  const pattern = /```([^\n`]*)\n([\s\S]*?)(?:```|$)/g;
  let cursor = 0;
  const paragraph = (text) => {if (text.trim()) {const p = document.createElement('p'); p.textContent = text; article.append(p);}};
  for (const match of content.matchAll(pattern)) {
    paragraph(content.slice(cursor, match.index));
    const block = document.createElement('div'); block.className = 'code-block';
    const bar = document.createElement('div'); bar.className = 'code-header';
    const language = document.createElement('span'); language.textContent = match[1].trim() || 'code';
    const copy = document.createElement('button'); copy.className = 'copy'; copy.textContent = 'Copy code'; copy.type = 'button';
    copy.addEventListener('click', async () => {
      try {await navigator.clipboard.writeText(match[2].trimEnd()); copy.textContent = 'Copied';}
      catch {copy.textContent = 'Select code to copy';}
      setTimeout(() => {copy.textContent = 'Copy code';}, 1800);
    });
    const pre = document.createElement('pre'), code = document.createElement('code'); code.textContent = match[2].trimEnd();
    pre.append(code); bar.append(language, copy); block.append(bar, pre); article.append(block);
    cursor = match.index + match[0].length;
  }
  paragraph(content.slice(cursor));
  $('#messages').append(article);
  return article;
}
function persist() {try {sessionStorage.setItem('forge-history', JSON.stringify(history));} catch { /* storage may be disabled */ }}
try {
  const saved = JSON.parse(sessionStorage.getItem('forge-history') || '[]');
  if (Array.isArray(saved) && saved.length <= 12 && saved.every((x, i) => x && x.role === (i % 2 ? 'assistant' : 'user') && typeof x.content === 'string')) {
    history = saved; history.forEach(message => renderMessage(message.role, message.content));
    $('#welcome').hidden = history.length > 0;
  }
} catch { /* ignore invalid local history */ }
$('#new-chat').addEventListener('click', () => {
  if (busy) return;
  history = []; persist(); $('#messages').replaceChildren(); $('#welcome').hidden = false; $('#error').hidden = true; $('#prompt').value = ''; $('#prompt').focus();
});
function showError(text) {$('#error').textContent = text; $('#error').hidden = false;}
$('#chat-form').addEventListener('submit', async event => {
  event.preventDefault();
  if (busy) return;
  if (!ready) return showError('Start the local model server and open http://localhost:8000 to chat. This preview cannot run the Python model.');
  const content = $('#prompt').value.trim(); if (!content) return;
  const messages = [...history.slice(-10), {role: 'user', content}];
  busy = true; $('#send').disabled = true; $('#new-chat').disabled = true; $('#send').textContent = 'Thinking…'; $('#prompt').disabled = true; $('#error').hidden = true; $('#welcome').hidden = true;
  const userNode = renderMessage('user', content);
  const pending = renderMessage('assistant', 'Working on your code…'); pending.setAttribute('aria-busy', 'true');
  pending.scrollIntoView({behavior: 'smooth', block: 'nearest'});
  try {
    const response = await fetch('/api/chat', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({mode, messages}), signal: AbortSignal.timeout(180000)});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'The model could not complete this request.');
    if (typeof data.reply !== 'string' || !data.reply) throw new Error('The model returned an empty response. Try a shorter prompt.');
    pending.remove(); renderMessage('assistant', data.reply);
    history = [...messages, {role: 'assistant', content: data.reply}]; persist(); $('#prompt').value = '';
  } catch (error) {
    pending.remove(); userNode.remove(); $('#welcome').hidden = history.length > 0;
    showError(error.name === 'TimeoutError' ? 'Generation timed out. The server may still be working; wait briefly before retrying.' : error.message);
  } finally {
    busy = false; $('#send').disabled = false; $('#new-chat').disabled = false; $('#prompt').disabled = false; $('#send').textContent = 'Send message'; $('#prompt').focus();
  }
});
$('#prompt').addEventListener('keydown', event => {if (event.key === 'Enter' && (event.ctrlKey || event.metaKey)) {event.preventDefault(); $('#chat-form').requestSubmit();}});
$('#model-info').addEventListener('click', () => $('#details').showModal());
$('#close-details').addEventListener('click', () => $('#details').close());
async function initialize() {
  try {
    const response = await fetch('/api/health', {signal: AbortSignal.timeout(5000)});
    if (!response.ok) throw new Error();
    const data = await response.json(); if (!data.ready) throw new Error();
    ready = true; $('#connection').textContent = 'Local model connected'; $('#connection').classList.add('ready');
  } catch {$('#connection').textContent = 'Website preview'; $('#offline').hidden = false;}
  try {
    const response = await fetch('training-report.json'); if (!response.ok) throw new Error();
    const report = await response.json(); $('#training-stats').replaceChildren();
    for (const [value, label] of [[report.train_examples, 'training examples'], [report.steps, 'optimizer steps'], [report.validation_loss_before.toFixed(3), 'validation loss · before'], [report.validation_loss_after.toFixed(3), 'validation loss · after']]) {
      const stat = document.createElement('div'); stat.className = 'stat'; const strong = document.createElement('strong'), span = document.createElement('span'); strong.textContent = value; span.textContent = label; stat.append(strong, span); $('#training-stats').append(stat);
    }
  } catch {$('#training-stats').textContent = 'No completed training report is available yet.';}
}
initialize();
