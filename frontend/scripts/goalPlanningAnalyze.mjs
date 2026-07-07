#!/usr/bin/env node
/**
 * CLI runner for goal-planning analysis (invoked by Flask backend).
 * Reads JSON from stdin: { goal, userProfile }
 * Writes JSON to stdout with analysis + recommendations + enrichment.
 */

import { runGoalPlanningPipeline } from '../src/features/goalPlanning/services/goalPlanningPipeline.js';
import { callClaudeApi } from '../src/features/goalPlanning/services/claudeClient.js';

async function readStdin() {
  const chunks = [];
  for await (const chunk of process.stdin) {
    chunks.push(chunk);
  }
  const raw = Buffer.concat(chunks).toString('utf8').trim();
  if (!raw) {
    throw new Error('No input provided on stdin.');
  }
  return JSON.parse(raw);
}

async function main() {
  const input = await readStdin();
  const goal = input?.goal;
  const userProfile = input?.userProfile;

  if (!goal || !userProfile) {
    throw new Error('Both goal and userProfile are required.');
  }

  const llmClient = (prompt) => callClaudeApi(prompt, {
    apiKey: process.env.ANTHROPIC_API_KEY,
  });

  const result = await runGoalPlanningPipeline(userProfile, goal, {
    llmClient,
    llmRetries: Number(process.env.GOAL_PLANNING_LLM_RETRIES ?? 2),
    timeoutMs: Number(process.env.GOAL_PLANNING_TIMEOUT_MS ?? 45000),
  });

  process.stdout.write(JSON.stringify(result));
}

main().catch((error) => {
  const message = error instanceof Error ? error.message : 'Goal planning analysis failed.';
  process.stderr.write(message);
  process.exit(1);
});
