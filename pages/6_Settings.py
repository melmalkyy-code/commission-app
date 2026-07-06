import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import streamlit as st
import pandas as pd
from src.startup import init_db
from src.auth import require_login, require_admin
init_db()
require_login()
require_admin()
from src.models import (
    get_setting, set_setting,
    get_branches, add_branch, update_branch, delete_branch,
    get_salespersons, add_salesperson, update_salesperson, delete_salesperson,
    get_tiers, add_tier, update_tier, set_tier_target, delete_tier,
    get_categories, add_category, update_category, delete_category,
    get_brackets, add_bracket, update_bracket, delete_bracket,
    get_kpi_items, add_kpi_item, update_kpi_item, delete_kpi_item, set_kpi_linked_category,
    get_multiplier_rules, add_multiplier_rule, delete_multiplier_rule,
    get_periods, lock_period, unlock_period, log_action, get_or_create_period,
)
from src.db import execute
from src.ui import inject_css, page_header, sidebar_logo
from src.i18n import t, q_label

PRIMARY = get_setting('primary_color', '#354f61')
COMPANY = get_setting('company_name', 'Surveying Experts')
st.set_page_config(page_title="Settings — Surveying Experts", layout="wide")
inject_css(PRIMARY)
sidebar_logo(COMPANY, PRIMARY)
page_header(t("Settings & Configuration"), t("Manage all system settings, targets, and commission rules"), PRIMARY)


def _save(fn, *args, ok="Saved.", err=""):
    try:
        result = fn(*args)
        st.cache_data.clear()
        st.success(ok)
        return result
    except Exception as e:
        msg = str(e).lower()
        if "unique" in msg or "duplicate" in msg:
            st.error(err or t("That name already exists - choose a different one."))
        else:
            st.error(f"Error: {e}")
        return None


tabs = st.tabs([
    t("Branding"), t("Branches"), t("Salespersons"), t("Target Tiers"),
    t("Categories"), t("Comm. Brackets"), t("KPI Settings"), t("Periods"), t("Users"),
])


# ── BRANDING ──────────────────────────────────────────────────────────────────
with tabs[0]:
    st.markdown(f"### {t('Company Branding')}")
    with st.form("branding_form"):
        c1, c2 = st.columns(2)
        company_name = c1.text_input(t("Company Name"), get_setting('company_name', 'Surveying Experts'), key="b_cname")
        website      = c2.text_input(t("Website"),      get_setting('company_website', ''),              key="b_web")
        phone        = c1.text_input(t("Phone"),         get_setting('company_phone', ''),               key="b_phone")
        primary_col  = c1.color_picker(t("Primary Color"), get_setting('primary_color', '#354f61'),      key="b_primary")
        accent_col   = c2.color_picker(t("Accent Color"),  get_setting('accent_color', '#f6ba3b'),       key="b_accent")
        report_hdr   = st.text_input(t("Report Header"), get_setting('report_header', ''),               key="b_rhdr")
        report_ftr   = st.text_input(t("Report Footer"), get_setting('report_footer', ''),               key="b_rftr")
        watermark    = st.text_input(t("PDF Watermark (optional)"), get_setting('watermark_text', ''),   key="b_wm")
        if st.form_submit_button(t("Save Branding"), type="primary"):
            for k, v in [
                ('company_name', company_name), ('company_website', website),
                ('company_phone', phone), ('primary_color', primary_col),
                ('accent_color', accent_col), ('report_header', report_hdr),
                ('report_footer', report_ftr), ('watermark_text', watermark),
            ]:
                set_setting(k, v)
            log_action("SETTINGS_CHANGE", "settings", notes="Branding updated")
            st.cache_data.clear()
            st.rerun()

    st.divider()
    st.markdown(f"#### {t('Company Logo')}")
    import base64 as _b64
    _existing_logo = get_setting('company_logo_b64', '')
    if _existing_logo:
        st.image(_b64.b64decode(_existing_logo), width=120)
        if st.button(t("Remove Logo"), key="remove_logo"):
            set_setting('company_logo_b64', '')
            st.cache_data.clear()
            st.rerun()
    uploaded_logo = st.file_uploader(
        t("Upload logo (PNG or JPG, max 500 KB)"),
        type=['png', 'jpg', 'jpeg'], key="b_logo",
    )
    if uploaded_logo:
        raw = uploaded_logo.read()
        if len(raw) > 500_000:
            st.error(t("File too large — keep it under 500 KB."))
        else:
            set_setting('company_logo_b64', _b64.b64encode(raw).decode())
            st.cache_data.clear()
            st.success(t("Logo saved."))
            st.rerun()


