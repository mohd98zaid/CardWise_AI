import { FormEvent, useEffect, useMemo, useState } from "react";

import {
  addPortfolioCard,
  compareScenario,
  createExport,
  createReminder,
  createScenario,
  deleteAccount,
  deleteReminder,
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
} from "./api";
import type { AuthResponse, CardRule, CardVariant, Comparison, OptimizerResult, Reminder, Scenario, SpendInput, User } from "./types";

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
  const [portfolio, setPortfolio] = useState<Array<{ card_variant_id: string; display_name: string }>>([]);
  const [reminders, setReminders] = useState<Reminder[]>([]);
  const [comparison, setComparison] = useState<Comparison | null>(null);
  const [optimizer, setOptimizer] = useState<OptimizerResult | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function reload() {
    try {
      const [loadedCards, loadedScenarios, loadedPortfolio, loadedReminders] = await Promise.all([getCards(), getScenarios(token), getPortfolio(token), getReminders(token)]);
      setCards(loadedCards); setScenarios(loadedScenarios); setPortfolio(loadedPortfolio); setReminders(loadedReminders);
    } catch (requestError) { setError(requestError instanceof Error ? requestError.message : "Could not load workspace."); }
  }
  useEffect(() => { void reload(); }, [token]);
  async function saveScenario(payload: { name: string; scenario_date: string; currency: string; spend: SpendInput[] }) {
    try { const created = await createScenario(token, payload); setScenarios((items) => [created, ...items]); setTab("scenarios"); setNotice("Scenario saved. You can now compare it or send it to the optimizer."); }
    catch (requestError) { setError(requestError instanceof Error ? requestError.message : "Scenario could not be saved."); }
  }
  async function compare(id: string, cardIds: string[]) {
    try { setComparison(await compareScenario(token, id, cardIds)); setTab("scenarios"); setNotice("Comparison calculated from the current scenario revision."); }
    catch (requestError) { setError(requestError instanceof Error ? requestError.message : "Comparison failed."); }
  }
  async function optimize(id: string, cardIds: string[]) {
    if (cardIds.length === 0) { setError("Add an existing card reference from Catalogue before running the optimizer."); setTab("catalogue"); return; }
    try {
      setOptimizer(await runOptimizer(token, id, cardIds)); setTab("optimizer");
    } catch (requestError) { setError(requestError instanceof Error ? requestError.message : "Optimization failed."); }
  }

  return <main className="app-shell">
    <header className="app-header"><a className="brand" href="#dashboard" onClick={() => setTab("dashboard")}><span className="brand-mark">cw</span><span>CardWise <em>AI</em></span></a><div className="header-actions"><span className="user-pill">{user.email}</span><button className="text-button" onClick={onLogout}>Sign out</button></div></header>
    <div className="app-layout">
      <nav className="sidebar" aria-label="Main navigation">{(["dashboard", "portfolio", "catalogue", "scenarios", "optimizer", "assistant", "settings"] as Tab[]).map((item) => <button key={item} className={tab === item ? "nav-item active" : "nav-item"} onClick={() => setTab(item)}><span className={`nav-icon ${item}`}>{item === "dashboard" ? "⌂" : item === "portfolio" ? "▣" : item === "catalogue" ? "▦" : item === "scenarios" ? "⌁" : item === "optimizer" ? "↗" : item === "assistant" ? "✦" : "⚙"}</span>{item[0].toUpperCase() + item.slice(1)}</button>)}</nav>
      <section className="content"><div className="content-top"><div><div className="eyebrow">PRIVATE WORKSPACE</div><h1>{tab === "dashboard" ? "Good planning starts with known assumptions." : tab[0].toUpperCase() + tab.slice(1)}</h1></div><span className="alpha-badge">Synthetic alpha</span></div>
        {notice && <div className="success-banner" role="status">✓ {notice}<button onClick={() => setNotice(null)}>×</button></div>}
        {error && <div className="error-banner" role="alert">{error}<button onClick={() => setError(null)}>×</button></div>}
        {tab === "dashboard" && <Dashboard cards={cards} scenarios={scenarios} reminders={reminders} onNavigate={setTab} />}
        {tab === "portfolio" && <Portfolio cards={cards} portfolio={portfolio} onRemove={async (id) => { await removePortfolioCard(token, id); await reload(); setNotice("Card reference removed from your portfolio."); }} />}
        {tab === "catalogue" && <Catalogue cards={cards} onAdd={async (id) => { await addPortfolioCard(token, id); await reload(); setNotice("Card reference added to your portfolio."); }} />}
        {tab === "scenarios" && <Scenarios cards={cards} scenarios={scenarios} comparison={comparison} onSave={saveScenario} onDuplicate={async (id) => { const copy = await duplicateScenario(token, id); setScenarios((items) => [copy, ...items]); setNotice("Scenario duplicated."); }} onCompare={compare} onOptimize={(id) => optimize(id, portfolio.map((item) => item.card_variant_id))} />}
        {tab === "optimizer" && <Optimizer scenarios={scenarios} cards={cards} portfolio={portfolio} result={optimizer} onRun={optimize} />}
        {tab === "assistant" && <Assistant token={token} />}
        {tab === "settings" && <Settings token={token} reminders={reminders} onReminder={async (label, dueAt) => { const reminder = await createReminder(token, label, dueAt); setReminders((items) => [...items, reminder]); setNotice("Reminder saved."); }} onExport={async () => { const exportFile = await createExport(token); setNotice(`Export created — expires ${new Date(exportFile.expires_at).toLocaleString()}. Contains: your account data, scenarios, and reminders. Export ID: ${exportFile.id}`); }} onDeleteReminder={async (id) => { await deleteReminder(token, id); setReminders((items) => items.filter((r) => r.id !== id)); }} onDelete={async () => { await deleteAccount(token); onLogout(); }} />}
      </section>
    </div>
    <footer><span>CardWise AI · Estimates, not guarantees</span><span>Calculator engine 0.1.0</span></footer>
  </main>;
}

