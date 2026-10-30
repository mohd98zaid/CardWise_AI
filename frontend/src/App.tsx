import { FormEvent, useEffect, useState } from "react";

import {
  addPortfolioCard,
  askAssistant,
  compareScenario,
  createExport,
  createReminder,
  createScenario,
  deleteAccount,
  deleteExport,
  deleteReminder,
  deleteScenario,
  duplicateScenario,
  getCardRules,
  getCards,
  getMe,
  getPortfolio,
  getReminders,
  getScenarios,
  login,
  logout,
  register,
  removePortfolioCard,
  runOptimizer,
  updateReminder,
  updateScenario,
} from "./api";
import type {
  AssistantResult,
  AuthResponse,
  CardRule,
  CardVariant,
  Comparison,
  ExportJobResponse,
  OptimizerResult,
  Reminder,
  Scenario,
  SpendInput,
  User,
} from "./types";

const currency = new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 2 });
const money = (value: string | number | null | undefined) => value === null || value === undefined ? "—" : currency.format(Number(value));
type Tab = "dashboard" | "portfolio" | "catalogue" | "scenarios" | "optimizer" | "assistant" | "settings";

function App() {
  const [token, setToken] = useState(() => localStorage.getItem("cardwise_token"));
  const [user, setUser] = useState<User | null>(null);
  const [authLoading, setAuthLoading] = useState(Boolean(token));
  const [authError, setAuthError] = useState<string | null>(null);

  async function finishAuth(response: AuthResponse) {
    localStorage.setItem("cardwise_token", response.access_token);
    setToken(response.access_token);
    setUser(response.user);
  }

  useEffect(() => {
    if (!token) { setAuthLoading(false); return; }
    getMe(token).then(setUser).catch(() => { localStorage.removeItem("cardwise_token"); setToken(null); }).finally(() => setAuthLoading(false));
  }, [token]);

  async function handleAuth(email: string, password: string, mode: "login" | "register") {
    setAuthError(null);
    try { await finishAuth(await (mode === "login" ? login(email, password) : register(email, password))); }
    catch (error) { setAuthError(error instanceof Error ? error.message : "Authentication failed."); }
  }

  if (authLoading) return <div className="auth-loading">Loading your workspace…</div>;
  if (!token || !user) return <AuthScreen onSubmit={handleAuth} error={authError} />;
  return <Workspace token={token} user={user} onLogout={async () => { await logout(token); localStorage.removeItem("cardwise_token"); setToken(null); setUser(null); }} />;
}

function AuthScreen({ onSubmit, error }: { onSubmit: (email: string, password: string, mode: "login" | "register") => void; error: string | null }) {
  const [mode, setMode] = useState<"login" | "register">("register");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  return <main className="auth-page"><div className="auth-card">
    <a className="brand" href="/"><span className="brand-mark">cw</span><span>CardWise <em>AI</em></span></a>
    <div className="eyebrow auth-eyebrow">EVIDENCE BEFORE CONFIDENCE</div>
    <h1>{mode === "register" ? "Build a clearer card strategy." : "Welcome back."}</h1>
    <p className="auth-copy">Compare planned spending across exact card variants. No full card numbers, issuer passwords, or payment credentials.</p>
    <form onSubmit={(event) => { event.preventDefault(); onSubmit(email, password, mode); }}>
      <label>Email<input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required /></label>
      <label>Password<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} minLength={8} required /></label>
      {error && <p className="error" role="alert">{error}</p>}
      <button className="primary-button" type="submit">{mode === "register" ? "Create workspace" : "Sign in"}<span>↗</span></button>
    </form>
    <button className="text-button" onClick={() => setMode(mode === "register" ? "login" : "register")}>
      {mode === "register" ? "Already have an account? Sign in" : "Need an account? Create one"}
    </button>
    <div className="auth-demo">Synthetic local MVP · fictional terms only</div>
  </div></main>;
}

