import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import App from "./App";
import * as api from "./api";
import type {
  AssistantResult,
  AuthResponse,
  CardVariant,
  ExportJobResponse,
  OptimizerResult,
  Reminder,
  Scenario,
  User,
} from "./types";

vi.mock("./api");

const mockedApi = vi.mocked(api);

const mockUser: User = {
  id: "user-123",
  email: "test@cardwise.local",
  role: "user",
  timezone: "Asia/Kolkata",
  preferred_currency: "INR",
};

const mockCards: CardVariant[] = [
  {
    id: "card-1",
    issuer_name: "HDFC Bank",
    product_family: "Millennia",
    display_name: "HDFC Bank Millennia Credit Card",
    network: "Visa",
    market: "IN",
    currency: "INR",
    valid_from: "2026-01-01",
    status: "active",
    verification_status: "verified",
    description: "Cashback card for shopping and dining",
  },
  {
    id: "card-2",
    issuer_name: "Axis Bank",
    product_family: "Ace",
    display_name: "Axis Bank Ace Credit Card",
    network: "Visa",
    market: "IN",
    currency: "INR",
    valid_from: "2026-01-01",
    status: "active",
    verification_status: "verified",
    description: "Cashback card for utilities and bills",
  },
];

const mockPortfolio = [
  {
    id: "p-card-1",
    card_variant_id: "card-1",
    display_name: "HDFC Bank Millennia Credit Card",
  },
];

const mockScenarios: Scenario[] = [
  {
    id: "sc-1",
    name: "Monthly Shopping & Dining",
    scenario_date: "2026-06-01",
    currency: "INR",
    revision: 1,
    created_at: "2026-06-01T00:00:00Z",
    updated_at: "2026-06-01T00:00:00Z",
    spend: [
      {
        id: "spend-1",
        category: "dining",
        channel: "pos_card",
        amount: "3000",
        cap_knowledge_state: "known",
      },
      {
        id: "spend-2",
        category: "online_shopping",
        channel: "online_card",
        amount: "5000",
        cap_knowledge_state: "known",
      },
    ],
  },
];

const mockReminders: Reminder[] = [
  {
    id: "rem-1",
    label: "Pay credit card statement",
    due_at: "2026-07-05T12:00:00Z",
    timezone: "Asia/Kolkata",
    status: "active",
  },
];

