
from src.dashboard import main


def test_dashboard_matches_buy_and_sell_orders(monkeypatch, capsys):
    """Verify interactive order entry and matching."""

    inputs = iter([
        "2",    # Add SELL order
        "100",  # Price
        "5",    # Quantity
        "1",    # Add BUY order
        "100",  # Price
        "3",    # Quantity
        "4",    # Exit
    ])

    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))

    main()

    output = capsys.readouterr().out

    assert "Order 1 accepted." in output
    assert "Order 2 accepted." in output
    assert "Buy 2 / Sell 1" in output
    assert "Price: 100" in output
    assert "Quantity: 3" in output
    assert "Total trades: 1" in output
    assert "Sell orders in book: 1" in output
    assert "1           100       2" in output


def test_dashboard_exits(monkeypatch, capsys):
    """Verify that the dashboard exits when option 4 is selected."""

    monkeypatch.setattr("builtins.input", lambda prompt="": "4")

    main()

    output = capsys.readouterr().out

    assert "Exiting ChronosMatch dashboard." in output
