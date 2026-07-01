import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import streamlit as st
from src.startup import init_db
from src.auth import require_login, logout_button
init_db()
require_login()

def _try_write(fn, *args, success_msg="? Saved.", error_hint=""):
    """Run a write function, rollback-safe. Clears cache and returns True on success."""
    try:
        result = fn(*args)
        st.cache_data.clear()
        st.success(success_msg)
        return result
    except Exception as e:
        msg = str(e).lower()
        if "unique" in msg or "duplicate" in msg:
            st.error(f"? {error_hint or 'That name already exists � please choose a different one.'}")
        else:
            st.error(f"? Database error: {e}")
        return None
from src.models import (get_setting, set_setting, get_all_settings,
                         get_branches, add_branch, update_branch, delete_branch,
                         get_salespersons, add_salesperson, update_salesperson, delete_salesperson,
                         get_tiers, add_tier, update_tier, set_tier_target, delete_tier,
                         get_categories, add_category, update_category, delete_category,
                         get_brackets, add_bracket, update_bracket, delete_bracket,
                         get_kpi_items, add_kpi_item, delete_kpi_item, set_kpi_linked_category,
                         get_multiplier_rules, add_multiplier_rule, delete_multiplier_rule,
                         get_periods, lock_period, unlock_period, log_action)
from src.db import execute, fetchone

PRIMARY = get_setting('primary_color', '#354f61')
st.set_page_config(page_title="Settings", layout="wide")
st.markdown(f"<h1 style='color:{PRIMARY}'>?? Settings & Configuration</h1>", unsafe_allow_html=True)

tab_labels = ["Branding", "Branches", "Salespersons", "Target Tiers", "Categories", "Comm. Brackets", "KPI Settings", "Periods", "Users"]
tabs = st.tabs(tab_labels)

# -- BRANDING ------------------------------------------------------------------
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
        submitted = st.form_submit_button("?? Save Branding", type="primary")
        if submitted:
            for k, v in [('company_name', company_name), ('company_website', website),
                          ('company_phone', phone), ('primary_color', primary_col),
                          ('accent_color', accent_col), ('report_header', report_hdr),
                          ('report_footer', report_ftr), ('watermark_text', watermark)]:
                set_setting(k, v)
            log_action("SETTINGS_CHANGE", "settings", notes="Branding updated")
            st.cache_data.clear()
            st.success("? Branding settings saved! Reload the page to see color changes.")

# -- BRANCHES ------------------------------------------------------------------
with tabs[1]:
    st.markdown("### Branches")
    branches = get_branches()

    with st.expander("? Add New Branch"):
        with st.form("add_branch"):
            n = st.text_input("Branch Name *")
            c = st.text_input("City")
            if st.form_submit_button("Add Branch", type="primary") and n:
                if _try_write(add_branch, n, c, success_msg=f"? Branch '{n}' added.", error_hint=f"Branch '{n}' already exists.") is not None:
                    log_action("ADD_BRANCH", "branch", entity_name=n)
                    st.rerun()

    for _bi, br in enumerate(branches):
        with st.expander(f"{'??' if br['is_active'] else '??'} {br['name']} � {br.get('city','')}"):
            with st.form(f"br_edit_{_bi}_{br['id']}"):
                new_name = st.text_input("Name", br['name'])
                new_city = st.text_input("City", br.get('city',''))
                is_active = st.checkbox("Active", bool(br['is_active']))
                c1, c2 = st.columns(2)
                if c1.form_submit_button("?? Save", type="primary"):
                    _try_write(update_branch, br['id'], new_name, new_city, is_active)
                    st.rerun()
                if c2.form_submit_button("??? Delete", type="secondary"):
                    _try_write(delete_branch, br['id'], success_msg=f"??? Deleted '{br['name']}'.")
                    st.rerun()