# ── BRANCHES ─────────────────────────────────────────────────────────────────
with tabs[1]:
    st.markdown(f"### {t('Branches')}")
    branches = get_branches()

    with st.expander(t("Add New Branch")):
        with st.form("add_branch_form"):
            n = st.text_input(t("Branch Name *"), key="new_br_name")
            r = st.text_input(t("Region"),        key="new_br_region")
            if st.form_submit_button(t("Add Branch"), type="primary") and n:
                if _save(add_branch, n, r, ok=f"Branch '{n}' added.",
                         err=f"Branch '{n}' already exists.") is not None:
                    log_action("ADD_BRANCH", "branch", entity_name=n)
                    st.rerun()

    for br in branches:
        _bid = br['id']
        status = t("Active") if br['is_active'] else t("Inactive")
        with st.expander(f"[{status}] {br['name']} — {br.get('region', '')}"):
            with st.form(f"br_edit_{_bid}"):
                new_name   = st.text_input(t("Name"),   br['name'],            key=f"br_n_{_bid}")
                new_region = st.text_input(t("Region"), br.get('region', ''), key=f"br_r_{_bid}")
                is_active  = st.checkbox(t("Active"),   bool(br['is_active']),  key=f"br_a_{_bid}")
                c1, c2    = st.columns(2)
                if c1.form_submit_button(t("Save"), type="primary"):
                    _save(update_branch, br['id'], new_name, new_region, is_active)
                    st.rerun()
                if c2.form_submit_button(t("Delete"), type="secondary"):
                    _save(delete_branch, br['id'], ok=f"Deleted '{br['name']}'.")
                    st.rerun()


# ── SALESPERSONS ──────────────────────────────────────────────────────────────
with tabs[2]:
    st.markdown(f"### {t('Salespersons')}")
    sps       = get_salespersons()
    branches  = get_branches(active_only=True)
    tiers_sp  = get_tiers(active_only=True)
    br_opts   = {br['name']: br['id'] for br in branches}
    tier_opts = {ti['name']: ti['id'] for ti in tiers_sp}
    br_names  = list(br_opts.keys())
    tier_names = list(tier_opts.keys())

    with st.expander(t("Add New Salesperson")):
        with st.form("add_sp_form"):
            n    = st.text_input(t("Full Name *"), key="new_sp_name")
            br   = st.selectbox(t("Branch *"),       br_names,  key="new_sp_br")
            tier = st.selectbox(t("Target Tier *"),  tier_names, key="new_sp_tier")
            em   = st.text_input(t("Email"),          key="new_sp_email")
            if st.form_submit_button(t("Add Salesperson"), type="primary") and n and br_names and tier_names:
                if _save(add_salesperson, n, br_opts[br], tier_opts[tier], em,
                         ok=f"'{n}' added.", err=f"'{n}' already exists.") is not None:
                    st.rerun()

    for sp in sps:
        _spid = sp['id']
        status = t("Active") if sp['is_active'] else t("Inactive")
        with st.expander(f"[{status}] {sp['name']} — {sp.get('branch_name', '')}"):
            with st.form(f"sp_edit_{_spid}"):
                new_n    = st.text_input(t("Name"),  sp['name'],              key=f"sp_n_{_spid}")
                new_em   = st.text_input(t("Email"), sp.get('email', ''),     key=f"sp_e_{_spid}")
                # Branch selectbox
                cur_br   = sp.get('branch_name', '')
                br_idx   = br_names.index(cur_br) if cur_br in br_names else 0
                new_br   = st.selectbox(t("Branch"),      br_names,  index=br_idx,  key=f"sp_br_{_spid}")
                # Tier selectbox
                cur_tier = sp.get('tier_name', '')
                tier_idx = tier_names.index(cur_tier) if cur_tier in tier_names else 0
                new_t    = st.selectbox(t("Target Tier"), tier_names, index=tier_idx, key=f"sp_ti_{_spid}")
                is_act   = st.checkbox(t("Active"), bool(sp['is_active']),     key=f"sp_a_{_spid}")
                c1, c2   = st.columns(2)
                if c1.form_submit_button(t("Save"), type="primary"):
                    if br_names and tier_names:
                        _save(update_salesperson, sp['id'], new_n,
                              br_opts[new_br], tier_opts[new_t], new_em, is_act)
                    st.rerun()
                if c2.form_submit_button(t("Delete"), type="secondary"):
                    _save(delete_salesperson, sp['id'], ok=f"Deleted '{sp['name']}'.")
                    st.rerun()


