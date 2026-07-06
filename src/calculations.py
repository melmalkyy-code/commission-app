from __future__ import annotations
"""Commission and KPI calculation engine for the web app."""
import streamlit as st
from src.models import (
    get_salespersons, get_categories, get_brackets, get_calc_method,
    get_tier_target, get_sales, get_kpi_items, get_multiplier_rules,
    get_kpi_score, get_kpi_adjustment, get_category_achievement,
    get_tiers, get_all_kpi_scores, get_all_kpi_adjustments,
)


def _safe_div(a, b, default=0.0):
    return (a / b) if b else default


def _calc_kpi_maps(sp_id, tier_id, kpi_items, scores_map, adj_map,
                   sales_map, tier_targets_map):
    """KPI calc for one salesperson using pre-loaded maps — no DB queries.
    Produces the same result dict as calc_kpi()."""
    weighted = 0.0
    details  = []
    for item in kpi_items:
        if item.get('linked_category_id'):
            cat_id = item['linked_category_id']
            actual = sales_map.get((sp_id, cat_id), 0.0)
            target = tier_targets_map.get(tier_id, {}).get(cat_id, 0.0)
            raw = min((actual / target * 100) if target else 0.0, 100.0)
            is_auto = True
        else:
            raw = scores_map.get((sp_id, item['id']), 0.0)
            is_auto = False
        norm    = _safe_div(raw, item['max_score']) * 100
        contrib = _safe_div(norm * item['weight'], 100)
        weighted += contrib
        details.append({**item, 'raw_score': raw, 'normalized': norm,
                        'contribution': contrib, 'is_auto': is_auto})

    bonus, penalty = adj_map.get(sp_id, (0.0, 0.0))
    final = max(0.0, min(weighted + bonus - penalty, 150.0))
    multiplier, applied = _get_multiplier_rule(final)
    return {
        'items': details,
        'weighted_score': round(weighted, 2),
        'bonus': bonus,
        'penalty': penalty,
        'final_score': round(final, 2),
        'multiplier': multiplier,
        'applied_rule': applied,
        'weight_total': sum(i['weight'] for i in kpi_items),
    }


# -- KPI ----------------------------------------------------------------------
def calc_kpi(period_id: int, sp_id: int) -> dict:
    items = get_kpi_items(active_only=True)
    weighted = 0.0
    details = []
    for item in items:
        if item.get('linked_category_id'):
            raw = get_category_achievement(period_id, sp_id, item['linked_category_id'])
            is_auto = True
        else:
            raw = get_kpi_score(period_id, sp_id, item['id'])
            is_auto = False
        norm = _safe_div(raw, item['max_score']) * 100
        contrib = _safe_div(norm * item['weight'], 100)
        weighted += contrib
        details.append({**item, 'raw_score': raw, 'normalized': norm, 'contribution': contrib, 'is_auto': is_auto})

    adj = get_kpi_adjustment(period_id, sp_id)
    bonus = adj.get('bonus_points', 0) or 0
    penalty = adj.get('penalty_points', 0) or 0
    final = max(0.0, min(weighted + bonus - penalty, 150.0))
    multiplier, applied = _get_multiplier_rule(final)

    return {
        'items': details,
        'weighted_score': round(weighted, 2),
        'bonus': bonus,
        'penalty': penalty,
        'final_score': round(final, 2),
        'multiplier': multiplier,
        'applied_rule': applied,          # the multiplier bracket that matched
        'weight_total': sum(i['weight'] for i in items),
    }


def _get_multiplier_rule(score: float):
    """Return (multiplier, rule_dict) for the bracket the score falls in."""
    for rule in get_multiplier_rules(active_only=True):
        upper = rule['score_to'] if not rule['is_unlimited'] else float('inf')
        if upper is None:
            upper = float('inf')
        if rule['score_from'] <= score <= upper:
            return rule['multiplier'], rule
    return 1.0, None


def _get_multiplier(score: float) -> float:
    return _get_multiplier_rule(score)[0]


# -- Commission brackets ------------------------------------------------------
def calc_flat(sales: float, brackets: list) -> tuple:
    if not brackets or sales <= 0:
        return 0.0, "No bracket", 0.0
    for b in sorted(brackets, key=lambda x: x['from_amount']):
        upper = b['to_amount'] if not b['is_unlimited'] else float('inf')
        if upper is None:
            upper = float('inf')
        if b['from_amount'] <= sales <= upper or (b['is_unlimited'] and sales >= b['from_amount']):
            rate = b['commission_rate']
            to_str = "Unlimited" if b['is_unlimited'] else "SAR {:,.0f}".format(b['to_amount'])
            label = "SAR {:,.0f} - {} @ {:.2f}%".format(b['from_amount'], to_str, rate)
            return round(sales * rate / 100, 2), label, rate
    last = brackets[-1]
    rate = last['commission_rate']
    return round(sales * rate / 100, 2), "SAR {:,.0f}+ @ {:.2f}%".format(last['from_amount'], rate), rate


