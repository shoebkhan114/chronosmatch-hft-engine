
from src.matching_engine import MatchingEngine
from src.models import Order, Side


def display_order_book(engine: MatchingEngine) -> None:
    """Display the current order book and recent trades."""

    print("\n" + "=" * 65)
    print("              CHRONOSMATCH HFT ENGINE")
    print("=" * 65)

    print("\nBUY ORDERS (Highest price first)")
    print("-" * 40)
    print(f"{'Order ID':<12}{'Price':<10}{'Remaining Qty':<15}")

    for order in engine.buy_orders[:10]:
        print(
            f"{order.order_id:<12}"
            f"{order.price_ticks:<10}"
            f"{order.quantity:<15}"
        )

    if not engine.buy_orders:
        print("No buy orders")

    print("\nSELL ORDERS (Lowest price first)")
    print("-" * 40)
    print(f"{'Order ID':<12}{'Price':<10}{'Remaining Qty':<15}")

    for order in engine.sell_orders[:10]:
        print(
            f"{order.order_id:<12}"
            f"{order.price_ticks:<10}"
            f"{order.quantity:<15}"
        )

    if not engine.sell_orders:
        print("No sell orders")

    print("\nRECENT TRADES")
    print("-" * 65)
    print(f"{'Buy ID':<10}{'Sell ID':<10}{'Price':<12}{'Quantity':<10}")

    for trade in engine.trades[-10:][::-1]:
        print(
            f"{trade.buy_order_id:<10}"
            f"{trade.sell_order_id:<10}"
            f"{trade.price_ticks:<12}"
            f"{trade.quantity:<10}"
        )

    if not engine.trades:
        print("No trades executed")

    print("-" * 65)
    print(f"Total trades: {len(engine.trades)}")
    print(f"Buy orders in book: {len(engine.buy_orders)}")
    print(f"Sell orders in book: {len(engine.sell_orders)}")
    print("=" * 65)


def main() -> None:
    engine = MatchingEngine()
    next_order_id = 1
    timestamp_ns = 0

    while True:
        print("\n--- MENU ---")
        print("1. Add BUY order")
        print("2. Add SELL order")
        print("3. View order book and trades")
        print("4. Exit")

        choice = input("Choose an option (1-4): ").strip()

        if choice == "4":
            print("Exiting ChronosMatch dashboard.")
            break

        if choice == "3":
            display_order_book(engine)
            continue

        if choice not in ("1", "2"):
            print("Invalid option. Please choose 1, 2, 3, or 4.")
            continue

        try:
            price = int(input("Enter price in ticks (positive integer): "))
            quantity = int(input("Enter quantity (positive integer): "))

            side = Side.BUY if choice == "1" else Side.SELL

            order = Order(
                order_id=next_order_id,
                timestamp_ns=timestamp_ns,
                side=side,
                price_ticks=price,
                quantity=quantity,
            )

            new_trades = engine.add_order(order)

            next_order_id += 1
            timestamp_ns += 1

            print(f"\nOrder {order.order_id} accepted.")

            if new_trades:
                print("Trades executed:")
                for trade in new_trades:
                    print(
                        f"Buy {trade.buy_order_id} / "
                        f"Sell {trade.sell_order_id} | "
                        f"Price: {trade.price_ticks} | "
                        f"Quantity: {trade.quantity}"
                    )
            else:
                print("No trades executed for this order.")

            display_order_book(engine)

        except ValueError as error:
            print(f"Invalid order: {error}")
        except NotImplementedError as error:
            print(f"Unsupported operation: {error}")


if __name__ == "__main__":
    main()
