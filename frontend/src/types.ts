export type CardVariant = {
  id: string;
  issuer_name: string;
  product_family: string;
  display_name: string;
  network: string;
  market: string;
  currency: string;
  valid_from: string;
  status: "active" | "historical" | "unknown";
  verification_status: "synthetic" | "unverified" | "verified";
  description: string;
};

export type User = {
  id: string;
  email: string;
  role: string;
  timezone: string;
  preferred_currency: string;
};

export type AuthResponse = { access_token: string; token_type: string; user: User };

export type CalculationRequest = {
  card_variant_id: string;
  amount: string;
  currency: string;
  scenario_date: string;
  category: string;
  channel: string;
  prior_cap_consumed: string | null;
  cap_knowledge_state: "known" | "unknown";
};

export type TraceStep = {
  sequence: number;
  step_type: string;
  reason: string;
  input: Record<string, string | null>;
  output: Record<string, string | null>;
  rule_id: string | null;
  evidence_ids: string[];
};

export type CalculationResult = {
  status: string;
  card_variant_id: string;
  eligible_spend: string;
  excluded_spend: string;
  exclusion_reason: string | null;
  gross_reward: string | null;
  cap_amount: string | null;
  cap_consumed_before: string | null;
  cap_remaining_before: string | null;
  estimated_reward: string | null;
  possible_reward_min: string | null;
  possible_reward_max: string | null;
  fee_allocation: string;
  estimated_net_value: string | null;
  currency: string;
  verification_status: string;
  warnings: string[];
  evidence_ids: string[];
  trace: TraceStep[];
  engine_version: string;
  manifest_hash: string;
};

export type SpendInput = {
  category: string;
  channel: string;
  amount: string;
  transaction_count?: number | null;
  is_fixed?: boolean;
  cap_usage?: string | null;
  cap_knowledge_state?: "known" | "unknown";
  point_value_per_point?: string | null;
};

export type Scenario = {
  id: string;
  name: string;
  scenario_date: string;
  currency: string;
  revision: number;
  created_at: string;
  updated_at: string;
  spend: SpendInput[];
};

export type Comparison = {
  scenario_id: string;
  revision: number;
  results: Array<{ card_variant_id: string; estimated_net_value: string; buckets: CalculationResult[] }>;
};

export type OptimizerResult = {
  scenario_id: string;
  method_version: string;
  baseline_value: string;
  proposed_value: string;
  incremental_value: string;
  total_spend_preserved: boolean;
  allocations: Array<Record<string, string | null>>;
  warnings: string[];
};

export type Reminder = { id: string; label: string; due_at: string; timezone: string; status: string };

export type CardRule = {
  id: string;
  rule_type: string;
  parameters: Record<string, unknown>;
  effective_from: string;
  effective_to: string | null;
  verification_status: string;
  evidence_ids: string[];
  notes: string;
};
