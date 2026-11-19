import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

test('global design system exposes the trusted-recruitment tokens and accessible states', async () => {
  const css = await readFile(new URL('../src/style.css', import.meta.url), 'utf8')

  for (const token of ['--rp-navy', '--rp-accent', '--rp-radius-lg', '--rp-focus-ring', '--rp-control-height']) {
    assert.match(css, new RegExp(token))
  }

  assert.match(css, /:focus-visible/)
  assert.match(css, /\.table-scroll/)
  assert.match(css, /\.el-button--primary:not\(\.is-link\):not\(\.is-text\):not\(\.is-plain\)/)
  assert.match(css, /\.el-button\.is-link/)
})
