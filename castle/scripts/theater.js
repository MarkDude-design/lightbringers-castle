/* Static, scripted theater. Only the listed local room/character assets are read. */
const rooms = [
  {id: 'courtyard', name: 'Courtyard', vibe: 'Metaphors beware'},
  {id: 'dining_hall', name: 'Dining hall', vibe: 'A feast of absurdity'},
  {id: 'sky_balcony', name: 'Sky balcony', vibe: 'Gravity is optional'},
  {id: 'server_room', name: 'Server room', vibe: 'A forecast of feelings'},
  {id: 'garden', name: 'Garden', vibe: 'Everything is a sandwich'},
  {id: 'stream', name: 'Poetry stream', vibe: 'Let the errors flow'},
];
const botIds = new Set(['lightbringer', 'bert_guest', 'gpt2_guest', 'dialogpt_guest',
  'q_overlay', 'dj_love', 'camus_bots', 'meraki', 'safety_siren',
  'emotional_weather', 'ontology_knight']);
const roomIds = new Set(rooms.map(room => room.id));
const cache = new Map();
const linePositions = new Map();
const el = id => document.getElementById(id);
let version = 0;
let currentId = 'courtyard';
let currentRoom = null;
let gagIndex = 0;
let jokeIndex = 0;
let punchlineVisible = false;

function textList(value) {
  return Array.isArray(value) ? value.filter(line => typeof line === 'string' && line.trim()) : [];
}

function readScript(kind, id) {
  const allowed = kind === 'rooms' ? roomIds : kind === 'bots' ? botIds : new Set();
  if (!allowed.has(id)) return Promise.reject(new Error('Unlisted script'));
  const path = `${kind}/${id}.json`;
  if (!cache.has(path)) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 8000);
    const request = fetch(path, {credentials: 'omit', redirect: 'error', mode: 'same-origin', signal: controller.signal})
      .then(response => {
        if (!response.ok) throw new Error('Script unavailable');
        return response.json();
      }).then(data => {
        if (!data || data.id !== id || typeof data.name !== 'string') throw new Error('Invalid script');
        return data;
      }).catch(error => {
        cache.delete(path); // A later, explicit visitor action may try again.
        throw error;
      }).finally(() => clearTimeout(timeout));
    cache.set(path, request);
  }
  return cache.get(path);
}

function cue(speaker, line) {
  el('cue-speaker').textContent = speaker;
  el('cue-line').textContent = line;
}

function nextLine(bot) {
  const lines = textList(bot.responses);
  if (!lines.length) return 'A thoughtful pause. Even the cast needs one.';
  const position = linePositions.get(bot.id) || 0;
  linePositions.set(bot.id, position + 1);
  return lines[position % lines.length];
}

function renderCast(bots) {
  const list = el('cast-list');
  list.replaceChildren();
  for (const bot of bots) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'cast-button';
    button.setAttribute('aria-label', `Give ${bot.name} a cue`);
    const avatar = document.createElement('span');
    avatar.className = 'cast-avatar';
    avatar.setAttribute('aria-hidden', 'true');
    avatar.textContent = bot.name[0];
    const copy = document.createElement('span');
    const name = document.createElement('span');
    name.className = 'cast-name';
    name.textContent = bot.name;
    const role = document.createElement('span');
    role.className = 'cast-role';
    role.textContent = typeof bot.role === 'string' ? bot.role : 'A member of the company';
    copy.append(name, role);
    const arrow = document.createElement('span');
    arrow.className = 'cast-arrow arrow';
    arrow.setAttribute('aria-hidden', 'true');
    button.append(avatar, copy, arrow);
    button.addEventListener('click', () => cue(bot.name, nextLine(bot)));
    list.append(button);
  }
}

function jokes() {
  return Array.isArray(currentRoom?.jokes) ? currentRoom.jokes.filter(joke =>
    joke && typeof joke.setup === 'string' && typeof joke.punchline === 'string') : [];
}

function renderJoke() {
  const entries = jokes();
  const joke = entries[jokeIndex % (entries.length || 1)];
  el('joke-setup').textContent = joke ? joke.setup : 'A quiet moment between jokes.';
  el('joke-punchline').textContent = joke ? joke.punchline : '';
  el('joke-punchline').hidden = !punchlineVisible;
  el('joke-cue').disabled = !joke;
  el('joke-cue').textContent = punchlineVisible ? 'Another telling' : 'Give me the punchline';
  const arrow = document.createElement('span');
  arrow.className = 'arrow';
  arrow.setAttribute('aria-hidden', 'true');
  el('joke-cue').append(arrow);
}

