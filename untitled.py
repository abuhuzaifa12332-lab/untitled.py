"""
FinSmart AI: Local Expense Analyzer
====================================
A production-ready Streamlit web app for personal finance tracking
and AI-powered insights — no external API keys required.

Run with:  streamlit run app.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import io

# ─────────────────────────────────────────────────────────────
# PAGE CONFIG & GLOBAL STYLES
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="FinSmart AI",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS — deep navy + electric teal palette, Inter-style type
st.markdown("""
<style>
  /* ── Base ── */
  [data-testid="stAppViewContainer"] {
      background: #0d1117;
      color: #e6edf3;
  }
  [data-testid="stSidebar"] {
      background: #161b22;
      border-right: 1px solid #30363d;
  }
  /* ── Typography ── */
  h1, h2, h3, h4 { color: #e6edf3; font-weight: 700; }
  .metric-card {
      background: #161b22;
      border: 1px solid #30363d;
      border-radius: 12px;
      padding: 20px 24px;
      margin-bottom: 12px;
  }
  .metric-value {
      font-size: 2rem;
      font-weight: 800;
      color: #58a6ff;
  }
  .metric-label {
      font-size: 0.8rem;
      color: #8b949e;
      text-transform: uppercase;
      letter-spacing: 0.08em;
  }
  /* ── Insight cards ── */
  .insight-warning {
      background: #1a1200;
      border-left: 4px solid #e3b341;
      border-radius: 8px;
      padding: 14px 18px;
      margin: 8px 0;
      color: #e3b341;
  }
  .insight-danger {
      background: #1a0000;
      border-left: 4px solid #f85149;
      border-radius: 8px;
      padding: 14px 18px;
      margin: 8px 0;
      color: #f85149;
  }
  .insight-success {
      background: #001a0e;
      border-left: 4px solid #3fb950;
      border-radius: 8px;
      padding: 14px 18px;
      margin: 8px 0;
      color: #3fb950;
  }
  .insight-info {
      background: #001133;
      border-left: 4px solid #58a6ff;
      border-radius: 8px;
      padding: 14px 18px;
      margin: 8px 0;
      color: #58a6ff;
  }
  /* ── Buttons ── */
  .stButton > button {
      background: #1f6feb;
      color: #fff;
      border: none;
      border-radius: 8px;
      font-weight: 600;
      padding: 0.5rem 1.4rem;
      transition: background 0.2s;
  }
  .stButton > button:hover { background: #388bfd; }
  /* ── Divider ── */
  hr { border-color: #30363d; }
  /* ── Section header ── */
  .section-header {
      font-size: 0.7rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.12em;
      color: #8b949e;
      margin-bottom: 4px;
  }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# SESSION STATE INITIALISATION
# ─────────────────────────────────────────────────────────────
def init_state():
    defaults = {
        "income": 0.0,
        "budget": 0.0,
        "expenses": pd.DataFrame(columns=["Category", "Amount", "Date"]),
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

init_state()

# ─────────────────────────────────────────────────────────────
# CONSTANTS — recommended budget ratios (50/30/20 rule variant)
# ─────────────────────────────────────────────────────────────
CATEGORY_BENCHMARKS = {
    "Food":          0.15,   # 15 % of income is a healthy food budget
    "Rent":          0.30,   # 30 % — housing rule of thumb
    "Bills":         0.10,   # 10 % — utilities / subscriptions
    "Entertainment": 0.05,   # 5 % — keep fun lean
    "Others":        0.10,   # catch-all
}

CATEGORY_ICONS = {
    "Food": "🍔",
    "Rent": "🏠",
    "Bills": "💡",
    "Entertainment": "🎮",
    "Others": "📦",
}

CHART_COLORS = ["#58a6ff", "#3fb950", "#e3b341", "#f85149", "#bc8cff"]


# ─────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────

def format_currency(value: float) -> str:
    """Return a dollar-formatted string, e.g. $1,234.56"""
    return f"${value:,.2f}"


def category_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate expenses by category."""
    if df.empty:
        return pd.DataFrame(columns=["Category", "Amount"])
    return (
        df.groupby("Category", as_index=False)["Amount"]
        .sum()
        .sort_values("Amount", ascending=False)
    )


# ─────────────────────────────────────────────────────────────
# RULE-BASED AI INSIGHTS ENGINE
# No external API required — pure heuristic logic
# ─────────────────────────────────────────────────────────────

def generate_insights(income: float, budget: float, summary: pd.DataFrame) -> list[dict]:
    """
    Evaluate the user's financial data against well-known personal-finance
    rules and return a list of insight dicts with keys:
        level  : 'danger' | 'warning' | 'success' | 'info'
        emoji  : decorative icon
        title  : short headline
        message: actionable explanation
    """
    insights = []
    if income <= 0:
        insights.append({
            "level": "info", "emoji": "ℹ️",
            "title": "Set your income",
            "message": "Enter your monthly income in the sidebar to unlock personalised AI insights.",
        })
        return insights

    total_spent = summary["Amount"].sum() if not summary.empty else 0.0
    savings     = income - total_spent
    savings_pct = savings / income if income else 0

    # ── 1. Overall budget check ──────────────────────────────
    if total_spent > budget and budget > 0:
        overage = total_spent - budget
        insights.append({
            "level": "danger", "emoji": "🚨",
            "title": "Over budget!",
            "message": (
                f"You have exceeded your monthly budget by {format_currency(overage)} "
                f"({overage/budget*100:.1f}%). Review your discretionary categories "
                f"immediately and aim to cut at least {format_currency(overage * 0.5)} next month."
            ),
        })
    elif total_spent > budget * 0.9 and budget > 0:
        insights.append({
            "level": "warning", "emoji": "⚠️",
            "title": "Approaching budget limit",
            "message": (
                f"You've used {total_spent/budget*100:.1f}% of your monthly budget. "
                f"Only {format_currency(budget - total_spent)} remaining — slow down spending."
            ),
        })

    # ── 2. Savings rate ──────────────────────────────────────
    if savings_pct < 0:
        insights.append({
            "level": "danger", "emoji": "💸",
            "title": "Spending exceeds income",
            "message": (
                f"You are spending {format_currency(abs(savings))} MORE than you earn. "
                "This path leads to debt. Identify and cut your top two expense categories now."
            ),
        })
    elif savings_pct < 0.10:
        insights.append({
            "level": "warning", "emoji": "🐷",
            "title": "Low savings rate",
            "message": (
                f"Your savings rate is only {savings_pct*100:.1f}% — below the recommended 10%. "
                f"Target saving at least {format_currency(income * 0.10)} per month to build an emergency fund."
            ),
        })
    elif savings_pct >= 0.20:
        insights.append({
            "level": "success", "emoji": "🌟",
            "title": "Excellent savings rate",
            "message": (
                f"You're saving {savings_pct*100:.1f}% of your income ({format_currency(savings)}). "
                "Consider investing the surplus in an index fund or high-yield savings account."
            ),
        })
    else:
        insights.append({
            "level": "info", "emoji": "✅",
            "title": "Healthy savings rate",
            "message": (
                f"You're saving {savings_pct*100:.1f}% of your income. "
                "Push toward 20% by trimming Entertainment or Others spending."
            ),
        })

    # ── 3. Per-category benchmark checks ────────────────────
    cat_map = dict(zip(summary["Category"], summary["Amount"])) if not summary.empty else {}
    for cat, benchmark_pct in CATEGORY_BENCHMARKS.items():
        spent = cat_map.get(cat, 0)
        pct   = spent / income
        icon  = CATEGORY_ICONS.get(cat, "📌")
        if pct > benchmark_pct * 1.5:
            insights.append({
                "level": "danger", "emoji": icon,
                "title": f"{cat} spending critical",
                "message": (
                    f"Your {cat} spend is {pct*100:.1f}% of income, "
                    f"nearly {pct/benchmark_pct:.1f}× the {benchmark_pct*100:.0f}% guideline. "
                    f"Reduce by {format_currency(spent - income * benchmark_pct)} to reach a healthy level."
                ),
            })
        elif pct > benchmark_pct:
            insights.append({
                "level": "warning", "emoji": icon,
                "title": f"{cat} slightly over guideline",
                "message": (
                    f"{cat} is at {pct*100:.1f}% of income (guideline: {benchmark_pct*100:.0f}%). "
                    f"Trim {format_currency(spent - income * benchmark_pct)} to stay on track."
                ),
            })

    # ── 4. Entertainment-specific nudge ─────────────────────
    ent = cat_map.get("Entertainment", 0)
    if ent / income > 0.10:
        insights.append({
            "level": "warning", "emoji": "🎬",
            "title": "Entertainment exceeds 10 % threshold",
            "message": (
                f"Entertainment is {ent/income*100:.1f}% of your income. "
                "Try the '24-hour rule': wait a day before any non-essential purchase. "
                "Cancel one subscription you rarely use to reclaim quick savings."
            ),
        })

    # ── 5. Rent / housing check (30 % rule) ─────────────────
    rent = cat_map.get("Rent", 0)
    if rent / income > 0.35:
        insights.append({
            "level": "danger", "emoji": "🏠",
            "title": "Housing cost too high",
            "message": (
                f"Rent is {rent/income*100:.1f}% of income — above the 30% safety threshold. "
                "Consider a roommate, renegotiating your lease, or relocating to reduce this ratio."
            ),
        })

    # ── 6. Food check ────────────────────────────────────────
    food = cat_map.get("Food", 0)
    if food / income > 0.20:
        insights.append({
            "level": "warning", "emoji": "🛒",
            "title": "Food spend above 20 %",
            "message": (
                "Meal-prepping twice a week typically cuts food costs by 25–30%. "
                "Track restaurant vs. grocery spending separately to find the leak."
            ),
        })

    # ── 7. Positive reinforcement if all looks good ──────────
    if not any(i["level"] in ("danger", "warning") for i in insights):
        insights.append({
            "level": "success", "emoji": "🏆",
            "title": "Finances look healthy!",
            "message": (
                "All your category ratios are within recommended guidelines. "
                "Keep it up — automate your savings transfer on payday so it's effortless."
            ),
        })

    # ── 8. Emergency fund nudge (always informative) ─────────
    emergency_target = income * 3
    insights.append({
        "level": "info", "emoji": "🛡️",
        "title": "Emergency fund target",
        "message": (
            f"A 3-month emergency fund for your income level is {format_currency(emergency_target)}. "
            "If you haven't reached it yet, prioritise it before any discretionary increases."
        ),
    })

    return insights


# ─────────────────────────────────────────────────────────────
# CHART BUILDERS
# ─────────────────────────────────────────────────────────────

def pie_chart(summary: pd.DataFrame) -> go.Figure:
    """Interactive donut chart of spending by category."""
    fig = px.pie(
        summary, values="Amount", names="Category",
        hole=0.55,
        color_discrete_sequence=CHART_COLORS,
    )
    fig.update_traces(
        textinfo="percent+label",
        hovertemplate="<b>%{label}</b><br>$%{value:,.2f}<br>%{percent}<extra></extra>",
    )
    fig.update_layout(
        paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
        font_color="#e6edf3",
        legend=dict(bgcolor="#161b22", bordercolor="#30363d", borderwidth=1),
        margin=dict(t=20, b=20, l=20, r=20),
        showlegend=True,
    )
    return fig


def bar_chart_budget_vs_actual(income: float, summary: pd.DataFrame) -> go.Figure:
    """Grouped bar chart: recommended budget vs actual spending per category."""
    cats      = list(CATEGORY_BENCHMARKS.keys())
    rec_vals  = [income * CATEGORY_BENCHMARKS[c] for c in cats]
    act_map   = dict(zip(summary["Category"], summary["Amount"])) if not summary.empty else {}
    act_vals  = [act_map.get(c, 0) for c in cats]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="Recommended",
        x=cats, y=rec_vals,
        marker_color="#30363d",
        text=[format_currency(v) for v in rec_vals],
        textposition="outside",
    ))
    fig.add_trace(go.Bar(
        name="Actual",
        x=cats, y=act_vals,
        marker_color=[
            "#f85149" if act_vals[i] > rec_vals[i] else "#3fb950"
            for i in range(len(cats))
        ],
        text=[format_currency(v) for v in act_vals],
        textposition="outside",
    ))
    fig.update_layout(
        barmode="group",
        paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
        font_color="#e6edf3",
        xaxis=dict(gridcolor="#21262d"),
        yaxis=dict(gridcolor="#21262d", tickprefix="$"),
        legend=dict(bgcolor="#161b22", bordercolor="#30363d", borderwidth=1),
        margin=dict(t=20, b=20, l=20, r=40),
    )
    return fig


def spending_gauge(total_spent: float, budget: float) -> go.Figure:
    """Gauge showing total spent vs budget."""
    pct = min((total_spent / budget * 100) if budget > 0 else 0, 150)
    color = "#f85149" if pct > 100 else "#e3b341" if pct > 80 else "#3fb950"
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=total_spent,
        delta={"reference": budget, "prefix": "$", "valueformat": ",.0f"},
        number={"prefix": "$", "valueformat": ",.0f", "font": {"color": color}},
        gauge={
            "axis": {"range": [0, max(budget * 1.2, total_spent * 1.1)],
                     "tickprefix": "$", "tickcolor": "#8b949e"},
            "bar": {"color": color},
            "bgcolor": "#161b22",
            "borderwidth": 0,
            "steps": [
                {"range": [0, budget * 0.8], "color": "#001a0e"},
                {"range": [budget * 0.8, budget], "color": "#1a1200"},
                {"range": [budget, max(budget * 1.2, total_spent * 1.1)], "color": "#1a0000"},
            ],
            "threshold": {
                "line": {"color": "#58a6ff", "width": 3},
                "thickness": 0.85,
                "value": budget,
            },
        },
    ))
    fig.update_layout(
        paper_bgcolor="#0d1117",
        font_color="#e6edf3",
        margin=dict(t=20, b=20, l=30, r=30),
        height=220,
    )
    return fig


# ─────────────────────────────────────────────────────────────
# SIDEBAR — income, budget, expense entry
# ─────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 💰 FinSmart AI")
    st.markdown("*Local AI. Zero API keys.*")
    st.divider()

    st.markdown('<p class="section-header">Monthly Finances</p>', unsafe_allow_html=True)
    income = st.number_input(
        "Monthly Income ($)", min_value=0.0, step=100.0,
        value=float(st.session_state.income),
        format="%.2f",
    )
    budget = st.number_input(
        "Monthly Budget ($)", min_value=0.0, step=100.0,
        value=float(st.session_state.budget),
        format="%.2f",
    )
    if st.button("💾 Save Settings"):
        st.session_state.income = income
        st.session_state.budget = budget
        st.success("Settings saved!")

    st.divider()
    st.markdown('<p class="section-header">Log an Expense</p>', unsafe_allow_html=True)

    category = st.selectbox(
        "Category",
        ["Food", "Rent", "Bills", "Entertainment", "Others"],
    )
    amount = st.number_input("Amount ($)", min_value=0.01, step=1.0, format="%.2f")

    if st.button("➕ Add Expense"):
        new_row = pd.DataFrame([{
            "Category": category,
            "Amount":   amount,
            "Date":     datetime.now().strftime("%Y-%m-%d"),
        }])
        st.session_state.expenses = pd.concat(
            [st.session_state.expenses, new_row], ignore_index=True
        )
        st.success(f"Added {format_currency(amount)} to {category}")

    st.divider()
    st.markdown('<p class="section-header">Upload CSV</p>', unsafe_allow_html=True)
    st.caption("Columns required: **Category**, **Amount**")
    uploaded = st.file_uploader("Drop CSV here", type=["csv"], label_visibility="collapsed")
    if uploaded:
        try:
            df_up = pd.read_csv(uploaded)
            # Validate required columns
            if {"Category", "Amount"}.issubset(df_up.columns):
                df_up = df_up[["Category", "Amount"]].copy()
                df_up["Amount"]   = pd.to_numeric(df_up["Amount"], errors="coerce").fillna(0)
                df_up["Category"] = df_up["Category"].str.strip().str.title()
                df_up["Category"] = df_up["Category"].apply(
                    lambda c: c if c in CATEGORY_BENCHMARKS else "Others"
                )
                df_up["Date"] = datetime.now().strftime("%Y-%m-%d")
                st.session_state.expenses = pd.concat(
                    [st.session_state.expenses, df_up], ignore_index=True
                )
                st.success(f"Imported {len(df_up)} rows ✓")
            else:
                st.error("CSV must have 'Category' and 'Amount' columns.")
        except Exception as e:
            st.error(f"Failed to parse CSV: {e}")

    st.divider()
    if st.button("🗑️ Clear All Expenses", type="secondary"):
        st.session_state.expenses = pd.DataFrame(columns=["Category", "Amount", "Date"])
        st.warning("Expenses cleared.")


# ─────────────────────────────────────────────────────────────
# MAIN AREA
# ─────────────────────────────────────────────────────────────
st.markdown("# FinSmart AI  <span style='font-size:1.1rem;color:#8b949e;font-weight:400'>Local Expense Analyzer</span>", unsafe_allow_html=True)
st.markdown("Track spending · Visualise trends · Get AI-powered financial insights — offline, private, free.")
st.divider()

# Pull live values
income  = float(st.session_state.income)
budget  = float(st.session_state.budget)
df      = st.session_state.expenses.copy()
summary = category_summary(df)
total_spent = summary["Amount"].sum() if not summary.empty else 0.0
savings     = income - total_spent

# ─── TOP METRIC CARDS ───────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"""
    <div class="metric-card">
      <div class="metric-label">Monthly Income</div>
      <div class="metric-value">{format_currency(income)}</div>
    </div>""", unsafe_allow_html=True)
with col2:
    st.markdown(f"""
    <div class="metric-card">
      <div class="metric-label">Monthly Budget</div>
      <div class="metric-value">{format_currency(budget)}</div>
    </div>""", unsafe_allow_html=True)
with col3:
    color = "#f85149" if total_spent > budget else "#e6edf3"
    st.markdown(f"""
    <div class="metric-card">
      <div class="metric-label">Total Spent</div>
      <div class="metric-value" style="color:{color}">{format_currency(total_spent)}</div>
    </div>""", unsafe_allow_html=True)
with col4:
    color = "#3fb950" if savings >= 0 else "#f85149"
    label = "Savings" if savings >= 0 else "Deficit"
    st.markdown(f"""
    <div class="metric-card">
      <div class="metric-label">{label}</div>
      <div class="metric-value" style="color:{color}">{format_currency(abs(savings))}</div>
    </div>""", unsafe_allow_html=True)

st.divider()

# ─── TABS ───────────────────────────────────────────────────
tab_dash, tab_log, tab_charts, tab_ai = st.tabs([
    "📊 Dashboard", "📋 Expense Log", "📈 Analytics", "🤖 AI Insights"
])

# ══════════════════════════════════════════════════════════════
# TAB 1 — DASHBOARD
# ══════════════════════════════════════════════════════════════
with tab_dash:
    if budget > 0 and income > 0:
        col_g, col_p = st.columns([1, 1])
        with col_g:
            st.markdown("#### Budget Gauge")
            st.plotly_chart(spending_gauge(total_spent, budget), use_container_width=True)
        with col_p:
            if not summary.empty:
                st.markdown("#### Spending Breakdown")
                st.plotly_chart(pie_chart(summary), use_container_width=True)
            else:
                st.info("No expenses logged yet. Add some in the sidebar or upload a CSV.")

        # Category mini-cards
        st.markdown("#### Category Snapshot")
        if not summary.empty:
            cols = st.columns(len(CATEGORY_BENCHMARKS))
            for i, (cat, bench) in enumerate(CATEGORY_BENCHMARKS.items()):
                spent  = dict(zip(summary["Category"], summary["Amount"])).get(cat, 0)
                limit  = income * bench
                pct    = spent / limit * 100 if limit else 0
                status = "🔴" if pct > 100 else "🟡" if pct > 80 else "🟢"
                icon   = CATEGORY_ICONS[cat]
                with cols[i]:
                    st.markdown(f"""
                    <div class="metric-card" style="text-align:center">
                      <div style="font-size:1.6rem">{icon}</div>
                      <div class="metric-label">{cat}</div>
                      <div style="font-size:1.1rem;font-weight:700;color:#58a6ff">{format_currency(spent)}</div>
                      <div style="font-size:0.75rem;color:#8b949e">of {format_currency(limit)} rec.</div>
                      <div style="font-size:1.2rem">{status}</div>
                    </div>""", unsafe_allow_html=True)
    else:
        st.info("👈 Set your Monthly Income and Budget in the sidebar to get started.")

# ══════════════════════════════════════════════════════════════
# TAB 2 — EXPENSE LOG
# ══════════════════════════════════════════════════════════════
with tab_log:
    if df.empty:
        st.info("No expenses logged yet. Use the sidebar to add expenses or upload a CSV.")
    else:
        st.markdown(f"**{len(df)} expense entries** · Total: **{format_currency(total_spent)}**")

        # Editable table
        edited = st.data_editor(
            df,
            column_config={
                "Category": st.column_config.SelectboxColumn(
                    options=list(CATEGORY_BENCHMARKS.keys())
                ),
                "Amount":   st.column_config.NumberColumn(format="$%.2f", min_value=0),
                "Date":     st.column_config.TextColumn(),
            },
            use_container_width=True,
            num_rows="dynamic",
            hide_index=True,
        )
        if st.button("💾 Save Edits"):
            st.session_state.expenses = edited
            st.success("Expense log updated.")

        # Download button
        csv_bytes = df.to_csv(index=False).encode()
        st.download_button(
            "⬇️ Download as CSV",
            data=csv_bytes,
            file_name="expenses.csv",
            mime="text/csv",
        )

        # Summary table
        st.markdown("#### Category Totals")
        display_summary = summary.copy()
        if income > 0:
            display_summary["% of Income"] = (display_summary["Amount"] / income * 100).round(1).astype(str) + "%"
        display_summary["Amount"] = display_summary["Amount"].apply(format_currency)
        st.dataframe(display_summary, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════
# TAB 3 — ANALYTICS
# ══════════════════════════════════════════════════════════════
with tab_charts:
    if summary.empty:
        st.info("Log some expenses first to see charts.")
    else:
        st.markdown("#### Recommended vs Actual Spending")
        st.caption("Blue = recommended limit (based on income), coloured bars = actual (🟢 under / 🔴 over)")
        if income > 0:
            st.plotly_chart(bar_chart_budget_vs_actual(income, summary), use_container_width=True)
        else:
            st.warning("Set your income to see recommended limits.")

        col_l, col_r = st.columns(2)
        with col_l:
            st.markdown("#### Spending Donut")
            st.plotly_chart(pie_chart(summary), use_container_width=True)
        with col_r:
            # Horizontal bar — sorted by amount
            st.markdown("#### Category Breakdown")
            fig_h = px.bar(
                summary.sort_values("Amount"),
                x="Amount", y="Category",
                orientation="h",
                color="Amount",
                color_continuous_scale=["#1f6feb", "#3fb950", "#e3b341", "#f85149"],
            )
            fig_h.update_traces(
                hovertemplate="<b>%{y}</b><br>$%{x:,.2f}<extra></extra>"
            )
            fig_h.update_layout(
                paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
                font_color="#e6edf3",
                xaxis=dict(gridcolor="#21262d", tickprefix="$"),
                yaxis=dict(gridcolor="#21262d"),
                coloraxis_showscale=False,
                margin=dict(t=10, b=10, l=10, r=10),
            )
            st.plotly_chart(fig_h, use_container_width=True)

        # Savings rate progress bar
        if income > 0:
            st.markdown("#### Savings Rate")
            savings_pct = max(savings / income, 0)
            target_pct  = 0.20
            col_a, col_b = st.columns([3, 1])
            with col_a:
                st.progress(min(savings_pct / target_pct, 1.0))
            with col_b:
                st.markdown(f"**{savings_pct*100:.1f}%** / 20% goal")

# ══════════════════════════════════════════════════════════════
# TAB 4 — AI INSIGHTS
# ══════════════════════════════════════════════════════════════
with tab_ai:
    st.markdown("### 🤖 AI Financial Insights")
    st.caption("Rule-based heuristics evaluate your data against personal-finance best practices — no internet or API key required.")

    insights = generate_insights(income, budget, summary)

    for ins in insights:
        st.markdown(
            f'<div class="insight-{ins["level"]}">'
            f'<strong>{ins["emoji"]} {ins["title"]}</strong><br>'
            f'{ins["message"]}'
            f'</div>',
            unsafe_allow_html=True,
        )

    if income > 0:
        st.divider()
        st.markdown("#### 📐 Benchmark Reference")
        bench_data = {
            "Category":          list(CATEGORY_BENCHMARKS.keys()),
            "Guideline %":       [f"{v*100:.0f}%" for v in CATEGORY_BENCHMARKS.values()],
            "Recommended ($)":   [format_currency(income * v) for v in CATEGORY_BENCHMARKS.values()],
        }
        st.dataframe(pd.DataFrame(bench_data), use_container_width=True, hide_index=True)

        st.markdown("#### 💡 Quick Win Tips")
        tips = [
            "**Pay yourself first** — automate a savings transfer on the day your salary arrives.",
            "**Cancel unused subscriptions** — the average person wastes $50+/month on forgotten services.",
            "**48-hour rule** — wait 48 hours before any non-essential purchase over $50.",
            "**Cook one extra meal at home per week** — saves ~$40–60/month without sacrifice.",
            "**Review insurance annually** — bundling policies can cut premiums by 10–20%.",
            "**Negotiate recurring bills** — internet, phone, and insurance are negotiable every 12 months.",
        ]
        for tip in tips:
            st.markdown(f"• {tip}")

# ─────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────
st.divider()
st.markdown(
    "<div style='text-align:center;color:#484f58;font-size:0.78rem'>"
    "FinSmart AI · Built with Streamlit &amp; Plotly · No API keys · Your data stays on your machine"
    "</div>",
    unsafe_allow_html=True,
)
