class Stock:

    def __init__(self, data):

        self.symbol = data.get("symbol")
        self.company_name = data.get("company_name")
        self.current_price = data.get("current_price")
        self.price_change = data.get("price_change")
        self.percent_change = data.get("percent_change")

        self.previous_close = data.get("previous_close")
        self.open_price = data.get("open_price")
        self.day_low = data.get("day_low")
        self.day_high = data.get("day_high")

        self.volume = data.get("volume")
        self.avg_volume = data.get("avg_volume")
        self.market_cap = data.get("market_cap")

        self.pe_ratio = data.get("pe_ratio")
        self.eps = data.get("eps")
        self.beta = data.get("beta")

        self.dividend = data.get("dividend")
        self.dividend_yield = data.get("dividend_yield")

        self.earnings_date = data.get("earnings_date")
        self.target_price = data.get("target_price")

        self.last_updated = data.get("last_updated")

    # ------------------ METHODS ------------------

    def calculate_price_range(self):
        if self.day_high is not None and self.day_low is not None:
            return self.day_high - self.day_low
        return None

    def check_volume_spike(self):
        if self.volume and self.avg_volume:
            if self.volume > self.avg_volume:
                print("High trading activity detected")
            else:
                print("No unusual trading activity")

    def check_target_price(self):
        if self.target_price and self.current_price:
            if self.current_price >= self.target_price:
                print("Target price reached")
            else:
                print("Target price not reached")

    def calculate_pe_category(self):
        if self.pe_ratio is None:
            print("PE Ratio not available")
        elif self.pe_ratio < 15:
            print("Undervalued")
        elif 15 <= self.pe_ratio <= 30:
            print("Fair Value")
        else:
            print("Overvalued")

    def dividend_income(self, shares):
        if self.dividend:
            return self.dividend * shares
        return None

    def is_bullish(self):
        if self.current_price and self.previous_close:
            if self.current_price > self.previous_close:
                print("Stock is Bullish Today")
            else:
                print("Stock is Bearish Today")

    def display_summary(self):

        print("\n📊 STOCK SUMMARY")
        print("-" * 40)

        for key, value in self.__dict__.items():
            print(f"{key.upper():20}: {value}")

        
        
        
    
        




