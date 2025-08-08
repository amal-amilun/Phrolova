# Phrolova
Trading bot for Bitcoin with trend-following (buy only) and stop-trailing strategy. Trust me, this strategy really outperforms every other strategies that I've made. Well I've tried full trend-following strategy (buy and sell using moving average) but the results weren't that good. I also tried mean-reversion strategy which of course didn't work well (since everyone knows that btc's market is trending and not ranging). I even made something that can detect if the market was trending or ranging and would switch between trend-follwing strategy and mean-reversion accordingly. But that inovation performs worse than any strategies I ever made.. guess the market of a coin just don't change at all.. 

### Best Parameters For 2011-2021 (1h timeframe):
- **MA FAST:** 5
- **MA SLOW:** 13
- **ATR Period:** 13
- **TRAILING MULTIPLIER:** 3
  
**NOTE: Works best for 2011-2021 where 5 can grow to 5.7M, while for 2018-2021 it can only grow from 5 to 55k**

### Best Parameters for 2018-2025 (1h timeframe):
- **MA FAST:** 4
- **MA SLOW:** 9
- **ATR PERIOD:** 9
- **TRAILING MULTIPLIER:** 2
  
**NOTE: Performs worse for 2011-2021 as only turn 5 to 225k, yet performs best for 2018-2025 as 5 can grow to 225k**

Looking at how different the chart from 2011-2021 and 2018-2025, it's better to use the second parameters if you aim for higher profits. However, as you can see the first parameters perform kinda well in both cases so pick the first one if you prefer more stable returns.

# TRADING FOR ALT-COIN
One more, while I originally designed this for a long-term investing in mind. This also can work quite well with short-term alt-coin trading. For that I'd suggest you using more shorter timeframe and adjusting parameters to whatever settings you think will perform best.

### MY FAVORITE PARAMETERS (5m timeframe):
- **MA FAST:** 3 | 2
- **MA SLOW:** 7 | 9
- **ATR PERIOD:** 7 | 9
- **TRAILING MULTIPLIER:** 3

**NOTE: I really don't recommend you trading alt-coins, as they're so unpredictable and are a lot of pump-and-dump schemes TT.. (Honestly, you can say their value is based more on one's many other solid fundamentals.. you really need lot of data to spot the real patterns in it). If you're chasing fast money that badly, remember there are many people wo can't even afford food or water for the whole day.. **
