import { fetchCurrentPrice } from './services/priceFetcher';
import { performTechnicalAnalysis } from './services/technicalAnalysis';
import { generateStockReport } from './reports/stockReport';
import { fetchStocksByCriteria } from './services/stockScreener';

async function analyzeStocks() {
    const stocks = await fetchStocksByCriteria({
        sectors: [
            'Technology',
            'Healthcare',
            'Consumer Defensive',
            'Industrials',
            'Financial Services',
            'Energy',
            'Utilities'
        ],
        min52wHighDrop: 15,
        max52wHighDrop: 35,
        minAnnualGrowth: 8,
        maxAnnualGrowth: 40,
        minPrice: 20,
        minVolume: 500000,
        minMarketCap: 2000000000, // $2B
        maxDebtToEquity: 1.0,
        minOperatingMargin: 10,
        onlyUS: true
    });

    const analyzedStocks = [];

    for (const stock of stocks) {
        const currentPrice = stock.currentPrice || await fetchCurrentPrice(stock.symbol);
        const technicalAnalysis = performTechnicalAnalysis(stock.symbol, currentPrice);

        analyzedStocks.push({
            symbol: stock.symbol,
            currentPrice,
            fiftyTwoWeekHigh: stock.fiftyTwoWeekHigh,
            sector: stock.sector,
            technicalAnalysis,
            justification: "Cumple criterios de calidad, crecimiento y descuento razonable para inversión en USA."
        });
    }

    const stockReports = generateStockReport(analyzedStocks);
    return stockReports;
}

analyzeStocks()
    .then(reports => {
        console.log('Stock Analysis Reports:', reports);
    })
    .catch(error => {
        console.error('Error analyzing stocks:', error);
    });