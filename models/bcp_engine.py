"""
BCP Engine — Business Continuity Planning model.
Computes BCP scores, generates contingency playbooks, calculates RTO,
maps critical assets, and manages incident logs.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta


class BCPEngine:
    """Business Continuity Planning engine for energy resilience."""

    def __init__(self):
        self.scores = None
        self.playbooks = None

    def compute_bcp_scores(self, stores_df, energy_df, inventory_df, sales_df=None):
        """Compute composite BCP resilience score per store (0-100).

        Score components (weighted):
        - Power Backup (25%): generator_kw relative to channel avg
        - Fuel Reserve (25%): days of diesel coverage
        - Solar Resilience (15%): has_solar + solar contribution
        - Cold Chain Risk (15%): cold_chain exposure vs backup capacity
        - Operational Resilience (20%): ERI + blackout survivability
        """
        results = []
        latest_date = energy_df["date"].max()
        week_ago = latest_date - pd.Timedelta(days=7)
        recent = energy_df[energy_df["date"] > week_ago]

        # Get latest inventory
        latest_inv = inventory_df[inventory_df["date"] == inventory_df["date"].max()]

        # Channel averages for generator comparison
        channel_gen_avg = stores_df.groupby("channel")["generator_kw"].mean()

        for _, store in stores_df.iterrows():
            sid = store["store_id"]
            store_energy = recent[recent["store_id"] == sid]
            store_inv = latest_inv[latest_inv["store_id"] == sid]

            # 1. Power Backup Score (25%) — generator capacity vs channel avg
            gen_kw = store["generator_kw"]
            channel_avg = channel_gen_avg.get(store["channel"], gen_kw)
            power_ratio = min(gen_kw / max(channel_avg, 1), 1.5)
            power_score = min(power_ratio * 67, 100)  # 100% of avg = 67, 150% = 100

            # 2. Fuel Reserve Score (25%) — days of diesel coverage
            days_coverage = 0
            if len(store_inv) > 0:
                days_coverage = store_inv["days_of_coverage"].iloc[0]
            if days_coverage >= 7:
                fuel_score = 100
            elif days_coverage >= 5:
                fuel_score = 80
            elif days_coverage >= 3:
                fuel_score = 60
            elif days_coverage >= 2:
                fuel_score = 40
            elif days_coverage >= 1:
                fuel_score = 20
            else:
                fuel_score = 0

            # 3. Solar Resilience Score (15%)
            solar_score = 0
            if store["has_solar"]:
                solar_score = 70  # Base score for having solar
                if len(store_energy) > 0 and "solar_kwh" in store_energy.columns:
                    solar_kwh = store_energy["solar_kwh"].mean()
                    if solar_kwh > 50:
                        solar_score = 100
                    elif solar_kwh > 20:
                        solar_score = 85

            # 4. Cold Chain Risk Score (15%)
            if store["cold_chain"]:
                # Cold chain stores need more backup — penalize if insufficient
                avg_blackout = store_energy["blackout_hours"].mean() if len(store_energy) > 0 else 5
                gen_hours = store_energy["generator_hours"].mean() if len(store_energy) > 0 else 0
                gap = max(avg_blackout - gen_hours, 0)
                if gap <= 0:
                    cold_score = 100  # Generator covers all blackout hours
                elif gap <= 1:
                    cold_score = 75
                elif gap <= 2:
                    cold_score = 50
                elif gap <= 4:
                    cold_score = 25
                else:
                    cold_score = 0
            else:
                cold_score = 80  # No cold chain = less risk

            # 5. Operational Resilience Score (20%)
            if len(store_energy) > 0:
                avg_blackout = store_energy["blackout_hours"].mean()
                # Score based on how well store survives blackouts
                if avg_blackout <= 2:
                    ops_score = 100
                elif avg_blackout <= 4:
                    ops_score = 80
                elif avg_blackout <= 6:
                    ops_score = 60
                elif avg_blackout <= 8:
                    ops_score = 40
                elif avg_blackout <= 10:
                    ops_score = 20
                else:
                    ops_score = 0
            else:
                ops_score = 50

            # Weighted composite
            bcp_score = (
                power_score * 0.25 +
                fuel_score * 0.25 +
                solar_score * 0.15 +
                cold_score * 0.15 +
                ops_score * 0.20
            )

            # BCP Grade
            if bcp_score >= 80:
                grade = "A"
                status = "RESILIENT"
            elif bcp_score >= 60:
                grade = "B"
                status = "ADEQUATE"
            elif bcp_score >= 40:
                grade = "C"
                status = "AT RISK"
            elif bcp_score >= 20:
                grade = "D"
                status = "VULNERABLE"
            else:
                grade = "F"
                status = "CRITICAL"

            results.append({
                "store_id": sid,
                "name": store["name"],
                "sector": store["sector"],
                "channel": store["channel"],
                "township": store["township"],
                "bcp_score": round(bcp_score, 1),
                "grade": grade,
                "status": status,
                "power_backup_score": round(power_score, 0),
                "fuel_reserve_score": round(fuel_score, 0),
                "solar_resilience_score": round(solar_score, 0),
                "cold_chain_score": round(cold_score, 0),
                "ops_resilience_score": round(ops_score, 0),
                "generator_kw": gen_kw,
                "has_solar": store["has_solar"],
                "cold_chain": store["cold_chain"],
                "diesel_days": round(days_coverage, 1),
                "avg_blackout_hrs": round(store_energy["blackout_hours"].mean(), 1) if len(store_energy) > 0 else 0,
            })

        self.scores = pd.DataFrame(results).sort_values("bcp_score", ascending=True)
        return self.scores

    def generate_playbooks(self, stores_df, energy_df):
        """Generate contingency playbooks per threat level."""
        threat_levels = {
            "Level 1 — Grid Down 4h": {
                "duration": "0-4 hours", "severity": "normal",
                "actions": [
                    "Activate backup generators at all stores",
                    "Switch non-essential lighting to minimum",
                    "Monitor cold chain temperatures every 30 minutes",
                    "Notify store managers via SMS alert",
                ],
                "cold_chain": "Monitor only — no transfer needed within 4 hours",
                "staffing": "Normal staffing, extend breaks to conserve generator fuel",
                "procurement": "No immediate action needed",
            },
            "Level 2 — Grid Down 8h": {
                "duration": "4-8 hours", "severity": "warning",
                "actions": [
                    "Reduce to essential operations only (refrigeration + POS)",
                    "Shut down AC, decorative lighting, non-critical equipment",
                    "Begin cold chain temp logging every 15 minutes",
                    "Dairy zone: transfer perishables if temp exceeds 8°C",
                    "Deploy portable generators to stores without backup",
                    "Notify sector managers + Holdings",
                ],
                "cold_chain": "ALERT — Dairy at risk after 4h. Begin transfer protocol if no generator.",
                "staffing": "Reduce to essential staff. Send non-essential home.",
                "procurement": "Confirm next diesel delivery. Top up all tanks below 50%.",
            },
            "Level 3 — Grid Down 12h": {
                "duration": "8-12 hours", "severity": "critical",
                "actions": [
                    "CRITICAL: Evaluate store closure for non-profitable locations",
                    "Transfer ALL perishables from non-generator stores",
                    "Activate mutual aid — share generators between nearby stores",
                    "F&B: Stop production, sell remaining inventory at discount",
                    "Distribution: Halt outbound deliveries, protect cold chain",
                    "Property: Activate tenant communication protocol",
                    "Emergency diesel procurement — contact all suppliers",
                ],
                "cold_chain": "CRITICAL — Frozen goods at risk. Execute full cold chain transfer.",
                "staffing": "Skeleton crew only. Activate emergency rotation.",
                "procurement": "EMERGENCY: Order diesel from all available suppliers. Accept premium pricing.",
            },
            "Level 4 — Grid Down 24h+": {
                "duration": "24+ hours", "severity": "critical",
                "actions": [
                    "CLOSE all non-essential stores immediately",
                    "Consolidate operations to top-10 most resilient stores (by BCP score)",
                    "Execute full perishable disposal/donation protocol",
                    "Deploy mobile generators from Distribution warehouses",
                    "Activate insurance claim process for spoilage losses",
                    "Holdings: Emergency board briefing on operational continuity",
                    "Notify suppliers of potential order cancellations",
                    "Media: Prepare customer communication re: closures",
                ],
                "cold_chain": "TOTAL LOSS RISK — Execute disposal protocol. Document for insurance.",
                "staffing": "Emergency only. Activate crisis management team.",
                "procurement": "Strategic reserve mode. Ration fuel to top-priority stores only.",
            },
        }
        self.playbooks = threat_levels
        return threat_levels

    def compute_rto(self, stores_df, energy_df):
        """Compute Recovery Time Objective per store.

        RTO = estimated time to resume full operations after total blackout.
        Based on: generator capacity, fuel on hand, solar availability, cold chain needs.
        """
        results = []
        latest = energy_df["date"].max()
        recent = energy_df[energy_df["date"] > latest - pd.Timedelta(days=7)]

        for _, store in stores_df.iterrows():
            sid = store["store_id"]
            store_data = recent[recent["store_id"] == sid]

            # Base RTO depends on channel complexity
            channel_rto = {
                "Hypermarket": 4.0, "Supermarket": 2.0, "Convenience": 0.5,
                "Bakery": 1.5, "Restaurant": 1.0, "Beverage": 0.5,
                "Warehouse": 1.0, "Cold Chain": 3.0, "Logistics": 0.5,
                "Mall": 6.0, "Office": 1.0,
            }
            base_rto = channel_rto.get(store["channel"], 2.0)

            # Adjustments
            if store["has_solar"]:
                base_rto *= 0.7  # Solar reduces RTO by 30%
            if store["generator_kw"] >= 200:
                base_rto *= 0.8  # Large generator = faster recovery
            if store["cold_chain"]:
                base_rto *= 1.3  # Cold chain adds complexity

            # RTO benchmark
            if base_rto <= 1:
                rto_status = "EXCELLENT"
            elif base_rto <= 2:
                rto_status = "GOOD"
            elif base_rto <= 4:
                rto_status = "ACCEPTABLE"
            else:
                rto_status = "NEEDS IMPROVEMENT"

            results.append({
                "store_id": sid,
                "name": store["name"],
                "sector": store["sector"],
                "channel": store["channel"],
                "rto_hours": round(base_rto, 1),
                "rto_status": rto_status,
                "has_solar": store["has_solar"],
                "generator_kw": store["generator_kw"],
                "cold_chain": store["cold_chain"],
            })

        return pd.DataFrame(results).sort_values("rto_hours", ascending=False)

    def get_critical_assets(self, stores_df):
        """Map critical assets per store."""
        assets = []
        for _, store in stores_df.iterrows():
            store_assets = []
            store_assets.append({"type": "Generator", "capacity": f"{store['generator_kw']} kW",
                                 "status": "Active", "criticality": "HIGH"})
            if store["has_solar"]:
                store_assets.append({"type": "Solar Panel", "capacity": "Variable",
                                     "status": "Active", "criticality": "MEDIUM"})
            if store["cold_chain"]:
                store_assets.append({"type": "Cold Chain Unit", "capacity": "Dairy/Frozen/Fresh",
                                     "status": "Active", "criticality": "HIGH"})
            store_assets.append({"type": "Fuel Tank", "capacity": f"{store['generator_kw'] * 2}L est.",
                                 "status": "Active", "criticality": "HIGH"})

            assets.append({
                "store_id": store["store_id"],
                "name": store["name"],
                "sector": store["sector"],
                "township": store["township"],
                "assets": store_assets,
                "total_assets": len(store_assets),
                "high_criticality": len([a for a in store_assets if a["criticality"] == "HIGH"]),
            })
        return pd.DataFrame(assets)

    def get_summary(self):
        """Get BCP summary statistics."""
        if self.scores is None:
            return {}
        return {
            "total_stores": len(self.scores),
            "avg_bcp_score": round(self.scores["bcp_score"].mean(), 1),
            "min_bcp_score": round(self.scores["bcp_score"].min(), 1),
            "max_bcp_score": round(self.scores["bcp_score"].max(), 1),
            "grade_a": len(self.scores[self.scores["grade"] == "A"]),
            "grade_b": len(self.scores[self.scores["grade"] == "B"]),
            "grade_c": len(self.scores[self.scores["grade"] == "C"]),
            "grade_d": len(self.scores[self.scores["grade"] == "D"]),
            "grade_f": len(self.scores[self.scores["grade"] == "F"]),
            "critical_stores": len(self.scores[self.scores["status"] == "CRITICAL"]),
            "vulnerable_stores": len(self.scores[self.scores["status"] == "VULNERABLE"]),
            "resilient_stores": len(self.scores[self.scores["status"] == "RESILIENT"]),
        }
