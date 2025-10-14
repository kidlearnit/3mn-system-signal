/**
 * Technical Analysis - Handles technical calculations
 */
class TechnicalAnalysis {
    constructor() {
        // Initialize any required properties
    }
    
    calculateSupportResistance(candlestickData, lookbackPeriod = 20) {
        if (!candlestickData || candlestickData.length < lookbackPeriod) {
            return { support: [], resistance: [] };
        }
        
        const highs = candlestickData.map(candle => candle.high);
        const lows = candlestickData.map(candle => candle.low);
        const times = candlestickData.map(candle => candle.time);
        
        const supportLevels = [];
        const resistanceLevels = [];
        
        // Find local highs and lows
        for (let i = lookbackPeriod; i < candlestickData.length - lookbackPeriod; i++) {
            const currentHigh = highs[i];
            const currentLow = lows[i];
            
            // Check if current high is a local maximum (resistance)
            let isResistance = true;
            for (let j = i - lookbackPeriod; j <= i + lookbackPeriod; j++) {
                if (j !== i && highs[j] >= currentHigh) {
                    isResistance = false;
                    break;
                }
            }
            
            if (isResistance) {
                resistanceLevels.push({
                    time: times[i],
                    price: currentHigh,
                    type: 'resistance'
                });
            }
            
            // Check if current low is a local minimum (support)
            let isSupport = true;
            for (let j = i - lookbackPeriod; j <= i + lookbackPeriod; j++) {
                if (j !== i && lows[j] <= currentLow) {
                    isSupport = false;
                    break;
                }
            }
            
            if (isSupport) {
                supportLevels.push({
                    time: times[i],
                    price: currentLow,
                    type: 'support'
                });
            }
        }
        
        return { support: supportLevels, resistance: resistanceLevels };
    }
}
