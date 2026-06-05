import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import streamlit as st
from src.models import (get_setting, set_setting, get_all_settings,
                         get_branches, add_branch, update_branch, delete_branch,
                         get_salespersons, add_salesperson, update_salesperson, delete_salesperson,
                         get_tiers, add_tier, update_tier, set_tier_target, delete_tier,
                         get_categories, add_category, update_category, delete_category,
                         get_brackets, add_bracket, update_bracket, delete_bracket,
                         get_kpi_items, get_multiplier_rules,
                         get_periods, lock_period, unlock_period, log_action)
from src.db import execute, fetchone

PRIMARY = get_setting('primary_color', '#354f61')
st.set_page_config(page_title="Settings", layout="wide")
st.markdown(f"<h1 style='color:{PRIMARY}'>⚙️ Settings & Configuration</h1>", unsafe_allow_html=True)

tab_labels = ["Branding", "Branches", "Salespersons", "Target Tiers", "Categories", "Comm. Brackets", "KPI Settings", "Periods"]
tabs = st.tabs(tab_labels)

# ── BRANDING ──────────────────────────────────────────────────────────────────
with tabs[0]:
    st.markdown("### Company Branding")
    st.caption("Changes are saved immediately when you click Save.")
    with st.form("branding_form"):
        c1, c2 = st.columns(2)
        company_name = c1.text_input("Company Name", get_setting('company_name', 'Surveying Experts'))
        website      = c2.text_input("Website", get_setting('company_website', ''))
        phone        = c1.text_input("Phone", get_setting('company_phone', ''))
        primary_col  = c1.color_picker("Primary Color", get_setting('primary_color', '#354f61'))
        accent_col   = c2.color_picker("Accent Color",  get_setting('accent_color', '#f6ba3b'))
        report_hdr   = st.text_input("Report Header", get_setting('report_header', ''))
        report_ftr   = st.text_input("Report Footer", get_setting('report_footer', ''))
        watermark    = st.text_input("PDF Watermark (optional)", get_setting('watermark_text', ''))
        submitted = st.form_submit_button("💾 Save Branding", type="primary")
        if submitted:
            for k, v in [('company_name', company_name), ('company_website', website),
                          ('company_phone', phone), ('primary_color', primary_col),
                          ('accent_color', accent_col), ('report_header', report_hdr),
                          ('report_footer', report_ftr), ('watermark_text', watermark)]:
                set_setting(k, v)
            log_action("SETTINGS_CHANGE", "settings", notes="Branding updated")
            st.success("✅ Branding settings saved! Reload the page to see color changes.")

# ── BRANCHES ──────────────────────────────────────────────────────────────────
with tabs[1]:
    st.markdown("### Branches")
    branches = get_branches()

    with st.expander("➕ Add New Branch"):
        with st.form("add_branch"):
            n = st.text_input("Branch Name *")
            c = st.text_input("City")
            if st.form_submit_button("Add Branch", type="primary") and n:
                add_branch(n, c)
                log_action("ADD_BRANCH", "branch", entity_name=n)
                st.success(f"✅ Branch '{n}' added.")
                st.rerun()

    for br in branches:
        with st.expander(f"{'🟢' if br['is_active'] else '🔴'} {br['name']} — {br.get('city','')}"):
            with st.form(f"edit_br_{br['id']}"):
                new_name = st.text_input("Name", br['name'])
                new_city = st.text_input("City", br.get('city',''))
                is_active = st.checkbox("Active", bool(br['is_active']))
                c1, c2 = st.columns(2)
                if c1.form_submit_button("💾 Save", type="primary"):
                    update_branch(br['id'], new_name, new_city, is_active)
                    st.success("✅ Saved.")
                    st.rerun()
                if c2.form_submit_button("🗑️ Delete", type="secondary"):
                    delete_branch(br['id'])
                    st.warning(f"Deleted '{br['name']}'.")
                    st.rerun()

