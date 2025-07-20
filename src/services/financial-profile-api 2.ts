export async function saveFinancialProfile(profile) {
  const res = await fetch('/api/financial-profile', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(profile)
  });
  return res.json();
}

export async function getFinancialProfile(userId) {
  const res = await fetch(`/api/financial-profile/${userId}`);
  return res.json();
}

export async function calculateHealthScore(data) {
  const res = await fetch('/api/financial-profile/calculate-health-score', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  return res.json();
}

export async function updateGoals(goals, userId) {
  const res = await fetch('/api/financial-profile/goals', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ goals, user_id: userId })
  });
  return res.json();
}

export async function deleteGoal(goalId) {
  const res = await fetch(`/api/financial-profile/goals/${goalId}`, { method: 'DELETE' });
  return res.json();
} 