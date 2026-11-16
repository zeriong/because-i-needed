import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { Entry } from '../types'

// dashboard on Claude Code: a rule, then one `{icon}label: value` per declared switch (root Rule 11), collected by
// scripts/dashboard.py. z-lab dashboard-lab/run-0.1.0 D01, plugin-platform-lab/mod-interactive-2.1.299 I01.

const entries = atom({ plugin: 'dashboard', key: 'entries' } as const, [] as Entry[])

// Files the status commands name in `watch`, with their contents at the last refresh. A blocked Stop never ends the
// turn, so a tool call that changes one redraws mid-turn (z-lab free-hands-lab eta-probes-r4-2.1.325 T08-T10).
let watched: Record<string, string> = {}

async function readOrEmpty($: EngineInterface, path: string): Promise<string> {
  try {
    return await $.fs.read(path)
  } catch {
    return ''
  }
}

function watchPaths(list: unknown[]): string[] {
  const paths = list.flatMap(raw => {
    const watch = raw && typeof raw === 'object' ? (raw as { watch?: unknown }).watch : null
    return Array.isArray(watch) ? watch.filter((path): path is string => typeof path === 'string') : []
  })
  return [...new Set(paths)]
}

function toEntry(raw: unknown): Entry | null {
  if (!raw || typeof raw !== 'object') return null
  const item = raw as Record<string, unknown>
  const text = (value: unknown): string | null => (typeof value === 'string' && value ? value : null)
  const label = text(item.label)
  const value = text(item.value)
  return label && value
    ? { icon: text(item.icon) ?? '🔹', label, value, where: text(item.where), detail: text(item.detail) }
    : null
}

async function refresh($: EngineInterface): Promise<void> {
  // read before the status runs: a change made while it runs is still caught by the next tool call
  const before: Record<string, string> = {}
  for (const path of Object.keys(watched)) before[path] = await readOrEmpty($, path)
  try {
    const settings = await $.settings.read()
    const enabled = Object.entries(settings.enabledPlugins ?? {})
      .filter(([, isOn]) => isOn === true)
      .map(([key]) => key)
    const ran = await $.process.run([
      'python3', `${$.plugin.root}/scripts/dashboard.py`, '--host', 'claude', '--enabled', enabled.join(','),
      '--cwd', await $.session.cwd(), '--json',
    ])
    const parsed: unknown = ran.exitCode === 0 ? JSON.parse(ran.stdout) : null
    const list = parsed && typeof parsed === 'object' ? (parsed as { entries?: unknown }).entries : []
    const next = Array.isArray(list) ? list.map(toEntry).filter((item): item is Entry => item !== null) : []
    await update($, entries, () => next)
    const seen: Record<string, string> = {}
    for (const path of Array.isArray(list) ? watchPaths(list) : []) {
      seen[path] = before[path] ?? (await readOrEmpty($, path))
    }
    watched = seen
  } catch {
    await update($, entries, () => [])
    watched = {}
  }
}

async function watchedChanged($: EngineInterface): Promise<boolean> {
  for (const [path, seen] of Object.entries(watched)) {
    if ((await readOrEmpty($, path)) !== seen) return true
  }
  return false
}

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    const result = await next(e)
    await refresh($)
    return result
  })

  on('turn.complete', async ($, e, next) => {
    const result = await next(e)
    await refresh($)
    return result
  })

  on('tool.call', async ($, e, next) => {
    const result = await next(e)
    if (await watchedChanged($)) await refresh($)
    return result
  }).catch(($, e, next) => next(e))

  on('session.measure', async ($, e, next) => {
    if (e.changed.includes('rateLimits')) await refresh($)
    return next(e)
  })

  on('ui.render', { component: 'AbovePrompt' }, async ($, e, next) => {
    const list = await read($, entries)
    if (!list.length || e.props.hasSurvey) return next(e)
    const { Box, Text } = $.ui.resolve(e)
    return (
      <Box flexDirection="column">
        <Text dimColor>{'─'.repeat(Math.max(e.props.bodyColumns, 1))}</Text>
        <Box flexWrap="wrap" columnGap={3}>
          {list.map(item => (
            <Text key={item.label}>
              {item.icon}
              <Text bold>{item.label}:</Text> {item.value}
              {item.where ? <Text dimColor> ({item.where})</Text> : null}
              {item.detail ? <Text dimColor> · {item.detail}</Text> : null}
            </Text>
          ))}
        </Box>
      </Box>
    )
  })
}
