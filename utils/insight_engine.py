"""
AI Insight Generator Engine
Compares current vs previous period KPIs and generates plain English insights.
Uses statistical analysis + rule-based templates to produce actionable text.
"""

import pandas as pd
import numpy as np
from datetime import timedelta
from config.settings import CURRENCY, THRESHOLDS


class InsightEngine:
    """Generate AI-powered text insights from energy and sales data."""

    def __init__(self, stores_df, energy_df, sales_df, inventory_df, prices_df, fx_df=None):
        self.stores = stores_df
        self.energy = energy_df
        self.sales = sales_df
        self.inventory = inventory_df
        self.prices = prices_df
        self.fx = fx_df
        self.latest_date = energy_df["date"].max()
        self.insights = []

    def generate_all(self, lookback_days=7) -> list:
        """Generate all insights comparing last `lookback_days` vs the period before."""
        self.insights = []
        self._energy_cost_insights(lookback_days)
        self._blackout_insights(lookback_days)
        self._diesel_price_insights(lookback_days)
        self._diesel_inventory_insights()
        self._solar_insights(lookback_days)
        self._store_profitability_insights(lookback_days)
        self._sector_comparison_insights(lookback_days)
        if self.fx is not None:
            self._fx_insights(lookback_days)

        # Sort by priority (critical first)
        self.insights.sort(key=lambda x: {"critical": 0, "warning": 1, "positive": 2, "info": 3}.get(x["level"], 4))
        return self.insights

    def _add(self, text: str, level: str = "info", category: str = "general", metric: str = None, change_pct: float = None):
        self.insights.append({
            "text": text,
            "level": level,       # critical, warning, positive, info
            "category": category,  # energy, diesel, blackout, solar, inventory, profitability, fx
            "metric": metric,
            "change_pct": change_pct,
        })

    def _period_split(self, df, lookback_days):
        """Split dataframe into current period and previous period."""
        current = df[df["date"] > self.latest_date - timedelta(days=lookback_days)]
        previous = df[
            (df["date"] > self.latest_date - timedelta(days=lookback_days * 2)) &
            (df["date"] <= self.latest_date - timedelta(days=lookback_days))
        ]
        return current, previous

    def _pct_change(self, current_val, previous_val):
        if previous_val == 0:
            return 0
        return round((current_val - previous_val) / abs(previous_val) * 100, 1)

    # ── Energy Cost Insights ──

    def _energy_cost_insights(self, lookback_days):
        curr, prev = self._period_split(self.energy, lookback_days)
        if len(prev) == 0:
            return

        curr_cost = curr["total_energy_cost_mmk"].sum()
        prev_cost = prev["total_energy_cost_mmk"].sum()
        change = self._pct_change(curr_cost, prev_cost)

        if abs(change) > 15:
            direction = "increased" if change > 0 else "decreased"
            level = "warning" if change > 0 else "positive"
            self._add(
                f"Total energy cost {direction} by {abs(change):.0f}% this week "
                f"({curr_cost/1e6:,.1f}M vs {prev_cost/1e6:,.1f}M {CURRENCY})",
                level=level, category="energy", metric="energy_cost", change_pct=change
            )

        # Diesel vs grid split
        curr_diesel = curr["diesel_cost_mmk"].sum()
        prev_diesel = prev["diesel_cost_mmk"].sum()
        diesel_change = self._pct_change(curr_diesel, prev_diesel)
        if abs(diesel_change) > 20:
            direction = "surged" if diesel_change > 20 else "dropped"
            self._add(
                f"Diesel cost {direction} {abs(diesel_change):.0f}% — "
                f"now {curr_diesel/curr_cost*100:.0f}% of total energy cost",
                level="warning" if diesel_change > 20 else "positive",
                category="energy", metric="diesel_cost", change_pct=diesel_change
            )

        # Top 3 stores with biggest cost increase
        curr_by_store = curr.groupby("store_id")["total_energy_cost_mmk"].sum()
        prev_by_store = prev.groupby("store_id")["total_energy_cost_mmk"].sum()
        store_changes = ((curr_by_store - prev_by_store) / prev_by_store.clip(lower=1) * 100).sort_values(ascending=False)

        worst = store_changes.head(3)
        for sid, pct in worst.items():
            if pct > 25:
                name = self.stores[self.stores["store_id"] == sid]["name"].values
                name = name[0] if len(name) > 0 else sid
                self._add(
                    f"{name}: energy cost up {pct:.0f}% vs last week — investigate generator efficiency or blackout increase",
                    level="warning", category="energy", metric="store_cost_spike", change_pct=pct
                )

    # ── Blackout Insights ──

    def _blackout_insights(self, lookback_days):
        curr, prev = self._period_split(self.energy, lookback_days)
        if len(prev) == 0:
            return

        curr_avg = curr["blackout_hours"].mean()
        prev_avg = prev["blackout_hours"].mean()
        change = self._pct_change(curr_avg, prev_avg)

        if abs(change) > 10:
            direction = "worsened" if change > 0 else "improved"
            level = "warning" if change > 0 else "positive"
            self._add(
                f"Average blackout hours {direction} by {abs(change):.0f}% "
                f"({curr_avg:.1f} hrs/day vs {prev_avg:.1f} hrs/day previously)",
                level=level, category="blackout", metric="avg_blackout", change_pct=change
            )

        # Township-level changes
        curr_merged = curr.merge(self.stores[["store_id", "township"]], on="store_id")
        prev_merged = prev.merge(self.stores[["store_id", "township"]], on="store_id")

        curr_township = curr_merged.groupby("township")["blackout_hours"].mean()
        prev_township = prev_merged.groupby("township")["blackout_hours"].mean()

        for township in curr_township.index:
            if township in prev_township.index:
                t_change = self._pct_change(curr_township[township], prev_township[township])
                if t_change > 30:
                    self._add(
                        f"{township} township: blackout hours up {t_change:.0f}% — "
                        f"now averaging {curr_township[township]:.1f} hrs/day",
                        level="warning", category="blackout", metric="township_blackout"
                    )
                elif t_change < -20:
                    self._add(
                        f"{township} township: blackout hours improved {abs(t_change):.0f}% — "
                        f"down to {curr_township[township]:.1f} hrs/day",
                        level="positive", category="blackout", metric="township_blackout"
                    )

    # ── Diesel Price Insights ──

    def _diesel_price_insights(self, lookback_days):
        if len(self.prices) < 14:
            return

        latest_price = self.prices["diesel_price_mmk"].iloc[-1]
        week_ago = self.prices["diesel_price_mmk"].iloc[-7]
        change = self._pct_change(latest_price, week_ago)

        if abs(change) > 5:
            direction = "up" if change > 0 else "down"
            level = "warning" if change > 5 else "positive"
            self._add(
                f"Diesel price {direction} {abs(change):.1f}% in 7 days — "
                f"now {latest_price:,.0f} {CURRENCY}/liter",
                level=level, category="diesel", metric="diesel_price", change_pct=change
            )

        # Volatility check
        recent_std = self.prices["diesel_price_mmk"].tail(7).std()
        prev_std = self.prices["diesel_price_mmk"].iloc[-14:-7].std()
        if recent_std > prev_std * 1.5 and recent_std > 50:
            self._add(
                f"Diesel price volatility increased — daily swings of {recent_std:.0f} {CURRENCY} "
                f"(was {prev_std:.0f}). Market unstable, consider bulk purchase.",
                level="warning", category="diesel", metric="price_volatility"
            )

    # ── Inventory Insights ──

    def _diesel_inventory_insights(self):
        latest = self.inventory[self.inventory["date"] == self.inventory["date"].max()]
        if len(latest) == 0:
            return

        critical = latest[latest["days_of_coverage"] < THRESHOLDS["diesel_critical_days"]]
        warning = latest[latest["days_of_coverage"] < THRESHOLDS["diesel_warning_days"]]

        if len(critical) > 0:
            names = critical.merge(self.stores[["store_id", "name"]], on="store_id")["name"].tolist()
            self._add(
                f"{len(critical)} store(s) at CRITICAL diesel level (under 1 day): "
                f"{', '.join(names[:5])}",
                level="critical", category="inventory", metric="diesel_critical"
            )

        if len(warning) > len(critical):
            count = len(warning) - len(critical)
            self._add(
                f"{count} additional store(s) below 2 days diesel coverage — order soon",
                level="warning", category="inventory", metric="diesel_warning"
            )

        # Network-wide average
        avg_coverage = latest["days_of_coverage"].mean()
        if avg_coverage < 5:
            self._add(
                f"Network average diesel coverage is {avg_coverage:.1f} days — below comfortable 5-day buffer",
                level="warning", category="inventory", metric="avg_coverage"
            )

    # ── Solar Insights ──

    def _solar_insights(self, lookback_days):
        curr, prev = self._period_split(self.energy, lookback_days)
        if len(prev) == 0:
            return

        solar_stores = self.stores[self.stores["has_solar"] == True]["store_id"].tolist()
        curr_solar = curr[curr["store_id"].isin(solar_stores)]["solar_kwh"].sum()
        prev_solar = prev[prev["store_id"].isin(solar_stores)]["solar_kwh"].sum()

        if prev_solar > 0:
            change = self._pct_change(curr_solar, prev_solar)
            if abs(change) > 10:
                direction = "up" if change > 0 else "down"
                level = "positive" if change > 0 else "warning"
                self._add(
                    f"Solar generation {direction} {abs(change):.0f}% this week "
                    f"({curr_solar:,.0f} kWh vs {prev_solar:,.0f} kWh) — "
                    f"{'good weather boosting output' if change > 0 else 'check panels or weather impact'}",
                    level=level, category="solar", metric="solar_generation", change_pct=change
                )

    # ── Store Profitability ──

    def _store_profitability_insights(self, lookback_days):
        curr_energy, prev_energy = self._period_split(self.energy, lookback_days)
        curr_sales, prev_sales = self._period_split(self.sales, lookback_days)

        if len(prev_energy) == 0 or len(prev_sales) == 0:
            return

        # Daily margin vs energy cost per store
        curr_margin = curr_sales.groupby("store_id")["gross_margin_mmk"].sum()
        curr_cost = curr_energy.groupby("store_id")["total_energy_cost_mmk"].sum()

        losing = []
        for sid in curr_cost.index:
            if sid in curr_margin.index:
                if curr_cost[sid] > curr_margin[sid] * 0.5:  # Energy > 50% of margin
                    name = self.stores[self.stores["store_id"] == sid]["name"].values
                    name = name[0] if len(name) > 0 else sid
                    ratio = curr_cost[sid] / max(curr_margin[sid], 1) * 100
                    losing.append((name, ratio))

        losing.sort(key=lambda x: -x[1])
        if losing:
            self._add(
                f"{len(losing)} store(s) with energy cost exceeding 50% of margin — "
                f"worst: {losing[0][0]} at {losing[0][1]:.0f}%",
                level="warning" if len(losing) < 5 else "critical",
                category="profitability", metric="high_energy_ratio"
            )

    # ── Sector Comparison ──

    def _sector_comparison_insights(self, lookback_days):
        curr, prev = self._period_split(self.energy, lookback_days)
        if len(prev) == 0:
            return

        curr_merged = curr.merge(self.stores[["store_id", "sector"]], on="store_id")
        prev_merged = prev.merge(self.stores[["store_id", "sector"]], on="store_id")

        curr_sector = curr_merged.groupby("sector")["total_energy_cost_mmk"].sum()
        prev_sector = prev_merged.groupby("sector")["total_energy_cost_mmk"].sum()

        worst_sector = None
        worst_change = 0
        for sector in curr_sector.index:
            if sector in prev_sector.index:
                change = self._pct_change(curr_sector[sector], prev_sector[sector])
                if change > worst_change:
                    worst_change = change
                    worst_sector = sector

        if worst_sector and worst_change > 10:
            self._add(
                f"{worst_sector} sector driving cost increase — energy cost up {worst_change:.0f}% this week",
                level="warning", category="energy", metric="sector_driver"
            )

    # ── FX Insights ──

    def _fx_insights(self, lookback_days):
        if self.fx is None or len(self.fx) < 14:
            return

        latest_fx = self.fx["usd_mmk"].iloc[-1]
        week_ago = self.fx["usd_mmk"].iloc[-7]
        change = self._pct_change(latest_fx, week_ago)

        if abs(change) > 2:
            direction = "depreciated" if change > 0 else "strengthened"
            impact = "pushing diesel costs higher" if change > 0 else "may ease diesel costs"
            self._add(
                f"MMK {direction} {abs(change):.1f}% vs USD this week "
                f"({latest_fx:,.0f} MMK/USD) — {impact}",
                level="warning" if change > 3 else "info",
                category="fx", metric="fx_rate", change_pct=change
            )

    # ── Output Formatting ──

    def get_insights_by_level(self, level: str) -> list:
        return [i for i in self.insights if i["level"] == level]

    def get_insights_by_category(self, category: str) -> list:
        return [i for i in self.insights if i["category"] == category]

    def get_top_insights(self, n: int = 5) -> list:
        return self.insights[:n]

    def get_summary_text(self) -> str:
        """Generate a single paragraph summary of all insights."""
        if not self.insights:
            return "No significant changes detected this period. Operations stable."

        critical = self.get_insights_by_level("critical")
        warnings = self.get_insights_by_level("warning")
        positives = self.get_insights_by_level("positive")

        parts = []

        if critical:
            parts.append(f"URGENT: {len(critical)} critical issue(s) — {critical[0]['text']}")

        if warnings:
            parts.append(f"{len(warnings)} warning(s) detected this week")
            # Add top 2 warning details
            for w in warnings[:2]:
                parts.append(w["text"])

        if positives:
            parts.append(f"Positive: {positives[0]['text']}")

        if not parts:
            parts.append("Operations within normal parameters. No significant deviations detected.")

        return " | ".join(parts)

    def get_briefing_paragraph(self) -> str:
        """Generate a morning briefing paragraph."""
        critical = self.get_insights_by_level("critical")
        warnings = self.get_insights_by_level("warning")
        positives = self.get_insights_by_level("positive")

        lines = ["AI INSIGHT SUMMARY", "=" * 40]

        if critical:
            lines.append(f"\nCRITICAL ({len(critical)}):")
            for c in critical:
                lines.append(f"  ! {c['text']}")

        if warnings:
            lines.append(f"\nWARNINGS ({len(warnings)}):")
            for w in warnings[:5]:
                lines.append(f"  > {w['text']}")
            if len(warnings) > 5:
                lines.append(f"  ... and {len(warnings) - 5} more")

        if positives:
            lines.append(f"\nPOSITIVE ({len(positives)}):")
            for p in positives[:3]:
                lines.append(f"  + {p['text']}")

        if not critical and not warnings:
            lines.append("\nAll systems normal. No significant deviations detected.")

        return "\n".join(lines)

    def get_llm_executive_summary(self, kpis: dict = None) -> str:
        """Get LLM-polished executive summary. Falls back to rule-based if no LLM."""
        from utils.llm_client import generate_executive_summary, is_llm_available

        if is_llm_available():
            llm_summary = generate_executive_summary(self.insights, kpis)
            if llm_summary:
                return llm_summary

        # Fallback: rule-based summary
        return self.get_summary_text()

    def get_llm_sector_summary(self, sector: str) -> str:
        """Get LLM-polished sector summary. Falls back to rule-based."""
        from utils.llm_client import generate_sector_insights, is_llm_available

        sector_insights = [i for i in self.insights if
                          sector.lower() in i.get("text", "").lower() or
                          i.get("category") in ["energy", "blackout", "profitability"]]

        if is_llm_available() and sector_insights:
            llm_text = generate_sector_insights(sector, sector_insights)
            if llm_text:
                return llm_text

        # Fallback
        if sector_insights:
            return " | ".join([i["text"] for i in sector_insights[:3]])
        return f"No significant changes in {sector} this period."
