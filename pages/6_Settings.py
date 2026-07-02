import sys, os; sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import streamlit as st
import pandas as pd
from src.startup import init_db
from src.auth import require_login, logout_button, require_admin
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
    get_kpi_items, add_kpi_item, delete_kpi_item, set_kpi_linked_category,
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
            c = st.text_input(t("City"),          key="new_br_city")
            if st.form_submit_button(t("Add Branch"), type="primary") and n:
                if _save(add_branch, n, c, ok=f"Branch '{n}' added.",
                         err=f"Branch '{n}' already exists.") is not None:
                    log_action("ADD_BRANCH", "branch", entity_name=n)
                    st.rerun()

    for _bi, br in enumerate(branches):
        status = t("Active") if br['is_active'] else t("Inactive")
        with st.expander(f"[{status}] {br['name']} — {br.get('city', '')}"):
            with st.form(f"br_edit_{_bi}"):
                new_name  = st.text_input(t("Name"),   br['name'],          key=f"br_n_{_bi}")
                new_city  = st.text_input(t("City"),   br.get('city', ''), key=f"br_c_{_bi}")
                is_active = st.checkbox(t("Active"),   bool(br['is_active']), key=f"br_a_{_bi}")
                c1, c2   = st.columns(2)
                if c1.form_submit_button(t("Save"), type="primary"):
                    _save(update_branch, br['id'], new_name, new_city, is_active)
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

    for _si, sp in enumerate(sps):
        status = t("Active") if sp['is_active'] else t("Inactive")
        with st.expander(f"[{status}] {sp['name']} — {sp.get('branch_name', '')}"):
            with st.form(f"sp_edit_{_si}"):
                new_n    = st.text_input(t("Name"),  sp['name'],              key=f"sp_n_{_si}")
                new_em   = st.text_input(t("Email"), sp.get('email', ''),     key=f"sp_e_{_si}")
                # Branch selectbox
                cur_br   = sp.get('branch_name', '')
                br_idx   = br_names.index(cur_br) if cur_br in br_names else 0
                new_br   = st.selectbox(t("Branch"),      br_names,  index=br_idx,  key=f"sp_br_{_si}")
                # Tier selectbox
                cur_tier = sp.get('tier_name', '')
                tier_idx = tier_names.index(cur_tier) if cur_tier in tier_names else 0
                new_t    = st.selectbox(t("Target Tier"), tier_names, index=tier_idx, key=f"sp_ti_{_si}")
                is_act   = st.checkbox(t("Active"), bool(sp['is_active']),     key=f"sp_a_{_si}")
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

    for _ti, tier in enumerate(tiers):
        total  = sum(tier['targets'].values())
        status = t("Active") if tier['is_active'] else t("Inactive")
        with st.expander(f"[{status}] {tier['name']} — Total: SAR {total:,.0f}"):
            with st.form(f"tier_edit_{_ti}"):
                tn     = st.text_input(t("Name"),        tier['name'],               key=f"t_n_{_ti}")
                td     = st.text_input(t("Description"),  tier.get('description', ''), key=f"t_d_{_ti}")
                is_act = st.checkbox(t("Active"),         bool(tier['is_active']),    key=f"t_a_{_ti}")
                if cats:
                    st.markdown(t("**Category Targets (SAR):**"))
                    cols    = st.columns(len(cats))
                    amounts = {}
                    for i, cat in enumerate(cats):
                        amounts[cat['id']] = cols[i].number_input(
                            cat['name'],
                            min_value=0, step=50000,
                            value=int(tier['targets'].get(cat['id'], 0)),
                            key=f"t_c_{_ti}_{i}",
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

    with st.expander(f"＋ {t('Add New Category')}"):
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

        if sb_col.button(t("💾 Save Changes"), type="primary", key="save_cats", use_container_width=True):
            for _, row in edited_cats.iterrows():
                update_category(int(row['ID']), row[_cn], int(row[_co]),
                                bool(row[_ct]), bool(row[_cc]),
                                bool(row[_ck]), bool(row[_ca]))
            st.cache_data.clear()
            st.success(t("Categories saved."))
            st.rerun()

        del_label = (f"🗑 Delete {len(selected_ids)} Selected"
                     if selected_ids else "🗑 Delete Selected")
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
        st.info(t("No categories yet. Use '＋ Add New Category' above to get started."))


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

                if sb1.button(t("💾 Save Brackets"), type="primary",
                              key="save_brackets", use_container_width=True):
                    for _, row in edited_br.iterrows():
                        to_amt = None if row[_bunlim] else row[_bto]
                        update_bracket(int(row['ID']), row[_bfrom], to_amt,
                                       row[_brate], bool(row[_bunlim]),
                                       bool(row[_bact]), int(row[_bsort]))
                    st.cache_data.clear()
                    st.success(t("Brackets saved."))
                    st.rerun()

                del_br_label = (f"🗑 Delete {len(selected_br_ids)} Selected"
                                if selected_br_ids else "🗑 Delete Selected")
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

            with st.expander(f"＋ {t('Add New Bracket')}"):
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

    with st.expander(t("Add New KPI Item")):
        with st.form("add_kpi_form"):
            c1, c2, c3, c4 = st.columns(4)
            kpi_name = c1.text_input(t("Name *"),      key="new_kpi_name")
            kpi_wt   = c2.number_input("Weight %",  min_value=0.0, max_value=100.0, step=1.0, value=10.0, key="new_kpi_wt")
            kpi_max  = c3.number_input(t("Max Score"), min_value=1.0, step=10.0, value=100.0,               key="new_kpi_max")
            kpi_sort = c4.number_input(t("Sort Order"), min_value=0, step=1, value=0,                        key="new_kpi_sort")
            if st.form_submit_button(t("Add KPI Item"), type="primary") and kpi_name:
                if _save(add_kpi_item, kpi_name, kpi_wt, kpi_max, kpi_sort,
                         ok=f"'{kpi_name}' added.") is not None:
                    st.rerun()

    kpi_items = get_kpi_items()
    total_wt  = sum(i['weight'] for i in kpi_items if i['is_active'])
    if abs(total_wt - 100) > 0.01:
        st.warning(t("Active KPI weights total {total_wt:.1f}% (should be 100%).").format(total_wt=total_wt))

    if kpi_items:
        _kn = t("Name"); _kw = "Weight %"; _km = t("Max Score")
        _ka = t("Active"); _ks = t("Sort")
        kpi_df = pd.DataFrame([{
            "ID": i['id'], _kn: i['name'], _kw: i['weight'],
            _km: i['max_score'], _ka: bool(i['is_active']),
            _ks: i['sort_order'],
        } for i in kpi_items])
        edited_kpi = st.data_editor(
            kpi_df, use_container_width=True, hide_index=True,
            disabled=["ID"], key="kpi_editor",
        )
        if st.button(t("Save KPI Items"), type="primary", key="save_kpi"):
            for _, row in edited_kpi.iterrows():
                execute(
                    "UPDATE kpi_items SET name=%s, weight=%s, max_score=%s, "
                    "is_active=%s, sort_order=%s WHERE id=%s",
                    (row[_kn], row[_kw], row[_km],
                     int(row[_ka]), int(row[_ks]), int(row['ID'])),
                )
            st.cache_data.clear()
            st.success(t("KPI items saved."))
            st.rerun()

        _sel_sentinel = t("-- select --")
        del_kpi = st.selectbox(
            t("Delete a KPI item"),
            [_sel_sentinel] + [i['name'] for i in kpi_items],
            key="del_kpi_sel",
        )
        if del_kpi != _sel_sentinel:
            item_to_del = next((i for i in kpi_items if i['name'] == del_kpi), None)
            if item_to_del and st.button(f"Delete '{del_kpi}'", type="secondary", key="do_del_kpi"):
                _save(delete_kpi_item, item_to_del['id'], ok=f"Deleted '{del_kpi}'.")
                st.rerun()

    # Category auto-link
    st.divider()
    st.markdown(f"### {t('Auto-Score from Category Achievement %')}")
    st.caption(t(
        "Link a KPI item to a sales category — score is computed automatically "
        "from Actual / Target x 100 (capped at 100). "
        "Linked items do NOT appear in the manual KPI entry table."
    ))
    cats_lnk        = get_categories(active_only=True)
    cat_name_to_id  = {c['name']: c['id'] for c in cats_lnk}
    _manual_opt     = t("Manual - Enter Score")
    cat_options     = [_manual_opt] + [c['name'] for c in cats_lnk]

    with st.form("kpi_links_form"):
        link_selections = {}
        for _kli, item in enumerate(kpi_items):
            c1, c2 = st.columns([2, 3])
            c1.markdown(f"**{item['name']}** ({item['weight']:.0f}%)")
            current_name = item.get('linked_category_name') or _manual_opt
            if current_name not in cat_options:
                current_name = _manual_opt
            link_selections[item['id']] = c2.selectbox(
                t("Source"), cat_options,
                index=cat_options.index(current_name),
                key=f"kpi_lnk_{_kli}",
                label_visibility="collapsed",
            )
        if st.form_submit_button(t("Save Category Links"), type="primary"):
            for item_id, selected_name in link_selections.items():
                set_kpi_linked_category(item_id, cat_name_to_id.get(selected_name))
            st.cache_data.clear()
            st.success(t("Category links saved."))
            st.rerun()

    # Multiplier rules
    st.divider()
    st.markdown(f"### {t('KPI Multiplier Rules')}")

    with st.expander(t("Add New Multiplier Rule")):
        with st.form("add_rule_form"):
            c1, c2, c3, c4 = st.columns(4)
            r_from  = c1.number_input(t("Score From"), min_value=0.0, step=5.0,  value=0.0,  key="new_rule_from")
            r_to    = c2.number_input(t("Score To"),   min_value=0.0, step=5.0,  value=80.0, key="new_rule_to")
            r_mult  = c3.number_input(t("Multiplier"), min_value=0.0, step=0.05, value=1.0,  key="new_rule_mult")
            r_unlim = c4.checkbox(t("Unlimited (no upper bound)"), key="new_rule_unlim")
            if st.form_submit_button(t("Add Rule"), type="primary"):
                _save(add_multiplier_rule, r_from,
                      None if r_unlim else r_to, r_mult, r_unlim, ok="Rule added.")
                st.rerun()

    rules = get_multiplier_rules(active_only=False)
    if rules:
        _rsf = t("Score From"); _rst = t("Score To")
        _rm = t("Multiplier"); _ru = t("Unlimited"); _ra = t("Active")
        rules_df = pd.DataFrame([{
            "ID": r['id'], _rsf: r['score_from'],
            _rst: r['score_to'] or 999,
            _rm: r['multiplier'],
            _ru: bool(r['is_unlimited']),
            _ra: bool(r['is_active']),
        } for r in rules])
        edited_rules = st.data_editor(
            rules_df, use_container_width=True, hide_index=True,
            disabled=["ID"], key="rules_editor",
        )
        if st.button(t("Save Multiplier Rules"), type="primary", key="save_rules"):
            for _, row in edited_rules.iterrows():
                to_val = None if row[_ru] else row[_rst]
                execute(
                    "UPDATE kpi_multiplier_rules SET score_from=%s, score_to=%s, "
                    "multiplier=%s, is_unlimited=%s, is_active=%s WHERE id=%s",
                    (row[_rsf], to_val, row[_rm],
                     int(row[_ru]), int(row[_ra]), int(row['ID'])),
                )
            st.cache_data.clear()
            st.success(t("Multiplier rules saved."))
            st.rerun()

        rule_labels = [
            f"Score {r['score_from']}-{r['score_to'] or 'max'} | x{r['multiplier']}"
            for r in rules
        ]
        _sel_rule_sentinel = t("-- select --")
        del_rule = st.selectbox(t("Delete a rule"), [_sel_rule_sentinel] + rule_labels, key="del_rule_sel")
        if del_rule != _sel_rule_sentinel:
            idx = rule_labels.index(del_rule)
            if st.button(t("Delete selected rule"), type="secondary", key="do_del_rule"):
                _save(delete_multiplier_rule, rules[idx]['id'], ok="Rule deleted.")
                st.rerun()


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
        for _ui, u in enumerate(users):
            badge = "[Admin]" if u['role'] == 'admin' else "[Viewer]"
            you   = " (you)" if u['username'] == current_user else ""
            with st.expander(f"{badge} {u['username']}{you} — {u['full_name'] or '-'} — {u['role']}"):
                with st.form(f"usr_edit_{_ui}"):
                    np1 = st.text_input(t("New Password"),         type="password",
                                        placeholder=t("Leave blank to keep current"),
                                        key=f"usr_pw1_{_ui}")
                    np2 = st.text_input(t("Confirm New Password"), type="password",
                                        key=f"usr_pw2_{_ui}")
                    nr  = st.selectbox(t("Role"), ["viewer", "admin"],
                                       index=0 if u['role'] == "viewer" else 1,
                                       key=f"usr_role_{_ui}")
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

logout_button()