# ── TARGET TIERS ─────────────────────────────────────────────────────────────
with tabs[3]:
    st.markdown(f"### {t('Salesperson Target Tiers')}")
    tiers = get_tiers()
    cats  = get_categories(active_only=True)

    with st.expander(t("Add New Tier")):
        with st.form("add_tier_form"):
            tn = st.text_input(t("Tier Name *"), key="new_tier_name")
            td = st.text_input(t("Description"), key="new_tier_desc")
            amounts = {}
            if cats:
                st.markdown(t("**Category Targets (SAR):**"))
                cols = st.columns(len(cats))
                for i, cat in enumerate(cats):
                    amounts[cat['id']] = cols[i].number_input(
                        cat['name'], min_value=0, step=50000, value=0,
                        key=f"new_tc_{i}",
                    )
            if st.form_submit_button(t("Add Tier"), type="primary") and tn:
                try:
                    tid = add_tier(tn, td)
                    for cat_id, amt in amounts.items():
                        set_tier_target(tid, cat_id, float(amt))
                    st.cache_data.clear()
                    st.success(f"Tier '{tn}' added.")
                    st.rerun()
                except Exception as e:
                    msg = str(e).lower()
                    st.error(f"Tier '{tn}' already exists." if "unique" in msg else str(e))

    for tier in tiers:
        _tid   = tier['id']
        total  = sum(tier['targets'].values())
        status = t("Active") if tier['is_active'] else t("Inactive")
        with st.expander(f"[{status}] {tier['name']} — Total: SAR {total:,.0f}"):
            with st.form(f"tier_edit_{_tid}"):
                tn     = st.text_input(t("Name"),        tier['name'],               key=f"t_n_{_tid}")
                td     = st.text_input(t("Description"),  tier.get('description', ''), key=f"t_d_{_tid}")
                is_act = st.checkbox(t("Active"),         bool(tier['is_active']),    key=f"t_a_{_tid}")
                if cats:
                    st.markdown(t("**Category Targets (SAR):**"))
                    cols    = st.columns(len(cats))
                    amounts = {}
                    for i, cat in enumerate(cats):
                        amounts[cat['id']] = cols[i].number_input(
                            cat['name'],
                            min_value=0, step=50000,
                            value=int(tier['targets'].get(cat['id'], 0)),
                            key=f"t_c_{_tid}_{cat['id']}",
                        )
                c1, c2 = st.columns(2)
                if c1.form_submit_button(t("Save"), type="primary"):
                    update_tier(tier['id'], tn, td, is_act)
                    for cat_id, amt in amounts.items():
                        set_tier_target(tier['id'], cat_id, float(amt))
                    st.cache_data.clear()
                    st.success(t("Saved."))
                    st.rerun()
                if c2.form_submit_button(t("Delete"), type="secondary"):
                    _save(delete_tier, tier['id'], ok=f"Deleted '{tier['name']}'.")
                    st.rerun()


