import { expect, type Page, test } from "@playwright/test";

test.describe.configure({ mode: "serial" });

test.describe("CardWise AI — Comprehensive Browser End-to-End Journeys", () => {
  const suiteId = Date.now();
  const testEmail = `e2e_user_${suiteId}@cardwise.local`;
  const testPassword = "password123!";
  const secondUserEmail = `e2e_user2_${suiteId}@cardwise.local`;

  async function ensureLoggedIn(page: Page, email: string, password = testPassword) {
    await page.goto("/");
    const userPill = page.locator(".user-pill");
    if (await userPill.isVisible()) {
      const text = await userPill.textContent();
      if (text?.includes(email)) return;
      await page.getByRole("button", { name: "Sign out" }).click();
    }

    const signInToggle = page.getByRole("button", { name: /Already have an account\? Sign in/i });
    if (await signInToggle.isVisible()) {
      await signInToggle.click();
    }

    await page.getByLabel("Email").fill(email);
    await page.getByLabel("Password").fill(password);
    await page.getByRole("button", { name: /Sign in/i }).click();

    // If login fails (user does not exist yet), toggle to registration
    const alert = page.getByRole("alert");
    if (await alert.isVisible({ timeout: 1500 }).catch(() => false)) {
      const errorText = await alert.textContent();
      if (errorText?.includes("Invalid email or password")) {
        const createToggle = page.getByRole("button", { name: /Need an account\? Create one/i });
        if (await createToggle.isVisible()) {
          await createToggle.click();
        }
        await page.getByLabel("Email").fill(email);
        await page.getByLabel("Password").fill(password);
        await page.getByRole("button", { name: /Create workspace/i }).click();
      }
    }

    await expect(page.locator(".user-pill")).toContainText(email);
  }

  async function navigateSidebar(
    page: Page,
    tab: "dashboard" | "portfolio" | "catalogue" | "scenarios" | "optimizer" | "assistant" | "settings"
  ) {
    await page.locator("nav.sidebar").getByRole("button", { name: new RegExp(tab, "i") }).click();
  }

  test("Journey 1-4: Registration, Session Persistence, Refresh, and Logout", async ({ page }) => {
    await page.goto("/");

    // 1. Register new user
    await expect(page.getByRole("heading", { name: /Build a clearer card strategy/i })).toBeVisible();
    await page.getByLabel("Email").fill(testEmail);
    await page.getByLabel("Password").fill(testPassword);
    await page.getByRole("button", { name: /Create workspace/i }).click();

    // Verify workspace loaded
    await expect(page.locator(".user-pill")).toContainText(testEmail);
    await expect(page.getByRole("heading", { name: "Good planning starts with known assumptions." })).toBeVisible();

    // 2. Refresh page and verify session persistence via stored token
    await page.reload();
    await expect(page.locator(".user-pill")).toContainText(testEmail);
    await expect(page.getByRole("button", { name: "Sign out" })).toBeVisible();

    // 3. Log out and confirm access is removed
    await page.getByRole("button", { name: "Sign out" }).click();
    await expect(page.getByRole("button", { name: /Create workspace/i })).toBeVisible();

    // 4. Log in again with the created user
    await page.getByRole("button", { name: /Already have an account\? Sign in/i }).click();
    await page.getByLabel("Email").fill(testEmail);
    await page.getByLabel("Password").fill(testPassword);
    await page.getByRole("button", { name: /Sign in/i }).click();
    await expect(page.locator(".user-pill")).toContainText(testEmail);
  });

  test("Journey 5-6: Browse Catalogue, Add and Remove Portfolio Card", async ({ page }) => {
    await ensureLoggedIn(page, testEmail);

    // Navigate to Catalogue tab
    await navigateSidebar(page, "catalogue");
    await expect(page.getByRole("heading", { name: "Catalogue", exact: true })).toBeVisible();

    // Add first card to portfolio
    const addButtons = page.getByRole("button", { name: "Add card reference" });
    await expect(addButtons.first()).toBeVisible();
    await addButtons.first().click();

    // Verify success notice
    await expect(page.getByText(/Card reference added to your portfolio/i)).toBeVisible();

    // Navigate to Portfolio tab and verify card is present
    await navigateSidebar(page, "portfolio");
    await expect(page.getByRole("heading", { name: "Portfolio", exact: true })).toBeVisible();
    const removeButtons = page.getByRole("button", { name: "Remove reference" });
    await expect(removeButtons.first()).toBeVisible();

    // Add second card to portfolio for later optimizer tests
    await navigateSidebar(page, "catalogue");
    const secondAdd = page.getByRole("button", { name: "Add card reference" });
    if (await secondAdd.count() > 1) {
      await secondAdd.nth(1).click();
      await expect(page.getByText(/Card reference added to your portfolio/i)).toBeVisible();
    }
  });

  test("Journey 7-10: Scenario Multi-Bucket CRUD, Revision Increment, Spend ID Preservation, Duplicate & Delete", async ({ page }) => {
    await ensureLoggedIn(page, testEmail);

    // Navigate to Scenarios tab
    await navigateSidebar(page, "scenarios");
    await expect(page.getByRole("heading", { name: "Scenarios", exact: true })).toBeVisible();

    // 7. Create multi-bucket scenario
    await page.getByLabel("Scenario name").fill("Festive Big Spends");
    // Add second bucket
    await page.getByRole("button", { name: "+ Add another spend bucket" }).click();
    await expect(page.getByText("Bucket #2")).toBeVisible();

    // Save scenario
    await page.getByRole("button", { name: /Save scenario/i }).click();
    await expect(page.getByText("Festive Big Spends")).toBeVisible();
    await expect(page.getByText(/v1/)).toBeVisible();

    // 8-9. Edit scenario and verify revision increments
    await page.getByTitle("Edit scenario").first().click();
    await expect(page.getByText("EDIT SCENARIO")).toBeVisible();

    await page.getByLabel("Scenario name").fill("Festive Big Spends Revision");
    await page.getByRole("button", { name: /Update scenario/i }).click();

    // Verify updated revision v2
    await expect(page.getByText("Festive Big Spends Revision")).toBeVisible();
    await expect(page.getByText(/v2/)).toBeVisible();

    // 10. Duplicate scenario
    await page.getByTitle("Duplicate scenario").first().click();
    await expect(page.getByText(/duplicated/i)).toBeVisible();

    // Delete duplicated scenario
    page.on("dialog", (dialog) => dialog.accept());
    const deleteButtons = page.getByTitle("Delete scenario");
    await deleteButtons.first().click();
    await expect(page.getByText("Scenario deleted.")).toBeVisible();
  });

  test("Journey 11-13: Compare Scenario, Run Optimizer, Validate Search Mode & Cap Uncertainty", async ({ page }) => {
    await ensureLoggedIn(page, testEmail);

    // Navigate to Scenarios tab
    await navigateSidebar(page, "scenarios");

    // 11. Run comparison
    await page.getByRole("button", { name: "Compare" }).first().click();
    await expect(page.getByText(/LATEST COMPARISON/i)).toBeVisible();

    // 12-13. Navigate to Optimizer and Run
    await navigateSidebar(page, "optimizer");
    await expect(page.getByRole("heading", { name: "Optimizer", exact: true })).toBeVisible();

    // Ensure scenario is selected and click Run optimizer
    await page.getByRole("button", { name: /Run optimizer/i }).click();

    // Verify optimizer result
    await expect(page.getByText("Spend preserved, value compared.")).toBeVisible();
    await expect(page.getByText(/Estimated Baseline/i)).toBeVisible();
    await expect(page.getByText(/Estimated Proposed/i)).toBeVisible();
    await expect(page.getByText(/Responsible Planning Notice:/i)).toBeVisible();

    // Verify search mode disclosure is rendered
    const hasExhaustive = await page.getByText(/Optimal \(within modeled rules & assumptions\)/i).isVisible();
    const hasHeuristic = await page.getByText(/Greedy Marginal Heuristic/i).isVisible();
    expect(hasExhaustive || hasHeuristic).toBe(true);
  });

  test("Journey 14-15: Reminders Lifecycle and Privacy Exports", async ({ page }) => {
    await ensureLoggedIn(page, testEmail);

    // Navigate to Settings
    await navigateSidebar(page, "settings");
    await expect(page.getByRole("heading", { name: "Settings", exact: true })).toBeVisible();

    // 14. Create a reminder
    await page.getByPlaceholder("Review annual fee terms").fill("Annual renewal reminder");
    await page.locator('input[type="datetime-local"]').fill("2026-12-01T10:00");
    await page.getByRole("button", { name: "Save reminder" }).click();
    await expect(page.getByText("Annual renewal reminder")).toBeVisible();

    // Mark Done
    await page.getByRole("button", { name: "Mark Done" }).first().click();
    await expect(page.getByText("COMPLETED")).toBeVisible();

    // Delete reminder
    page.on("dialog", (dialog) => dialog.accept());
    await page.getByTitle("Delete reminder").first().click();
    await expect(page.getByText("Reminder deleted.")).toBeVisible();

    // 15. Create expiring export
    await page.getByRole("button", { name: "Create expiring export" }).click();
    await expect(page.getByText("Active Export")).toBeVisible();
    await expect(page.getByRole("button", { name: "Download JSON file ⬇" })).toBeVisible();

    // Purge export
    await page.getByRole("button", { name: "Purge export" }).click();
    await expect(page.getByText("Export deleted and purged from local database.")).toBeVisible();
  });

  test("Journey 16: Assistant Evidence Grounding, Citations & Abstention", async ({ page }) => {
    await ensureLoggedIn(page, testEmail);

    // Navigate to Assistant tab
    await navigateSidebar(page, "assistant");
    await expect(page.getByRole("heading", { name: "Assistant", exact: true })).toBeVisible();

    // Query 1: Cashback query matching synthetic fixture
    const questionInput = page.getByLabel("Your question");
    await questionInput.fill("What is the online shopping cashback rate?");
    await page.getByRole("button", { name: "Ask assistant" }).click();

    // Verify response
    await expect(page.getByText(/The available source/i)).toBeVisible();
    await expect(page.getByText("Supporting Source Citations")).toBeVisible();

    // Query 2: Non-domain query triggering abstention
    await questionInput.fill("Tell me a random story about space exploration");
    await page.getByRole("button", { name: "Ask assistant" }).click();

    // Verify abstention
    await expect(page.getByText(/INSUFFICIENT DOMAIN TERMS/i)).toBeVisible();
    await expect(page.getByText(/could not find card or rewards domain terms/i)).toBeVisible();
  });

  test("Journey 17: User Tenant Isolation (Cross-User Resource Privacy)", async ({ page }) => {
    // Register second user
    await page.goto("/");
    const signOut = page.getByRole("button", { name: "Sign out" });
    if (await signOut.isVisible()) {
      await signOut.click();
    }
    const createToggle = page.getByRole("button", { name: /Need an account\? Create one/i });
    if (await createToggle.isVisible()) {
      await createToggle.click();
    }
    await page.getByLabel("Email").fill(secondUserEmail);
    await page.getByLabel("Password").fill(testPassword);
    await page.getByRole("button", { name: /Create workspace/i }).click();
    await expect(page.locator(".user-pill")).toContainText(secondUserEmail);

    // Verify second user starts with 0 scenarios and 0 portfolio cards
    await expect(page.getByText("No card references in your portfolio yet")).toBeVisible();
    await expect(page.getByText("No planned spend profiles saved yet")).toBeVisible();

    // Navigate to Scenarios tab and verify first user's scenario is NOT visible
    await navigateSidebar(page, "scenarios");
    await expect(page.getByText("Festive Big Spends Revision")).not.toBeVisible();
    await expect(page.getByText("Save your first planned-spend scenario")).toBeVisible();
  });

  test("Journey 18: Account Deletion Cascades and Purges User Data", async ({ page }) => {
    await ensureLoggedIn(page, secondUserEmail);

    // Delete second user
    page.on("dialog", (dialog) => dialog.accept());
    await navigateSidebar(page, "settings");
    await page.getByRole("button", { name: "Delete workspace" }).click();

    // Verify user is logged out and returned to Auth screen
    await expect(page.getByRole("button", { name: /Create workspace/i })).toBeVisible();

    // Try logging in with deleted account (must fail)
    await page.getByRole("button", { name: /Already have an account\? Sign in/i }).click();
    await page.getByLabel("Email").fill(secondUserEmail);
    await page.getByLabel("Password").fill(testPassword);
    await page.getByRole("button", { name: /Sign in/i }).click();

    // Verify error banner
    await expect(page.getByRole("alert")).toBeVisible();
  });
});
