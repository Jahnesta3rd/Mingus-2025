import create from 'zustand';
import { supabase } from '../lib/supabaseClient';
import { ImportantDate } from '../types';

interface DashboardState {
  importantDates: ImportantDate[];
  currentBalance: number;
  cashBalanceAsOf: string | null;
  activeTab: string;
  setActiveTab: (tab: string) => void;
  fetchImportantDates: () => Promise<void>;
  fetchCashBalance: () => Promise<void>;
  updateCashBalance: (balance: number, asOf: string) => Promise<void>;
}

export const useDashboardStore = create<DashboardState>((set) => ({
  importantDates: [],
  currentBalance: 0,
  cashBalanceAsOf: null,
  activeTab: 'base-case',
  setActiveTab: (tab) => set({ activeTab: tab }),
  fetchImportantDates: async () => {
    const { data, error } = await supabase
      .from('user_important_dates')
      .select('*');
    if (data) set({ importantDates: data });
  },
  fetchCashBalance: async () => {
    const user = await supabase.auth.getUser();
    if (!user.data.user) return;
    const { data, error } = await supabase
      .from('user_cash_balances')
      .select('*')
      .eq('user_id', user.data.user.id)
      .order('as_of_date', { ascending: false })
      .limit(1);
    if (data && data.length > 0) {
      set({ currentBalance: data[0].balance, cashBalanceAsOf: data[0].as_of_date });
    }
  },
  updateCashBalance: async (balance, asOf) => {
    if (isNaN(balance) || balance < 0) throw new Error('Invalid balance');
    const user = await supabase.auth.getUser();
    if (!user.data.user) throw new Error('User not authenticated');
    const { error } = await supabase.from('user_cash_balances').insert([
      { user_id: user.data.user.id, balance, as_of_date: asOf }
    ]);
    if (error) throw error;
    set({ currentBalance: balance, cashBalanceAsOf: asOf });
  },
})); 