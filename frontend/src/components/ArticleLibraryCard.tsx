import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Bookmark } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { csrfHeaders } from '../utils/csrfHeaders';

interface Article {
  id: number;
  url: string;
  title: string;
  description: string;
  source: string;
  domain: string;
  tags: string[];
  read_time_minutes: number;
}

interface DomainInfo {
  domain: string;
  count: number;
  label: string;
  top_tags?: string[];
}

interface ArticlesResponse {
  articles: Article[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

const DOMAIN_DOT_COLORS: Record<string, string> = {
  career_income: 'bg-blue-400',
  housing: 'bg-purple-400',
  financial_habits: 'bg-green-400',
  mental_health_money: 'bg-pink-400',
  physical_wellness: 'bg-orange-400',
  relationships_money: 'bg-red-400',
  mental_models: 'bg-amber-400',
};

function authHeaders(getAccessToken: () => string | null): Record<string, string> {
  const token = getAccessToken();
  return {
    ...csrfHeaders(),
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

function BookmarkButton({
  articleId,
  bookmarked,
  onToggle,
  className = '',
}: {
  articleId: number;
  bookmarked: boolean;
  onToggle: (id: number) => void;
  className?: string;
}) {
  return (
    <button
      type="button"
      onClick={() => onToggle(articleId)}
      className={`shrink-0 rounded p-1 transition-colors hover:bg-gray-50 ${className}`}
      aria-label={bookmarked ? 'Remove bookmark' : 'Bookmark article'}
    >
      <Bookmark
        className={`h-4 w-4 ${bookmarked ? 'fill-teal-500 text-teal-500' : 'text-gray-300'}`}
        aria-hidden
      />
    </button>
  );
}

export default function ArticleLibraryCard() {
  const { isAuthenticated, getAccessToken, userTier } = useAuth();

  const [domains, setDomains] = useState<DomainInfo[]>([]);
  const [activeDomain, setActiveDomain] = useState<string | null>(null);
  const [activeTags, setActiveTags] = useState<string[]>([]);
  const [searchInput, setSearchInput] = useState('');
  const [debouncedQuery, setDebouncedQuery] = useState('');
  const [articles, setArticles] = useState<Article[]>([]);
  const [recommended, setRecommended] = useState<Article[]>([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState(false);
  const [bookmarkedIds, setBookmarkedIds] = useState<Set<number>>(() => new Set());

  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const fetchIdRef = useRef(0);

  const totalArticles = useMemo(
    () => domains.reduce((sum, d) => sum + d.count, 0),
    [domains]
  );

  const subtitle = useMemo(() => {
    if (domains.length === 0) {
      return '698 articles across 7 topics';
    }
    return `${totalArticles} articles across ${domains.length} topics`;
  }, [domains.length, totalArticles]);

  const showRecommended =
    isAuthenticated && !debouncedQuery && activeDomain === null;

  const activeTopTags = useMemo(() => {
    if (!activeDomain) return [];
    const domain = domains.find((d) => d.domain === activeDomain);
    return domain?.top_tags ?? [];
  }, [activeDomain, domains]);

  useEffect(() => {
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }
    debounceRef.current = setTimeout(() => {
      setDebouncedQuery(searchInput.trim());
    }, 400);
    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, [searchInput]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch('/api/articles/domains', { credentials: 'include' });
        if (!res.ok) return;
        const data = (await res.json()) as { domains?: DomainInfo[] };
        if (!cancelled && Array.isArray(data.domains)) {
          setDomains(data.domains);
        }
      } catch {
        /* non-fatal */
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!showRecommended) {
      setRecommended([]);
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch('/api/articles/recommended', {
          credentials: 'include',
          headers: authHeaders(getAccessToken),
        });
        if (!res.ok) return;
        const data = (await res.json()) as { articles?: Article[] };
        if (!cancelled && Array.isArray(data.articles)) {
          setRecommended(data.articles);
        }
      } catch {
        /* non-fatal */
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [showRecommended, getAccessToken, userTier]);

  const fetchArticles = useCallback(
    async (targetPage: number, append: boolean) => {
      const fetchId = ++fetchIdRef.current;
      if (append) {
        setLoadingMore(true);
      } else {
        setLoading(true);
        setError(false);
      }

      const params = new URLSearchParams({
        page: String(targetPage),
        per_page: '20',
      });
      if (activeDomain) {
        params.set('domain', activeDomain);
      }
      if (debouncedQuery) {
        params.set('q', debouncedQuery);
      }
      if (activeTags.length > 0) {
        params.set('tags', activeTags.join(','));
      }

      try {
        const res = await fetch(`/api/articles?${params.toString()}`, {
          credentials: 'include',
        });
        if (!res.ok) {
          throw new Error('fetch failed');
        }
        const data = (await res.json()) as ArticlesResponse;
        if (fetchId !== fetchIdRef.current) {
          return;
        }
        setArticles((prev) =>
          append ? [...prev, ...(data.articles ?? [])] : (data.articles ?? [])
        );
        setPage(data.page ?? targetPage);
        setTotalPages(data.pages ?? 0);
        setError(false);
      } catch {
        if (fetchId === fetchIdRef.current && !append) {
          setError(true);
          setArticles([]);
        }
      } finally {
        if (fetchId === fetchIdRef.current) {
          setLoading(false);
          setLoadingMore(false);
        }
      }
    },
    [activeDomain, activeTags, debouncedQuery]
  );

  useEffect(() => {
    void fetchArticles(1, false);
  }, [fetchArticles]);

  const handleLoadMore = useCallback(() => {
    if (loadingMore || page >= totalPages) return;
    void fetchArticles(page + 1, true);
  }, [fetchArticles, loadingMore, page, totalPages]);

  const handleToggleBookmark = useCallback(
    async (articleId: number) => {
      try {
        const res = await fetch(`/api/articles/${articleId}/bookmark`, {
          method: 'POST',
          credentials: 'include',
          headers: authHeaders(getAccessToken),
        });
        if (!res.ok) return;
        const data = (await res.json()) as { bookmarked?: boolean };
        setBookmarkedIds((prev) => {
          const next = new Set(prev);
          if (data.bookmarked) {
            next.add(articleId);
          } else {
            next.delete(articleId);
          }
          return next;
        });
      } catch {
        /* ignore */
      }
    },
    [getAccessToken]
  );

  const handleRetry = useCallback(() => {
    void fetchArticles(1, false);
  }, [fetchArticles]);

  const openArticle = useCallback((url: string) => {
    window.open(url, '_blank', 'noopener,noreferrer');
  }, []);

  if (loading && articles.length === 0 && !error) {
    return (
      <div className="rounded-xl bg-white p-6 shadow-sm" role="status" aria-label="Loading articles">
        <div className="mb-4 h-5 w-48 animate-pulse rounded bg-gray-100" />
        <div className="space-y-3">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-12 animate-pulse rounded-xl bg-gray-100" />
          ))}
        </div>
      </div>
    );
  }

  if (error && articles.length === 0) {
    return (
      <div className="rounded-xl bg-white p-6 shadow-sm text-center">
        <p className="text-sm text-gray-500">Unable to load articles.</p>
        <button
          type="button"
          onClick={handleRetry}
          className="mt-3 text-sm text-teal-600 underline"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="rounded-xl bg-white p-6 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="font-semibold text-gray-800">Article Library</h2>
          <p className="text-sm text-gray-500">{subtitle}</p>
        </div>
        <input
          type="search"
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          placeholder="Search articles..."
          className="w-40 rounded-full border border-gray-200 px-3 py-1 text-sm transition-all focus:w-56 focus:outline-none focus:ring-2 focus:ring-teal-500/30"
          aria-label="Search articles"
        />
      </div>

      <div className="mt-4 flex gap-2 overflow-x-auto pb-1">
        <button
          type="button"
          onClick={() => {
            setActiveDomain(null);
            setActiveTags([]);
          }}
          className={`shrink-0 cursor-pointer rounded-full px-3 py-1 text-xs ${
            activeDomain === null
              ? 'bg-teal-500 text-white'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
        >
          All
        </button>
        {domains.map((d) => (
          <button
            key={d.domain}
            type="button"
            onClick={() => {
              setActiveDomain(d.domain);
              setActiveTags([]);
            }}
            className={`shrink-0 cursor-pointer rounded-full px-3 py-1 text-xs ${
              activeDomain === d.domain
                ? 'bg-teal-500 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {d.label}
          </button>
        ))}
      </div>

      {activeDomain !== null && activeTopTags.length > 0 && (
        <div className="mt-2 flex gap-2 overflow-x-auto pb-1">
          {activeTopTags.map((tag) => {
            const selected = activeTags.includes(tag);
            return (
              <button
                key={tag}
                type="button"
                onClick={() => {
                  setActiveTags((prev) =>
                    selected ? prev.filter((t) => t !== tag) : [...prev, tag]
                  );
                }}
                className={`shrink-0 cursor-pointer rounded-full px-3 py-1 text-xs ${
                  selected
                    ? 'border border-teal-400 bg-teal-100 text-teal-700'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                {tag}
              </button>
            );
          })}
        </div>
      )}

      {showRecommended && recommended.length > 0 && (
        <div className="mt-5">
          <p className="text-xs font-semibold tracking-widest text-teal-600">
            RECOMMENDED FOR YOU
          </p>
          <div className="mt-2 flex gap-3 overflow-x-auto pb-1">
            {recommended.slice(0, 3).map((article) => (
              <div
                key={article.id}
                className="relative w-48 shrink-0 rounded-xl bg-teal-50 p-3"
              >
                {isAuthenticated && (
                  <BookmarkButton
                    articleId={article.id}
                    bookmarked={bookmarkedIds.has(article.id)}
                    onToggle={handleToggleBookmark}
                    className="absolute right-1 top-1"
                  />
                )}
                <button
                  type="button"
                  onClick={() => openArticle(article.url)}
                  className="text-left"
                >
                  <p className="line-clamp-2 text-sm font-medium text-gray-800">
                    {article.title}
                  </p>
                  <p className="mt-1 text-xs text-gray-500">
                    {article.source} · {article.read_time_minutes} min read
                  </p>
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="mt-4 max-h-[500px] space-y-3 overflow-y-auto">
        {articles.length === 0 && debouncedQuery ? (
          <div className="mt-8 text-center">
            <p className="text-sm text-gray-500">
              No articles found for &apos;{debouncedQuery}&apos;
            </p>
            <p className="text-xs text-gray-400">Try a different search term.</p>
          </div>
        ) : (
          articles.map((article) => (
            <div key={article.id} className="flex gap-3">
              <span
                className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${
                  DOMAIN_DOT_COLORS[article.domain] ?? 'bg-gray-300'
                }`}
                aria-hidden
              />
              <div className="min-w-0 flex-1">
                <button
                  type="button"
                  onClick={() => openArticle(article.url)}
                  className="cursor-pointer text-left text-sm font-medium text-gray-800 hover:text-teal-600"
                >
                  {article.title}
                </button>
                <p className="mt-0.5 text-xs text-gray-400">
                  {article.source} · {article.read_time_minutes} min read
                </p>
                {article.tags.length > 0 && (
                  <div className="mt-1.5 flex flex-wrap gap-1">
                    {article.tags.slice(0, 3).map((tag) => (
                      <span
                        key={tag}
                        className="rounded bg-gray-100 px-1.5 py-0.5 text-xs text-gray-500"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
              </div>
              {isAuthenticated && (
                <BookmarkButton
                  articleId={article.id}
                  bookmarked={bookmarkedIds.has(article.id)}
                  onToggle={handleToggleBookmark}
                />
              )}
            </div>
          ))
        )}
      </div>

      {page < totalPages && (
        <div className="mt-4 text-center">
          <button
            type="button"
            onClick={handleLoadMore}
            disabled={loadingMore}
            className="text-sm text-teal-600 underline disabled:opacity-50"
          >
            {loadingMore ? 'Loading…' : 'Load more'}
          </button>
        </div>
      )}
    </div>
  );
}