# -- SALESPERSONS --------------------------------------------------------------
with tabs[2]:
    st.markdown("### Salespersons")
    sps      = get_salespersons()
    branches = get_branches(active_only=True)
    tiers    = get_tiers(active_only=True)
    br_opts  = {br['name']: br['id'] for br in branches}
    tier_opts = {t['name']: t['id'] for t in tiers}

    with st.expander("? Add New Salesperson"):
        with st.form("add_sp"):
            n    = st.text_input("Full Name *")
            br   = st.selectbox("Branch *", list(br_opts.keys()))
            tier = st.selectbox("Target Tier *", list(tier_opts.keys()))
            em   = st.text_input("Email")
            if st.form_submit_button("Add Salesperson", type="primary") and n:
                if _try_write(add_salesperson, n, br_opts[br], tier_opts[tier], em,
                              success_msg=f"? '{n}' added.",
                              error_hint=f"A salesperson named '{n}' already exists.") is not None:
                    st.rerun()

    for _si, sp in enumerate(sps):
        with st.expander(f"{'??' if sp['is_active'] else '??'} {sp['name']} � {sp.get('branch_name','')}"):
            with st.form(f"sp_edit_{_si}_{sp['id']}"):
                new_n   = st.text_input("Name", sp['name'])
                new_br  = st.selectbox("Branch", list(br_opts.keys()), index=list(br_opts.keys()).index(sp.get('branch_name','')) if sp.get('branch_name') in br_opts else 0)
                new_t   = st.selectbox("Target Tier", list(tier_opts.keys()), index=list(tier_opts.keys()).index(sp.get('tier_name','')) if sp.get('tier_name') in tier_opts else 0)
                new_em  = st.text_input("Email", sp.get('email',''))
                is_act  = st.checkbox("Active", bool(sp['is_active']))
                c1, c2  = st.columns(2)
                if c1.form_submit_button("?? Save", type="primary"):
                    _try_write(update_salesperson, sp['id'], new_n, br_opts[new_br], tier_opts[new_t], new_em, is_act)
                    st.rerun()
                if c2.form_submit_button("??? Delete"):
                    _try_write(delete_salesperson, sp['id'], success_msg=f"??? Deleted '{sp['name']}'.")
                    st.rerun()

# -- TARGET TIERS --------------------------------------------------------------
with tabs[3]:
    st.markdown("### Salesperson Target Tiers")
    tiers = get_tiers()
    cats  = get_categories(active_only=True)

    with st.expander("? Add New Tier"):
        with st.form("add_tier"):
            tn = st.text_input("Tier Name *")
            td = st.text_input("Description")
            amounts = {}
            st.markdown("**Category Targets (SAR):**")
            cols = st.columns(len(cats) if cats else 1)
            for i, cat in enumerate(cats):
                amounts[cat['id']] = cols[i].number_input(cat['name'], min_value=0, step=50000, value=0)
            if st.form_submit_button("Add Tier", type="primary") and tn:
                try:
                    tid = add_tier(tn, td)
                    for cat_id, amt in amounts.items():
                        set_tier_target(tid, cat_id, float(amt))
                    st.cache_data.clear()
                    st.success(f"? Tier '{tn}' added.")
                    st.rerun()
                except Exception as e:
                    msg = str(e).lower()
                    st.error(f"? Tier '{tn}' already exists." if "unique" in msg or "duplicate" in msg else f"? {e}")

    for _ti, tier in enumerate(tiers):
        total = sum(tier['targets'].values())
        with st.expander(f"{'??' if tier['is_active'] else '??'} {tier['name']} � Total: SAR {total:,.0f}"):
            with st.form(f"tier_edit_{_ti}_{tier['id']}"):
                tn = st.text_input("Name", tier['name'])
                td = st.text_input("Desc", tier.get('description',''))
                is_act = st.checkbox("Active", bool(tier['is_active']))
                st.markdown("**Category Targets (SAR):**")
                cols = st.columns(len(cats) if cats else 1)
                amounts = {}
                for i, cat in enumerate(cats):
                    amounts[cat['id']] = cols[i].number_input(cat['name'], min_value=0, step=50000, value=int(tier['targets'].get(cat['id'], 0)))
                c1, c2 = st.columns(2)
                if c1.form_submit_button("?? Save", type="primary"):
                    update_tier(tier['id'], tn, td, is_act)
                    for cat_id, amt in amounts.items():
                        set_tier_target(tier['id'], cat_id, float(amt))
                    st.cache_data.clear()
                    st.success("? Saved.")
                    st.rerun()
                if c2.form_submit_button("??? Delete"):
                    _try_write(delete_tier, tier['id'], success_msg=f"??? Deleted '{tier['name']}'.")
                    st.rerun()

