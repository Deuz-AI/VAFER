export const meta = {
  name: 'vafer-brainstorm',
  description: 'Brainstorm: ideators work alone from different angles, builders combine, three judges score, the best ideas become cards',
  whenToUse: 'Started by the vafer-brainstorm skill, which passes the topic, goal, context and run folder as args.',
  phases: [
    { title: 'Diverge', detail: 'ideators work alone, each from a different angle' },
    { title: 'Build', detail: 'builders combine and stretch what is on the table' },
    { title: 'Converge', detail: 'a curator merges duplicates; three judges score every idea' },
    { title: 'Write', detail: 'the best ideas become short concept cards' },
  ],
}

const A = args && typeof args === 'object' ? args : {}
const missing = ['topic', 'run'].filter((k) => !A[k])
if (missing.length) return { ok: false, error: 'missing args: ' + missing.join(', ') }

// lenses: ideators; ideas: per ideator; builders and built: the build round; picks and bold: what gets a card
const DEPTHS = {
  quick: { lenses: 3, ideas: 8, builders: 0, built: 0, picks: 3, bold: 1 },
  standard: { lenses: 5, ideas: 10, builders: 2, built: 6, picks: 5, bold: 2 },
  deep: { lenses: 8, ideas: 12, builders: 4, built: 6, picks: 7, bold: 3 },
}
const depth = DEPTHS[A.depth] ? A.depth : 'standard'
const D = { ...DEPTHS[depth], ...(A.limits || {}) } // limits shrinks a run for smoke tests
const LENSES = [
  { name: "The user's seat", how: 'Sit where the people affected sit. Start from their pains, their workarounds and the moments they would love.' },
  { name: 'First principles', how: 'Forget how it is done today. Go back to the goal itself and rebuild the answer from scratch.' },
  { name: 'Borrowed from elsewhere', how: 'Other industries, nature, games and history have solved problems of the same shape. Carry their solutions over.' },
  { name: 'Inversion', how: 'Ask how to get the opposite result or fail badly, then flip each answer. Drop one rule that everyone treats as fixed.' },
  { name: 'Extremes', how: 'Solve it with a hundred times the means, with none, in one day, over ten years. Keep what survives the trip back.' },
  { name: 'The pragmatist', how: 'Look for the smallest thing that could be tried this week, and for cheap experiments that would teach the most.' },
  { name: 'The contrarian', how: 'List what the experts in this field take for granted, and build on the chance that they are wrong.' },
  { name: 'The trend rider', how: 'Start from what has only recently become possible, cheap or normal, and ask what it unlocks here.' },
]
const MOVES = [
  { name: 'Combine', how: 'Join two ideas that came from different angles into one idea that is stronger than either.' },
  { name: 'Stretch', how: 'Take a timid idea to its extreme, or shrink a grand one until it could start tomorrow.' },
  { name: 'Repair', how: 'Pick ideas with an obvious flaw and change them until the flaw is gone.' },
  { name: 'Transplant', how: 'Move an idea to a different user, moment, place or medium.' },
]
const CRITERIA = [
  { key: 'value', name: 'value', question: 'If it worked, how much would it move the goal?' },
  { key: 'feasibility', name: 'feasibility', question: 'Could the person asking really do it with the means and limits described?' },
  { key: 'novelty', name: 'novelty', question: 'How far is it from what most people would think of first?' },
]
const run = String(A.run).replace(/\\/g, '/').replace(/\/$/, '')
const lang = A.language || 'the language of the topic'
const turkish = /t[uü]rk/i.test(lang)
const H = turkish
  ? { picks: 'En iyi fikirler', bold: 'Cesur fikirler', all: 'Bütün fikirler', next: 'Sıradaki adımlar', other: 'Diğer' }
  : { picks: 'Top picks', bold: 'Bold bets', all: 'All ideas', next: 'Next', other: 'Other' }
const custom = Array.isArray(A.lenses) ? A.lenses.map((l) => (typeof l === 'string' ? { name: l, how: '' } : l)).filter((l) => l && l.name) : []
const lenses = (custom.length ? custom.slice(0, 10) : LENSES.slice(0, D.lenses)).map((l, i) => ({ ...l, id: i + 1 }))
const frame = `Topic: ${A.topic}${A.goal ? `\nGoal, what a good idea would achieve: ${A.goal}` : ''}${A.context ? `\nContext and constraints: ${A.context}` : ''}${A.focus ? `\nStay within: ${A.focus}` : ''}`
const avoid = Array.isArray(A.avoid) && A.avoid.length ? `\nAlready on the table from an earlier round; do not repeat these, go beyond them:\n${A.avoid.map((t) => `- ${t}`).join('\n')}` : ''