function Workspace({ token, user, onLogout }: { token: string; user: User; onLogout: () => void }) {
  const [tab, setTab] = useState<Tab>("dashboard");
  const [cards, setCards] = useState<CardVariant[]>([]);
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [portfolio, setPortfolio] = useState<Array<{ id?: string; card_variant_id: string; display_name: string; nickname?: string | null }>>([]);
  const [reminders, setReminders] = useState<Reminder[]>([]);
  const [comparison, setComparison] = useState<Comparison | null>(null);
  const [optimizer, setOptimizer] = useState<OptimizerResult | null>(null);
  const [latestExport, setLatestExport] = useState<ExportJobResponse | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  async function reload() {
    setLoading(true);
    try {
      const [loadedCards, loadedScenarios, loadedPortfolio, loadedReminders] = await Promise.all([
        getCards(),
        getScenarios(token),
        getPortfolio(token),
        getReminders(token),
      ]);
      setCards(loadedCards);
      setScenarios(loadedScenarios);
      setPortfolio(loadedPortfolio);
      setReminders(loadedReminders);
      setError(null);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Could not load workspace.");
    } finally {
      setLoading(false);
    }
  }
  useEffect(() => { void reload(); }, [token]);

  async function saveScenario(payload: { name: string; scenario_date: string; currency: string; spend: SpendInput[] }) {
    try {
      const created = await createScenario(token, payload);
      setScenarios((items) => [created, ...items]);
      setTab("scenarios");
      setNotice("Scenario saved. You can now compare it or send it to the optimizer.");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Scenario could not be saved.");
    }
  }

  async function handleUpdateScenario(scenarioId: string, payload: { name?: string; scenario_date?: string; currency?: string; spend?: SpendInput[] }) {
    try {
      const updated = await updateScenario(token, scenarioId, payload);
      setScenarios((items) => items.map((s) => (s.id === scenarioId ? updated : s)));
      setNotice(`Scenario updated to revision ${updated.revision}. Spend IDs and allocations preserved.`);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Scenario update failed.");
    }
  }

  async function handleDeleteScenario(scenarioId: string) {
    try {
      await deleteScenario(token, scenarioId);
      setScenarios((items) => items.filter((s) => s.id !== scenarioId));
      setNotice("Scenario deleted.");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Scenario deletion failed.");
    }
  }

  async function compare(id: string, cardIds: string[]) {
    try {
      setComparison(await compareScenario(token, id, cardIds));
      setTab("scenarios");
      setNotice("Comparison calculated from the current scenario revision.");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Comparison failed.");
    }
  }

  async function optimize(id: string, cardIds: string[]) {
    if (cardIds.length === 0) {
      setError("Please add at least one owned card to your portfolio before running the optimizer.");
      setTab("catalogue");
      return;
    }
    try {
      setOptimizer(await runOptimizer(token, id, cardIds));
      setTab("optimizer");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Optimization failed.");
    }
  }

  async function handleUpdateReminder(reminderId: string, payload: { label?: string; due_at?: string; status?: string }) {
    try {
      const updated = await updateReminder(token, reminderId, payload);
      setReminders((items) => items.map((r) => (r.id === reminderId ? updated : r)));
      setNotice("Reminder updated.");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Failed to update reminder.");
    }
  }

  async function handleExport() {
    try {
      const exportFile = await createExport(token);
      setLatestExport(exportFile as unknown as ExportJobResponse);
      setNotice(`Export created — expires ${new Date(exportFile.expires_at).toLocaleString()}. You can now download or inspect it.`);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Failed to create export.");
    }
  }

  async function handleDeleteExport(exportId: string) {
    try {
      await deleteExport(token, exportId);
      if (latestExport?.id === exportId) {
        setLatestExport(null);
      }
      setNotice("Export deleted and purged from local database.");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Failed to delete export.");
    }
  }

  return (
    <main className="app-shell">
      <header className="app-header">
        <a className="brand" href="#dashboard" onClick={() => setTab("dashboard")}>
          <span className="brand-mark">cw</span>
          <span>CardWise <em>AI</em></span>
        </a>
        <div className="header-actions">
          <span className="user-pill">{user.email}</span>
          <button className="text-button" onClick={onLogout}>Sign out</button>
        </div>
      </header>
      <div className="app-layout">
        <nav className="sidebar" aria-label="Main navigation">
          {(["dashboard", "portfolio", "catalogue", "scenarios", "optimizer", "assistant", "settings"] as Tab[]).map((item) => (
            <button
              key={item}
              className={tab === item ? "nav-item active" : "nav-item"}
              onClick={() => setTab(item)}
            >
              <span className={`nav-icon ${item}`}>
                {item === "dashboard" ? "⌂" : item === "portfolio" ? "▣" : item === "catalogue" ? "▦" : item === "scenarios" ? "⌁" : item === "optimizer" ? "↗" : item === "assistant" ? "✦" : "⚙"}
              </span>
              {item[0].toUpperCase() + item.slice(1)}
            </button>
          ))}
        </nav>
        <section className="content">
          <div className="content-top">
            <div>
              <div className="eyebrow">PRIVATE WORKSPACE</div>
              <h1>{tab === "dashboard" ? "Good planning starts with known assumptions." : tab[0].toUpperCase() + tab.slice(1)}</h1>
            </div>
            <span className="alpha-badge">{loading ? "Updating…" : "Synthetic alpha"}</span>
          </div>
          {notice && <div className="success-banner" role="status">✓ {notice}<button onClick={() => setNotice(null)}>×</button></div>}
          {error && (
            <div className="error-banner" role="alert">
              <span>{error}</span>
              <div style={{ display: "flex", gap: "0.5rem" }}>
                <button className="text-button" style={{ color: "inherit", textDecoration: "underline" }} onClick={() => void reload()}>
                  Retry
                </button>
                <button onClick={() => setError(null)}>×</button>
              </div>
            </div>
          )}
          {tab === "dashboard" && (
            <Dashboard
              portfolio={portfolio}
              scenarios={scenarios}
              reminders={reminders}
              onNavigate={setTab}
            />
          )}
          {tab === "portfolio" && (
            <Portfolio
              cards={cards}
              portfolio={portfolio}
              onRemove={async (id) => {
                try {
                  await removePortfolioCard(token, id);
                  await reload();
                  setNotice("Card reference removed from your portfolio.");
                } catch (e) {
                  setError(e instanceof Error ? e.message : "Failed to remove card.");
                }
              }}
            />
          )}
          {tab === "catalogue" && (
            <Catalogue
              cards={cards}
              onAdd={async (id) => {
                try {
                  await addPortfolioCard(token, id);
                  await reload();
                  setNotice("Card reference added to your portfolio.");
                } catch (e) {
                  setError(e instanceof Error ? e.message : "Failed to add card.");
                }
              }}
            />
          )}
          {tab === "scenarios" && (
            <Scenarios
              cards={cards}
              scenarios={scenarios}
              comparison={comparison}
              onSave={saveScenario}
              onUpdate={handleUpdateScenario}
              onDelete={handleDeleteScenario}
              onDuplicate={async (id) => {
                try {
                  const copy = await duplicateScenario(token, id);
                  setScenarios((items) => [copy, ...items]);
                  setNotice("Scenario duplicated with allocations preserved.");
                } catch (e) {
                  setError(e instanceof Error ? e.message : "Failed to duplicate scenario.");
                }
              }}
              onCompare={compare}
              onOptimize={(id) => optimize(id, portfolio.map((item) => item.card_variant_id))}
            />
          )}
          {tab === "optimizer" && (
            <Optimizer
              scenarios={scenarios}
              cards={cards}
              portfolio={portfolio}
              result={optimizer}
              onRun={optimize}
            />
          )}
          {tab === "assistant" && <Assistant token={token} />}
          {tab === "settings" && (
            <Settings
              reminders={reminders}
              latestExport={latestExport}
              onReminder={async (label, dueAt) => {
                try {
                  const reminder = await createReminder(token, label, dueAt);
                  setReminders((items) => [...items, reminder]);
                  setNotice("Reminder saved.");
                } catch (e) {
                  setError(e instanceof Error ? e.message : "Failed to save reminder.");
                }
              }}
              onUpdateReminder={handleUpdateReminder}
              onDeleteReminder={async (id) => {
                try {
                  await deleteReminder(token, id);
                  setReminders((items) => items.filter((r) => r.id !== id));
                  setNotice("Reminder deleted.");
                } catch (e) {
                  setError(e instanceof Error ? e.message : "Failed to delete reminder.");
                }
              }}
              onExport={handleExport}
              onDeleteExport={handleDeleteExport}
              onDelete={async () => {
                try {
                  await deleteAccount(token);
                  onLogout();
                } catch (e) {
                  setError(e instanceof Error ? e.message : "Failed to delete account.");
                }
              }}
            />
          )}
        </section>
      </div>
      <footer>
        <span>CardWise AI · Estimates, not guarantees</span>
        <span>Calculator engine 0.1.0</span>
      </footer>
    </main>
  );
}

