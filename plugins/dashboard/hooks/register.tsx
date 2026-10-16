import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { Entry } from '../types'

// dashboard on Claude Code: a rule, then one `{icon}label: value` per declared switch (root Rule 11), collected by
// scripts/dashboard.py. z-lab dashboard-lab/run-0.1.0 D01, plugin-platform-lab/mod-interactive-2.1.299 I01.

const entries = atom({ plugin: 'dashboard', key: 'entries' } as const, [] as Entry[])

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
  } catch {
    await update($, entries, () => [])
  }
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
