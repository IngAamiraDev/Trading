export interface Stock {
    symbol: string;
    currentPrice: number;
    fiftyTwoWeekHigh: number;
    sector: string;
    technicalAnalysis: {
        entrySignal: string;
        stopLoss: number;
        takeProfit: number;
        riskManagement: {
            riskPercentage: number;
            positionSize: number;
        };
    };
    justification: string;
}

export function generateStockReport(stocks: Stock[]): string[] {
    return stocks.map(stock => {
        const report = `
        Stock: ${stock.symbol}
        Current Price: $${stock.currentPrice.toFixed(2)}
        52-Week High: $${stock.fiftyTwoWeekHigh.toFixed(2)}
        Sector: ${stock.sector}
        
        Trading Plan:
        Entry Signal: ${stock.technicalAnalysis.entrySignal}
        Stop Loss: $${stock.technicalAnalysis.stopLoss.toFixed(2)}
        Take Profit: $${stock.technicalAnalysis.takeProfit.toFixed(2)}
        
        Risk Management:
        Risk Percentage: ${stock.technicalAnalysis.riskManagement.riskPercentage}%
        Position Size: ${stock.technicalAnalysis.riskManagement.positionSize}        
       
        Justification: ${stock.justification}
        `;
        return report;
    });
}