# -- CATEGORIES ----------------------------------------------------------------
with tabs[4]:
    st.markdown("### Product / Service Categories")
    cats = get_categories()
    with st.expander("? Add Category"):
        with st.form("add_cat"):
            cn = st.text_input("Category Name *")
            co = st.number_input("Display Order", min_value=0, value=0)
            if st.form_submit_button("Add", type="primary") and cn:
                try:
                    cid = add_category(cn, co)
                    update_category(cid, cn, co, True, True, True, True)
                    st.cache_data.clear()
                    st.success(f"? '{cn}' added.")
                    st.rerun()
                except Exception as e:
                    msg = str(e).lower()
                    st.error(f"? Category '{cn}' already exists." if "unique" in msg or "duplicate" in msg else f"? {e}")

    import pandas as pd
    cat_df = pd.DataFrame([{
        "ID": c['id'], "Name": c['name'], "Order": c['display_order'],
        "In Target": bool(c['include_in_target']), "In Commission": bool(c['include_in_commission']),
        "In KPI": bool(c['include_in_kpi']), "Active": bool(c['is_active']),
    } for c in cats])
    edited_cats = st.data_editor(cat_df, use_container_width=True, hide_index=True,
                                  disabled=["ID"], num_rows="fixed",
                                  column_config={"ID": st.column_config.NumberColumn(width="small")})
    if st.button("?? Save Category Changes", type="primary"):
        for _, row in edited_cats.iterrows():
            update_category(int(row['ID']), row['Name'], int(row['Order']),
                             bool(row['In Target']), bool(row['In Commission']),
                             bool(row['In KPI']), bool(row['Active']))
        st.cache_data.clear()
        st.success("? Categories saved.")
        st.rerun()

# -- COMMISSION BRACKETS -------------------------------------------------------
with tabs[5]:
    st.markdown("### Category Commission Brackets")
    cats = get_categories(active_only=True)
    selected_cat = st.selectbox("Select Category", [c['name'] for c in cats], key="bracket_cat")
    cat_obj = next((c for c in cats if c['name'] == selected_cat), None)

    calc_method = st.selectbox("Calculation Method", ["flat", "progressive"],
                                index=0 if get_setting('global_calc_method','flat') == 'flat' else 1)
    if st.button("Save Method"):
        set_setting('global_calc_method', calc_method)
        st.success("? Method saved.")

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
            if st.button("?? Save Brackets", type="primary"):
                for _, row in edited_br.iterrows():
                    to_amt = None if row['Unlimited'] else row['To (SAR)']
                    update_bracket(int(row['ID']), row['From (SAR)'], to_amt,
                                   row['Rate %'], bool(row['Unlimited']), bool(row['Active']), int(row['Sort']))
                st.cache_data.clear()
                st.success("? Brackets saved.")
                st.rerun()

        with st.expander("? Add Bracket"):
            with st.form("add_bracket"):
                c1, c2, c3 = st.columns(3)
                frm = c1.number_input("From (SAR)", min_value=0, step=50000)
                to  = c2.number_input("To (SAR)",   min_value=0, step=50000)
                rate = c3.number_input("Rate %", min_value=0.0, max_value=100.0, step=0.5)
                unlimited = st.checkbox("Unlimited upper range (last bracket)")
                if st.form_submit_button("Add Bracket", type="primary"):
                    _try_write(add_bracket, cat_obj['id'], frm, None if unlimited else to, rate, unlimited, len(brackets),
                               success_msg="? Bracket added.")
                    st.rerun()

