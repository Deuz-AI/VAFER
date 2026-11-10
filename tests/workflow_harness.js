// Runs skills/vafer-deep-research/workflows/deep-research.js offline with stubbed agents.
// Usage: node workflow_harness.js <script> <scenario json>; prints {result, calls, logs} as JSON.
const fs = require('fs')

const scenario = JSON.parse(process.argv[3])
const source = fs.readFileSync(process.argv[2], 'utf8').replace('export const meta', 'const meta')
const calls = []
const logs = []

const section = (n) => ({
  title: 'Section ' + n,
  rows: [
    { item: `row ${n}a`, record: 'record a', headline: true },
    { item: `row ${n}b`, record: 'record b' },
  ],
  queries: ['q' + n],
})

async function agent(prompt, opts = {}) {
  calls.push({ label: opts.label, phase: opts.phase, effort: opts.effort, model: opts.model, prompt })
  const kind = String(opts.label).split(':')[0]
  if ((scenario.fail || []).includes(opts.label)) throw new Error('stub failure')
  if (kind === 'plan') return scenario.plan === null ? null : { title: 'Title', records: 'records', sections: Array.from({ length: scenario.planned || 3 }, (_, i) => section(i + 1)) }
  if (kind === 'research') {
    const open = (scenario.open || []).includes(opts.label)
    return {
      no_web: !!scenario.noWeb,
      files_written: true,
      rows: [{ item: 'a', state: open ? 'NOT-FOUND' : 'COVERED', note: open ? 'queries' : '' }, { item: 'b', state: 'COVERED' }],
      conflicts: (scenario.unsettled || []).includes(opts.label) ? [{ claim: 'c', a: 'a', b: 'b', verdict: 'v', settled: false }] : [],
      leads: [{ topic: 'lead of ' + opts.label, why: 'why' }],
      searches: 3,
      opens: 4,
    }
  }
  if (kind === 'critic') return { gaps: Array.from({ length: scenario.gaps === undefined ? 2 : scenario.gaps }, (_, i) => ({ ...section('gap' + (i + 1)), why: 'missing' })) }
  if (kind === 'write') return scenario.write === null ? null : { answer: 'The answer.', check: '9 of 10 figures matched', words: 1000, sources: 12, flags_open: 0 }
  throw new Error('unexpected label ' + opts.label)
}
const parallel = (thunks) => Promise.all(thunks.map((t) => t().catch(() => null)))
const pipeline = async () => {
  throw new Error('pipeline is not stubbed')
}
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor
const body = new AsyncFunction('args', 'agent', 'parallel', 'pipeline', 'phase', 'log', 'budget', 'workflow', source + '\n;return undefined')
body(scenario.args, agent, parallel, pipeline, () => {}, (m) => logs.push(m), { total: null }, null)
  .then((result) => console.log(JSON.stringify({ result, calls, logs })))
  .catch((e) => {
    console.error(e)
    process.exit(1)
  })