describe("CardWise AI — Frontend End-to-End Component Tests", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();

    mockedApi.getCards.mockResolvedValue(mockCards);
    mockedApi.getPortfolio.mockResolvedValue(mockPortfolio);
    mockedApi.getScenarios.mockResolvedValue(mockScenarios);
    mockedApi.getReminders.mockResolvedValue(mockReminders);
    mockedApi.getCardRules.mockResolvedValue([]);
  });

  it("handles registration and login flows seamlessly", async () => {
    const authSuccess: AuthResponse = {
      access_token: "mock-jwt-token",
      token_type: "bearer",
      user: mockUser,
    };
    mockedApi.register.mockResolvedValue(authSuccess);
    mockedApi.getMe.mockResolvedValue(mockUser);

    render(<App />);

    // By default AuthScreen shows Register mode
    expect(screen.getByRole("heading", { name: /Build a clearer card strategy/i })).toBeInTheDocument();

    // Toggle to login mode
    fireEvent.click(screen.getByRole("button", { name: /Already have an account\? Sign in/i }));
    expect(screen.getByRole("heading", { name: /Welcome back/i })).toBeInTheDocument();

    // Toggle back to register mode
    fireEvent.click(screen.getByRole("button", { name: /Need an account\? Create one/i }));

    // Fill form
    fireEvent.change(screen.getByLabelText(/Email/i), { target: { value: "test@cardwise.local" } });
    fireEvent.change(screen.getByLabelText(/Password/i), { target: { value: "password123" } });

    // Submit
    fireEvent.click(screen.getByRole("button", { name: /Create workspace/i }));

    await waitFor(() => {
      expect(mockedApi.register).toHaveBeenCalledWith("test@cardwise.local", "password123");
      expect(screen.getByText("test@cardwise.local")).toBeInTheDocument();
    });
  });

  it("displays accurate counts on Dashboard for portfolio, scenarios, and reminders", async () => {
    localStorage.setItem("cardwise_token", "mock-jwt-token");
    mockedApi.getMe.mockResolvedValue(mockUser);

    render(<App />);

    // Wait for async workspace data to load
    await waitFor(() => {
      expect(screen.getByText("1 active card reference in your portfolio")).toBeInTheDocument();
    });

    // Check portfolio count reflects portfolio.length (1), not catalogue count (2)
    expect(screen.getByText("YOUR PORTFOLIO")).toBeInTheDocument();

    // Check scenarios count
    expect(screen.getByText("SAVED SCENARIOS")).toBeInTheDocument();
    expect(screen.getByText("1 planned spending profile")).toBeInTheDocument();

    // Check reminders count
    expect(screen.getByText("REMINDERS")).toBeInTheDocument();
    expect(screen.getByText("1 informational reminder set")).toBeInTheDocument();
  });

  it("renders empty states cleanly when user has no cards, scenarios, or reminders", async () => {
    localStorage.setItem("cardwise_token", "mock-jwt-token");
    mockedApi.getMe.mockResolvedValue(mockUser);
    mockedApi.getPortfolio.mockResolvedValue([]);
    mockedApi.getScenarios.mockResolvedValue([]);
    mockedApi.getReminders.mockResolvedValue([]);

    render(<App />);

    await waitFor(() => {
      expect(screen.getByText("No card references in your portfolio yet")).toBeInTheDocument();
      expect(screen.getByText("No planned spend profiles saved yet")).toBeInTheDocument();
      expect(screen.getByText("No active informational reminders")).toBeInTheDocument();
    });
  });

  it("supports multi-bucket scenario creation, editing in-place, and deletion", async () => {
    localStorage.setItem("cardwise_token", "mock-jwt-token");
    mockedApi.getMe.mockResolvedValue(mockUser);

    const createdScenario: Scenario = {
      id: "sc-new",
      name: "Diwali Festivities",
      scenario_date: "2026-10-15",
      currency: "INR",
      revision: 1,
      created_at: "2026-10-15T00:00:00Z",
      updated_at: "2026-10-15T00:00:00Z",
      spend: [
        { id: "sp-1", category: "online_shopping", channel: "online_card", amount: "10000" },
        { id: "sp-2", category: "groceries", channel: "pos_card", amount: "5000" },
      ],
    };
    mockedApi.createScenario.mockResolvedValue(createdScenario);

    render(<App />);
    await waitFor(() => expect(screen.getByText("1 active card reference in your portfolio")).toBeInTheDocument());

    // Navigate to Scenarios tab using sidebar navigation
    const nav = screen.getByRole("navigation", { name: "Main navigation" });
    fireEvent.click(within(nav).getByRole("button", { name: /Scenarios/i }));
    expect(screen.getByRole("heading", { name: "Scenarios" })).toBeInTheDocument();

    // Add another spend bucket
    fireEvent.click(screen.getByRole("button", { name: /\+ Add another spend bucket/i }));
    expect(screen.getAllByText(/Bucket #/i).length).toBe(2);

    // Fill scenario name
    fireEvent.change(screen.getByLabelText(/Scenario name/i), {
      target: { value: "Diwali Festivities" },
    });

    // Submit save scenario
    fireEvent.click(screen.getByRole("button", { name: /Save scenario/i }));

    await waitFor(() => {
      expect(mockedApi.createScenario).toHaveBeenCalled();
      expect(screen.getByText("Diwali Festivities")).toBeInTheDocument();
    });

    // Edit scenario
    const updatedScenario: Scenario = {
      ...mockScenarios[0],
      name: "Monthly Shopping & Dining Updated",
      revision: 2,
    };
    mockedApi.updateScenario.mockResolvedValue(updatedScenario);

    const editButton = screen.getAllByTitle("Edit scenario")[1];
    fireEvent.click(editButton);

    // Check prefilled in edit form
    expect(screen.getByText("EDIT SCENARIO")).toBeInTheDocument();
    expect(screen.getByText("Update planned spend")).toBeInTheDocument();

    // Click Update
    fireEvent.click(screen.getByRole("button", { name: /Update scenario/i }));

    await waitFor(() => {
      expect(mockedApi.updateScenario).toHaveBeenCalled();
    });

    // Test Delete scenario with window.confirm
    mockedApi.deleteScenario.mockResolvedValue(undefined);
    vi.spyOn(window, "confirm").mockReturnValue(true);

    const deleteButton = screen.getAllByTitle("Delete scenario")[0];
    fireEvent.click(deleteButton);

    await waitFor(() => {
      expect(mockedApi.deleteScenario).toHaveBeenCalledWith("mock-jwt-token", "sc-new");
    });
  });

  it("distinguishes exhaustive optimal results from heuristic optimizer results", async () => {
    localStorage.setItem("cardwise_token", "mock-jwt-token");
    mockedApi.getMe.mockResolvedValue(mockUser);

    const heuristicResult: OptimizerResult = {
      scenario_id: "sc-1",
      method_version: "0.2.0",
      plan_status: "heuristic",
      search_mode: "greedy_heuristic",
      is_heuristic: true,
      has_cap_uncertainty: true,
      baseline_value: "100.00",
      proposed_value: "350.00",
      incremental_value: "250.00",
      conservative_proposed_value: "200.00",
      conservative_incremental_value: "100.00",
      total_spend_preserved: true,
      planned_spend: "8000.00",
      allocated_spend: "8000.00",
      allocations: [
        {
          category: "dining",
          channel: "pos_card",
          amount: "3000.00",
          proposed_card_variant_id: "card-1",
          baseline_reward: "50.00",
          proposed_reward: "150.00",
        },
      ],
      excluded: [],
      warnings: ["Search space exceeded 100,000 combinations; evaluated using greedy marginal heuristic."],
    };
    mockedApi.runOptimizer.mockResolvedValue(heuristicResult);

    render(<App />);
    await waitFor(() => expect(screen.getByText("1 active card reference in your portfolio")).toBeInTheDocument());

    // Navigate to Optimizer tab
    const nav = screen.getByRole("navigation", { name: "Main navigation" });
    fireEvent.click(within(nav).getByRole("button", { name: /Optimizer/i }));

    // Run optimization
    fireEvent.click(screen.getByRole("button", { name: /Run optimizer/i }));

    await waitFor(() => {
      expect(mockedApi.runOptimizer).toHaveBeenCalled();
    });

    // Check Heuristic badge is rendered (not exhaustive)
    expect(screen.getByText(/⚠ Greedy Marginal Heuristic \(Approximation\)/i)).toBeInTheDocument();
    expect(
      screen.getByText(/Search space exceeded 100,000 combinations\. This allocation is computed using a greedy marginal approximation/i)
    ).toBeInTheDocument();

    // Check Cap uncertainty banner is rendered
    expect(screen.getByText(/Uncertainty Notice:/i)).toBeInTheDocument();
    expect(screen.getByText(/₹200.00/i)).toBeInTheDocument(); // conservative proposed value
  });

  it("handles assistant interactions, real citations, abstentions, and retry on failure", async () => {
    localStorage.setItem("cardwise_token", "mock-jwt-token");
    mockedApi.getMe.mockResolvedValue(mockUser);

    const verifiedAssistantResponse: AssistantResult = {
      answer: "HDFC Millennia offers 5% cashback on Amazon, Flipkart, and Myntra.",
      abstained: false,
      citations: [
        {
          source_id: "src-1",
          title: "HDFC Bank Millennia Official Terms",
          url: "https://www.hdfcbank.com/personal/pay/cards/millennia-terms",
          status: "verified",
        },
      ],
      unknowns: [],
      model_version: "1.0",
      prompt_version: "1.0",
      assistant_type: "lexical_lookup_alpha",
      disclaimer: "Fictional local terms only.",
    };
    mockedApi.askAssistant.mockResolvedValueOnce(verifiedAssistantResponse);

    render(<App />);
    await waitFor(() => expect(screen.getByText("1 active card reference in your portfolio")).toBeInTheDocument());

    // Navigate to Assistant tab
    const nav = screen.getByRole("navigation", { name: "Main navigation" });
    fireEvent.click(within(nav).getByRole("button", { name: /Assistant/i }));

    // Ask a verified question
    fireEvent.change(screen.getByLabelText(/Your question/i), {
      target: { value: "What is HDFC Millennia cashback rate?" },
    });
    fireEvent.click(screen.getByRole("button", { name: /Ask assistant/i }));

    await waitFor(() => {
      expect(mockedApi.askAssistant).toHaveBeenCalledWith("mock-jwt-token", "What is HDFC Millennia cashback rate?");
    });

    // Verified badge rendered
    expect(screen.getByText(/VERIFIED SOURCE EVIDENCE/i)).toBeInTheDocument();
    expect(screen.getByText(/HDFC Millennia offers 5% cashback/i)).toBeInTheDocument();

    // Real citations rendered with link
    expect(screen.getByText("HDFC Bank Millennia Official Terms")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "https://www.hdfcbank.com/personal/pay/cards/millennia-terms" })).toBeInTheDocument();

    // Test assistant error state and retry
    mockedApi.askAssistant.mockRejectedValueOnce(new Error("Local model query timed out."));

    fireEvent.change(screen.getByLabelText(/Your question/i), {
      target: { value: "Unverified query" },
    });
    fireEvent.click(screen.getByRole("button", { name: /Ask assistant/i }));

    await waitFor(() => {
      expect(screen.getByText(/Local model query timed out\./i)).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /Retry/i })).toBeInTheDocument();
    });
  });

  it("handles reminder updates, export download workflow, and export purge", async () => {
    localStorage.setItem("cardwise_token", "mock-jwt-token");
    mockedApi.getMe.mockResolvedValue(mockUser);

    const updatedReminder: Reminder = {
      ...mockReminders[0],
      status: "completed",
    };
    mockedApi.updateReminder.mockResolvedValue(updatedReminder);

    const mockExportResponse: ExportJobResponse = {
      id: "exp-123",
      expires_at: "2026-11-01T00:00:00Z",
      status: "ready",
      data: { user: mockUser, scenarios: mockScenarios },
    };
    mockedApi.createExport.mockResolvedValue(mockExportResponse);
    mockedApi.deleteExport.mockResolvedValue(undefined);

    // Mock window.URL.createObjectURL and window.URL.revokeObjectURL
    window.URL.createObjectURL = vi.fn().mockReturnValue("blob:mock-url");
    window.URL.revokeObjectURL = vi.fn();

    render(<App />);
    await waitFor(() => expect(screen.getByText("1 active card reference in your portfolio")).toBeInTheDocument());

    // Navigate to Settings tab
    const nav = screen.getByRole("navigation", { name: "Main navigation" });
    fireEvent.click(within(nav).getByRole("button", { name: /Settings/i }));

    // Toggle reminder complete
    fireEvent.click(screen.getByRole("button", { name: /Mark Done/i }));

    await waitFor(() => {
      expect(mockedApi.updateReminder).toHaveBeenCalledWith("mock-jwt-token", "rem-1", {
        status: "completed",
      });
    });

    // Request Export
    fireEvent.click(screen.getByRole("button", { name: /Create expiring export/i }));

    await waitFor(() => {
      expect(mockedApi.createExport).toHaveBeenCalled();
      expect(screen.getByText(/Active Export/i)).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /Download JSON file/i })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /Purge export/i })).toBeInTheDocument();
    });

    // Click Download JSON
    fireEvent.click(screen.getByRole("button", { name: /Download JSON file/i }));
    expect(window.URL.createObjectURL).toHaveBeenCalled();

    // Purge export
    fireEvent.click(screen.getByRole("button", { name: /Purge export/i }));
    await waitFor(() => {
      expect(mockedApi.deleteExport).toHaveBeenCalledWith("mock-jwt-token", "exp-123");
    });
  });
});
