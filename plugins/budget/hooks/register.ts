import type { Register } from 'claude-code'

// budget on Claude Code: past the user's threshold of the five-hour window, hold the next tool call (a subagent's
// too), ask once in the engine's own dialog, and go on or stop. z-lab plugin-platform-lab/mod-interactive-2.1.299
// I02-I05, mod-dual-host-2.1.299 M07.

const YES = '예'
const NO = '아니오'

type Window = { kind: string; percentUsed: number; resetsAt?: string }
type Host = {
  env: { get: (name: string) => Promise<string | undefined> }
  fs: {
    exists: (path: string) => Promise<boolean>
    read: (path: string) => Promise<string>
    write: (path: string, text: string) => Promise<void>
  }
}

function question(n: number): string {
  return `지정한 ${n}%에 도달했습니다, 작업을 이어서 진행하시겠어요?`
}

async function stateDir($: Host): Promise<string> {
  const xdg = await $.env.get('XDG_CONFIG_HOME')
  return `${xdg || `${await $.env.get('HOME')}/.config`}/because-i-needed`
}

async function readJson($: Host, path: string): Promise<Record<string, unknown> | null> {
  try {
    if (!(await $.fs.exists(path))) return null
    const value: unknown = JSON.parse(await $.fs.read(path))
    return value && typeof value === 'object' ? (value as Record<string, unknown>) : null
  } catch {
    return null
  }
}

// Two readings of one window: a reset time that moved by seconds is the same window (z-lab budget-lab run-0.1.0 XB2).
function sameWindow(a: unknown, b: unknown): boolean {
  const seconds = (value: unknown): number =>
    typeof value === 'number' ? value : typeof value === 'string' ? Date.parse(value) / 1000 : Number.NaN
  const gap = Math.abs(seconds(a) - seconds(b))
  return Number.isFinite(gap) && gap <= 600
}

async function threshold($: Host, dir: string): Promise<number | null> {
  const percent = (await readJson($, `${dir}/budget.json`))?.percent
  return typeof percent === 'number' && Number.isInteger(percent) && percent >= 1 && percent <= 100 ? percent : null
}

export const register: Register = on => {
  let window: Window | undefined
  let turnId: string | undefined
  let asking: Promise<boolean> | undefined

  on('session.measure', async ($, e, next) => {
    window = e.rateLimits.find(r => r.kind === 'five_hour')
    if (window) {
      const dir = await stateDir($)
      await $.fs.write(`${dir}/budget/usage.json`, JSON.stringify({
        kind: 'five_hour', used: window.percentUsed, resets_at: window.resetsAt ?? null, host: 'claude',
        at: Math.floor(Date.now() / 1000),
      }))
    }
    return next(e)
  })

  on('turn.start', async ($, e, next) => {
    turnId = e.turnId
    return next(e)
  })

  on('tool.call', async ($, e, next) => {
    if (e.tool === 'AskUserQuestion') return next(e)
    const current = window
    const dir = await stateDir($)
    const n = await threshold($, dir)
    if (n === null || !current || current.percentUsed < n) return next(e)
    const sid = await $.session.id()
    const resetsAt = current.resetsAt ?? null
    if (sameWindow((await readJson($, `${dir}/budget/acks/${sid}.json`))?.resets_at, resetsAt)) return next(e)
    // One question for every call that arrives while it is open (parallel subagents share it).
    asking ??= (async () => {
      const pending = `${dir}/budget/pending/${sid}.json`
      await $.fs.write(pending, JSON.stringify({ open: true, resets_at: resetsAt, used: current.percentUsed, threshold: n }))
      let answer = ''
      try {
        answer = await $.ui.ask(question(n), { options: [YES, NO], header: 'budget' })
      } catch {
        answer = '' // dismissed, or nobody to ask (a -p run): stop
      }
      await $.fs.write(pending, JSON.stringify({ open: false }))
      if (answer === YES) await $.fs.write(`${dir}/budget/acks/${sid}.json`, JSON.stringify({ resets_at: resetsAt }))
      return answer === YES
    })().finally(() => {
      asking = undefined
    })
    if (await asking) return next(e)
    if (turnId) {
      try {
        await $.turn.abort({ turnId })
      } catch {
        // the turn already ended
      }
    }
    return { deny: `budget: the five-hour usage window reached the ${n}% threshold and the user did not choose to continue. Stop here.` }
  }).catch(($, e, next) => next(e)) // budget's own failure never blocks the call
}