# ── CATEGORIES ───────────────────────────────────────────────────────────────
with tabs[4]:
    st.markdown(f"### {t('Product / Service Categories')}")
    cats = get_categories()

    with st.expander(f"+ {t('Add New Category')}"):
        with st.form("add_cat_form"):
            cc1, cc2 = st.columns([3, 1])
            cn = cc1.text_input(t("Category Name *"), key="new_cat_name")
            co = cc2.number_input(t("Display Order"), min_value=0, value=len(cats), key="new_cat_order")
            if st.form_submit_button(t("Add Category"), type="primary") and cn:
                try:
                    cid = add_category(cn, co)
                    update_category(cid, cn, co, True, True, True, True)
                    st.cache_data.clear()
                    st.success(f"'{cn}' added.")
                    st.rerun()
                except Exception as e:
                    msg = str(e).lower()
                    st.error(f"'{cn}' already exists." if "unique" in msg else str(e))

    if cats:
        cat_df = pd.DataFrame([{
            "✓":              False,
            "ID":             c['id'],
            t("Name"):        c['name'],
            t("Order"):       c['display_order'],
            t("In Target"):   bool(c['include_in_target']),
            t("In Commission"):bool(c['include_in_commission']),
            t("In KPI"):      bool(c['include_in_kpi']),
            t("Active"):      bool(c['is_active']),
        } for c in cats])

        _cn = t("Name"); _co = t("Order"); _ct = t("In Target")
        _cc = t("In Commission"); _ck = t("In KPI"); _ca = t("Active")

        edited_cats = st.data_editor(
            cat_df, use_container_width=True, hide_index=True,
            disabled=["ID"], num_rows="fixed", key="cat_editor",
            column_config={
                "✓":   st.column_config.CheckboxColumn("✓", default=False),
                "ID":  st.column_config.NumberColumn("ID", disabled=True),
                _co:   st.column_config.NumberColumn(_co, min_value=0, step=1),
            },
        )

        selected_ids = edited_cats.loc[edited_cats["✓"] == True, "ID"].tolist()
        sb_col, db_col, _ = st.columns([2, 3, 7])

        if sb_col.button(t("Save Changes"), type="primary", key="save_cats", use_container_width=True):
            for _, row in edited_cats.iterrows():
                update_category(int(row['ID']), row[_cn], int(row[_co]),
                                bool(row[_ct]), bool(row[_cc]),
                                bool(row[_ck]), bool(row[_ca]))
            st.cache_data.clear()
            st.success(t("Categories saved."))
            st.rerun()

        del_label = (f"Delete {len(selected_ids)} Selected"
                     if selected_ids else "Delete Selected")
        if db_col.button(del_label, type="secondary", key="del_cats",
                         use_container_width=True, disabled=not selected_ids):
            for cid in selected_ids:
                try:
                    delete_category(int(cid))
                except Exception as e:
                    st.error(f"Cannot delete category: {e}")
            st.cache_data.clear()
            st.success(
                f"Deleted {len(selected_ids)} "
                f"categor{'y' if len(selected_ids) == 1 else 'ies'}."
            )
            st.rerun()
    else:
        st.info(t("No categories yet. Use '+ Add New Category' above to get started."))