# -- KPI SETTINGS -------------------------------------------------------------
with tabs[6]:
    import pandas as pd
    from src.db import execute

    st.markdown("### KPI Items & Weights")

    with st.expander("? Add New KPI Item"):
        with st.form("add_kpi"):
            c1, c2, c3, c4 = st.columns(4)
            kpi_name  = c1.text_input("Name *")
            kpi_wt    = c2.number_input("Weight %", min_value=0.0, max_value=100.0, step=1.0, value=10.0)
            kpi_max   = c3.number_input("Max Score", min_value=1.0, step=10.0, value=100.0)
            kpi_sort  = c4.number_input("Sort Order", min_value=0, step=1, value=0)
            if st.form_submit_button("Add KPI Item", type="primary") and kpi_name:
                if _try_write(add_kpi_item, kpi_name, kpi_wt, kpi_max, kpi_sort,
                              success_msg=f"? '{kpi_name}' added.") is not None:
                    st.rerun()

    kpi_items = get_kpi_items()
    total_wt  = sum(i['weight'] for i in kpi_items if i['is_active'])
    if abs(total_wt - 100) > 0.01:
        st.warning(f"?? Active KPI weights total {total_wt:.1f}% (should be 100%).")

    kpi_df = pd.DataFrame([{
        "ID": i['id'], "Name": i['name'], "Weight %": i['weight'],
        "Max Score": i['max_score'], "Active": bool(i['is_active']), "Sort": i['sort_order']
    } for i in kpi_items])
    edited_kpi = st.data_editor(kpi_df, use_container_width=True, hide_index=True, disabled=["ID"])

    c_save, c_del = st.columns([1, 4])
    if c_save.button("?? Save KPI Items", type="primary"):
        for _, row in edited_kpi.iterrows():
            execute("UPDATE kpi_items SET name=%s, weight=%s, max_score=%s, is_active=%s, sort_order=%s WHERE id=%s",
                    (row['Name'], row['Weight %'], row['Max Score'], int(row['Active']), int(row['Sort']), int(row['ID'])))
        st.cache_data.clear()
        st.success("? KPI items saved.")
        st.rerun()

    if kpi_items:
        del_kpi = st.selectbox("Delete a KPI item", ["� select �"] + [i['name'] for i in kpi_items], key="del_kpi")
        if del_kpi != "� select �":
            item_to_del = next(i for i in kpi_items if i['name'] == del_kpi)
            if st.button(f"??? Delete '{del_kpi}'", type="secondary", key="do_del_kpi"):
                _try_write(delete_kpi_item, item_to_del['id'], success_msg=f"??? Deleted '{del_kpi}'.")
                st.rerun()

    # Category link section
    st.divider()
    st.markdown("### Auto-Score from Category Achievement %")
    st.caption(
        "Link a KPI item to a sales category - the score is computed automatically from "
        "Actual Sales / Target x 100 (capped at 100). "
        "Linked items won't appear in the manual KPI entry table."
    )

    cats_for_link = get_categories(active_only=True)
    cat_name_to_id = {c['name']: c['id'] for c in cats_for_link}
    cat_options = ["Manual - Enter Score"] + [c['name'] for c in cats_for_link]

    with st.form("kpi_category_links"):
        link_selections = {}
        for _kli, item in enumerate(kpi_items):
            c1, c2 = st.columns([2, 3])
            c1.markdown(f"**{item['name']}** ({item['weight']:.0f}%)")
            current_name = item.get('linked_category_name') or "Manual - Enter Score"
            if current_name not in cat_options:
                current_name = "Manual - Enter Score"
            idx = cat_options.index(current_name)
            link_selections[item['id']] = c2.selectbox(
                "Source", cat_options, index=idx,
                key=f"kpi_lnk_{_kli}_{item['id']}", label_visibility="collapsed"
            )
        if st.form_submit_button("Save Category Links", type="primary"):
            for item_id, selected_name in link_selections.items():
                new_cat_id = cat_name_to_id.get(selected_name)  # None if Manual
                set_kpi_linked_category(item_id, new_cat_id)
            st.cache_data.clear()
            st.success("Category links saved.")
            st.rerun()

    st.divider()
    st.markdown("### KPI Multiplier Rules")

    with st.expander("? Add New Multiplier Rule"):
        with st.form("add_rule"):
            c1, c2, c3, c4 = st.columns(4)
            r_from  = c1.number_input("Score From", min_value=0.0, step=5.0, value=0.0)
            r_to    = c2.number_input("Score To",   min_value=0.0, step=5.0, value=80.0)
            r_mult  = c3.number_input("Multiplier", min_value=0.0, step=0.05, value=1.0)
            r_unlim = c4.checkbox("Unlimited (no upper bound)")
            if st.form_submit_button("Add Rule", type="primary"):
                _try_write(add_multiplier_rule, r_from, None if r_unlim else r_to, r_mult, r_unlim,
                           success_msg="? Rule added.")
                st.rerun()

    rules = get_multiplier_rules(active_only=False)
    rules_df = pd.DataFrame([{
        "ID": r['id'], "Score From": r['score_from'], "Score To": r['score_to'] or 999,
        "Multiplier": r['multiplier'], "Unlimited": bool(r['is_unlimited']), "Active": bool(r['is_active'])
    } for r in rules])
    edited_rules = st.data_editor(rules_df, use_container_width=True, hide_index=True, disabled=["ID"])

    c_save2, c_del2 = st.columns([1, 4])
    if c_save2.button("?? Save Multiplier Rules", type="primary"):
        for _, row in edited_rules.iterrows():
            to_val = None if row['Unlimited'] else row['Score To']
            execute("UPDATE kpi_multiplier_rules SET score_from=%s, score_to=%s, multiplier=%s, is_unlimited=%s, is_active=%s WHERE id=%s",
                    (row['Score From'], to_val, row['Multiplier'], int(row['Unlimited']), int(row['Active']), int(row['ID'])))
        st.cache_data.clear()
        st.success("? Multiplier rules saved.")
        st.rerun()

    if rules:
        del_rule = st.selectbox("Delete a rule", ["� select �"] + [f"Score {r['score_from']}�{r['score_to'] or '8'} � {r['multiplier']}" for r in rules], key="del_rule")
        if del_rule != "� select �":
            idx = [f"Score {r['score_from']}�{r['score_to'] or '8'} � {r['multiplier']}" for r in rules].index(del_rule)
            if st.button(f"??? Delete selected rule", type="secondary", key="do_del_rule"):
                _try_write(delete_multiplier_rule, rules[idx]['id'], success_msg="??? Rule deleted.")
                st.rerun()