function Dashboard({ cards, scenarios, reminders, onNavigate }: { cards: CardVariant[]; scenarios: Scenario[]; reminders: Reminder[]; onNavigate: (tab: Tab) => void }) {
  return <><div className="dashboard-grid"><div className="dashboard-card accent-card"><span className="card-kicker">YOUR PORTFOLIO</span><strong>{cards.length}</strong><p>synthetic catalogue variant available</p><button onClick={() => onNavigate("catalogue")}>Browse catalogue →</button></div><div className="dashboard-card"><span className="card-kicker">SAVED SCENARIOS</span><strong>{scenarios.length}</strong><p>planned spending profiles</p><button onClick={() => onNavigate("scenarios")}>Open scenarios →</button></div><div className="dashboard-card"><span className="card-kicker">REMINDERS</span><strong>{reminders.length}</strong><p>user-entered informational reminders</p><button onClick={() => onNavigate("settings")}>Manage reminders →</button></div></div><div className="dashboard-lower"><div className="panel intro-panel"><div className="eyebrow">HOW CARDWISE WORKS</div><h2>Every estimate leaves a trail.</h2><p>Rules are typed data. Calculations use Decimal arithmetic. Unknown cap usage stays visible instead of quietly becoming zero.</p><div className="principle-list"><span><b>01</b> Select an exact variant</span><span><b>02</b> Enter existing planned spend</span><span><b>03</b> Inspect the evidence and trace</span></div></div><div className="panel disclosure-panel"><span className="notice-icon">i</span><strong>Synthetic local MVP</strong><p>No real issuer terms are activated. The demo card is fictional and exists only for testing the calculation flow.</p></div></div></>;
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
                <p className="muted">No rules currently listed for this variant.</p>
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

function Portfolio({ cards, portfolio, onRemove }: { cards: CardVariant[]; portfolio: Array<{ id?: string; card_variant_id: string; display_name: string; nickname?: string | null }>; onRemove: (id: string) => void }) {
  return <div className="catalogue-grid">{portfolio.length === 0 ? <div className="panel empty-box">No card references yet. Add an exact variant from the Catalogue.</div> : portfolio.map((item) => <article className="panel catalogue-card" key={item.id ?? item.card_variant_id}><div className="card-art"><span>cw</span><small>Owned reference</small></div><div className="card-kicker">PORTFOLIO REFERENCE</div><h2>{cards.find((card) => card.id === item.card_variant_id)?.display_name ?? item.display_name}</h2><p>{item.nickname || "No nickname set."}</p><div className="tag-row"><span className="tag synthetic">No credentials stored</span></div><button className="danger-button" onClick={() => item.id && onRemove(item.id)}>Remove reference</button></article>)}</div>;
}

function Scenarios({ cards, scenarios, comparison, onSave, onDuplicate, onCompare, onOptimize }: { cards: CardVariant[]; scenarios: Scenario[]; comparison: Comparison | null; onSave: (payload: { name: string; scenario_date: string; currency: string; spend: SpendInput[] }) => void; onDuplicate: (id: string) => void; onCompare: (id: string, cards: string[]) => void; onOptimize: (id: string) => void }) {
  const [name, setName] = useState("Monthly online plan"); const [date, setDate] = useState("2026-01-15"); const [amount, setAmount] = useState("8000"); const [category, setCategory] = useState("online_shopping"); const [channel, setChannel] = useState("online_card"); const [capUnknown, setCapUnknown] = useState(true); const [pointValue, setPointValue] = useState("");
  return <div className="scenario-layout"><form className="panel scenario-form" onSubmit={(event) => { event.preventDefault(); onSave({ name, scenario_date: date, currency: "INR", spend: [{ category, channel, amount, cap_usage: capUnknown ? null : "0", cap_knowledge_state: capUnknown ? "unknown" : "known", point_value_per_point: pointValue || null }] }); }}><div className="eyebrow">SCENARIO BUILDER</div><h2>Plan existing spend</h2><p className="muted">The optimizer preserves this amount. It never recommends spending more to unlock a benefit.</p><label>Scenario name<input value={name} onChange={(event) => setName(event.target.value)} /></label><div className="two-column"><label>Planned spend<div className="input-with-prefix"><span>₹</span><input type="number" min="0" value={amount} onChange={(event) => setAmount(event.target.value)} /></div></label><label>Scenario date<input type="date" value={date} onChange={(event) => setDate(event.target.value)} /></label></div><div className="two-column"><label>Category<select value={category} onChange={(event) => setCategory(event.target.value)}><option value="online_shopping">Online shopping</option><option value="offline_retail">Offline retail</option><option value="groceries">Groceries</option><option value="dining">Dining</option><option value="fuel">Fuel</option><option value="utilities">Utilities and bills</option><option value="travel">Travel and hotels</option><option value="transport">Transport</option><option value="healthcare">Healthcare</option><option value="education">Education</option><option value="entertainment">Entertainment and subscriptions</option><option value="upi">UPI</option><option value="other">Other</option><option value="unknown">Unknown</option></select></label><label>Channel<select value={channel} onChange={(event) => setChannel(event.target.value)}><option value="online_card">Online card</option><option value="in_store_card">In-store card</option><option value="upi">UPI</option><option value="wallet">Wallet</option><option value="contactless">Contactless</option><option value="emi">EMI</option><option value="subscription">Subscription</option><option value="other">Other</option><option value="unknown">Unknown</option></select></label></div><div className="two-column"><label>Point value <span className="optional">optional</span><div className="input-with-prefix"><span>₹</span><input type="number" min="0" step="0.0001" placeholder="Unknown" value={pointValue} onChange={(event) => setPointValue(event.target.value)} /></div><small>Used only for points rules; this is your assumption.</small></label><label className="check-label cap-check"><input type="checkbox" checked={capUnknown} onChange={(event) => setCapUnknown(event.target.checked)} /> Prior cap usage is unknown</label></div><button className="primary-button" type="submit">Save scenario <span>↗</span></button></form><div className="scenario-list"><div className="section-title"><div><div className="eyebrow">SAVED INPUTS</div><h2>Your scenarios</h2></div><span>{scenarios.length}</span></div>{scenarios.length === 0 ? <div className="empty-box">Save your first planned-spend scenario to compare cards.</div> : scenarios.map((scenario) => <div className="scenario-row" key={scenario.id}><div><strong>{scenario.name}</strong><span>{scenario.scenario_date} · {scenario.spend.map((item) => money(item.amount)).join(" + ")}</span></div><div className="row-actions"><button onClick={() => onCompare(scenario.id, cards.map((card) => card.id))}>Compare</button><button onClick={() => onOptimize(scenario.id)}>Optimize owned cards</button><button aria-label={`Duplicate ${scenario.name}`} onClick={() => onDuplicate(scenario.id)}>⧉</button></div></div>)}{comparison && <ComparisonView comparison={comparison} cards={cards} />}</div></div>;
}

function ComparisonView({ comparison, cards }: { comparison: Comparison; cards: CardVariant[] }) {
  return <div className="comparison-box"><div className="eyebrow">LATEST COMPARISON</div>{comparison.results.map((result) => <div key={result.card_variant_id}><div className="compare-row"><span>{cards.find((card) => card.id === result.card_variant_id)?.display_name ?? result.card_variant_id}</span><strong>{money(result.estimated_net_value)}</strong></div><details className="trace"><summary>View bucket trace <span>{result.buckets.length} buckets</span></summary>{result.buckets.map((bucket, index) => <div className="allocation-row" key={index}><span>{bucket.status.replaceAll("_", " ")}</span><strong>{bucket.trace.length} steps</strong></div>)}</details></div>)}<p className="muted">Values may be unknown when cap usage is not supplied. Every bucket retains its rule and evidence trace.</p></div>;
}

function Optimizer({ scenarios, cards, portfolio, result, onRun }: { scenarios: Scenario[]; cards: CardVariant[]; portfolio: Array<{ card_variant_id: string }>; result: OptimizerResult | null; onRun: (id: string, cards: string[]) => void }) {
  const [scenarioId, setScenarioId] = useState(scenarios[0]?.id ?? "");
  const [selected, setSelected] = useState<string[]>(portfolio.map((item) => item.card_variant_id));
  useEffect(() => { if (!scenarioId && scenarios[0]) setScenarioId(scenarios[0].id); }, [scenarios, scenarioId]);
  return <div className="optimizer-layout"><div className="panel"><div className="eyebrow">CONSTRAINED ALLOCATION</div><h2>Optimize existing spend</h2><p className="muted">Only selected card references are eligible. Total planned spend is preserved per bucket.</p><label>Scenario<select value={scenarioId} onChange={(event) => setScenarioId(event.target.value)}>{scenarios.map((scenario) => <option key={scenario.id} value={scenario.id}>{scenario.name}</option>)}</select></label><fieldset><legend>Cards available to optimizer</legend>{cards.map((card) => <label className="check-label" key={card.id}><input type="checkbox" checked={selected.includes(card.id)} onChange={(event) => setSelected((items) => event.target.checked ? [...items, card.id] : items.filter((id) => id !== card.id))} />{card.display_name}<small>{portfolio.some((item) => item.card_variant_id === card.id) ? "Owned reference" : "Will be added as a local reference"}</small></label>)}</fieldset><button className="primary-button" disabled={!scenarioId || selected.length === 0} onClick={() => onRun(scenarioId, selected)}>Run optimizer <span>↗</span></button></div><div className="panel optimizer-result">{result ? <><div className="eyebrow">RESULT · {result.method_version}</div><h2>Spend preserved, value compared.</h2><div className="optimizer-metrics"><Metric label="Baseline" value={money(result.baseline_value)} /><Metric label="Proposed" value={money(result.proposed_value)} /><Metric label="Incremental" value={money(result.incremental_value)} /></div><div className="success-banner">✓ Total planned spend preserved: {String(result.total_spend_preserved)}</div>{result.allocations.map((allocation, index) => {
    const proposedName = cards.find((c) => c.id === allocation.proposed_card_variant_id)?.display_name ?? allocation.proposed_card_variant_id;
    const baselineName = allocation.baseline_card_variant_id ? (cards.find((c) => c.id === allocation.baseline_card_variant_id)?.display_name ?? allocation.baseline_card_variant_id) : null;
    return <div className="allocation-row" key={index}><span>{allocation.category as string} · {allocation.amount as string}</span><strong>{proposedName as string}{baselineName ? ` (vs ${baselineName})` : ""}</strong></div>;
  })}{result.warnings.map((warning) => <p className="muted" key={warning}>{warning}</p>)}</> : <div className="empty-box">Run the optimizer to see a baseline, proposal, delta, and method version.</div>}</div></div>;
}

function Metric({ label, value }: { label: string; value: string }) { return <div className="metric"><span>{label}</span><strong>{value}</strong></div>; }

function Assistant({ token }: { token: string }) {
  const [question, setQuestion] = useState("Does this card cover online shopping?"); const [answer, setAnswer] = useState<string | null>(null); const [loading, setLoading] = useState(false);
  async function ask(event: FormEvent) { event.preventDefault(); setLoading(true); const response = await fetch(`${import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000"}/api/v1/assistant/ask`, { method: "POST", headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` }, body: JSON.stringify({ question }) }); const data = await response.json() as { answer: string }; setAnswer(data.answer); setLoading(false); }
  return <div className="assistant-layout"><div className="panel assistant-panel"><div className="eyebrow">TERMS ASSISTANT</div><h2>Ask, but keep evidence in charge.</h2><p className="muted">The assistant is intentionally abstaining in the synthetic MVP until permitted, verified sources and an evaluation set are configured.</p><form onSubmit={ask}><label>Your question<textarea value={question} onChange={(event) => setQuestion(event.target.value)} rows={5} /></label><button className="primary-button" disabled={loading}>{loading ? "Checking sources…" : "Ask assistant"}<span>↗</span></button></form>{answer && <div className="abstain-box"><strong>Abstained</strong><p>{answer}</p><span>No citations available</span></div>}</div></div>;
}

function Settings({ token, reminders, onReminder, onExport, onDeleteReminder, onDelete }: { token: string; reminders: Reminder[]; onReminder: (label: string, dueAt: string) => void; onExport: () => void; onDeleteReminder: (id: string) => void; onDelete: () => void }) {
  const [label, setLabel] = useState(""); const [dueAt, setDueAt] = useState("");
  return <div className="settings-grid"><div className="panel"><div className="eyebrow">REMINDERS</div><h2>Keep your own dates</h2><p className="muted">Reminders are informational and do not imply an issuer deadline.</p><form onSubmit={(event) => { event.preventDefault(); onReminder(label, new Date(dueAt).toISOString()); setLabel(""); setDueAt(""); }}><label>Label<input value={label} onChange={(event) => setLabel(event.target.value)} required placeholder="Review annual fee terms" /></label><label>Due date<input type="datetime-local" value={dueAt} onChange={(event) => setDueAt(event.target.value)} required /></label><button className="secondary-button" type="submit">Save reminder</button></form>{reminders.map((reminder) => <div className="reminder-row" key={reminder.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}><div><span>{reminder.label}</span><br /><small>{new Date(reminder.due_at).toLocaleString()}</small></div><button className="danger-button" style={{ padding: "0.2rem 0.5rem", fontSize: "0.8rem" }} title="Delete reminder" onClick={() => onDeleteReminder(reminder.id)}>✕</button></div>)}</div><div className="panel"><div className="eyebrow">PRIVACY CONTROLS</div><h2>Your data, your controls.</h2><p className="muted">Exports expire automatically. Account deletion removes user-owned records from the local database. Backups are not configured in this synthetic track.</p><button className="secondary-button" onClick={onExport}>Create expiring export</button><button className="danger-button" onClick={() => { if (window.confirm("Delete this local workspace?")) onDelete(); }}>Delete workspace</button><div className="privacy-list"><span>✓ No full card number stored</span><span>✓ No issuer credentials collected</span><span>✓ Assistant does not send data to a model</span></div></div></div>;
}

export default App;