# ── COMMISSION BRACKETS ───────────────────────────────────────────────────────
with tabs[5]:
    st.markdown(f"### {t('Category Commission Brackets')}")
    cats_br      = get_categories(active_only=True)
    cat_br_names = [c['name'] for c in cats_br]

    if not cats_br:
        st.info(t("No active categories. Add categories first."))
    else:
        sel_cat_name = st.selectbox(t("Select Category"), cat_br_names, key="bracket_cat")
        cat_obj      = next((c for c in cats_br if c['name'] == sel_cat_name), None)

        calc_method  = st.selectbox(
            t("Calculation Method"), ["flat", "progressive"],
            index=0 if get_setting('global_calc_method', 'flat') == 'flat' else 1,
            key="calc_method_sel",
        )
        if st.button(t("Save Method"), key="save_method"):
            set_setting('global_calc_method', calc_method)
            st.success(t("Method saved."))

        if cat_obj:
            brackets = get_brackets(cat_obj['id'], active_only=False)

            if brackets:
                _bfrom = t("From (SAR)"); _bto = t("To (SAR)")
                _brate = t("Rate %"); _bunlim = t("Unlimited"); _bact = t("Active")
                _bsort = t("Sort")

                br_df = pd.DataFrame([{
                    "✓":      False,
                    "ID":     b['id'],
                    _bfrom:   b['from_amount'],
                    _bto:     b['to_amount'] or 0,
                    _brate:   b['commission_rate'],
                    _bunlim:  bool(b['is_unlimited']),
                    _bact:    bool(b['is_active']),
                    _bsort:   b['sort_order'],
                } for b in brackets])

                edited_br = st.data_editor(
                    br_df, use_container_width=True, hide_index=True,
                    disabled=["ID"],
                    key=f"br_editor_{cat_obj['id']}",
                    column_config={
                        "✓":    st.column_config.CheckboxColumn("✓", default=False),
                        "ID":   st.column_config.NumberColumn("ID", disabled=True),
                        _bfrom: st.column_config.NumberColumn(_bfrom, min_value=0, step=50000),
                        _bto:   st.column_config.NumberColumn(_bto,   min_value=0, step=50000),
                        _brate: st.column_config.NumberColumn(_brate, min_value=0.0, max_value=100.0, step=0.5, format="%.2f%%"),
                        _bsort: st.column_config.NumberColumn(_bsort, min_value=0, step=1),
                    },
                )

                selected_br_ids = edited_br.loc[edited_br["✓"] == True, "ID"].tolist()
                sb1, sb2, _ = st.columns([2, 3, 7])

                if sb1.button(t("Save Brackets"), type="primary",
                              key="save_brackets", use_container_width=True):
                    for _, row in edited_br.iterrows():
                        to_amt = None if row[_bunlim] else row[_bto]
                        update_bracket(int(row['ID']), row[_bfrom], to_amt,
                                       row[_brate], bool(row[_bunlim]),
                                       bool(row[_bact]), int(row[_bsort]))
                    st.cache_data.clear()
                    st.success(t("Brackets saved."))
                    st.rerun()

                del_br_label = (f"Delete {len(selected_br_ids)} Selected"
                                if selected_br_ids else "Delete Selected")
                if sb2.button(del_br_label, type="secondary", key="del_brackets",
                              use_container_width=True, disabled=not selected_br_ids):
                    for bid in selected_br_ids:
                        try:
                            delete_bracket(int(bid))
                        except Exception as e:
                            st.error(f"Cannot delete bracket: {e}")
                    st.cache_data.clear()
                    st.success(f"Deleted {len(selected_br_ids)} bracket(s).")
                    st.rerun()
            else:
                st.info(t("No brackets yet for this category. Add one below."))

            with st.expander(f"+ {t('Add New Bracket')}"):
                with st.form(f"add_bracket_form_{cat_obj['id']}"):
                    c1, c2, c3 = st.columns(3)
                    frm       = c1.number_input(t("From (SAR)"), min_value=0, step=50000, key="new_br_from")
                    to        = c2.number_input(t("To (SAR)"),   min_value=0, step=50000, key="new_br_to")
                    rate      = c3.number_input(t("Rate %"), min_value=0.0, max_value=100.0, step=0.5, key="new_br_rate")
                    unlimited = st.checkbox(t("Unlimited upper range (last bracket)"), key="new_br_unlim")
                    if st.form_submit_button(t("Add Bracket"), type="primary"):
                        _save(add_bracket, cat_obj['id'], frm,
                              None if unlimited else to, rate, unlimited,
                              len(brackets) if brackets else 0, ok="Bracket added.")
                        st.rerun()


