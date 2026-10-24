import { useQuery } from '@tanstack/react-query';
import { fetchStockData } from '../api/client';

export const useStockData = (code: string) => {
  return useQuery({
    queryKey: ['stock', code],
    queryFn: () => fetchStockData(code),
    // 4桁以上のコードが入力された時だけ通信する
    enabled: !!code && code.length >= 4,
    // 1時間キャッシュを保持(無駄なAPIコールを防止)
    staleTime: 1000 * 60 * 60, 
    retry: 1,
  });
};