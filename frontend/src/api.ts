import type {
  AssistantResult,
  AuthResponse,
  CardRule,
  CardVariant,
  CalculationRequest,
  CalculationResult,
  Comparison,
  ExportJobResponse,
  OptimizerResult,
  Reminder,
  Scenario,
  SpendInput,
  User,
} from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit, token?: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options?.headers ?? {}),
    },
    ...options,
  });
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as
      | { detail?: string | Array<{ msg?: string }>; message?: string }
      | null;
    let errorMessage = "The CardWise API could not complete that request.";
    if (body?.message) {
      errorMessage = body.message;
    } else if (typeof body?.detail === "string") {
      errorMessage = body.detail;
    } else if (Array.isArray(body?.detail) && body.detail.length > 0) {
      errorMessage = body.detail.map((d) => d.msg || JSON.stringify(d)).join(", ");
    }
    throw new Error(errorMessage);
  }
  if (response.status === 204) {
    return undefined as unknown as T;
  }
  const text = await response.text();
  if (!text) {
    return undefined as unknown as T;
  }
  return JSON.parse(text) as T;
}

export function getCards(): Promise<CardVariant[]> {
  return request<CardVariant[]>("/api/v1/catalogue/cards");
}

export function register(email: string, password: string): Promise<AuthResponse> {
  return request<AuthResponse>("/api/v1/auth/register", { method: "POST", body: JSON.stringify({ email, password }) });
}

export function login(email: string, password: string): Promise<AuthResponse> {
  return request<AuthResponse>("/api/v1/auth/login", { method: "POST", body: JSON.stringify({ email, password }) });
}

export function getMe(token: string): Promise<User> {
  return request<User>("/api/v1/me", undefined, token);
}

export function logout(token: string): Promise<void> {
  return request<void>("/api/v1/auth/logout", { method: "POST" }, token);
}

export function getScenarios(token: string): Promise<Scenario[]> {
  return request<Scenario[]>("/api/v1/me/scenarios", undefined, token);
}

export function createScenario(token: string, payload: { name: string; scenario_date: string; currency: string; spend: SpendInput[] }): Promise<Scenario> {
  return request<Scenario>("/api/v1/me/scenarios", { method: "POST", body: JSON.stringify(payload) }, token);
}

export function updateScenario(
  token: string,
  scenarioId: string,
  payload: { name?: string; scenario_date?: string; currency?: string; spend?: SpendInput[] }
): Promise<Scenario> {
  return request<Scenario>(`/api/v1/me/scenarios/${scenarioId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  }, token);
}

export function deleteScenario(token: string, scenarioId: string): Promise<void> {
  return request<void>(`/api/v1/me/scenarios/${scenarioId}`, { method: "DELETE" }, token);
}

export function duplicateScenario(token: string, id: string): Promise<Scenario> {
  return request<Scenario>(`/api/v1/me/scenarios/${id}/duplicate`, { method: "POST" }, token);
}

export function compareScenario(token: string, scenarioId: string, cardIds: string[]): Promise<Comparison> {
  return request<Comparison>("/api/v1/calculations/compare", { method: "POST", body: JSON.stringify({ scenario_id: scenarioId, card_variant_ids: cardIds }) }, token);
}

export function getPortfolio(token: string): Promise<Array<{ id: string; card_variant_id: string; display_name: string; nickname?: string | null }>> {
  return request<Array<{ id: string; card_variant_id: string; display_name: string; nickname?: string | null }>>("/api/v1/me/cards", undefined, token);
}

export function addPortfolioCard(token: string, cardId: string): Promise<void> {
  return request<void>(`/api/v1/me/cards?card_variant_id=${encodeURIComponent(cardId)}`, { method: "POST" }, token);
}

export function removePortfolioCard(token: string, portfolioCardId: string): Promise<void> {
  return request<void>(`/api/v1/me/cards/${portfolioCardId}`, { method: "DELETE" }, token);
}

export function runOptimizer(token: string, scenarioId: string, cardIds: string[]): Promise<OptimizerResult> {
  return request<OptimizerResult>("/api/v1/optimizer/run", { method: "POST", body: JSON.stringify({ scenario_id: scenarioId, card_variant_ids: cardIds }) }, token);
}

export function getReminders(token: string): Promise<Reminder[]> {
  return request<Reminder[]>("/api/v1/reminders", undefined, token);
}

export function createReminder(token: string, label: string, dueAt: string): Promise<Reminder> {
  return request<Reminder>("/api/v1/reminders", { method: "POST", body: JSON.stringify({ label, due_at: dueAt, timezone: "Asia/Kolkata" }) }, token);
}

export function createExport(token: string): Promise<{ id: string; expires_at: string; data: unknown }> {
  return request<{ id: string; expires_at: string; data: unknown }>("/api/v1/exports", { method: "POST" }, token);
}

export function deleteAccount(token: string): Promise<void> {
  return request<void>("/api/v1/me", { method: "DELETE" }, token);
}

export function estimateRewards(payload: CalculationRequest): Promise<CalculationResult> {
  return request<CalculationResult>("/api/v1/calculations/estimate", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getCardRules(variantId: string): Promise<CardRule[]> {
  return request<CardRule[]>(`/api/v1/card-variants/${variantId}/rules`);
}

export function deleteReminder(token: string, reminderId: string): Promise<void> {
  return request<void>(`/api/v1/reminders/${reminderId}`, { method: "DELETE" }, token);
}

export function updateReminder(
  token: string,
  reminderId: string,
  payload: { label?: string; due_at?: string; status?: string }
): Promise<Reminder> {
  return request<Reminder>(`/api/v1/reminders/${reminderId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
  }, token);
}

export function getExport(token: string, exportId: string): Promise<ExportJobResponse> {
  return request<ExportJobResponse>(`/api/v1/exports/${exportId}`, undefined, token);
}

export function deleteExport(token: string, exportId: string): Promise<void> {
  return request<void>(`/api/v1/exports/${exportId}`, { method: "DELETE" }, token);
}

export function askAssistant(token: string, question: string): Promise<AssistantResult> {
  return request<AssistantResult>("/api/v1/assistant/ask", {
    method: "POST",
    body: JSON.stringify({ question }),
  }, token);
}
