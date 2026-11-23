import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api';
export const useMediaHistory = () => useQuery({ queryKey: ['media-history'], queryFn: api.history, retry: 1, staleTime: 30000 });