function Dashboard({
  portfolio,
  scenarios,
  reminders,
  onNavigate,
}: {
  portfolio: Array<{ id?: string; card_variant_id: string; display_name: string }>;
  scenarios: Scenario[];
  reminders: Reminder[];
  onNavigate: (tab: Tab) => void;
}) {
  return (
    <>
      <div className="dashboard-grid">
        <div className="dashboard-card accent-card">
          <span className="card-kicker">YOUR PORTFOLIO</span>
          <strong>{portfolio.length}</strong>
          <p>
            {portfolio.length === 0
              ? "No card references in your portfolio yet"
              : portfolio.length === 1
              ? "1 active card reference in your portfolio"
              : `${portfolio.length} active card references in your portfolio`}
          </p>
          <button onClick={() => onNavigate(portfolio.length > 0 ? "portfolio" : "catalogue")}>
            {portfolio.length > 0 ? "Manage portfolio →" : "Browse catalogue to add cards →"}
          </button>
        </div>
        <div className="dashboard-card">
          <span className="card-kicker">SAVED SCENARIOS</span>
          <strong>{scenarios.length}</strong>
          <p>
            {scenarios.length === 0
              ? "No planned spend profiles saved yet"
              : scenarios.length === 1
              ? "1 planned spending profile"
              : `${scenarios.length} planned spending profiles`}
          </p>
          <button onClick={() => onNavigate("scenarios")}>
            {scenarios.length > 0 ? "Open scenarios →" : "Build your first scenario →"}
          </button>
        </div>
        <div className="dashboard-card">
          <span className="card-kicker">REMINDERS</span>
          <strong>{reminders.length}</strong>
          <p>
            {reminders.length === 0
              ? "No active informational reminders"
              : reminders.length === 1
              ? "1 informational reminder set"
              : `${reminders.length} informational reminders set`}
          </p>
          <button onClick={() => onNavigate("settings")}>
            {reminders.length > 0 ? "Manage reminders →" : "Set a reminder in Settings →"}
          </button>
        </div>
      </div>
      {portfolio.length === 0 && (
        <div className="empty-box" style={{ marginTop: "16px" }}>
          <strong>Your portfolio is empty.</strong> Add card variants from the Catalogue to begin evaluating rewards.
          <div style={{ marginTop: "10px" }}>
            <button className="secondary-button" onClick={() => onNavigate("catalogue")}>Browse catalogue</button>
          </div>
        </div>
      )}
      <div className="dashboard-lower">
        <div className="panel intro-panel">
          <div className="eyebrow">HOW CARDWISE WORKS</div>
          <h2>Every estimate leaves a trail.</h2>
          <p>
            Rules are typed data. Calculations use Decimal arithmetic. Unknown cap usage stays visible
            instead of quietly becoming zero.
          </p>
          <div className="principle-list">
            <span><b>01</b> Select an exact variant</span>
            <span><b>02</b> Enter existing planned spend</span>
            <span><b>03</b> Inspect the evidence and trace</span>
          </div>
        </div>
        <div className="panel disclosure-panel">
          <span className="notice-icon">i</span>
          <strong>Synthetic local MVP</strong>
          <p>
            No real issuer terms are activated. The demo cards are fictional and exist only for
            testing the calculation flow.
          </p>
        </div>
      </div>
    </>
  );
}

function Catalogue({ cards, onAdd }: { cards: CardVariant[]; onAdd: (id: string) => void }) {
  const [selectedCardId, setSelectedCardId] = useState<string | null>(null);
  const [rules, setRules] = useState<CardRule[]>([]);
  const [loadingRules, setLoadingRules] = useState(false);
  const [rulesError, setRulesError] = useState<string | null>(null);

  async function loadRules(cardId: string) {
    setLoadingRules(true);
    setRulesError(null);
    try {
      const data = await getCardRules(cardId);
      setRules(data);
    } catch (err) {
      setRules([]);
      setRulesError(err instanceof Error ? err.message : "Failed to load card rules.");
    } finally {
      setLoadingRules(false);
    }
  }

  async function handleSelectCard(cardId: string) {
    if (selectedCardId === cardId) {
      setSelectedCardId(null);
      setRules([]);
      setRulesError(null);
      return;
    }
    setSelectedCardId(cardId);
    await loadRules(cardId);
  }

  return (
    <div className="catalogue-grid">
      {cards.map((card) => (
        <article className="panel catalogue-card" key={card.id}>
          <div className="card-art">
            <span>cw</span>
            <small>{card.network}</small>
          </div>
          <div className="card-kicker">{card.issuer_name} · {card.market}</div>
          <h2>{card.display_name}</h2>
          <p>{card.description}</p>
          <div className="tag-row">
            <span className="tag synthetic">{card.verification_status}</span>
            <span className="tag">From {card.valid_from}</span>
          </div>
          <div style={{ display: "flex", gap: "0.5rem", marginTop: "0.5rem" }}>
            <button className="secondary-button" onClick={() => onAdd(card.id)}>
              Add card reference
            </button>
            <button className="text-button" onClick={() => handleSelectCard(card.id)}>
              {selectedCardId === card.id ? "Hide rules ▲" : "View rules ▼"}
            </button>
          </div>
          {selectedCardId === card.id && (
            <div className="card-detail-box" style={{ marginTop: "1rem", padding: "0.75rem", background: "var(--color-bg-subtle, #f8f9fa)", borderRadius: "4px" }}>
              <h4 style={{ margin: "0 0 0.5rem" }}>Card Rules & Verification</h4>
              {loadingRules ? (
                <p className="muted">Loading rules...</p>
              ) : rulesError ? (
                <div style={{ margin: "0.5rem 0", color: "#c0392b" }}>
                  <p style={{ margin: "0 0 0.5rem", fontSize: "0.9rem" }}>{rulesError}</p>
                  <button
                    className="secondary-button"
                    style={{ fontSize: "0.8rem", padding: "0.25rem 0.5rem" }}
                    onClick={() => loadRules(card.id)}
                  >
                    Retry loading rules
                  </button>
                </div>
              ) : rules.length === 0 ? (
                <p className="muted">No published rules currently listed for this variant.</p>
              ) : (
                rules.map((rule) => (
                  <div key={rule.id} style={{ marginBottom: "0.5rem", borderBottom: "1px solid #eee", paddingBottom: "0.5rem" }}>
                    <div style={{ display: "flex", justifyContent: "space-between" }}>
                      <strong>{rule.rule_type.replace("_", " ")}</strong>
                      <span className={`tag ${rule.verification_status}`}>{rule.verification_status}</span>
                    </div>
                    <small>Effective: {rule.effective_from} {rule.effective_to ? `to ${rule.effective_to}` : "onwards"}</small>
                    <pre style={{ fontSize: "0.8rem", overflowX: "auto" }}>{JSON.stringify(rule.parameters, null, 2)}</pre>
                    {rule.notes && <p style={{ fontSize: "0.85rem", fontStyle: "italic", margin: "0.25rem 0" }}>{rule.notes}</p>}
                    {rule.evidence_ids.length > 0 && (
                      <small className="muted">Evidence IDs: {rule.evidence_ids.join(", ")}</small>
                    )}
                  </div>
                ))
              )}
              <small className="muted" style={{ display: "block", marginTop: "0.5rem" }}>
                ⚠️ Fictional / synthetic rule fixture for local alpha only.
              </small>
            </div>
          )}
        </article>
      ))}
    </div>
  );
}

