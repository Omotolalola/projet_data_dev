from src.dynamic_optimizer import KnapsackPlanner


def test_knapsack_solution():
    items = [
        {"id": 1, "value": 100, "duration_hours": 2},
        {"id": 2, "value": 150, "duration_hours": 3},
        {"id": 3, "value": 200, "duration_hours": 5},
    ]

    planner = KnapsackPlanner(capacity_hours=5)

    result = planner.solve(items)

    assert result["total_value"] >= 250