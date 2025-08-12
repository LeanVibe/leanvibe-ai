import { test, expect } from '@playwright/test'

// Minimal smoke to ensure app renders key pages

test('dashboard renders', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByText(/Dashboard/i)).toBeVisible()
})

test('projects page renders', async ({ page }) => {
  await page.goto('/projects')
  await expect(page.getByText(/Projects/i)).toBeVisible()
})