# ── SALESPERSONS ──────────────────────────────────────────────────────────────
with tabs[2]:
    st.markdown("### Salespersons")
    sps      = get_salespersons()
    branches = get_branches(active_only=True)
    tiers    = get_tiers(active_only=True)
    br_opts  = {br['name']: br['id'] for br in branches}
    tier_opts = {t['name']: t['id'] for t in tiers}

    with st.expander("➕ Add New Salesperson"):
        with st.form("add_sp"):
            n    = st.text_input("Full Name *")
            br   = st.selectbox("Branch *", list(br_opts.keys()))
            tier = st.selectbox("Target Tier *", list(tier_opts.keys()))
            em   = st.text_input("Email")
            if st.form_submit_button("Add Salesperson", type="primary") and n:
                add_salesperson(n, br_opts[br], tier_opts[tier], em)
                st.success(f"✅ '{n}' added.")
                st.rerun()

    for sp in sps:
        with st.expander(f"{'🟢' if sp['is_active'] else '🔴'} {sp['name']} — {sp.get('branch_name','')}"):
            with st.form(f"edit_sp_{sp['id']}"):
                new_n   = st.text_input("Name", sp['name'])
                new_br  = st.selectbox("Branch", list(br_opts.keys()), index=list(br_opts.keys()).index(sp.get('branch_name','')) if sp.get('branch_name') in br_opts else 0)
                new_t   = st.selectbox("Target Tier", list(tier_opts.keys()), index=list(tier_opts.keys()).index(sp.get('tier_name','')) if sp.get('tier_name') in tier_opts else 0)
                new_em  = st.text_input("Email", sp.get('email',''))
                is_act  = st.checkbox("Active", bool(sp['is_active']))
                c1, c2  = st.columns(2)
                if c1.form_submit_button("💾 Save", type="primary"):
                    update_salesperson(sp['id'], new_n, br_opts[new_br], tier_opts[new_t], new_em, is_act)
                    st.success("✅ Saved.")
                    st.rerun()
                if c2.form_submit_button("🗑️ Delete"):
                    delete_salesperson(sp['id'])
                    st.rerun()

# ── TARGET TIERS ──────────────────────────────────────────────────────────────
with tabs[3]:
    st.markdown("### Salesperson Target Tiers")
    tiers = get_tiers()
    cats  = get_categories(active_only=True)

    with st.expander("➕ Add New Tier"):
        with st.form("add_tier"):
            tn = st.text_input("Tier Name *")
            td = st.text_input("Description")
            amounts = {}
            st.markdown("**Category Targets (SAR):**")
            cols = st.columns(len(cats) if cats else 1)
            for i, cat in enumerate(cats):
                amounts[cat['id']] = cols[i].number_input(cat['name'], min_value=0, step=50000, value=0)
            if st.form_submit_button("Add Tier", type="primary") and tn:
                tid = add_tier(tn, td)
                for cat_id, amt in amounts.items():
                    set_tier_target(tid, cat_id, float(amt))
                st.success(f"✅ Tier '{tn}' added.")
                st.rerun()

    for tier in tiers:
        total = sum(tier['targets'].values())
        with st.expander(f"{'🟢' if tier['is_active'] else '🔴'} {tier['name']} — Total: SAR {total:,.0f}"):
            with st.form(f"edit_tier_{tier['id']}"):
                tn = st.text_input("Name", tier['name'])
                td = st.text_input("Desc", tier.get('description',''))
                is_act = st.checkbox("Active", bool(tier['is_active']))
                st.markdown("**Category Targets (SAR):**")
                cols = st.columns(len(cats) if cats else 1)
                amounts = {}
                for i, cat in enumerate(cats):
                    amounts[cat['id']] = cols[i].number_input(cat['name'], min_value=0, step=50000, value=int(tier['targets'].get(cat['id'], 0)))
                c1, c2 = st.columns(2)
                if c1.form_submit_button("💾 Save", type="primary"):
                    update_tier(tier['id'], tn, td, is_act)
                    for cat_id, amt in amounts.items():
                        set_tier_target(tier['id'], cat_id, float(amt))
                    st.success("✅ Saved.")
                    st.rerun()
                if c2.form_submit_button("🗑️ Delete"):
                    delete_tier(tier['id'])
                    st.rerun()

