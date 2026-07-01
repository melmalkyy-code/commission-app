from __future__ import annotations
"""Commission and KPI calculation engine for the web app."""
from src.models import (
    get_salespersons, get_categories, get_brackets, get_calc_method,
    get_tier_target, get_sales, get_kpi_items, get_multiplier_rules,
    get_kpi_score, get_kpi_adjustment, get_category_achievement
)


def _safe_div(a, b, default=0.0):
    return (a / b) if b else default


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
    multiplier = _get_multiplier(final)

    return {
        'items': details,
        'weighted_score': round(weighted, 2),
        'bonus': bonus,
        'penalty': penalty,
        'final_score': round(final, 2),
        'multiplier': multiplier,
        'weight_total': sum(i['weight'] for i in items),
    }


def _get_multiplier(score: float) -> float:
    for rule in get_multiplier_rules(active_only=True):
        upper = rule['score_to'] if not rule['is_unlimited'] else float('inf')
        if upper is None:
            upper = float('inf')
        if rule['score_from'] <= score <= upper:
            return rule['multiplier']
    return 1.0


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
def calc_all_commissions(period_id: int) -> list:
    salespersons = get_salespersons(active_only=True)
    categories   = [c for c in get_categories(active_only=True) if c['include_in_commission']]
    all_sales    = get_sales(period_id)

    sales_map = {(r['salesperson_id'], r['category_id']): r['actual_sales'] for r in all_sales}

    results = []
    for sp in salespersons:
        kpi = calc_kpi(period_id, sp['id'])
        cat_results = []
        base = 0.0
        for cat in categories:
            actual   = sales_map.get((sp['id'], cat['id']), 0.0)
            target   = get_tier_target(sp['tier_id'], cat['id']) if sp['tier_id'] else 0.0
            ach      = _safe_div(actual * 100, target)
            method   = get_calc_method(cat['id'])
            brackets = get_brackets(cat['id'], active_only=True)
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
