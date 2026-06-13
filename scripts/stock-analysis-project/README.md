# Stock Analysis Project

## Overview
The Stock Analysis Project automatically identifies and analyzes potential investment opportunities in the New York Stock Exchange (NYSE). The app dynamically selects five stocks based on technical fundamentals, news, and market conditions, aiming for a potential gain of 10–15% for the year 2025.  
**Stocks are not hardcoded:** The app fetches candidates in real time using financial APIs and applies your custom filters.

## Project Structure
```
stock-analysis-project
├── src
│   ├── services
│   │   ├── priceFetcher.ts
│   │   ├── technicalAnalysis.ts
│   │   └── stockScreener.ts
│   ├── utils
│   │   └── riskManagement.ts
│   ├── reports
│   │   └── stockReport.ts
│   └── app.ts
├── package.json
├── tsconfig.json
└── README.md
```

## Features
- **Dynamic Stock Screening**: Fetches and filters stocks from external APIs (e.g., Yahoo Finance, Finnhub) based on sector, 52-week high drop, and growth criteria.
- **Price Fetching**: Retrieves the current price of stocks.
- **News Fetching**: Gathers the latest news articles related to selected stocks for informed decision-making.
- **Technical Analysis**: Calculates moving averages and RSI to validate entry signals.
- **Risk Management**: Calculates position sizes based on stop loss and total capital to manage investment risk.
- **Reporting**: Compiles analysis results into a comprehensive report for each stock.

## Setup Instructions
1. Clone the repository:
   ```
   git clone <repository-url>
   ```
2. Navigate to the project directory:
   ```
   cd stock-analysis-project
   ```
3. Install dependencies:
   ```
   npm install
   ```
4. Compile TypeScript files:
   ```
   npm run build
   ```
5. Run the application:
   ```
   npm start
   ```

## Usage
- The application automatically fetches stock data, news, and performs technical analysis.
- It generates reports for the top 5 stocks matching your criteria, providing a clear trading plan: entry, stop loss, take profit, and risk management strategies.

## Contribution
Contributions are welcome! Please submit a pull request or open an issue for any suggestions or improvements.

## License
This project is licensed under the MIT License. See the LICENSE file for details.