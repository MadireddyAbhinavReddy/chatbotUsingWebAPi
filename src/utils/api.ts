import type { ApiResponse } from '@/types';

export const fetchData = async (
  query: string,
  tab: string,
  language: string,
  imageData: string
  
): Promise<ApiResponse> => {
  const res = await fetch('http://localhost:8000/query', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      tab,
      query,
      language,
      imageData
    }),
  });

  if (!res.ok) {
    throw new Error(`HTTP ${res.status}`);
  }

  return res.json();
};