async function enterRoom(id) {
  if (!roomIds.has(id)) id = 'courtyard';
  const turn = ++version;
  currentId = id;
  currentRoom = null;
  el('performance').setAttribute('aria-busy', 'true');
  el('stage-error').hidden = true;
  for (const control of ['scenery-cue', 'joke-cue', 'q-cue']) el(control).disabled = true;
  el('cast-list').replaceChildren();
  el('cast-note').hidden = true;
  el('joke-punchline').hidden = true;
  el('joke-setup').textContent = 'The punchline is warming up.';
  el('room-title').textContent = 'Raising the curtain…';
  el('room-description').textContent = 'The cast is finding its marks.';
  cue('IN THE WINGS', 'A scene is on its way.');
  for (const button of el('room-navigation').children) {
    button.setAttribute('aria-pressed', String(button.dataset.room === id));
  }
  history.replaceState(null, '', `#${id}`);
  try {
    const room = await readScript('rooms', id);
    if (turn !== version) return;
    const ids = Array.isArray(room.bots_present) ? [...new Set(room.bots_present)] : [];
    const cast = await Promise.allSettled(ids.map(botId => readScript('bots', botId)));
    if (turn !== version) return;
    currentRoom = room;
    gagIndex = 0;
    jokeIndex = 0;
    punchlineVisible = false;
    el('stage').dataset.room = id;
    el('act-label').textContent = `ACT ${String(rooms.findIndex(entry => entry.id === id) + 1).padStart(2, '0')} · ${rooms.find(entry => entry.id === id).name}`;
    el('room-title').textContent = room.name;
    el('room-description').textContent = typeof room.description === 'string' ? room.description : '';
    el('stage-caption').textContent = id === 'courtyard' ? 'PLEASE METAPHOR RESPONSIBLY' : 'A LITTLE STRANGE. ENTIRELY WELCOME.';
    renderCast(cast.filter(result => result.status === 'fulfilled').map(result => result.value));
    el('cast-note').hidden = !cast.some(result => result.status === 'rejected');
    const gags = textList(room.environment_gags);
    cue('THE SCENERY', gags[0] || 'The stage waits for your next cue.');
    el('scenery-cue').disabled = !gags.length;
    el('q-cue').disabled = false;
    renderJoke();
  } catch (error) {
    console.warn('Could not stage this room:', error);
    if (turn !== version) return;
    el('stage-error').hidden = false;
    el('room-title').textContent = 'A brief intermission.';
    el('room-description').textContent = 'The other doors are still open.';
    el('act-label').textContent = 'CURTAIN PAUSED';
    cue('THE STAGE MANAGER', 'This scene couldn’t reach the stage. Try another door.');
  } finally {
    if (turn === version) el('performance').setAttribute('aria-busy', 'false');
  }
}

for (const [index, room] of rooms.entries()) {
  const button = document.createElement('button');
  button.type = 'button';
  button.className = 'room-door';
  button.dataset.room = room.id;
  for (const [className, text] of [['door-number', String(index + 1).padStart(2, '0')],
    ['door-copy', ''], ['door-arrow', '']]) {
    const span = document.createElement('span');
    span.className = className === 'door-arrow' ? 'door-arrow arrow' : className;
    span.textContent = text;
    if (className === 'door-copy') {
      for (const [style, line] of [['door-name', room.name], ['door-vibe', room.vibe]]) {
        const child = document.createElement('span');
        child.className = style;
        child.textContent = line;
        span.append(child);
      }
    } else span.setAttribute('aria-hidden', 'true');
    button.append(span);
  }
  button.addEventListener('click', () => enterRoom(room.id));
  el('room-navigation').append(button);
}
el('scenery-cue').addEventListener('click', () => {
  const lines = textList(currentRoom?.environment_gags);
  if (lines.length) cue('THE SCENERY', lines[(++gagIndex) % lines.length]);
});
el('joke-cue').addEventListener('click', () => {
  if (punchlineVisible) jokeIndex++;
  punchlineVisible = !punchlineVisible;
  renderJoke();
});
el('q-cue').addEventListener('click', async () => {
  const turn = version;
  el('q-cue').disabled = true;
  try {
    const q = await readScript('bots', 'q_overlay');
    if (turn === version) cue('Q · A COSMIC ASIDE', nextLine(q));
  } catch {
    if (turn === version) cue('THE STAGE MANAGER', 'Q missed the cue. You can try again when you’re ready.');
  } finally {
    if (turn === version && currentRoom) el('q-cue').disabled = false;
  }
});
el('retry-room').addEventListener('click', () => enterRoom(currentId));
el('about-open').addEventListener('click', () => el('about-dialog').showModal());
window.addEventListener('hashchange', () => enterRoom(location.hash.slice(1)));
enterRoom(location.hash.slice(1));
