import asyncio
from datetime import datetime
from playwright.async_api import async_playwright
import yfinance as yf
from stock import Stock


class StockScraper:

    # ---------------- UTILITIES ----------------
    def convert_number(self, value):
        if not value:
            return None
        value = str(value).replace(",", "").replace("\n", "").strip()
        if value in ["N/A", "-", ""]:
            return None
        try:
            if "M" in value:
                return float(value.replace("M", "")) * 1_000_000
            if "B" in value:
                return float(value.replace("B", "")) * 1_000_000_000
            return float(value)

        except:
            return None

    async def safe_get_text(self, selector, timeout=15000):
        try:
            element = self.page.locator(selector).first
            await element.wait_for(state="attached", timeout=timeout)
            text = await element.inner_text()
            return text.strip() if text else None
        except:
            return None

    # ---------------- START BROWSER ----------------
    async def start_browser(self, symbol):
        self.symbol = symbol
        self.data = {}

        self.p = await async_playwright().start()
        self.browser = await self.p.chromium.launch(headless=False)
        self.context = await self.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
        )
        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined})
        """)
        self.page = await self.context.new_page()

        # Open Yahoo homepage
        await self.page.goto("https://finance.yahoo.com", wait_until="domcontentloaded")
        # Handle consent popup
        try:
            await self.page.click('button[name="agree"]', timeout=5000)
        except:
            try:
                await self.page.click('button:has-text("Accept")', timeout=5000)
            except:
                pass

        # Search for stock
        await self.page.fill('input[name="p"]', self.symbol)
        await self.page.keyboard.press("Enter")
        await self.page.wait_for_timeout(3000)
        # Scroll page to load all elements
        await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await self.page.wait_for_timeout(3000)

    # ---------------- SCRAPE FIELDS ----------------
    async def scrape_fields(self):

        # SYMBOL
        self.data["symbol"] = self.symbol

        # COMPANY NAME
        company_name = await self.safe_get_text("h1")
        if company_name in [None, "Yahoo Finance", ""]:
            stock_yf = yf.Ticker(self.symbol)
            info = stock_yf.info
            company_name = info.get("longName", self.symbol)
        self.data["company_name"] = company_name

        # STOCK PRICES
        self.data["current_price"] = self.convert_number(
            await self.safe_get_text('fin-streamer[data-field="regularMarketPrice"]')
        )
        self.data["price_change"] = self.convert_number(
            await self.safe_get_text('fin-streamer[data-field="regularMarketChange"]')
        )
        self.data["percent_change"] = await self.safe_get_text(
            'fin-streamer[data-field="regularMarketChangePercent"]'
        )

        # PRICE RANGE
        self.data["previous_close"] = self.convert_number(
            await self.safe_get_text("td:has-text('Previous Close') + td")
        )
        self.data["open_price"] = self.convert_number(
            await self.safe_get_text("td:has-text('Open') + td")
        )
        day_range = await self.safe_get_text("td:has-text('Day') + td")
        if day_range and " - " in day_range:
            low, high = day_range.split(" - ")
        else:
            low, high = None, None
        self.data["day_low"] = self.convert_number(low)
        self.data["day_high"] = self.convert_number(high)

        # MARKET DATA
        self.data["volume"] = self.convert_number(
            await self.safe_get_text("td:has-text('Volume') + td")
        )
        self.data["avg_volume"] = self.convert_number(
            await self.safe_get_text("td:has-text('Avg. Volume') + td")
        )
        self.data["market_cap"] = await self.safe_get_text("td:has-text('Market Cap') + td")

        # FINANCIAL DATA
        self.data["pe_ratio"] = self.convert_number(
            await self.safe_get_text("td:has-text('PE Ratio (TTM)') + td") or
            await self.safe_get_text("td:has-text('PE Ratio') + td")
        )
        self.data["eps"] = self.convert_number(
            await self.safe_get_text("td:has-text('EPS (TTM)') + td") or
            await self.safe_get_text("td:has-text('EPS') + td")
        )
        self.data["beta"] = self.convert_number(
            await self.safe_get_text("td:has-text('Beta') + td")
        )

    # ---------------- YFINANCE FALLBACK ----------------
    def yfinance_fallback(self):
        stock_yf = yf.Ticker(self.symbol)
        info = stock_yf.info

        # Fill missing fields
        fallback_fields = {
            "current_price": "regularMarketPrice",
            "previous_close": "previousClose",
            "open_price": "open",
            "day_low": "dayLow",
            "day_high": "dayHigh",
            "volume": "volume",
            "avg_volume": "averageVolume",
            "market_cap": "marketCap",
            "pe_ratio": "trailingPE",
            "eps": "trailingEps",
            "beta": "beta",
            "dividend": "dividendRate",
            "dividend_yield": "dividendYield",
            "earnings_date": "earningsDate",
            "target_price": "targetMeanPrice",
        }

        for key, yf_key in fallback_fields.items():
            if self.data.get(key) in [None, ""]:
                val = info.get(yf_key)
                if key == "dividend_yield" and val:
                    val = val * 100  # Convert fraction to percent
                if key == "earnings_date" and val:
                    val = val[0] if isinstance(val, (list, tuple)) else val
                self.data[key] = val

    # ---------------- CLOSE ----------------
    async def close_browser(self):
        await self.browser.close()
        await self.p.stop()

    # ---------------- MAIN RUN ----------------
    async def run(self, symbol):
        try:
            await self.start_browser(symbol)
            await self.scrape_fields()
            self.yfinance_fallback()
            self.data["last_updated"] = datetime.now()

            # Format numeric fields like Yahoo style
            for field in ["current_price", "price_change", "previous_close", "open_price",
                          "day_low", "day_high", "pe_ratio", "eps", "beta"]:
                if self.data.get(field) is not None:
                    self.data[field] = round(self.data[field], 2)

            stock = Stock(self.data)
            stock.display_summary()
            stock.is_bullish()
            stock.calculate_pe_category()

        except Exception as e:
            print("❌ Error:", e)
        finally:
            await self.close_browser()