# ── CATEGORIES ────────────────────────────────────────────────────────────────
with tabs[4]:
    st.markdown("### Product / Service Categories")
    cats = get_categories()
    with st.expander("➕ Add Category"):
        with st.form("add_cat"):
            cn = st.text_input("Category Name *")
            co = st.number_input("Display Order", min_value=0, value=0)
            if st.form_submit_button("Add", type="primary") and cn:
                cid = add_category(cn, co)
                update_category(cid, cn, co, True, True, True, True)
                st.success(f"✅ '{cn}' added.")
                st.rerun()

    import pandas as pd
    cat_df = pd.DataFrame([{
        "ID": c['id'], "Name": c['name'], "Order": c['display_order'],
        "In Target": bool(c['include_in_target']), "In Commission": bool(c['include_in_commission']),
        "In KPI": bool(c['include_in_kpi']), "Active": bool(c['is_active']),
    } for c in cats])
    edited_cats = st.data_editor(cat_df, use_container_width=True, hide_index=True,
                                  disabled=["ID"], num_rows="fixed",
                                  column_config={"ID": st.column_config.NumberColumn(width="small")})
    if st.button("💾 Save Category Changes", type="primary"):
        for _, row in edited_cats.iterrows():
            update_category(int(row['ID']), row['Name'], int(row['Order']),
                             bool(row['In Target']), bool(row['In Commission']),
                             bool(row['In KPI']), bool(row['Active']))
        st.success("✅ Categories saved.")
        st.rerun()

# ── COMMISSION BRACKETS ───────────────────────────────────────────────────────
with tabs[5]:
    st.markdown("### Category Commission Brackets")
    cats = get_categories(active_only=True)
    selected_cat = st.selectbox("Select Category", [c['name'] for c in cats], key="bracket_cat")
    cat_obj = next((c for c in cats if c['name'] == selected_cat), None)

    calc_method = st.selectbox("Calculation Method", ["flat", "progressive"],
                                index=0 if get_setting('global_calc_method','flat') == 'flat' else 1)
    if st.button("Save Method"):
        set_setting('global_calc_method', calc_method)
        st.success("✅ Method saved.")

    if cat_obj:
        brackets = get_brackets(cat_obj['id'], active_only=False)
        if brackets:
            import pandas as pd
            br_df = pd.DataFrame([{
                "ID": b['id'], "From (SAR)": b['from_amount'], "To (SAR)": b['to_amount'] or 0,
                "Rate %": b['commission_rate'], "Unlimited": bool(b['is_unlimited']),
                "Active": bool(b['is_active']), "Sort": b['sort_order'],
            } for b in brackets])
            edited_br = st.data_editor(br_df, use_container_width=True, hide_index=True, disabled=["ID"])
            if st.button("💾 Save Brackets", type="primary"):
                for _, row in edited_br.iterrows():
                    to_amt = None if row['Unlimited'] else row['To (SAR)']
                    update_bracket(int(row['ID']), row['From (SAR)'], to_amt,
                                   row['Rate %'], bool(row['Unlimited']), bool(row['Active']), int(row['Sort']))
                st.success("✅ Brackets saved.")
                st.rerun()

        with st.expander("➕ Add Bracket"):
            with st.form("add_bracket"):
                c1, c2, c3 = st.columns(3)
                frm = c1.number_input("From (SAR)", min_value=0, step=50000)
                to  = c2.number_input("To (SAR)",   min_value=0, step=50000)
                rate = c3.number_input("Rate %", min_value=0.0, max_value=100.0, step=0.5)
                unlimited = st.checkbox("Unlimited upper range (last bracket)")
                if st.form_submit_button("Add Bracket", type="primary"):
                    add_bracket(cat_obj['id'], frm, None if unlimited else to, rate, unlimited, len(brackets))
                    st.success("✅ Added.")
                    st.rerun()

