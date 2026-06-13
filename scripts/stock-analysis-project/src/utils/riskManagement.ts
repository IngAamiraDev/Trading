// src/utils/riskManagement.ts

export function calculatePositionSize(totalCapital: number, stopLoss: number, riskPercentage: number): number {
    const riskAmount = totalCapital * (riskPercentage / 100);
    const positionSize = riskAmount / stopLoss;
    return positionSize;
}

export function calculateRiskRewardRatio(entryPrice: number, stopLoss: number, takeProfit: number): number {
    const risk = entryPrice - stopLoss;
    const reward = takeProfit - entryPrice;
    return reward / risk;
}

export function isRiskAcceptable(totalCapital: number, stopLoss: number, riskPercentage: number): boolean {
    const riskAmount = totalCapital * (riskPercentage / 100);
    return stopLoss <= riskAmount;
}