const str = (description) => (description ? { type: 'string', description } : { type: 'string' })
const list = (items, description) => (description ? { type: 'array', description, items } : { type: 'array', items })
const obj = (required, properties) => ({ type: 'object', required, properties })
const IDEA = { title: str('at most 8 words'), pitch: str('one or two sentences: what it is and why it could work') }
const IDEAS = obj(['ideas'], { ideas: list(obj(['title', 'pitch'], IDEA)) })
const BUILT = obj(['ideas'], { ideas: list(obj(['title', 'pitch'], { ...IDEA, builds_on: list({ type: 'integer' }, 'numbers of the ideas it builds on') })) })
const THEMES = obj(['themes'], {
  themes: list(obj(['name', 'ideas'], { name: str('theme name'), ideas: list(obj(['title', 'pitch', 'from'], { ...IDEA, from: list({ type: 'integer' }, 'numbers of the raw ideas merged into this one') })) })),
})
const SCORES = obj(['scores'], {
  scores: list(obj(['id', 'score'], { id: { type: 'integer' }, score: { type: 'integer', description: '1 to 5' }, why: str('at most 12 words, only for a 5 or a 1') })),
})
const LINE = list(obj(['title', 'line'], { title: str(), line: str('one sentence for a chat reply') }))
const WRITE = obj(['summary', 'picks'], { summary: str('two sentences: where the strongest ideas cluster and what that suggests'), picks: LINE, bold: LINE })

const numbered = (pool) => pool.map((x, i) => `${i + 1}. ${x.title} — ${x.pitch}`).join('\n')
const ideaBrief = (lens) => `You are one of several people brainstorming on the same topic, each from a different angle. You work alone: nobody sees your list until everyone has finished, so do not hold back and do not judge your ideas yet.
${frame}${avoid}

Your angle: ${lens.name}. ${lens.how}

Give ${D.ideas} ideas in ${lang}.
- The first ideas that come to mind are the ones everyone has. Give at most two of those, then go further out.
- An idea is a specific thing to make, do or try. "Use AI for reports" is a theme; "a bot that drafts the Friday report from the week's commits" is an idea.
- Make the ideas differ in kind, not in detail.
- Stay inside your angle; others cover the rest. Include one idea that feels too bold.
For each idea give a title of at most 8 words and a pitch of one or two sentences: what it is and why it could work. No tools are needed; answer from your own head.`

const buildBrief = (move, pool) => `A group has brainstormed on a topic, each person alone. Everything on the table is below. Your job is to build on it, not to judge it.
${frame}

On the table:
${numbered(pool)}

Your move: ${move.name}. ${move.how}
Give ${D.built} new ideas in ${lang}, each clearly different from anything on the table. For each: a title of at most 8 words, a pitch of one or two sentences, and the numbers of the ideas it builds on. No tools are needed.`

const curateBrief = (pool) => `Below are ${pool.length} raw ideas from a brainstorm, numbered. Tidy the list without judging it.
${frame}

- Merge duplicates and near-duplicates into one idea, with the clearest title and the sharper pitch. Two ideas that would be built differently are not duplicates.
- Keep every other idea. Drop nothing because it looks weak or odd.
- Group the ideas into 4 to 8 themes, named in ${lang}.
For each idea that remains, return its title, its pitch and the numbers of the raw ideas it came from. Every raw number appears exactly once. No tools are needed.

${numbered(pool)}`

const judgeBrief = (c, ideas) => `Score the ideas of a brainstorm on one criterion only: ${c.name}. ${c.question} Other judges cover the other criteria, so ignore them.
${frame}

Give every idea a whole number from 1 to 5: 5 is outstanding, 3 is average for this list, 1 is poor. Use the whole scale; a list where everything gets 4 tells nobody anything. For a 5 or a 1, add a reason of at most 12 words. No tools are needed.

${ideas.map((x) => `${x.id}. ${x.title} — ${x.pitch}`).join('\n')}`

const card = (x) => `- ${x.title} — ${x.pitch} (${CRITERIA.map((c) => `${c.name} ${x.s[c.key]}`).join(', ')}${x.why.length ? '; ' + x.why.join('; ') : ''})`
const writeBrief = (picks, bold, themes) => `Write up a brainstorm for the person who asked for it, in ${lang}.
${frame}

Every idea was scored from 1 to 5 on value, feasibility and novelty.
Top picks, best first:
${picks.map(card).join('\n')}
Bold bets, the most novel ideas outside the top picks:
${bold.map(card).join('\n') || '- none'}
All ideas by theme, with the total out of 15:
${themes.map((t) => `${t.name}\n${t.ideas.map((x) => `- ${x.title} — ${x.pitch} (${x.total})`).join('\n')}`).join('\n')}

Write ${run}/brainstorm.md with your file tool (UTF-8):
- "# <the topic as a short title>", then two sentences on where the strongest ideas cluster and what that suggests.
- "## ${H.picks}": one card per top pick, with the title as a "### " heading: what it is, concretely, in two or three sentences; why it could work; a first step that can be taken this week; the main risk and the cheapest way to test it.
- "## ${H.bold}": the same card, shorter, for each bold bet.
- "## ${H.all}": every idea by theme, one line each: title — pitch (total).
- "## ${H.next}": two to four questions whose answers would decide between the top picks.${turkish ? '' : ` Translate the four headings when the language is not English.`}
Develop the ideas given and add no new ones. Use plain words and no hype, and leave out how the list was made.
Reply through the structured output: a two-sentence summary, then each top pick and each bold bet with its title and one sentence for a chat reply.`

