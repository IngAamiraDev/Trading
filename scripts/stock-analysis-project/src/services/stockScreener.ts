import axios from 'axios';
import fs from 'fs';
import path from 'path';

const configPath = path.resolve(__dirname, '../conf/local-config.json');
const config = JSON.parse(fs.readFileSync(configPath, 'utf-8'));
const FINNHUB_API_KEY = config.FINNHUB_API_KEY;

const FINNHUB_BASE_URL = 'https://finnhub.io/api/v1';

export interface StockScreenerCriteria {
    sectors: string[];
    min52wHighDrop: number;
    max52wHighDrop: number;
    minAnnualGrowth: number;
    maxAnnualGrowth: number;
    minPrice: number;
    minVolume: number;
    minMarketCap: number;
    maxDebtToEquity: number;
    minOperatingMargin: number;
    onlyUS: boolean;
}

export interface StockResult {
    symbol: string;
    currentPrice: number;
    fiftyTwoWeekHigh: number;
    sector: string;
    volume: number;
}

// Auxiliar para pausar entre requests
function sleep(ms: number) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

async function getProfile(symbol: string) {
    const { data } = await axios.get(`${FINNHUB_BASE_URL}/stock/profile2`, {
        params: { symbol, token: FINNHUB_API_KEY }
    });
    return data;
}

async function getQuote(symbol: string) {
    const { data } = await axios.get(`${FINNHUB_BASE_URL}/quote`, {
        params: { symbol, token: FINNHUB_API_KEY }
    });
    return data;
}

async function getMetrics(symbol: string) {
    const { data } = await axios.get(`${FINNHUB_BASE_URL}/stock/metric`, {
        params: { symbol, metric: "all", token: FINNHUB_API_KEY }
    });
    return data?.metric || {};
}

export async function fetchStocksByCriteria(criteria: StockScreenerCriteria): Promise<StockResult[]> {
    const { minPrice, minVolume, sectors, min52wHighDrop, max52wHighDrop } = criteria;
    const filteredStocks: StockResult[] = [];

    // Traemos símbolos de USA
    const symbolsRes = await axios.get(`${FINNHUB_BASE_URL}/stock/symbol`, {
        params: { exchange: 'US', token: FINNHUB_API_KEY }
    });

    const symbols = symbolsRes.data
        .filter((s: any) => s.type === 'Common Stock')
        .slice(0, 30); // limitamos para free tier

    for (const sym of symbols) {
        try {
            const profile = await getProfile(sym.symbol);
            if (!profile || !sectors.includes(profile.finnhubIndustry)) {
                await sleep(1200); // delay igualmente para respetar rate limit
                continue;
            }

            const quote = await getQuote(sym.symbol);
            const metrics = await getMetrics(sym.symbol);

            const price = quote.c;
            const high52w = metrics['52WeekHigh'];
            const volume = quote.v;

            if (!price || !high52w || price < minPrice || volume < minVolume) {
                await sleep(1200);
                continue;
            }

            const drop = ((high52w - price) / high52w) * 100;
            if (drop < min52wHighDrop || drop > max52wHighDrop) {
                await sleep(1200);
                continue;
            }

            filteredStocks.push({
                symbol: sym.symbol,
                currentPrice: price,
                fiftyTwoWeekHigh: high52w,
                sector: profile.finnhubIndustry,
                volume
            });

            console.log(`✔ Stock válido: ${sym.symbol} | Precio: ${price} | Drop: ${drop.toFixed(2)}%`);

            if (filteredStocks.length >= 50) break;

        } catch (err) {
            if (axios.isAxiosError(err) && err.response?.status === 429) {
                console.warn(`⚠️ Rate limit alcanzado en ${sym.symbol}, esperando 2s...`);
                await sleep(2000);
            } else if (err instanceof Error) {
                console.error(`❌ Error procesando ${sym.symbol}:`, err.message);
            } else {
                console.error(`❌ Error desconocido en ${sym.symbol}:`, err);
            }
        }

        // Delay entre cada símbolo para no romper límite (≈60/min en free tier)
        await sleep(1200);
    }

    return filteredStocks;
}
