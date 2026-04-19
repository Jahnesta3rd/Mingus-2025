import type { Message } from '../../types/modularOnboarding';

export interface MessageBubbleProps {
  message: Message;
}

function formatTime(ts: number): string {
  return new Date(ts).toLocaleTimeString([], {
    hour: 'numeric',
    minute: '2-digit',
  });
}

export function MessageBubble({ message }: MessageBubbleProps) {
  if (message.role === 'system') {
    return (
      <div className="flex justify-center my-2">
        <div className="px-3 py-1 rounded-full bg-slate-50 text-slate-600 text-[12px]">
          {message.content}
        </div>
      </div>
    );
  }

  if (message.role === 'user') {
    return (
      <div className="flex flex-col items-end">
        <div className="max-w-[80%] bg-[#5B2D8E] text-white rounded-2xl rounded-tr-none px-4 py-3 text-[15px] leading-[1.6] whitespace-pre-wrap">
          {message.content}
        </div>
        <div className="mt-1 text-[11px] text-gray-500">
          {formatTime(message.timestamp)}
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-start">
      <div className="max-w-[80%] bg-white text-gray-900 rounded-2xl rounded-tl-none shadow-sm px-4 py-3 text-[15px] leading-[1.6] whitespace-pre-wrap">
        {message.content}
      </div>
      <div className="mt-1 text-[11px] text-gray-500">
        {formatTime(message.timestamp)}
      </div>
    </div>
  );
}