let agents = 0
const ask = async (prompt, opts) => {
  agents += 1
  try {
    return await agent(prompt, A.model ? { ...opts, model: A.model } : opts)
  } catch (e) {
    log(`${opts.label} failed: ${String((e && e.message) || e).slice(0, 160)}`)
    return null
  }
}
const clean = (r) => ((r && r.ideas) || []).filter((x) => x && x.title && x.pitch).map((x) => ({ title: String(x.title).trim(), pitch: String(x.pitch).trim() }))

phase('Diverge')
log(`Depth ${depth}: ${lenses.length} ideators${D.builders ? `, ${D.builders} builders` : ''}, 3 judges`)
const first = await parallel(lenses.map((l) => () => ask(ideaBrief(l), { label: 'idea:' + l.id, phase: 'Diverge', schema: IDEAS, effort: 'medium' })))
const pool = first.flatMap(clean)
if (first.filter(Boolean).length < Math.min(2, lenses.length) || !pool.length) return { ok: false, error: 'too few ideators returned ideas', agents }

if (D.builders) {
  phase('Build')
  const built = await parallel(MOVES.slice(0, D.builders).map((m, i) => () => ask(buildBrief(m, pool), { label: 'build:' + (i + 1), phase: 'Build', schema: BUILT, effort: 'medium' })))
  pool.push(...built.flatMap(clean))
}
log(`${pool.length} raw ideas on the table`)

phase('Converge')
const curated = await ask(curateBrief(pool), { label: 'curate', phase: 'Converge', schema: THEMES, effort: 'medium' })
const seen = new Set()
const themes = ((curated && curated.themes) || [])
  .map((t) => ({
    name: String(t.name || H.other),
    ideas: (t.ideas || []).filter((x) => x && x.title && x.pitch).map((x) => {
      ;(x.from || []).forEach((n) => seen.add(n))
      return { title: String(x.title).trim(), pitch: String(x.pitch).trim() }
    }),
  }))
  .filter((t) => t.ideas.length)
// nothing is lost: a raw idea the curator did not account for goes back in as it was
const stray = pool.filter((_, i) => !seen.has(i + 1))
if (stray.length) {
  if (curated) log(`${stray.length} raw ideas were not accounted for by the curator and were kept as they were`)
  else log('The curator did not finish; the raw ideas are used without merging')
  themes.push({ name: H.other, ideas: stray })
}
let next = 0
themes.forEach((t) => t.ideas.forEach((x) => Object.assign(x, { id: (next += 1), theme: t.name, s: {}, why: [] })))
const ideas = themes.flatMap((t) => t.ideas)

const rotate = (list, by) => list.slice(by).concat(list.slice(0, by)) // each judge reads the list from a different place
const judged = await parallel(
  CRITERIA.map((c, i) => () => ask(judgeBrief(c, rotate(ideas, Math.floor((i * ideas.length) / CRITERIA.length))), { label: 'judge:' + c.key, phase: 'Converge', schema: SCORES, effort: 'low' })),
)
const byId = new Map(ideas.map((x) => [x.id, x]))
CRITERIA.forEach((c, i) => {
  ;((judged[i] && judged[i].scores) || []).forEach((row) => {
    const x = byId.get(row.id)
    if (!x) return
    x.s[c.key] = Math.max(1, Math.min(5, Math.round(row.score) || 3))
    if (row.why) x.why.push(`${c.name}: ${row.why}`)
  })
  ideas.forEach((x) => (x.s[c.key] = x.s[c.key] || 3)) // an idea a judge skipped gets the middle score
})
const counts = { raw: pool.length, ideas: ideas.length, themes: themes.length }
if (!judged.some(Boolean)) {
  return { ok: false, error: 'no judge returned scores; the ideas are unranked', ideas: ideas.slice(0, 40).map((x) => `${x.title} — ${x.pitch}`), counts, agents }
}
ideas.forEach((x) => (x.total = CRITERIA.reduce((n, c) => n + x.s[c.key], 0)))
const ranked = [...ideas].sort((a, b) => b.total - a.total || b.s.value - a.s.value || b.s.novelty - a.s.novelty || a.id - b.id)
const picks = ranked.slice(0, D.picks)
const bold = ranked
  .slice(D.picks)
  .filter((x) => x.s.novelty >= 4)
  .sort((a, b) => b.s.novelty - a.s.novelty || b.s.value - a.s.value || a.id - b.id)
  .slice(0, D.bold)
themes.forEach((t) => t.ideas.sort((a, b) => b.total - a.total || a.id - b.id))

phase('Write')
const w = await ask(writeBrief(picks, bold, themes), { label: 'write', phase: 'Write', schema: WRITE, effort: 'medium' })
const plain = (xs) => xs.map((x) => ({ title: x.title, line: x.pitch }))
if (!w) return { ok: false, error: 'the writer did not finish; the ranked ideas are below', picks: plain(picks), bold: plain(bold), counts, agents }
return { ok: true, file: run + '/brainstorm.md', summary: w.summary, picks: w.picks, bold: w.bold || [], counts, depth, agents }
