import React, { useCallback, useEffect, useRef, useState } from 'react';

export type EmployerSelectValue = {
  cik: string | null;
  name: string;
};

type SearchResult = {
  cik: string;
  name: string;
  ticker?: string | null;
  exchange?: string | null;
};

const inputClass =
  'w-full min-h-11 rounded-lg border border-[#E2E8F0] bg-white px-3 py-2.5 pr-10 text-[#1E293B] placeholder:text-[#64748B] focus:border-[#5B2D8E] focus:outline-none focus:ring-1 focus:ring-[#5B2D8E]';

interface EmployerSelectProps {
  value: EmployerSelectValue | null;
  onChange: (val: EmployerSelectValue) => void;
  placeholder?: string;
  disabled?: boolean;
  id?: string;
}

export default function EmployerSelect({
  value,
  onChange,
  placeholder = 'Search your employer…',
  disabled = false,
  id = 'employer-select',
}: EmployerSelectProps) {
  const [inputText, setInputText] = useState(value?.name ?? '');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const [noResults, setNoResults] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setInputText(value?.name ?? '');
  }, [value?.name, value?.cik]);

  const runSearch = useCallback(async (query: string) => {
    if (query.trim().length < 2) {
      setResults([]);
      setNoResults(false);
      setOpen(false);
      return;
    }
    setLoading(true);
    try {
      const res = await fetch(
        `/api/employer/search?q=${encodeURIComponent(query.trim())}`,
        { credentials: 'include' }
      );
      if (!res.ok) {
        setResults([]);
        setNoResults(false);
        setOpen(false);
        return;
      }
      const data = (await res.json()) as { results?: SearchResult[] };
      const list = data.results ?? [];
      setResults(list.slice(0, 5));
      setNoResults(list.length === 0);
      setOpen(true);
    } catch {
      setResults([]);
      setNoResults(false);
      setOpen(false);
    } finally {
      setLoading(false);
    }
  }, []);

  const handleInputChange = (text: string) => {
    setInputText(text);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => runSearch(text), 300);
  };

  const handleSelect = (item: SearchResult) => {
    setInputText(item.name);
    setOpen(false);
    setResults([]);
    onChange({ cik: item.cik, name: item.name });
  };

  const handleBlur = () => {
    window.setTimeout(() => {
      if (!containerRef.current?.contains(document.activeElement)) {
        setOpen(false);
        const trimmed = inputText.trim();
        if (!trimmed) {
          onChange({ cik: null, name: '' });
          return;
        }
        if (value?.cik && value.name === trimmed) return;
        onChange({ cik: null, name: trimmed });
      }
    }, 150);
  };

  useEffect(() => {
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, []);

  return (
    <div ref={containerRef} className="relative">
      <input
        id={id}
        type="text"
        className={inputClass}
        value={inputText}
        disabled={disabled}
        placeholder={placeholder}
        role="combobox"
        aria-expanded={open}
        aria-autocomplete="list"
        aria-controls={`${id}-listbox`}
        onChange={(e) => handleInputChange(e.target.value)}
        onFocus={() => {
          if (results.length > 0 || noResults) setOpen(true);
        }}
        onBlur={handleBlur}
      />
      {loading && (
        <span
          className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-[#64748B]"
          aria-hidden
        >
          <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
            />
          </svg>
        </span>
      )}
      {open && (results.length > 0 || noResults) && (
        <ul
          id={`${id}-listbox`}
          role="listbox"
          className="absolute z-50 mt-1 w-full rounded-md border border-[#E2E8F0] bg-white py-1 shadow-lg"
        >
          {results.map((item) => (
            <li
              key={`${item.cik}-${item.name}`}
              role="option"
              className="cursor-pointer px-3 py-2 hover:bg-[#F8FAFC]"
              onMouseDown={(e) => e.preventDefault()}
              onClick={() => handleSelect(item)}
            >
              <span className="font-medium text-[#1E293B]">{item.name}</span>
              {item.ticker ? (
                <span className="ml-2 rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-600">
                  {item.ticker}
                </span>
              ) : null}
            </li>
          ))}
          {noResults && results.length === 0 && (
            <li className="px-3 py-2 text-sm text-[#64748B]">
              No public company found — we&apos;ll use your assessment answers for this employer.
            </li>
          )}
        </ul>
      )}
    </div>
  );
}
