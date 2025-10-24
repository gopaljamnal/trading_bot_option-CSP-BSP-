 ~screens all Dow Jones and S&P500 stocks
# More conservative (further OTM)
MIN_OTM_PERCENT = 20
MAX_OTM_PERCENT = 30

# Shorter timeframe
MIN_DTE = 7
MAX_DTE = 14

# Higher return requirement
MIN_RETURN_ON_RISK = 25

**Requirements Implemented:**

**Strike Price:** 15-20% OTM from current stock price (configurable)
**DTE Range:** 7-28 days (easy to modify at top of file)
**Spread Width:** Exactly $5.00 width ($500 max risk per contract)
**Return on Risk:** Minimum 20% ROR filter
Dow Jones Stocks: All 30 components included

#Simple Configuration Section at Top:
MIN_DTE = 7               # Change to 10, 14, etc.
MAX_DTE = 28              # Change to 21, 30, etc.
MIN_OTM_PERCENT = 15      # 15% out of money minimum
MAX_OTM_PERCENT = 25      # 25% out of money maximum
SPREAD_WIDTH = 5.00       # $5 spread = $500 max risk
MIN_RETURN_ON_RISK = 20   # 20% minimum ROR