# ── KPI SETTINGS ─────────────────────────────────────────────────────────────
with tabs[6]:
    st.markdown(f"### {t('KPI Items & Weights')}")

    kpi_items = get_kpi_items()
    total_wt  = sum(i['weight'] for i in kpi_items if i['is_active'])
    if kpi_items and abs(total_wt - 100) > 0.01:
        st.warning(t("Active KPI weights total {total_wt:.1f}% (should be 100%).").format(total_wt=total_wt))

    with st.expander(f"＋ {t('Add KPI Item')}", expanded=not bool(kpi_items)):
        with st.form("add_kpi_form", clear_on_submit=True):
            c1, c2, c3, c4 = st.columns([3, 1.5, 1.5, 1])
            kpi_name = c1.text_input(t("Name *"), key="new_kpi_name")
            kpi_wt   = c2.number_input("Weight %", min_value=0.0, max_value=100.0, step=1.0, value=10.0, key="new_kpi_wt")
            kpi_max  = c3.number_input(t("Max Score"), min_value=1.0, step=10.0, value=100.0, key="new_kpi_max")
            kpi_sort = c4.number_input(t("Sort"), min_value=0, step=1, value=len(kpi_items), key="new_kpi_sort")
            if st.form_submit_button(f"＋ {t('Add KPI Item')}", type="primary") and kpi_name:
                if _save(add_kpi_item, kpi_name, kpi_wt, kpi_max, kpi_sort, ok=f"'{kpi_name}' added.") is not None:
                    st.rerun()

    if not kpi_items:
        st.info(t("No KPI items yet. Add one above."))
    for item in kpi_items:
        _kid = item['id']
        status_lbl = t("Active") if item['is_active'] else t("Inactive")
        with st.expander(f"[{status_lbl}] {item['name']} — {item['weight']:.0f}%"):
            with st.form(f"kpi_edit_{_kid}"):
                c1, c2, c3, c4 = st.columns([3, 1.5, 1.5, 1])
                new_name   = c1.text_input(t("Name"), item['name'], key=f"kpi_n_{_kid}")
                new_wt     = c2.number_input("Weight %", min_value=0.0, max_value=100.0, step=1.0,
                                             value=float(item['weight']), key=f"kpi_w_{_kid}")
                new_max    = c3.number_input(t("Max Score"), min_value=1.0, step=10.0,
                                             value=float(item['max_score']), key=f"kpi_m_{_kid}")
                new_sort   = c4.number_input(t("Sort"), min_value=0, step=1,
                                             value=int(item['sort_order']), key=f"kpi_s_{_kid}")
                new_active = st.checkbox(t("Active"), value=bool(item['is_active']), key=f"kpi_a_{_kid}")
                col1, col2 = st.columns(2)
                if col1.form_submit_button(t("Save"), type="primary"):
                    _save(update_kpi_item, item['id'], new_name, new_wt, new_max, new_active, new_sort,
                          ok=f"'{new_name}' saved.")
                    st.rerun()
                if col2.form_submit_button(t("Delete"), type="secondary"):
                    _save(delete_kpi_item, item['id'], ok=f"Deleted '{item['name']}'.")
                    st.rerun()

    # ── Category auto-link ────────────────────────────────────────────────────
    st.markdown(f"### {t('Auto-Score from Category Achievement %')}")
    st.caption(t(
        "Link a KPI item to a sales category — score is computed automatically "
        "from Actual / Target x 100 (capped at 100). "
        "Linked items do NOT appear in the manual KPI entry table."
    ))
    cats_lnk       = get_categories(active_only=True)
    cat_name_to_id = {c['name']: c['id'] for c in cats_lnk}
    _manual_opt    = t("Manual - Enter Score")
    cat_options    = [_manual_opt] + [c['name'] for c in cats_lnk]

    with st.form("kpi_links_form"):
        link_selections = {}
        for item in kpi_items:
            c1, c2 = st.columns([2, 3])
            c1.markdown(f"**{item['name']}** ({item['weight']:.0f}%)")
            current_name = item.get('linked_category_name') or _manual_opt
            if current_name not in cat_options:
                current_name = _manual_opt
            link_selections[item['id']] = c2.selectbox(
                t("Source"), cat_options,
                index=cat_options.index(current_name),
                key=f"kpi_lnk_{item['id']}",
                label_visibility="collapsed",
            )
        if st.form_submit_button(t("Save Category Links"), type="primary"):
            for item_id, selected_name in link_selections.items():
                set_kpi_linked_category(item_id, cat_name_to_id.get(selected_name))
            st.cache_data.clear()
            st.success(t("Category links saved."))
            st.rerun()

    # ── KPI Multiplier Rules ──────────────────────────────────────────────────
    st.divider()
    st.markdown(f"### {t('KPI Multiplier Rules')}")

    rules = get_multiplier_rules(active_only=False)

    with st.form("add_rule_form", clear_on_submit=True):
        rc = st.columns([1.2, 1.2, 1.2, 1.5, 1.8])
        r_from  = rc[0].number_input(t("Score From"), min_value=0.0, step=5.0,  value=0.0,  key="new_rule_from")
        r_to    = rc[1].number_input(t("Score To"),   min_value=0.0, step=5.0,  value=80.0, key="new_rule_to")
        r_mult  = rc[2].number_input(t("Multiplier"), min_value=0.0, step=0.05, value=1.0,  key="new_rule_mult")
        r_unlim = rc[3].checkbox(t("No upper bound"), key="new_rule_unlim")
        rc[4].markdown("<div style='height:27px'></div>", unsafe_allow_html=True)
        if rc[4].form_submit_button(f"＋ {t('Add Rule')}", type="primary", use_container_width=True):
            _save(add_multiplier_rule, r_from, None if r_unlim else r_to, r_mult, r_unlim, ok="Rule added.")
            st.rerun()

    if not rules:
        st.info(t("No multiplier rules yet."))
    else:
        rh = st.columns([1.2, 1.2, 1.2, 1, 1, 0.8, 0.8])
        for col, lbl in zip(rh, [t("Score From"), t("Score To"), t("Multiplier"), t("Unlimited"), t("Active"), "", ""]):
            col.markdown(f"<small><b>{lbl}</b></small>", unsafe_allow_html=True)
        st.divider()

        _editing_rule = st.session_state.get('_rule_edit_id')
        for rule in rules:
            if _editing_rule == rule['id']:
                with st.form(f"rule_edit_form_{rule['id']}"):
                    rc = st.columns([1.2, 1.2, 1.2, 1, 1, 0.8, 0.8])
                    rf  = rc[0].number_input("", min_value=0.0, step=5.0, value=float(rule['score_from']), label_visibility="collapsed", key=f"re_f_{rule['id']}")
                    rt  = rc[1].number_input("", min_value=0.0, step=5.0, value=float(rule['score_to'] or 100), label_visibility="collapsed", key=f"re_t_{rule['id']}")
                    rm  = rc[2].number_input("", min_value=0.0, step=0.05, value=float(rule['multiplier']), label_visibility="collapsed", key=f"re_m_{rule['id']}")
                    ru  = rc[3].checkbox("", value=bool(rule['is_unlimited']), key=f"re_u_{rule['id']}")
                    ra  = rc[4].checkbox("", value=bool(rule['is_active']), key=f"re_a_{rule['id']}")
                    rs  = rc[5].form_submit_button("✓", type="primary", use_container_width=True)
                    rx  = rc[6].form_submit_button("✕", use_container_width=True)
                    if rs:
                        execute("UPDATE kpi_multiplier_rules SET score_from=%s, score_to=%s, "
                                "multiplier=%s, is_unlimited=%s, is_active=%s WHERE id=%s",
                                (rf, None if ru else rt, rm, int(ru), int(ra), rule['id']))
                        st.session_state.pop('_rule_edit_id', None)
                        st.cache_data.clear()
                        st.rerun()
                    if rx:
                        st.session_state.pop('_rule_edit_id', None)
                        st.rerun()
            else:
                rc = st.columns([1.2, 1.2, 1.2, 1, 1, 0.8, 0.8])
                rc[0].write(f"{rule['score_from']:.0f}")
                rc[1].write(f"{rule['score_to'] or '∞'}")
                rc[2].write(f"×{rule['multiplier']:.2f}")
                rc[3].write("✓" if rule['is_unlimited'] else "—")
                rc[4].write("✓" if rule['is_active'] else "—")
                if rc[5].button(t("Edit"), key=f"rule_edit_btn_{rule['id']}", use_container_width=True):
                    st.session_state['_rule_edit_id'] = rule['id']
                    st.rerun()
                if rc[6].button(t("Del"), key=f"rule_del_btn_{rule['id']}", type="secondary", use_container_width=True):
                    _save(delete_multiplier_rule, rule['id'], ok="Rule deleted.")
                    st.rerun()
            st.divider()


