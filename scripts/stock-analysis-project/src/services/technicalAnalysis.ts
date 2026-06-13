export interface Stock {
    symbol: string;
    currentPrice: number;
    fiftyTwoWeekHigh: number;
    prices: number[];
}

export function calculateSMA(prices: number[], period: number): number {
    if (prices.length < period) {
        throw new Error("Not enough data to calculate SMA");
    }
    const sum = prices.slice(-period).reduce((acc, price) => acc + price, 0);
    return sum / period;
}

export function calculateRSI(prices: number[], period: number): number {
    if (prices.length < period) {
        throw new Error("Not enough data to calculate RSI");
    }
    let gains = 0;
    let losses = 0;

    for (let i = 1; i < period; i++) {
        const change = prices[i] - prices[i - 1];
        if (change > 0) {
            gains += change;
        } else {
            losses -= change; // losses are negative, so we subtract
        }
    }

    const averageGain = gains / period;
    const averageLoss = losses / period;

    if (averageLoss === 0) {
        return 100; // RSI is 100 if there are no losses
    }

    const rs = averageGain / averageLoss;
    return 100 - (100 / (1 + rs));
}

export function validateEntrySignal(stock: Stock): boolean {
    const sma5 = calculateSMA(stock.prices, 5);
    const sma20 = calculateSMA(stock.prices, 20);
    const rsi = calculateRSI(stock.prices, 14);

    return sma5 > sma20 && rsi < 70; // Long entry signal
}

export function performTechnicalAnalysis(symbol: string, currentPrice: number) {
    // Dummy implementation, replace with real logic as needed
    return {
        entrySignal: "SMA/RSI strategy",
        stopLoss: currentPrice * 0.95,
        takeProfit: currentPrice * 1.10,
        riskManagement: {
            riskPercentage: 2,
            positionSize: 100
        }
    };
}