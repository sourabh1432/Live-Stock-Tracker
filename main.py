import asyncio
from StockScraper import StockScraper  # Import your class
import csv
from datetime import datetime

async def scrape_stocks_to_csv(symbols, filename="stocks_data.csv"):
    results = []

    for symbol in symbols:
        print(f"\n📌 Scraping {symbol}...")
        scraper = StockScraper()
        await scraper.run(symbol)
        results.append(scraper.data)

    # CSV fields
    fields = [
        "symbol", "company_name", "current_price", "price_change", "percent_change",
        "previous_close", "open_price", "day_low", "day_high", "volume", "avg_volume",
        "market_cap", "pe_ratio", "eps", "beta",
        "dividend", "dividend_yield", "earnings_date", "target_price",
        "last_updated"
    ]

    # Write CSV
    with open(filename, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in results:
            writer.writerow(row)

    print(f"\n✅ All data saved to {filename}")


if __name__ == "__main__":
    # Example stocks
    stock_symbols = ["RELIANCE.NS"]
    asyncio.run(scrape_stocks_to_csv(stock_symbols))