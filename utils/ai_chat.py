"""
AI Chat Widget — Reusable on all dashboard pages.
Answers natural language questions about the energy data.
Uses OpenRouter LLM when available, shows helpful message otherwise.
"""

import streamlit as st
from utils.llm_client import is_llm_available, answer_data_question, get_active_model


def _get_chat_mode_label() -> str:
    """Return label showing current chat mode."""
    try:
        from agents.config import is_agent_mode_available
        if is_agent_mode_available():
            return "⚡ Agent Mode (can run models + tools)"
    except Exception:
        pass
    if is_llm_available():
        return f"Model: {get_active_model()}"
    return "Rule-based mode (add OPENROUTER_API_KEY for AI chat)"


def build_context(page_name: str = "general") -> str:
    """Build data context string for the LLM from current session data."""
    context_parts = [f"Page: {page_name}"]

    try:
        from utils.data_loader import load_stores, load_daily_energy, load_diesel_prices
        stores = load_stores()
        energy = load_daily_energy()
        prices = load_diesel_prices()

        # Basic stats
        context_parts.append(f"Total stores: {len(stores)}")
        context_parts.append(f"Sectors: {', '.join(stores['sector'].unique())}")
        context_parts.append(f"Date range: {energy['date'].min().date()} to {energy['date'].max().date()}")

        # Latest metrics
        latest_energy = energy[energy["date"] == energy["date"].max()]
        context_parts.append(f"Latest date: {energy['date'].max().date()}")
        context_parts.append(f"Avg blackout today: {latest_energy['blackout_hours'].mean():.1f} hrs")
        context_parts.append(f"Total diesel cost today: {latest_energy['diesel_cost_mmk'].sum():,.0f} MMK")
        context_parts.append(f"Diesel price: {prices['diesel_price_mmk'].iloc[-1]:,.0f} MMK/L")

        # Solar
        solar_count = stores["has_solar"].sum()
        context_parts.append(f"Solar sites: {solar_count} of {len(stores)}")
        context_parts.append(f"Solar kWh today: {latest_energy['solar_kwh'].sum():,.0f}")

        # Per sector summary
        sector_cost = latest_energy.merge(stores[["store_id", "sector"]], on="store_id")
        for sector in sector_cost["sector"].unique():
            s = sector_cost[sector_cost["sector"] == sector]
            context_parts.append(
                f"{sector}: {len(s)} stores, "
                f"avg blackout {s['blackout_hours'].mean():.1f}hrs, "
                f"diesel cost {s['diesel_cost_mmk'].sum():,.0f} MMK"
            )

        # 7-day trends
        last_7 = energy[energy["date"] > energy["date"].max() - __import__("pandas").Timedelta(days=7)]
        prev_7 = energy[
            (energy["date"] > energy["date"].max() - __import__("pandas").Timedelta(days=14)) &
            (energy["date"] <= energy["date"].max() - __import__("pandas").Timedelta(days=7))
        ]
        if len(prev_7) > 0:
            cost_change = (last_7["total_energy_cost_mmk"].sum() - prev_7["total_energy_cost_mmk"].sum()) / prev_7["total_energy_cost_mmk"].sum() * 100
            bo_change = (last_7["blackout_hours"].mean() - prev_7["blackout_hours"].mean()) / prev_7["blackout_hours"].mean() * 100
            context_parts.append(f"7-day energy cost change: {cost_change:+.1f}%")
            context_parts.append(f"7-day blackout change: {bo_change:+.1f}%")

        # FX
        try:
            from utils.data_loader import load_fx_rates
            fx = load_fx_rates()
            context_parts.append(f"USD/MMK rate: {fx['usd_mmk'].iloc[-1]:,.0f}")
        except Exception:
            pass

        # Inventory
        try:
            from utils.data_loader import load_diesel_inventory
            inv = load_diesel_inventory()
            latest_inv = inv[inv["date"] == inv["date"].max()]
            low_stores = (latest_inv["days_of_coverage"] < 2).sum()
            context_parts.append(f"Stores below 2 days diesel: {low_stores}")
            context_parts.append(f"Avg diesel coverage: {latest_inv['days_of_coverage'].mean():.1f} days")
        except Exception:
            pass

    except Exception as e:
        context_parts.append(f"Error loading context: {str(e)}")

    return "\n".join(context_parts)