function Portfolio({
  cards,
  portfolio,
  onRemove,
}: {
  cards: CardVariant[];
  portfolio: Array<{ id?: string; card_variant_id: string; display_name: string; nickname?: string | null }>;
  onRemove: (id: string) => void;
}) {
  return (
    <div className="catalogue-grid">
      {portfolio.length === 0 ? (
        <div className="panel empty-box">No card references yet. Add an exact variant from the Catalogue.</div>
      ) : (
        portfolio.map((item) => (
          <article className="panel catalogue-card" key={item.id ?? item.card_variant_id}>
            <div className="card-art">
              <span>cw</span>
              <small>Owned reference</small>
            </div>
            <div className="card-kicker">PORTFOLIO REFERENCE</div>
            <h2>{cards.find((card) => card.id === item.card_variant_id)?.display_name ?? item.display_name}</h2>
            <p>{item.nickname || "No nickname set."}</p>
            <div className="tag-row">
              <span className="tag synthetic">No credentials stored</span>
            </div>
            <button className="danger-button" onClick={() => item.id && onRemove(item.id)}>
              Remove reference
            </button>
          </article>
        ))
      )}
    </div>
  );
}

type SpendBucketForm = {
  id?: string;
  category: string;
  channel: string;
  amount: string;
  is_fixed: boolean;
  cap_unknown: boolean;
  cap_usage: string;
  point_value: string;
};

const defaultBucket = (): SpendBucketForm => ({
  category: "online_shopping",
  channel: "online_card",
  amount: "5000",
  is_fixed: false,
  cap_unknown: false,
  cap_usage: "0",
  point_value: "",
});

