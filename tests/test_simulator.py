from src.simulator import MarketSimulator


def test_load_data():
    simulator = MarketSimulator()
    data = simulator.load_data()

    assert not data.empty
    assert "Close" in data.columns
    assert "Symbol" in data.columns


def test_generate_order():
    simulator = MarketSimulator()
    data = simulator.load_data()

    order = simulator.generate_order(data.iloc[0], 1)

    assert order["order_id"] == 1
    assert order["side"] in ["BUY", "SELL"]
    assert order["price"] > 0
    assert 1 <= order["quantity"] <= 100