import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import { MCIProvider, useMCI } from "./MCIContext";
import type { MCISnapshot } from "../types/mci";

jest.mock("../hooks/useAuth", () => ({
  useAuth: () => ({
    user: null,
    isAuthenticated: true,
    getAccessToken: () => null,
    loading: false,
    login: async () => undefined,
    register: async () => undefined,
    logout: () => undefined,
  }),
}));

const fixtureSnapshot: MCISnapshot = {
  composite_score: 56.0,
  composite_direction: "improving",
  composite_severity: "amber",
  composite_headline: "Mixed worst constituent headline",
  snapshot_date: "2026-03-18",
  next_refresh: "2026-03-25",
  constituents: [
    {
      name: "Labor Market Strength",
      slug: "labor_market_strength",
      current_value: 1.3,
      previous_value: 1.1,
      direction: "up",
      severity: "green",
      headline: "Labor market improving",
      source: "mock",
      as_of: "2026-03-18",
      weight: 0.25,
      raw: {},
    },
    {
      name: "Housing Affordability Pressure",
      slug: "housing_affordability_pressure",
      current_value: 8.0,
      previous_value: 7.8,
      direction: "up",
      severity: "red",
      headline: "Rates are high",
      source: "mock",
      as_of: "2026-03-18",
      weight: 0.25,
      raw: {},
    },
    {
      name: "Transportation Cost Burden",
      slug: "transportation_cost_burden",
      current_value: 3.5,
      previous_value: 3.6,
      direction: "down",
      severity: "amber",
      headline: "Gas prices elevated",
      source: "mock",
      as_of: "2026-03-18",
      weight: 0.1,
      raw: {},
    },
    {
      name: "Consumer Debt Conditions",
      slug: "consumer_debt_conditions",
      current_value: 20.0,
      previous_value: 21.0,
      direction: "down",
      severity: "amber",
      headline: "APR in middle range",
      source: "mock",
      as_of: "2026-03-18",
      weight: 0.2,
      raw: {},
    },
    {
      name: "Career Income Mobility",
      slug: "career_income_mobility",
      current_value: 2.8,
      previous_value: 2.7,
      direction: "up",
      severity: "green",
      headline: "Workers feel confident",
      source: "mock",
      as_of: "2026-03-18",
      weight: 0.15,
      raw: {},
    },
    {
      name: "Wellness Cost Index",
      slug: "wellness_cost_index",
      current_value: 5.0,
      previous_value: 5.0,
      direction: "flat",
      severity: "green",
      headline: "Healthcare is benchmarked at 5%",
      source: "mock",
      as_of: "2023-12-31",
      weight: 0.05,
      raw: {},
    },
  ],
};

function MCIConsumer() {
  const { snapshot, loading } = useMCI();
  return (
    <div>
      <span data-testid="loading">{loading ? "true" : "false"}</span>
      <span data-testid="score">{snapshot ? snapshot.composite_score : ""}</span>
    </div>
  );
}

describe("MCIContext", () => {
  it("fetches snapshot once and exposes it via useMCI", async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => fixtureSnapshot,
    });

    const localStorageMock = {
      getItem: jest.fn().mockReturnValue("mock-token"),
      setItem: jest.fn(),
      removeItem: jest.fn(),
      clear: jest.fn(),
      length: 0,
      key: jest.fn(),
    };
    Object.defineProperty(window, "localStorage", { value: localStorageMock });

    render(
      <MCIProvider>
        <MCIConsumer />
      </MCIProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId("loading")).toHaveTextContent("false");
      expect(screen.getByTestId("score")).toHaveTextContent("56");
    });
  });
});

