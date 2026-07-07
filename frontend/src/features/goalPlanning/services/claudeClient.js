export const CLAUDE_MODEL = 'claude-sonnet-4-6';
export const ANTHROPIC_MESSAGES_URL = 'https://api.anthropic.com/v1/messages';

/**
 * Resolves Anthropic API key from runtime environment.
 * @param {string} [explicitKey]
 * @returns {string | undefined}
 */
function resolveApiKey(explicitKey) {
  if (explicitKey) {
    return explicitKey;
  }

  if (typeof process !== 'undefined' && process.env?.ANTHROPIC_API_KEY) {
    return process.env.ANTHROPIC_API_KEY;
  }

  return undefined;
}

/**
 * Calls the Anthropic Messages API.
 * @param {string} prompt
 * @param {Object} [options]
 * @param {string} [options.apiKey]
 * @param {typeof fetch} [options.fetchFn]
 * @returns {Promise<string | null>}
 */
export async function callClaudeApi(prompt, options = {}) {
  const apiKey = resolveApiKey(options.apiKey);

  if (!apiKey) {
    return null;
  }

  const fetchFn = options.fetchFn ?? fetch;

  try {
    const response = await fetchFn(ANTHROPIC_MESSAGES_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'x-api-key': apiKey,
        'anthropic-version': '2023-06-01',
      },
      body: JSON.stringify({
        model: CLAUDE_MODEL,
        max_tokens: 4096,
        messages: [{ role: 'user', content: prompt }],
      }),
    });

    if (!response.ok) {
      return null;
    }

    const data = await response.json();
    const textBlock = data?.content?.find((block) => block?.type === 'text');
    return textBlock?.text ?? null;
  } catch {
    return null;
  }
}
