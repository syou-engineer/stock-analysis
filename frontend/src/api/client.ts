import type { StockDataResponse } from '../types';

const BASE_URL = 'http://localhost:8000/api';

export const fetchStockData = async (code: string): Promise<StockDataResponse> => {
  const response = await fetch(`${BASE_URL}/stocks/${code}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // fetchは404や500などのHTTPエラーでも例外を投げないため、手動でチェックする
  if (!response.ok) {
    let errorMessage = `HTTP Error: ${response.status}`;
    try {
      const errorData = await response.json();
      errorMessage = errorData.detail || errorMessage;
    } catch {
      // JSONパースに失敗した場合はテキストとして取得
      errorMessage = await response.text() || errorMessage;
    }
    throw new Error(errorMessage);
  }

  return response.json();
};