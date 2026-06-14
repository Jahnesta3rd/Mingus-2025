import { useEffect, useState } from 'react';

interface Article {
  id: number;
  title: string;
  url: string;
  source: string;
  domain: string;
  tags: string[];
  read_time_minutes: number;
}

interface MyRecommendationsResponse {
  trigger: string | null;
  domain?: string;
  articles: Article[];
  generated_at?: string;
}

export interface ArticleRecommendationStripProps {
  heading?: string;
  subheading?: string;
  className?: string;
  onArticleOpen?: (url: string) => void;
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

function openArticle(url: string, onArticleOpen?: (url: string) => void) {
  if (onArticleOpen) {
    onArticleOpen(url);
    return;
  }
  window.open(url, '_blank', 'noopener,noreferrer');
}

export default function ArticleRecommendationStrip({
  heading = 'Reading for you',
  subheading = 'Based on your latest check-in',
  className = '',
  onArticleOpen,
}: ArticleRecommendationStripProps) {
  const [articles, setArticles] = useState<Article[]>([]);

  useEffect(() => {
    let cancelled = false;

    void (async () => {
      try {
        const res = await fetch('/api/articles/my-recommendations', {
          credentials: 'include',
        });
        if (!res.ok) return;
        const data = (await res.json()) as MyRecommendationsResponse;
        if (!cancelled && Array.isArray(data.articles) && data.articles.length > 0) {
          setArticles(data.articles);
        }
      } catch {
        /* silent */
      }
    })();

    return () => {
      cancelled = true;
    };
  }, []);

  if (articles.length === 0) {
    return null;
  }

  return (
    <div
      className={`rounded-xl bg-gradient-to-br from-[#1A1030] to-[#3D2460] p-4 ${className}`.trim()}
    >
      <p className="text-xs font-semibold uppercase tracking-widest text-amber-400">
        {heading}
      </p>
      <p className="mb-3 mt-0.5 text-xs text-gray-400">{subheading}</p>

      <div className="flex gap-3 overflow-x-auto pb-2">
        {articles.slice(0, 3).map((article) => (
          <button
            key={article.id}
            type="button"
            onClick={() => openArticle(article.url, onArticleOpen)}
            className="w-44 shrink-0 cursor-pointer rounded-xl border border-white/10 bg-white/8 p-3 text-left"
          >
            <p className="mt-1 line-clamp-2 text-sm font-medium text-white">
              <span
                className={`mr-1.5 inline-block h-2 w-2 rounded-full align-middle ${
                  DOMAIN_DOT_COLORS[article.domain] ?? 'bg-gray-400'
                }`}
                aria-hidden
              />
              {article.title}
            </p>
            <p className="mt-1 text-xs text-gray-400">{article.source}</p>
            <p className="text-xs text-gray-500">· {article.read_time_minutes} min read</p>
          </button>
        ))}
      </div>
    </div>
  );
}
