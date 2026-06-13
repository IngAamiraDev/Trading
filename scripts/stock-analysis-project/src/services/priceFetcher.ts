import axios from 'axios';
import fs from 'fs';
import path from 'path';

const configPath = path.resolve(__dirname, '../../conf/local-config.json');
const config = JSON.parse(fs.readFileSync(configPath, 'utf-8'));
const FINNHUB_API_KEY = config.FINNHUB_API_KEY;

const API_URL = 'https://finnhub.io/api/v1/quote';

export const fetchCurrentPrice = async (symbol: string): Promise<number> => {
    try {
        const response = await axios.get(API_URL, {
            params: {
                symbol,
                token: FINNHUB_API_KEY
            }
        });
        return response.data.c; // 'c' es el precio actual en Finnhub
    } catch (error) {
        console.error(`Error fetching price for ${symbol}:`, error);
        throw new Error('Failed to fetch current price');
    }
};