# ── PERIODS ───────────────────────────────────────────────────────────────────
with tabs[7]:
    st.markdown(f"### {t('Period Settings')}")
    periods = get_periods()

    with st.form("create_period_form"):
        c1, c2 = st.columns(2)
        py = c1.selectbox(t("Year"),    [2024, 2025, 2026, 2027], index=2, key="new_period_y")
        pq = c2.selectbox(t("Quarter"), [1, 2, 3, 4], index=1, format_func=q_label, key="new_period_q")
        if st.form_submit_button(t("Create Period"), type="primary"):
            get_or_create_period(py, pq)
            st.success(f"Period Q{pq} {py} ready.")
            st.rerun()

    for p in periods:
        status  = t("Locked") if p['is_locked'] else t("Open")
        current = " [Current]" if p['is_current'] else ""
        with st.expander(f"[{status}]{current}  Q{p['quarter']} {p['year']}"):
            c1, c2 = st.columns(2)
            if p['is_locked']:
                if c1.button(f"Unlock Q{p['quarter']} {p['year']}",
                              key=f"unlock_{p['id']}"):
                    unlock_period(p['id'])
                    log_action("QUARTER_UNLOCK", "period", p['id'], f"Q{p['quarter']} {p['year']}")
                    st.success(t("Unlocked."))
                    st.rerun()
            else:
                if c1.button(f"Lock Q{p['quarter']} {p['year']}",
                              key=f"lock_{p['id']}"):
                    lock_period(p['id'])
                    log_action("QUARTER_LOCK", "period", p['id'], f"Q{p['quarter']} {p['year']}")
                    st.success(t("Locked."))
                    st.rerun()
            if c2.button(t("Set as Current"), key=f"curr_{p['id']}"):
                execute("UPDATE periods SET is_current=0")
                execute("UPDATE periods SET is_current=1 WHERE id=%s", (p['id'],))
                st.success(t("Set as current."))
                st.rerun()


