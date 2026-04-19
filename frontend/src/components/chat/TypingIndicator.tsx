export function TypingIndicator() {
  return (
    <div className="flex flex-col items-start">
      <div className="bg-white rounded-2xl rounded-tl-none shadow-sm px-4 py-3 flex gap-1">
        <span
          className="animate-bounce text-slate-500"
          style={{ animationDelay: '0ms' }}
        >
          •
        </span>
        <span
          className="animate-bounce text-slate-500"
          style={{ animationDelay: '150ms' }}
        >
          •
        </span>
        <span
          className="animate-bounce text-slate-500"
          style={{ animationDelay: '300ms' }}
        >
          •
        </span>
      </div>
    </div>
  );
}