def render_chat_widget(page_name: str = "Dashboard"):
    """Render the AI chat widget at the bottom of a page.

    Args:
        page_name: Name of the current page for context
    """
    st.markdown("")
    st.markdown("""
    <div style="background:linear-gradient(135deg,#0f172a,#1e293b);color:white;padding:14px 18px;border-radius:12px 12px 0 0">
        <div style="display:flex;align-items:center;gap:8px">
            <span style="font-size:1.2rem">🤖</span>
            <strong>AI Assistant</strong>
            <span style="font-size:0.8rem;opacity:0.6;margin-left:auto">""" +
        (_get_chat_mode_label()) +
    """</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Chat container — load from SQLite
    from utils.database import get_chat_messages, save_chat_message, clear_chat_messages

    chat_page = page_name

    # Load persistent messages from DB
    db_messages = get_chat_messages(chat_page, limit=50)

    # Display chat history from database
    for msg in db_messages:
        if msg["role"] == "user":
            st.markdown(f"""
            <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;padding:10px 14px;margin:6px 0">
                <div style="display:flex;justify-content:space-between">
                    <strong style="color:#1e40af">You</strong>
                    <span style="font-size:0.7rem;color:#94a3b8">{msg.get('created_at', '')}</span>
                </div>
                <div style="margin-top:4px">{msg['content']}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:10px;padding:10px 14px;margin:6px 0">
                <div style="display:flex;justify-content:space-between">
                    <strong style="color:#166534">AI</strong>
                    <span style="font-size:0.7rem;color:#94a3b8">{msg.get('created_at', '')}</span>
                </div>
                <div style="margin-top:4px">{msg['content']}</div>
            </div>
            """, unsafe_allow_html=True)

    # Input
    col1, col2 = st.columns([5, 1])
    with col1:
        question = st.text_input(
            "Ask about your energy data...",
            placeholder="e.g., Which stores should I close today? Why did energy cost spike?",
            key=f"input_chat_{page_name.replace(' ', '_').lower()}",
            label_visibility="collapsed",
        )
    with col2:
        ask_clicked = st.button("Ask", key=f"btn_chat_{page_name.replace(' ', '_').lower()}",
                                type="primary", use_container_width=True)

    if ask_clicked and question:
        # Save user message to DB
        save_chat_message(chat_page, "user", question)

        # Try agentic chat first (tool-calling agent)
        answer = None
        agent_used = False
        try:
            from agents.config import is_agent_mode_available
            if is_agent_mode_available():
                from agents.chat_agent import ChatAgent
                with st.spinner("🤖 Agent thinking... (may run models)"):
                    agent = ChatAgent()
                    # Load recent chat history for context
                    history = []
                    for msg in db_messages[-6:]:
                        history.append({"role": msg["role"], "content": msg["content"]})
                    result = agent.run(question, context={"page": page_name},
                                       conversation_history=history)
                    if result.success and result.text:
                        answer = result.text
                        agent_used = True
                        # Show tool calls in expander if any
                        if result.tool_calls_made:
                            tools_used = ", ".join(tc["name"] for tc in result.tool_calls_made)
                            answer = f"*Tools used: {tools_used}*\n\n{answer}"
        except Exception:
            pass  # Fall through to standard LLM or rule-based

        # Fallback: standard LLM chat
        if not answer and is_llm_available():
            with st.spinner("Thinking..."):
                context = build_context(page_name)
                answer = answer_data_question(question, context)

        # Fallback: rule-based
        if not answer:
            answer = _rule_based_answer(question)

        # Save AI answer to DB
        save_chat_message(chat_page, "assistant", answer)
        st.rerun()

    # Clear chat button
    if db_messages:
        if st.button("Clear chat history", key=f"clear_chat_{page_name.replace(' ', '_').lower()}"):
            clear_chat_messages(chat_page)
            st.rerun()


def _rule_based_answer(question: str) -> str:
    """Simple rule-based answers when no LLM is available."""
    q = question.lower()

    try:
        from utils.data_loader import load_stores, load_daily_energy, load_diesel_prices
        stores = load_stores()
        energy = load_daily_energy()
        prices = load_diesel_prices()
        latest = energy[energy["date"] == energy["date"].max()]

        if any(w in q for w in ["close", "shut", "which store"]):
            # Find stores with high energy cost ratio
            return (
                f"Based on current data, check the Store Decisions page (Page 5) for the AI-generated "
                f"Daily Operating Plan. Currently tracking {len(stores)} stores. "
                f"Today's avg blackout: {latest['blackout_hours'].mean():.1f} hrs. "
                f"Diesel price: {prices['diesel_price_mmk'].iloc[-1]:,.0f} MMK/L. "
                f"For full FULL/REDUCED/CLOSE recommendations, see the Store Decisions dashboard."
            )

        if any(w in q for w in ["diesel", "price", "cost", "fuel"]):
            price = prices["diesel_price_mmk"].iloc[-1]
            prev = prices["diesel_price_mmk"].iloc[-7]
            change = (price - prev) / prev * 100
            return (
                f"Current diesel price: {price:,.0f} MMK/L ({change:+.1f}% in 7 days). "
                f"Today's total diesel cost across network: {latest['diesel_cost_mmk'].sum():,.0f} MMK. "
                f"Check the Diesel Intelligence page for 7-day forecast and buy/hold signal."
            )

        if any(w in q for w in ["blackout", "power", "outage"]):
            avg = latest["blackout_hours"].mean()
            return (
                f"Today's average blackout: {avg:.1f} hours across {len(latest)} stores. "
                f"Check the Blackout Monitor page for township-level predictions and tomorrow's forecast."
            )

        if any(w in q for w in ["solar", "panel", "renewable"]):
            solar_count = stores["has_solar"].sum()
            solar_kwh = latest["solar_kwh"].sum()
            return (
                f"{solar_count} sites have solar panels. Today's generation: {solar_kwh:,.0f} kWh. "
                f"Check Solar Performance page for diesel offset and CAPEX prioritization."
            )

        if any(w in q for w in ["alert", "warning", "critical"]):
            return "Check the Alerts Center page for all Tier 1/2/3 alerts from all 8 AI models."

        return (
            f"I'm running in rule-based mode (no LLM API key configured). "
            f"I can answer basic questions about diesel prices, blackouts, solar, and store decisions. "
            f"Add your OpenRouter API key as OPENROUTER_API_KEY environment variable for full AI chat. "
            f"Current stats: {len(stores)} stores, "
            f"avg blackout {latest['blackout_hours'].mean():.1f} hrs, "
            f"diesel {prices['diesel_price_mmk'].iloc[-1]:,.0f} MMK/L."
        )

    except Exception as e:
        return f"Could not load data to answer your question. Error: {str(e)}"