# -- PERIODS -------------------------------------------------------------------
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
            st.success(f"? Period Q{pq} {py} created.")
            st.rerun()

    for p in periods:
        status = "?? LOCKED" if p['is_locked'] else "?? Open"
        current = " ? Current" if p['is_current'] else ""
        with st.expander(f"{status}{current} � Q{p['quarter']} {p['year']}"):
            c1, c2, c3 = st.columns(3)
            if p['is_locked']:
                if c1.button(f"?? Unlock Q{p['quarter']} {p['year']}", key=f"unlock_{p['id']}"):
                    unlock_period(p['id'])
                    log_action("QUARTER_UNLOCK", "period", p['id'], f"Q{p['quarter']} {p['year']}")
                    st.success("Unlocked.")
                    st.rerun()
            else:
                if c1.button(f"?? Lock Q{p['quarter']} {p['year']}", key=f"lock_{p['id']}"):
                    lock_period(p['id'])
                    log_action("QUARTER_LOCK", "period", p['id'], f"Q{p['quarter']} {p['year']}")
                    st.success("Locked.")
                    st.rerun()
            if c2.button("Set as Current", key=f"curr_{p['id']}"):
                execute("UPDATE periods SET is_current=0")
                execute("UPDATE periods SET is_current=1 WHERE id=%s", (p['id'],))
                st.success("Set as current.")
                st.rerun()

# -- USERS ---------------------------------------------------------------------
with tabs[8]:
    from src.auth import list_users, create_user, update_user_password, delete_user, is_admin, hash_password

    st.markdown("### App Users")
    st.caption("Manage who can log in. Only admins can access this tab.")

    if not is_admin():
        st.warning("?? Only admins can manage users.")
    else:
        with st.expander("? Add New User"):
            with st.form("add_user"):
                c1, c2 = st.columns(2)
                new_uname = c1.text_input("Username *").strip().lower()
                new_fname = c2.text_input("Full Name")
                new_pw    = c1.text_input("Password *", type="password")
                new_pw2   = c2.text_input("Confirm Password *", type="password")
                new_role  = st.selectbox("Role", ["viewer", "admin"])
                if st.form_submit_button("Create User", type="primary"):
                    if not new_uname or not new_pw:
                        st.error("Username and password are required.")
                    elif new_pw != new_pw2:
                        st.error("Passwords do not match.")
                    else:
                        _try_write(create_user, new_uname, new_pw, new_fname, new_role,
                                   success_msg=f"? User '{new_uname}' created.",
                                   error_hint=f"Username '{new_uname}' already exists.")

        users = list_users()
        if users:
            st.markdown("#### Current Users")
            current_user = st.session_state.get('username', '')
            for _ui, u in enumerate(users):
                badge = "??" if u['role'] == 'admin' else "??"
                you   = " (you)" if u['username'] == current_user else ""
                with st.expander(f"{badge} {u['username']}{you} � {u['full_name'] or '�'} � {u['role']}"):
                    with st.form(f"usr_edit_{_ui}_{u['id']}"):
                        np1 = st.text_input("New Password", type="password", placeholder="Leave blank to keep current")
                        np2 = st.text_input("Confirm New Password", type="password")
                        nr  = st.selectbox("Role", ["viewer", "admin"],
                                           index=0 if u['role'] == "viewer" else 1)
                        c1, c2 = st.columns(2)
                        if c1.form_submit_button("?? Save", type="primary"):
                            if np1:
                                if np1 != np2:
                                    st.error("Passwords do not match.")
                                else:
                                    update_user_password(u['id'], np1)
                                    st.success("? Password updated.")
                            execute("UPDATE app_users SET role=%s WHERE id=%s", (nr, u['id']))
                            st.success("? Saved.")
                            st.rerun()
                        if c2.form_submit_button("??? Delete", type="secondary"):
                            if u['username'] == current_user:
                                st.error("You cannot delete your own account.")
                            else:
                                _try_write(delete_user, u['id'], success_msg=f"??? User '{u['username']}' deleted.")
                                st.rerun()
