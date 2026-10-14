export type Line = string

declare module 'claude-code' {
  interface PluginState {
    dashboard: { line: Line }
  }
}
