def compute_team_totals(team):
    sale_items = team.included_items if hasattr(team, "included_items") else team.items_bought
    team.spend = sum(i.shop_price for i in sale_items)
    team.revenue = sum(i.auction_price for i in sale_items)
    team.profit = team.revenue - team.spend

def golden_gavel(team) -> bool:
    # Golden gavel if ALL 3 team-bought items (non-expert pick) make a profit.
    team_items = [i for i in team.items_bought if not i.is_expert_pick]
    if len(team_items) != 3:
        return False
    return all(i.auction_price > i.shop_price for i in team_items)
