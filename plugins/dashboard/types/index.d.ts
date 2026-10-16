export type Entry = {
  icon: string
  label: string
  value: string
  where: string | null
  detail: string | null
}

declare module 'claude-code' {
  interface PluginState {
    dashboard: { entries: Entry[] }
  }
}