function Scenarios({
  cards,
  scenarios,
  comparison,
  onSave,
  onUpdate,
  onDelete,
  onDuplicate,
  onCompare,
  onOptimize,
}: {
  cards: CardVariant[];
  scenarios: Scenario[];
  comparison: Comparison | null;
  onSave: (payload: { name: string; scenario_date: string; currency: string; spend: SpendInput[] }) => void;
  onUpdate: (id: string, payload: { name?: string; scenario_date?: string; currency?: string; spend?: SpendInput[] }) => void;
  onDelete: (id: string) => void;
  onDuplicate: (id: string) => void;
  onCompare: (id: string, cards: string[]) => void;
  onOptimize: (id: string) => void;
}) {
  const [editingScenarioId, setEditingScenarioId] = useState<string | null>(null);
  const [name, setName] = useState("Monthly online plan");
  const [date, setDate] = useState("2026-06-01");
  const [buckets, setBuckets] = useState<SpendBucketForm[]>([defaultBucket()]);

  function startEdit(scenario: Scenario) {
    setEditingScenarioId(scenario.id);
    setName(scenario.name);
    setDate(scenario.scenario_date);
    setBuckets(
      scenario.spend.map((item) => ({
        id: item.id,
        category: item.category,
        channel: item.channel,
        amount: String(item.amount),
        is_fixed: Boolean(item.is_fixed),
        cap_unknown: item.cap_knowledge_state === "unknown",
        cap_usage: item.cap_usage || "0",
        point_value: item.point_value_per_point || "",
      }))
    );
  }

  function cancelEdit() {
    setEditingScenarioId(null);
    setName("Monthly online plan");
    setDate("2026-06-01");
    setBuckets([defaultBucket()]);
  }

  function addBucket() {
    setBuckets((prev) => [...prev, defaultBucket()]);
  }

  function removeBucket(index: number) {
    if (buckets.length > 1) {
      setBuckets((prev) => prev.filter((_, idx) => idx !== index));
    }
  }

  function updateBucket(index: number, patch: Partial<SpendBucketForm>) {
    setBuckets((prev) =>
      prev.map((b, idx) => (idx === index ? { ...b, ...patch } : b))
    );
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!name.trim()) return;

    const spendPayload: SpendInput[] = buckets.map((b) => ({
      id: b.id,
      category: b.category,
      channel: b.channel,
      amount: b.amount,
      is_fixed: b.is_fixed,
      cap_usage: b.cap_unknown ? null : b.cap_usage || "0",
      cap_knowledge_state: b.cap_unknown ? "unknown" : "known",
      point_value_per_point: b.point_value ? b.point_value : null,
    }));

    if (editingScenarioId) {
      onUpdate(editingScenarioId, {
        name,
        scenario_date: date,
        currency: "INR",
        spend: spendPayload,
      });
      cancelEdit();
    } else {
      onSave({
        name,
        scenario_date: date,
        currency: "INR",
        spend: spendPayload,
      });
    }
  }

  return (
    <div className="scenario-layout">
      <form className="panel scenario-form" onSubmit={handleSubmit}>
        <div className="eyebrow">{editingScenarioId ? "EDIT SCENARIO" : "SCENARIO BUILDER"}</div>
        <h2>{editingScenarioId ? "Update planned spend" : "Plan existing spend"}</h2>
        <p className="muted">
          The optimizer preserves this spend. Multiple buckets are supported under shared card caps.
        </p>

        <label>
          Scenario name
          <input value={name} onChange={(event) => setName(event.target.value)} required />
        </label>
        <label>
          Scenario date
          <input type="date" value={date} onChange={(event) => setDate(event.target.value)} required />
        </label>

        <div style={{ marginTop: "16px", marginBottom: "8px" }}>
          <strong style={{ fontSize: "13px", color: "#22392e" }}>
            Spending Buckets ({buckets.length})
          </strong>
        </div>

        {buckets.map((bucket, index) => (
          <div className="spend-bucket-card" key={index}>
            <div className="spend-bucket-header">
              <span>Bucket #{index + 1} {bucket.id ? `(ID: ${bucket.id.slice(0, 8)}…)` : ""}</span>
              {buckets.length > 1 && (
                <button
                  type="button"
                  className="text-button"
                  style={{ color: "#a44e40", padding: 0 }}
                  onClick={() => removeBucket(index)}
                >
                  Remove bucket ✕
                </button>
              )}
            </div>

            <div className="two-column">
              <label>
                Category
                <select
                  value={bucket.category}
                  onChange={(e) => updateBucket(index, { category: e.target.value })}
                >
                  <option value="online_shopping">Online shopping</option>
                  <option value="offline_retail">Offline retail</option>
                  <option value="groceries">Groceries</option>
                  <option value="dining">Dining</option>
                  <option value="fuel">Fuel</option>
                  <option value="utilities">Utilities and bills</option>
                  <option value="travel">Travel and hotels</option>
                  <option value="transport">Transport</option>
                  <option value="healthcare">Healthcare</option>
                  <option value="education">Education</option>
                  <option value="entertainment">Entertainment and subscriptions</option>
                  <option value="upi">UPI</option>
                  <option value="other">Other</option>
                  <option value="unknown">Unknown</option>
                </select>
              </label>

              <label>
                Channel
                <select
                  value={bucket.channel}
                  onChange={(e) => updateBucket(index, { channel: e.target.value })}
                >
                  <option value="online_card">Online card</option>
                  <option value="in_store_card">In-store card</option>
                  <option value="pos_card">POS card</option>
                  <option value="upi">UPI</option>
                  <option value="wallet">Wallet</option>
                  <option value="contactless">Contactless</option>
                  <option value="emi">EMI</option>
                  <option value="subscription">Subscription</option>
                  <option value="other">Other</option>
                  <option value="unknown">Unknown</option>
                </select>
              </label>
            </div>

            <div className="two-column">
              <label>
                Planned spend
                <div className="input-with-prefix">
                  <span>₹</span>
                  <input
                    type="number"
                    min="0.01"
                    step="0.01"
                    value={bucket.amount}
                    onChange={(e) => updateBucket(index, { amount: e.target.value })}
                    required
                  />
                </div>
              </label>

              <label>
                Point value <span className="optional">optional</span>
                <div className="input-with-prefix">
                  <span>₹</span>
                  <input
                    type="number"
                    min="0"
                    step="0.0001"
                    placeholder="Unknown"
                    value={bucket.point_value}
                    onChange={(e) => updateBucket(index, { point_value: e.target.value })}
                  />
                </div>
              </label>
            </div>

            <div style={{ display: "grid", gap: "8px", marginTop: "4px" }}>
              <label className="check-label">
                <input
                  type="checkbox"
                  checked={bucket.is_fixed}
                  onChange={(e) => updateBucket(index, { is_fixed: e.target.checked })}
                />
                Fixed allocation (lock to baseline card during optimization)
              </label>

              <label className="check-label">
                <input
                  type="checkbox"
                  checked={bucket.cap_unknown}
                  onChange={(e) => updateBucket(index, { cap_unknown: e.target.checked })}
                />
                Prior monthly cap usage is unknown
              </label>
            </div>
          </div>
        ))}

        <div style={{ display: "flex", gap: "8px", marginTop: "10px" }}>
          <button type="button" className="secondary-button" onClick={addBucket}>
            + Add another spend bucket
          </button>
        </div>

        <div style={{ display: "flex", gap: "10px", marginTop: "16px" }}>
          <button className="primary-button" type="submit">
            {editingScenarioId ? "Update scenario" : "Save scenario"} <span>↗</span>
          </button>
          {editingScenarioId && (
            <button
              type="button"
              className="secondary-button"
              style={{ marginTop: "7px" }}
              onClick={cancelEdit}
            >
              Cancel edit
            </button>
          )}
        </div>
      </form>

      <div className="scenario-list">
        <div className="section-title">
          <div>
            <div className="eyebrow">SAVED INPUTS</div>
            <h2>Your scenarios</h2>
          </div>
          <span>{scenarios.length}</span>
        </div>

        {scenarios.length === 0 ? (
          <div className="empty-box">Save your first planned-spend scenario to compare cards.</div>
        ) : (
          scenarios.map((scenario) => {
            const totalSpend = scenario.spend.reduce((sum, item) => sum + Number(item.amount), 0);
            return (
              <div className="scenario-row" key={scenario.id}>
                <div>
                  <strong>
                    {scenario.name} <span className="tag" style={{ marginLeft: "4px" }}>v{scenario.revision}</span>
                  </strong>
                  <span>
                    {scenario.scenario_date} · {scenario.spend.length} bucket(s) · Total: {money(totalSpend)}
                  </span>
                </div>
                <div className="row-actions">
                  <button onClick={() => onCompare(scenario.id, cards.map((card) => card.id))}>
                    Compare
                  </button>
                  <button onClick={() => onOptimize(scenario.id)}>
                    Optimize
                  </button>
                  <button title="Edit scenario" onClick={() => startEdit(scenario)}>
                    ✏️ Edit
                  </button>
                  <button
                    aria-label={`Duplicate ${scenario.name}`}
                    title="Duplicate scenario"
                    onClick={() => onDuplicate(scenario.id)}
                  >
                    ⧉
                  </button>
                  <button
                    title="Delete scenario"
                    style={{ color: "#a44e40" }}
                    onClick={() => {
                      if (window.confirm(`Are you sure you want to delete scenario "${scenario.name}"? This will permanently remove its allocations and trace history.`)) {
                        onDelete(scenario.id);
                      }
                    }}
                  >
                    🗑️
                  </button>
                </div>
              </div>
            );
          })
        )}

        {comparison && <ComparisonView comparison={comparison} cards={cards} />}
      </div>
    </div>
  );
}