# ── USERS ─────────────────────────────────────────────────────────────────────
with tabs[8]:
    from src.auth import (list_users, create_user, update_user_password,
                           delete_user, is_admin)
    st.markdown(f"### {t('App Users')}")

    if not is_admin():
        st.warning(t("Only admins can manage users."))
    else:
        with st.expander(t("Add New User")):
            with st.form("add_user_form"):
                c1, c2    = st.columns(2)
                new_uname = c1.text_input(t("Username *"), key="new_usr_name").strip().lower()
                new_fname = c2.text_input(t("Full Name"),  key="new_usr_fname")
                new_pw    = c1.text_input(t("Password *"),         type="password", key="new_usr_pw")
                new_pw2   = c2.text_input(t("Confirm Password *"), type="password", key="new_usr_pw2")
                new_role  = st.selectbox(t("Role"), ["viewer", "admin"], key="new_usr_role")
                if st.form_submit_button(t("Create User"), type="primary"):
                    if not new_uname or not new_pw:
                        st.error(t("Username and password are required."))
                    elif new_pw != new_pw2:
                        st.error(t("Passwords do not match."))
                    else:
                        _save(create_user, new_uname, new_pw, new_fname, new_role,
                              ok=f"User '{new_uname}' created.",
                              err=f"Username '{new_uname}' already exists.")

        users = list_users()
        current_user = st.session_state.get('username', '')
        for u in users:
            _uid = u['id']
            badge = "[Admin]" if u['role'] == 'admin' else "[Viewer]"
            you   = " (you)" if u['username'] == current_user else ""
            with st.expander(f"{badge} {u['username']}{you} — {u['full_name'] or '-'} — {u['role']}"):
                with st.form(f"usr_edit_{_uid}"):
                    np1 = st.text_input(t("New Password"),         type="password",
                                        placeholder=t("Leave blank to keep current"),
                                        key=f"usr_pw1_{_uid}")
                    np2 = st.text_input(t("Confirm New Password"), type="password",
                                        key=f"usr_pw2_{_uid}")
                    nr  = st.selectbox(t("Role"), ["viewer", "admin"],
                                       index=0 if u['role'] == "viewer" else 1,
                                       key=f"usr_role_{_uid}")
                    c1, c2 = st.columns(2)
                    if c1.form_submit_button(t("Save"), type="primary"):
                        if np1:
                            if np1 != np2:
                                st.error(t("Passwords do not match."))
                            else:
                                update_user_password(u['id'], np1)
                                st.success("Password updated.")
                        execute("UPDATE app_users SET role=%s WHERE id=%s", (nr, u['id']))
                        st.success(t("Saved."))
                        st.rerun()
                    if c2.form_submit_button(t("Delete"), type="secondary"):
                        if u['username'] == current_user:
                            st.error(t("Cannot delete your own account."))
                        else:
                            _save(delete_user, u['id'], ok=f"User '{u['username']}' deleted.")
                            st.rerun()


