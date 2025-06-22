import React, { useState } from 'react';
import { useDashboardStore } from '../../store/dashboardStore';

export function DashboardHeader() {
  const { currentBalance, cashBalanceAsOf, updateCashBalance } = useDashboardStore();
  const [editing, setEditing] = useState(false);
  const [balance, setBalance] = useState(currentBalance);
  const [asOf, setAsOf] = useState(cashBalanceAsOf || new Date().toISOString().slice(0,10));
  const [error, setError] = useState('');

  const handleSave = async () => {
    setError('');
    if (isNaN(balance) || balance < 0) {
      setError('Please enter a valid, non-negative balance.');
      return;
    }
    try {
      await updateCashBalance(balance, asOf);
      setEditing(false);
    } catch (err: any) {
      setError(err.message || 'Failed to update balance.');
    }
  };

  return (
    <div className="flex flex-col md:flex-row items-center gap-4 mb-6 bg-[#23272a] border-2 border-[#ff2d2d] rounded-xl p-4 shadow-lg dark:bg-[#23272a] dark:text-white">
      <div className="text-lg font-bold text-[#00e676]">
        Current Cash Balance: <span className="text-white">${currentBalance.toFixed(2)}</span>
        {cashBalanceAsOf && <span className="ml-2 text-gray-400">(as of {cashBalanceAsOf})</span>}
      </div>
      <button className="bg-[#00e676] text-[#181a1b] font-semibold rounded-lg px-4 py-2 hover:bg-[#00c060] transition" onClick={() => setEditing(!editing)}>
        {editing ? 'Cancel' : 'Update Cash Balance'}
      </button>
      {editing && (
        <div className="flex flex-col md:flex-row items-center gap-2 mt-2 md:mt-0">
          <input
            type="number"
            value={balance}
            min={0}
            step={0.01}
            onChange={e => setBalance(Number(e.target.value))}
            className="input input-bordered bg-[#181a1b] text-[#00e676] border border-[#444] rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-[#00e676]"
            placeholder="Enter new balance"
          />
          <input
            type="date"
            value={asOf}
            onChange={e => setAsOf(e.target.value)}
            className="input input-bordered bg-[#181a1b] text-[#00e676] border border-[#444] rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-[#00e676]"
          />
          <button className="bg-[#00e676] text-[#181a1b] font-semibold rounded-lg px-4 py-2 hover:bg-[#00c060] transition" onClick={handleSave}>Save</button>
          {error && <span className="text-red-500 ml-2">{error}</span>}
        </div>
      )}
    </div>
  );
} 