function ComparisonView({ comparison, cards }: { comparison: Comparison; cards: CardVariant[] }) {
  return (
    <div className="comparison-box">
      <div className="eyebrow">LATEST COMPARISON (Rev: {comparison.revision})</div>
      {comparison.results.map((result) => (
        <div key={result.card_variant_id}>
          <div className="compare-row">
            <span>
              {cards.find((card) => card.id === result.card_variant_id)?.display_name ?? result.card_variant_id}
            </span>
            <strong>{money(result.estimated_net_value)}</strong>
          </div>
          <details className="trace">
            <summary>
              View bucket trace <span>{result.buckets.length} buckets</span>
            </summary>
            {result.buckets.map((bucket, index) => (
              <div className="allocation-row" key={index}>
                <span>{bucket.status.replaceAll("_", " ")}</span>
                <strong>{bucket.trace.length} steps</strong>
              </div>
            ))}
          </details>
        </div>
      ))}
      <p className="muted">
        Values may be conservative or uncertain when cap usage is not supplied. Every bucket retains its rule and evidence trace.
      </p>
    </div>
  );
}

function Optimizer({
  scenarios,
  cards,
  portfolio,
  result,
  onRun,
}: {
  scenarios: Scenario[];
  cards: CardVariant[];
  portfolio: Array<{ id?: string; card_variant_id: string }>;
  result: OptimizerResult | null;
  onRun: (id: string, cards: string[]) => void;
}) {
  const [scenarioId, setScenarioId] = useState(scenarios[0]?.id ?? "");
  const ownedIds = new Set(portfolio.map((item) => item.card_variant_id));
  const ownedCards = cards.filter((card) => ownedIds.has(card.id));
  const [selected, setSelected] = useState<string[]>(portfolio.map((item) => item.card_variant_id));

  useEffect(() => {
    if (!scenarioId && scenarios[0]) setScenarioId(scenarios[0].id);
  }, [scenarios, scenarioId]);

  useEffect(() => {
    const validOwned = portfolio.map((item) => item.card_variant_id);
    setSelected((prev) => {
      const filtered = prev.filter((id) => validOwned.includes(id));
      return filtered.length > 0 ? filtered : validOwned;
    });
  }, [portfolio]);

  return (
    <div className="optimizer-layout">
      <div className="panel">
        <div className="eyebrow">CONSTRAINED ALLOCATION</div>
        <h2>Optimize existing spend</h2>
        <p className="muted">
          Only owned cards in your portfolio are eligible. Total planned spend is preserved per bucket.
        </p>
        <label>
          Scenario
          <select value={scenarioId} onChange={(event) => setScenarioId(event.target.value)}>
            {scenarios.map((scenario) => (
              <option key={scenario.id} value={scenario.id}>
                {scenario.name}
              </option>
            ))}
          </select>
        </label>
        <fieldset>
          <legend>Owned portfolio cards available to optimizer</legend>
          {ownedCards.length === 0 ? (
            <p className="muted">
              You do not have any cards in your portfolio. Please add cards from the Catalogue tab first.
            </p>
          ) : (
            ownedCards.map((card) => (
              <label className="check-label" key={card.id}>
                <input
                  type="checkbox"
                  checked={selected.includes(card.id)}
                  onChange={(event) =>
                    setSelected((items) =>
                      event.target.checked
                        ? [...items, card.id]
                        : items.filter((id) => id !== card.id)
                    )
                  }
                />
                {card.display_name}
                <small>Owned card</small>
              </label>
            ))
          )}
        </fieldset>
        <button
          className="primary-button"
          disabled={!scenarioId || selected.length === 0 || ownedCards.length === 0}
          onClick={() => onRun(scenarioId, selected)}
        >
          Run optimizer <span>↗</span>
        </button>
      </div>

      <div className="panel optimizer-result">
        {result ? (
          <>
            <div className="eyebrow" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span>RESULT · {result.method_version}</span>
              <span className={`tag ${result.plan_status}`}>{result.plan_status.toUpperCase()}</span>
            </div>

            <div style={{ margin: "8px 0 16px" }}>
              {result.is_heuristic || result.search_mode === "greedy_heuristic" ? (
                <div>
                  <span className="tag heuristic">⚠ Greedy Marginal Heuristic (Approximation)</span>
                  <p className="muted" style={{ marginTop: "6px", fontSize: "12px" }}>
                    Search space exceeded 100,000 combinations. This allocation is computed using a greedy marginal approximation and is not proven globally optimal.
                  </p>
                </div>
              ) : (
                <div>
                  <span className="tag exhaustive">✓ Exhaustive Global Optimum</span>
                  <p className="muted" style={{ marginTop: "6px", fontSize: "12px" }}>
                    Mathematically verified global maximum across all possible allocations under shared monthly caps.
                  </p>
                </div>
              )}
            </div>

            <h2>Spend preserved, value compared.</h2>
            <div className="optimizer-metrics">
              <Metric label="Baseline" value={money(result.baseline_value)} />
              <Metric label="Proposed" value={money(result.proposed_value)} />
              <Metric label="Incremental" value={money(result.incremental_value)} />
            </div>

            {result.has_cap_uncertainty && result.conservative_proposed_value && (
              <div className="error-banner" style={{ marginBottom: "1rem" }}>
                <div>
                  <strong>Uncertainty Notice:</strong> One or more cards have unknown prior cap usage.
                  <div style={{ marginTop: "4px" }}>
                    Conservative estimate: <b>{money(result.conservative_proposed_value)}</b> (incremental: <b>{money(result.conservative_incremental_value ?? "0.00")}</b>).
                  </div>
                </div>
              </div>
            )}

            <div className="success-banner">
              ✓ Total planned spend preserved: {String(result.total_spend_preserved)} (Planned: {money(result.planned_spend)} · Allocated: {money(result.allocated_spend)})
            </div>

            {result.allocations.map((allocation, index) => {
              const proposedName =
                cards.find((c) => c.id === allocation.proposed_card_variant_id)?.display_name ??
                allocation.proposed_card_variant_id;
              const baselineName = allocation.baseline_card_variant_id
                ? cards.find((c) => c.id === allocation.baseline_card_variant_id)?.display_name ??
                  allocation.baseline_card_variant_id
                : null;
              return (
                <div className="allocation-row" key={index}>
                  <span>
                    {allocation.category as string} · {allocation.amount as string}
                  </span>
                  <strong>
                    {proposedName as string}
                    {baselineName ? ` (vs ${baselineName})` : ""}
                  </strong>
                </div>
              );
            })}

            {result.excluded && result.excluded.length > 0 && (
              <div style={{ marginTop: "1rem", padding: "10px", background: "#fff5f5", borderRadius: "8px", border: "1px solid #ffd4d4" }}>
                <h4 style={{ margin: "0 0 6px", color: "#a44e40" }}>
                  Excluded Spend Buckets ({result.excluded.length})
                </h4>
                {result.excluded.map((exc, idx) => (
                  <p key={idx} className="muted" style={{ fontSize: "0.85rem", color: "#a44e40", margin: "4px 0" }}>
                    • {exc.category}/{exc.channel} (₹{exc.amount}): {exc.reason}
                  </p>
                ))}
              </div>
            )}

            {result.warnings.map((warning) => (
              <p className="muted" key={warning}>
                {warning}
              </p>
            ))}
          </>
        ) : (
          <div className="empty-box">Run the optimizer to see a baseline, proposal, delta, and search method.</div>
        )}
      </div>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function Assistant({ token }: { token: string }) {
  const [question, setQuestion] = useState("Does this card cover online shopping?");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AssistantResult | null>(null);

  async function ask(event?: FormEvent) {
    if (event) event.preventDefault();
    if (!question.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const response = await askAssistant(token, question);
      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to retrieve assistant answer.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="assistant-layout">
      <div className="panel assistant-panel">
        <div className="eyebrow">TERMS ASSISTANT</div>
        <h2>Ask, but keep evidence in charge.</h2>
        <p className="muted">
          The assistant is strictly grounded in verified source excerpts. It never fabricates citations and discloses uncertainties when evidence is partial.
        </p>

        <form onSubmit={ask}>
          <label>
            Your question
            <textarea
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              rows={4}
              required
            />
          </label>
          <button className="primary-button" disabled={loading || !question.trim()}>
            {loading ? "Checking authoritative sources…" : "Ask assistant"}
            <span>↗</span>
          </button>
        </form>

        {error && (
          <div className="error-banner" style={{ marginTop: "16px" }}>
            <span>{error}</span>
            <button className="text-button" style={{ color: "inherit", textDecoration: "underline" }} onClick={() => void ask()}>
              Retry
            </button>
          </div>
        )}

        {result && (
          <div className="abstain-box" style={{ marginTop: "18px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span
                className="tag"
                style={{
                  background: result.abstained ? "#fffbe6" : "#f6ffed",
                  color: result.abstained ? "#d48806" : "#389e0d",
                  fontWeight: 600,
                  fontSize: "11px",
                }}
              >
                {result.abstained ? "ABSTAINED / UNVERIFIED" : "VERIFIED SOURCE EVIDENCE"}
              </span>
              <small className="muted">{result.assistant_type}</small>
            </div>

            <p style={{ fontSize: "14px", fontWeight: 500, color: "#1e3028", marginTop: "12px" }}>
              {result.answer}
            </p>

            <div style={{ marginTop: "14px" }}>
              <strong style={{ fontSize: "12px", color: "#315943" }}>
                Authoritative Source Citations ({result.citations.length})
              </strong>
              {result.citations.length === 0 ? (
                <p className="muted" style={{ margin: "6px 0", fontSize: "12px" }}>
                  No citations returned by authoritative sources.
                </p>
              ) : (
                result.citations.map((c, idx) => (
                  <div className="citation-card" key={idx}>
                    <div style={{ display: "flex", justifyContent: "space-between" }}>
                      <strong>{c.title}</strong>
                      <span className="tag">{c.status}</span>
                    </div>
                    {c.url && (
                      <div style={{ marginTop: "4px" }}>
                        <a href={c.url} target="_blank" rel="noopener noreferrer">
                          {c.url}
                        </a>
                      </div>
                    )}
                    <small className="muted">Source ID: {c.source_id}</small>
                  </div>
                ))
              )}
            </div>

            {result.unknowns.length > 0 && (
              <div style={{ marginTop: "14px" }}>
                <strong style={{ fontSize: "12px", color: "#a44e40" }}>
                  Disclosed Uncertainties & Limitations
                </strong>
                <ul style={{ margin: "6px 0 0", paddingLeft: "18px", fontSize: "12px", color: "#666" }}>
                  {result.unknowns.map((u, i) => (
                    <li key={i}>{u}</li>
                  ))}
                </ul>
              </div>
            )}

            <div style={{ marginTop: "14px", borderTop: "1px solid #eee", paddingTop: "8px" }}>
              <small className="muted">{result.disclaimer}</small>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function Settings({
  reminders,
  latestExport,
  onReminder,
  onUpdateReminder,
  onDeleteReminder,
  onExport,
  onDeleteExport,
  onDelete,
}: {
  reminders: Reminder[];
  latestExport: ExportJobResponse | null;
  onReminder: (label: string, dueAt: string) => void;
  onUpdateReminder: (id: string, payload: { label?: string; due_at?: string; status?: string }) => void;
  onDeleteReminder: (id: string) => void;
  onExport: () => void;
  onDeleteExport: (id: string) => void;
  onDelete: () => void;
}) {
  const [label, setLabel] = useState("");
  const [dueAt, setDueAt] = useState("");
  const [editingReminderId, setEditingReminderId] = useState<string | null>(null);
  const [editLabel, setEditLabel] = useState("");
  const [editDueAt, setEditDueAt] = useState("");

  function startEditReminder(r: Reminder) {
    setEditingReminderId(r.id);
    setEditLabel(r.label);
    setEditDueAt(r.due_at.slice(0, 16));
  }

  function handleSaveEditReminder(id: string) {
    onUpdateReminder(id, {
      label: editLabel,
      due_at: new Date(editDueAt).toISOString(),
    });
    setEditingReminderId(null);
  }

  function handleDownloadExport(exp: ExportJobResponse) {
    const dataStr = JSON.stringify(exp.data ?? exp, null, 2);
    const blob = new Blob([dataStr], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `cardwise-export-${exp.id}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="settings-grid">
      <div className="panel">
        <div className="eyebrow">REMINDERS</div>
        <h2>Keep your own dates</h2>
        <p className="muted">Reminders are informational and do not imply an issuer deadline.</p>

        <form
          onSubmit={(event) => {
            event.preventDefault();
            onReminder(label, new Date(dueAt).toISOString());
            setLabel("");
            setDueAt("");
          }}
        >
          <label>
            Label
            <input
              value={label}
              onChange={(event) => setLabel(event.target.value)}
              required
              placeholder="Review annual fee terms"
            />
          </label>
          <label>
            Due date
            <input
              type="datetime-local"
              value={dueAt}
              onChange={(event) => setDueAt(event.target.value)}
              required
            />
          </label>
          <button className="secondary-button" type="submit">
            Save reminder
          </button>
        </form>

        <div style={{ marginTop: "18px" }}>
          {reminders.map((reminder) => (
            <div className="reminder-row" key={reminder.id} style={{ display: "block", marginBottom: "8px" }}>
              {editingReminderId === reminder.id ? (
                <div style={{ padding: "8px 0" }}>
                  <input
                    value={editLabel}
                    onChange={(e) => setEditLabel(e.target.value)}
                    style={{ marginBottom: "6px" }}
                  />
                  <input
                    type="datetime-local"
                    value={editDueAt}
                    onChange={(e) => setEditDueAt(e.target.value)}
                    style={{ marginBottom: "6px" }}
                  />
                  <div style={{ display: "flex", gap: "6px" }}>
                    <button
                      className="secondary-button"
                      style={{ fontSize: "11px", padding: "4px 8px" }}
                      onClick={() => handleSaveEditReminder(reminder.id)}
                    >
                      Save
                    </button>
                    <button
                      className="text-button"
                      style={{ fontSize: "11px", padding: 0 }}
                      onClick={() => setEditingReminderId(null)}
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <div>
                    <span style={{ fontWeight: 600 }}>{reminder.label}</span>
                    <span
                      className={`tag ${reminder.status === "completed" ? "completed" : ""}`}
                      style={{ marginLeft: "6px", fontSize: "10px" }}
                    >
                      {reminder.status.toUpperCase()}
                    </span>
                    <br />
                    <small>{new Date(reminder.due_at).toLocaleString()}</small>
                  </div>
                  <div style={{ display: "flex", gap: "4px", alignItems: "center" }}>
                    <button
                      className="text-button"
                      style={{ fontSize: "11px" }}
                      onClick={() =>
                        onUpdateReminder(reminder.id, {
                          status: reminder.status === "completed" ? "active" : "completed",
                        })
                      }
                    >
                      {reminder.status === "completed" ? "Mark Active" : "Mark Done"}
                    </button>
                    <button
                      className="text-button"
                      style={{ fontSize: "11px" }}
                      onClick={() => startEditReminder(reminder)}
                    >
                      Edit
                    </button>
                    <button
                      className="danger-button"
                      style={{ padding: "0.2rem 0.5rem", fontSize: "0.8rem", margin: 0 }}
                      title="Delete reminder"
                      onClick={() => {
                        if (window.confirm("Are you sure you want to delete this reminder?")) {
                          onDeleteReminder(reminder.id);
                        }
                      }}
                    >
                      ✕
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      <div className="panel">
        <div className="eyebrow">PRIVACY CONTROLS</div>
        <h2>Your data, your controls.</h2>
        <p className="muted">
          Exports expire automatically. Account deletion permanently removes all user-owned records, scenarios, portfolio cards, and reminders from the local database.
        </p>

        <button className="secondary-button" onClick={onExport}>
          Create expiring export
        </button>

        {latestExport && (
          <div style={{ marginTop: "16px", padding: "12px", background: "#f8faf7", border: "1px solid #dce8de", borderRadius: "8px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <strong style={{ fontSize: "13px" }}>Active Export</strong>
              <span className="tag">{latestExport.status}</span>
            </div>
            <p className="muted" style={{ margin: "6px 0", fontSize: "12px" }}>
              ID: {latestExport.id.slice(0, 12)}… · Expires: {new Date(latestExport.expires_at).toLocaleString()}
            </p>
            <div style={{ display: "flex", gap: "8px", marginTop: "8px" }}>
              <button
                className="download-button"
                onClick={() => handleDownloadExport(latestExport)}
              >
                Download JSON file ⬇
              </button>
              <button
                className="secondary-button"
                style={{ color: "#a44e40" }}
                onClick={() => onDeleteExport(latestExport.id)}
              >
                Purge export
              </button>
            </div>
          </div>
        )}

        <button
          className="danger-button"
          onClick={() => {
            if (
              window.confirm(
                "Are you sure you want to permanently delete this local workspace? All scenarios, portfolio cards, reminders, and export data will be purged immediately."
              )
            ) {
              onDelete();
            }
          }}
        >
          Delete workspace
        </button>

        <div className="privacy-list">
          <span>✓ No full card numbers stored</span>
          <span>✓ No issuer credentials collected</span>
          <span>✓ Local-only deterministic calculations</span>
          <span>✓ Expired export payloads purged automatically</span>
        </div>
      </div>
    </div>
  );
}

export default App;