def calc_progressive(sales: float, brackets: list) -> tuple:
    if not brackets or sales <= 0:
        return 0.0, "Progressive", 0.0
    total = 0.0
    for b in sorted(brackets, key=lambda x: x['from_amount']):
        upper = (b['to_amount'] if not b['is_unlimited'] and b['to_amount'] is not None else float('inf'))
        taxable = min(sales, upper) - b['from_amount']
        if taxable > 0:
            total += taxable * b['commission_rate'] / 100
        if sales <= upper:
            break
    eff = _safe_div(total * 100, sales)
    return round(total, 2), "Progressive ({:.2f}% eff.)".format(eff), eff


# -- Full commission calculation -----------------------------------------------
@st.cache_data(ttl=120, show_spinner=False)
def calc_all_commissions(period_id: int) -> list:
    # Cached: this orchestrates many per-record DB reads (sales, KPI scores,
    # adjustments) for every salesperson. On a remote PostgreSQL each of those
    # is a network round-trip, so recomputing on every rerun made the app very
    # slow. Write pages (Sales, KPI, Settings) call st.cache_data.clear(), so
    # edits are reflected immediately.
    salespersons = get_salespersons(active_only=True)
    categories   = [c for c in get_categories(active_only=True) if c['include_in_commission']]
    all_sales    = get_sales(period_id)
    sales_map    = {(r['salesperson_id'], r['category_id']): r['actual_sales'] for r in all_sales}

    # Bulk-load everything the loop needs so it makes ZERO per-salesperson
    # queries (was ~40-50 round-trips to the remote DB per computation).
    kpi_items        = get_kpi_items(active_only=True)
    scores_map       = get_all_kpi_scores(period_id)
    adj_map          = get_all_kpi_adjustments(period_id)
    tier_targets_map = {t['id']: t['targets'] for t in get_tiers()}
    bracket_map      = {c['id']: get_brackets(c['id'], active_only=True) for c in categories}
    method_map       = {c['id']: get_calc_method(c['id']) for c in categories}

    results = []
    for sp in salespersons:
        kpi = _calc_kpi_maps(sp['id'], sp.get('tier_id'), kpi_items,
                             scores_map, adj_map, sales_map, tier_targets_map)
        cat_results = []
        base = 0.0
        for cat in categories:
            actual   = sales_map.get((sp['id'], cat['id']), 0.0)
            target   = tier_targets_map.get(sp.get('tier_id'), {}).get(cat['id'], 0.0)
            ach      = _safe_div(actual * 100, target)
            method   = method_map[cat['id']]
            brackets = bracket_map[cat['id']]
            if method == 'progressive':
                comm, label, rate = calc_progressive(actual, brackets)
            else:
                comm, label, rate = calc_flat(actual, brackets)
            base += comm
            cat_results.append({
                'category_id':   cat['id'],
                'category_name': cat['name'],
                'actual_sales':  actual,
                'target':        target,
                'achievement':   ach,
                'bracket':       label,
                'rate':          rate,
                'commission':    comm,
            })

        total_actual = sum(c['actual_sales'] for c in cat_results)
        total_target = sum(c['target'] for c in cat_results)
        final = round(base * kpi['multiplier'], 2)

        results.append({
            'salesperson_id':   sp['id'],
            'salesperson_name': sp['name'],
            'branch_name':      sp.get('branch_name', ''),
            'tier_name':        sp.get('tier_name', ''),
            'tier_id':          sp.get('tier_id'),
            'categories':       cat_results,
            'base_commission':  round(base, 2),
            'kpi_score':        kpi['final_score'],
            'kpi_multiplier':   kpi['multiplier'],
            'kpi':              kpi,   # full breakdown: items, bonus, penalty, weighted_score
            'final_commission': final,
            'total_actual':     total_actual,
            'total_target':     total_target,
            'achievement':      _safe_div(total_actual * 100, total_target),
        })

    return results


def get_totals(commissions: list) -> dict:
    total_sales  = sum(c['total_actual'] for c in commissions)
    total_target = sum(c['total_target'] for c in commissions)
    total_base   = sum(c['base_commission'] for c in commissions)
    total_final  = sum(c['final_commission'] for c in commissions)
    ach          = _safe_div(total_sales * 100, total_target)
    achieved     = sum(1 for c in commissions if c['achievement'] >= 100)
    best         = max(commissions, key=lambda c: c['achievement'], default=None)
    worst        = min(commissions, key=lambda c: c['achievement'], default=None)
    top5         = sorted(commissions, key=lambda c: c['total_actual'], reverse=True)[:5]
    return {
        'total_sales': total_sales, 'total_target': total_target,
        'achievement': ach, 'total_base': total_base, 'total_final': total_final,
        'achieved_count': achieved, 'total_count': len(commissions),
        'best': best['salesperson_name'] if best else '',
        'worst': worst['salesperson_name'] if worst else '',
        'top5': top5,
    }
