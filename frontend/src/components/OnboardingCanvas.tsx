import type {
  CommitFieldResponse,
  CommitModuleResponse,
  ModuleData,
  ModuleId,
  OnboardingPhase,
  OnboardingState,
} from '../types/modularOnboarding';
import { ModulePanel } from './canvas/ModulePanel';
import { ModuleRail } from './canvas/ModuleRail';

export interface OnboardingCanvasProps {
  modules: OnboardingState['modules'];
  currentModule: ModuleId | null;
  data: ModuleData;
  phase: OnboardingPhase;
  progressPct: number;
  completedCount: number;
  commitField: (
    moduleId: ModuleId,
    fieldPath: string,
    value: unknown
  ) => Promise<CommitFieldResponse | undefined>;
  revisitModule: (moduleId: ModuleId) => Promise<void>;
  skipCurrentModule: () => Promise<void>;
  commitCurrentModule: () => Promise<CommitModuleResponse | undefined>;
  userTier: 'budget' | 'mid_tier' | 'professional' | null;
}

export function OnboardingCanvas({
  modules,
  currentModule,
  data,
  phase,
  progressPct,
  completedCount,
  commitField,
  revisitModule,
  skipCurrentModule,
  commitCurrentModule,
  userTier,
}: OnboardingCanvasProps) {
  return (
    <div className="bg-[#FAF5FF] min-h-screen">
      <div className="max-w-5xl mx-auto px-4 py-6">
        <ModuleRail
          modules={modules}
          currentModule={currentModule}
          progressPct={progressPct}
          completedCount={completedCount}
          onJumpTo={(id) => {
            void revisitModule(id);
          }}
        />
        {currentModule && (
          <div className="mt-6">
            <ModulePanel
              moduleId={currentModule}
              moduleState={modules[currentModule]}
              data={data}
              onEditField={(fieldPath, value) =>
                commitField(currentModule, fieldPath, value)
              }
              onSkip={skipCurrentModule}
              onCommit={commitCurrentModule}
              userTier={userTier}
            />
          </div>
        )}
        {phase === 'complete' && (
          <div className="mt-6 rounded-2xl border-[1.5px] bg-white p-6 shadow-sm text-center">
            <div className="text-lg font-bold text-[#5B2D8E] mb-2">All set.</div>
            <div className="text-sm text-slate-600">
              Your dashboard is ready — head to your snapshot to see how these
              pieces fit together.
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