# ── KPI SETTINGS ─────────────────────────────────────────────────────────────
with tabs[6]:
    st.markdown("### KPI Items & Weights")
    kpi_items = get_kpi_items()
    total_wt  = sum(i['weight'] for i in kpi_items if i['is_active'])
    if abs(total_wt - 100) > 0.01:
        st.warning(f"⚠️ Active KPI weights total {total_wt:.1f}% (should be 100%).")

    import pandas as pd
    kpi_df = pd.DataFrame([{
        "ID": i['id'], "Name": i['name'], "Weight %": i['weight'],
        "Max Score": i['max_score'], "Active": bool(i['is_active']), "Sort": i['sort_order']
    } for i in kpi_items])
    edited_kpi = st.data_editor(kpi_df, use_container_width=True, hide_index=True, disabled=["ID"])
    if st.button("💾 Save KPI Items", type="primary"):
        from src.db import execute
        for _, row in edited_kpi.iterrows():
            execute("UPDATE kpi_items SET name=%s, weight=%s, max_score=%s, is_active=%s, sort_order=%s WHERE id=%s",
                    (row['Name'], row['Weight %'], row['Max Score'], int(row['Active']), int(row['Sort']), int(row['ID'])))
        st.success("✅ KPI items saved.")
        st.rerun()

    st.markdown("### KPI Multiplier Rules")
    rules = get_multiplier_rules(active_only=False)
    rules_df = pd.DataFrame([{
        "ID": r['id'], "Score From": r['score_from'], "Score To": r['score_to'] or 999,
        "Multiplier": r['multiplier'], "Unlimited": bool(r['is_unlimited']), "Active": bool(r['is_active'])
    } for r in rules])
    edited_rules = st.data_editor(rules_df, use_container_width=True, hide_index=True, disabled=["ID"])
    if st.button("💾 Save Multiplier Rules", type="primary"):
        for _, row in edited_rules.iterrows():
            to_val = None if row['Unlimited'] else row['Score To']
            execute("UPDATE kpi_multiplier_rules SET score_from=%s, score_to=%s, multiplier=%s, is_unlimited=%s, is_active=%s WHERE id=%s",
                    (row['Score From'], to_val, row['Multiplier'], int(row['Unlimited']), int(row['Active']), int(row['ID'])))
        st.success("✅ Multiplier rules saved.")
        st.rerun()

# ── PERIODS ───────────────────────────────────────────────────────────────────
with tabs[7]:
    st.markdown("### Period Settings")
    periods = get_periods()

    with st.form("create_period"):
        c1, c2 = st.columns(2)
        py = c1.selectbox("Year", [2024,2025,2026,2027], index=2)
        pq = c2.selectbox("Quarter", [1,2,3,4], index=1, format_func=lambda q: f"Q{q}")
        if st.form_submit_button("Create Period", type="primary"):
            from src.models import get_or_create_period
            get_or_create_period(py, pq)
            st.success(f"✅ Period Q{pq} {py} created.")
            st.rerun()

    for p in periods:
        status = "🔒 LOCKED" if p['is_locked'] else "🔓 Open"
        current = " ⭐ Current" if p['is_current'] else ""
        with st.expander(f"{status}{current} — Q{p['quarter']} {p['year']}"):
            c1, c2, c3 = st.columns(3)
            if p['is_locked']:
                if c1.button(f"🔓 Unlock Q{p['quarter']} {p['year']}", key=f"unlock_{p['id']}"):
                    unlock_period(p['id'])
                    log_action("QUARTER_UNLOCK", "period", p['id'], f"Q{p['quarter']} {p['year']}")
                    st.success("Unlocked.")
                    st.rerun()
            else:
                if c1.button(f"🔒 Lock Q{p['quarter']} {p['year']}", key=f"lock_{p['id']}"):
                    lock_period(p['id'])
                    log_action("QUARTER_LOCK", "period", p['id'], f"Q{p['quarter']} {p['year']}")
                    st.success("Locked.")
                    st.rerun()
            if c2.button("Set as Current", key=f"curr_{p['id']}"):
                execute("UPDATE periods SET is_current=0")
                execute("UPDATE periods SET is_current=1 WHERE id=%s", (p['id'],))
                st.success("Set as current.")
                st.rerun()
