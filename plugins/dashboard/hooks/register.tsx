import { atom, read, update } from 'claude-code'
import type { EngineInterface, Register } from 'claude-code'

import type { Line } from '../types'

// dashboard on Claude Code: one band above the prompt with the state every enabled because-i-needed plugin declares
// (root Rule 11), collected by scripts/dashboard.py. z-lab plugin-platform-lab/mod-interactive-2.1.299 I01,
// mod-dual-host-2.1.299 M06.

const line = atom({ plugin: 'dashboard', key: 'line' } as const, '' as Line)

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
    const parsed: unknown = JSON.parse(ran.stdout)
    const next = ran.exitCode === 0 && parsed && typeof parsed === 'object' ? (parsed as { line?: unknown }).line : ''
    await update($, line, () => (typeof next === 'string' ? next : ''))
  } catch {
    await update($, line, () => '')
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
    const text = await read($, line)
    if (!text || e.props.hasSurvey) return next(e)
    const { Box, Text } = $.ui.resolve(e)
    return (
      <Box>
        <Text dimColor>{text}</Text>
      </Box>
    )
  })
}
