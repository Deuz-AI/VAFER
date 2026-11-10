// Runs skills/vafer-brainstorm/workflows/brainstorm.js offline with stubbed agents.
// Usage: node brainstorm_harness.js <script> <scenario json>; prints {result, calls, logs} as JSON.
const fs = require('fs')

const scenario = JSON.parse(process.argv[3])
const source = fs.readFileSync(process.argv[2], 'utf8').replace('export const meta', 'const meta')
const calls = []
const logs = []
const perAgent = scenario.perAgent || 2

async function agent(prompt, opts = {}) {
  calls.push({ label: opts.label, phase: opts.phase, effort: opts.effort, model: opts.model, prompt })
  const [kind, who] = String(opts.label).split(':')
  if ((scenario.fail || []).includes(opts.label) || (scenario.fail || []).includes(kind)) throw new Error('stub failure')
  if (kind === 'idea' || kind === 'build') {
    return { ideas: Array.from({ length: perAgent }, (_, i) => ({ title: `${kind} ${who}.${i + 1}`, pitch: `pitch of ${kind} ${who}.${i + 1}` })) }
  }
  if (kind === 'curate') {
    // the pool is numbered in the prompt; merge the pairs the scenario names and leave out the ones it drops
    const raw = [...prompt.matchAll(/^(\d+)\. (.+?) — (.+)$/gm)].map((m) => ({ n: Number(m[1]), title: m[2], pitch: m[3] }))
    const merged = new Map((scenario.merge || []).map(([keep, gone]) => [gone, keep]))
    const dropped = new Set(scenario.drop || [])
    const kept = raw.filter((x) => !merged.has(x.n) && !dropped.has(x.n))
    const ideas = kept.map((x) => ({ title: x.title, pitch: x.pitch, from: [x.n, ...[...merged].filter(([, keep]) => keep === x.n).map(([gone]) => gone)] }))
    const half = Math.ceil(ideas.length / 2)
    return { themes: [{ name: 'Theme A', ideas: ideas.slice(0, half) }, { name: 'Theme B', ideas: ideas.slice(half) }] }
  }
  if (kind === 'judge') {
    const ids = [...prompt.matchAll(/^(\d+)\. /gm)].map((m) => Number(m[1]))
    const table = (scenario.scores || {})[who] || {}
    return { scores: ids.filter((id) => !(scenario.skip || []).includes(id)).map((id) => ({ id, score: table[id] || 3, why: table[id] === 5 ? 'strong' : undefined })), order: ids }
  }
  if (kind === 'write') return { summary: 'Summary.', picks: [{ title: 'P', line: 'L' }], bold: [] }
  throw new Error('unexpected label ' + opts.label)
}
const parallel = (thunks) => Promise.all(thunks.map((t) => t().catch(() => null)))
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor
const body = new AsyncFunction('args', 'agent', 'parallel', 'pipeline', 'phase', 'log', 'budget', 'workflow', source + '\n;return undefined')
body(scenario.args, agent, parallel, null, () => {}, (m) => logs.push(m), { total: null }, null)
  .then((result) => console.log(JSON.stringify({ result, calls, logs })))
  .catch((e) => {
    console.error(e)
    process.exit(1)
  })
