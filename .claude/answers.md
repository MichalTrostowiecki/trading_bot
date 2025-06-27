The strategy I use for my manual trading is based of the Elliot wave concepts. Basically what I try to do with this frctals and dominant swings is to find the impulsive move (pottentially wave 3) then we look for a correction ( potential wave 4) and we want to place ourselfs in for the wave 5. Thats why I would need to find the dominant swing to potentially find impulsive moves (waves). This is just to give you some idea of what I'm looking for. This is just theory. As also we could potentially have the wave 1-2 and enter into new wave 3. But when we use swings dominant most likley always will be impulsive move.


Q1: How many bars do you use to define a fractal?
 - Do you use the standard 5-bar fractal (where the middle bar is the highest/lowest of the 5)?
  - Or do you prefer a different number like 3-bar or 7-bar fractals?

  Answer: 
   - regarding the fractals I think this is something we will have to test. For example when only using 5 bars fractals this might not be significant enought to capture the market structure. I'd say best would be to have the number of bars for the fractals as a variable that we can test and optimize.
   - I have noticed in the past that we need a logic where we get two highest/lowest bar that are exact same price. To make sure we don't get false fractals.

Q2: Do you use different fractal periods for different timeframes?
  - For example: 3-bar fractals on M1/M5, 5-bar fractals on H1/H4, 7-bar fractals on D1?
  - Or do you keep it consistent across all timeframes?

  Answer:
   - If we're running the bot on the the m1 we're interested in the m1 fractals. At some point we might add the way to test if we add some confluence with higher time frame fractals impacting the results we receive.

  Q3: Do you require a minimum distance between fractals?
  - Should there be at least X bars between consecutive fractals to avoid noise?
  - Any minimum percentage price difference between fractals?

  Answer:
   - This is irrelevant for example if we will be looking for the fractals based on the 21 bars so we need to make sure to find all fractals.

   2. Swing Identification

  Q4: How do you define a "major swing"?
  - Is it simply fractal-to-fractal movement (up fractal to down fractal and vice versa)?
  - Do you require a minimum percentage move to qualify as a swing?
  - Any other validation criteria?

  Answer:
   - A swing is a movement from one fractal to the next. If we have fractal up and fractal down this is a swing. We don't need to have a minimum percentage move to qualify as a swing. If for example we have period where we look for the swing identifed as last 140 candles. So we would need to do is to go from the last candle (the newest one shown on the chart) and go 140 candles back and identify all swings in that period. However we would focus on the latest swings. If you identified swing down and swing up then you need to check which one is bigger swing ( amount of pips moved ) The one with bigger move means it's dominant. When new swing is created because you get new fractal then you need to compare this new swing with the previous dominant swing and check which one is bigger. The bigger one is the dominant swing.
   Scenario:
    - We get down swing as dominant,
    - Then we get new fractal up and we get new swing up
    - We compare this swing up with the down swing and check which one is bigger
    - The bigger one is the dominant swing
    - If the swing up is bigger than the swing down then we have new dominant swing up
    - If the swing down is bigger than the swing up then the dominant swing down is still the dominant swing
    - also make sure we only keep last swing down and up so when new swing is created we compare it with the last swing of the opposite direction. 

Q5: What's your lookback period for identifying swings?
  - Do you look at the last 50 bars, 100 bars, or some other number?
  - Or do you prefer looking at the last N fractals instead of bars?
  - Should this be dynamic based on market volatility?

  Answer: 
    - This is something we will be testing also so this lookback period cannot be fixed we will have to adjust this to find the optimal value.

  Q6: Do you filter swings by minimum size?
  - What's the minimum percentage move required for a swing to be considered?
  - Should this be relative to recent volatility (ATR-based) or fixed percentage?

  Answer:
   - This is something we will be testing also so this minimum swing size cannot be fixed we will have to adjust this to find the optimal value.

3. Dominant Swing Selection

  Q7: How do you determine which swing is "dominant"?
  When you have multiple swings in your lookback period, how do you choose which one to use for Fibonacci calculations? Please rank       
  these factors by importance:
  - Size/magnitude of the swing
  - How recent the swing is
  - Volume during the swing
  - Momentum/speed of the swing
  - Any other factors?

  Answer:
   - Dominant swing should alway be the biggest swing in the look up period. As correction of the price will never go beyond the impulsive move.

Q8: Do you prioritize recent swings over larger but older ones?
  - If you have a large swing from 50 bars ago vs. a smaller swing from 10 bars ago, which takes priority?
  - What's the balance between recency and size?

    Answer:
     - Dominant swing should alway be the biggest swing in the look up period. So every time new candle is printed we check for the fractals and based on the distance from the bottom of the fractal to the top of the fractal we can calculate the size of the swing. If the swing is bigger than the current dominant swing then we have new dominant swing.


     