import React from 'react';
import { Link2, TrendingUp, Zap, Award, Lightbulb, BarChart3 } from 'lucide-react';
import { DollarHighlight } from './DollarHighlight';

export type InsightType =
  | 'correlation'
  | 'trend'
  | 'anomaly'
  | 'achievement'
  | 'recommendation'
  | 'spending_pattern';

export type InsightCategory =
  | 'physical'
  | 'mental'
  | 'relational'
  | 'financial'
  | 'spending';

export interface WellnessInsight {
  type: InsightType;
  title: string;
  message: string;
  data_backing: string;
  action: string;
  priority: number;
  category: InsightCategory;
  dollar_amount?: number;
}

const TYPE_ICONS: Record<InsightType, React.ElementType> = {
  correlation: Link2,
  trend: TrendingUp,
  anomaly: Zap,
  achievement: Award,
  recommendation: Lightbulb,
  spending_pattern: BarChart3,
};

const TYPE_LABELS: Record<InsightType, string> = {
  correlation: 'Correlation',
  trend: 'Trend',
  anomaly: 'Anomaly',
  achievement: 'Achievement',
  recommendation: 'Recommendation',
  spending_pattern: 'Spending pattern',
};

const CATEGORY_STYLES: Record<
  InsightCategory,
  { bg: string; border: string; iconBg: string }
> = {
  physical: { bg: 'bg-emerald-500/10', border: 'border-emerald-500/30', iconBg: 'bg-emerald-500/20 text-emerald-400' },
  mental: { bg: 'bg-violet-500/10', border: 'border-violet-500/30', iconBg: 'bg-violet-500/20 text-violet-400' },
  relational: { bg: 'bg-pink-500/10', border: 'border-pink-500/30', iconBg: 'bg-pink-500/20 text-pink-400' },
  financial: { bg: 'bg-blue-500/10', border: 'border-blue-500/30', iconBg: 'bg-blue-500/20 text-blue-400' },
  spending: { bg: 'bg-amber-500/10', border: 'border-amber-500/30', iconBg: 'bg-amber-500/20 text-amber-400' },
};

export interface InsightCardProps {
  insight: WellnessInsight;
  /** Index for staggered animation delay */
  index?: number;
  className?: string;
}

/**
 * Single insight card: type icon, title, message, dollar highlight, data backing, action.
 * Category colors; celebration style for achievement; prominent for anomaly/spending.
 */
export const InsightCard: React.FC<InsightCardProps> = ({
  insight,
  index = 0,
  className = '',
}) => {
  const Icon = TYPE_ICONS[insight.type];
  const styles = CATEGORY_STYLES[insight.category];
  const isAchievement = insight.type === 'achievement';
  const isAlert = insight.type === 'anomaly' || insight.type === 'spending_pattern';
  const hasAction = insight.action && insight.action.trim().length > 0;

  return (
    <article
      className={`
        rounded-xl border p-4
        animate-fade-in-up
        ${styles.bg} ${styles.border}
        ${isAchievement ? 'ring-2 ring-amber-400/40' : ''}
        ${isAlert ? 'ring-1 ring-amber-500/30' : ''}
        ${className}
      `}
      style={{ animationDelay: `${index * 80}ms`, animationFillMode: 'backwards' }}
      role="article"
      aria-labelledby={`insight-title-${index}`}
      aria-describedby={`insight-desc-${index}`}
    >
      <div className="flex items-start gap-3">
        <div
          className={`w-10 h-10 rounded-lg flex items-center justify-center shrink-0 ${styles.iconBg}`}
          aria-hidden
        >
          <Icon className="w-5 h-5" />
        </div>
        <div className="min-w-0 flex-1">
          <span className="sr-only">{TYPE_LABELS[insight.type]}</span>
          <h3
            id={`insight-title-${index}`}
            className="text-base font-bold text-slate-100"
          >
            {insight.title}
          </h3>
          <div id={`insight-desc-${index}`} className="mt-2 space-y-2">
            <p className="text-slate-300 text-sm leading-relaxed">{insight.message}</p>
            {insight.dollar_amount != null && insight.dollar_amount > 0 && (
              <p className="text-slate-100">
                <DollarHighlight
                  amount={insight.dollar_amount}
                  suffix=" more"
                  ariaLabel={`$${Math.round(insight.dollar_amount)} more`}
                />
              </p>
            )}
            {insight.data_backing && (
              <p className="text-slate-500 text-xs italic mt-1" role="note">
                {insight.data_backing}
              </p>
            )}
          </div>
          {hasAction && (
            <div
              className="mt-3 rounded-lg bg-slate-800/60 border border-slate-600 px-3 py-2"
              role="complementary"
              aria-label="Suggested action"
            >
              <p className="text-slate-300 text-sm font-medium">
                {insight.action}
              </p>
            </div>
          )}
        </div>
      </div>
    </article>
  );
};

export default InsightCard;
