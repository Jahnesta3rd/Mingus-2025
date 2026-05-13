import React, {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
} from 'react';
import { useAuth } from '../hooks/useAuth';
import AddImportantDateModal from '../components/important-dates/AddImportantDateModal';

export type ImportantDateModalContextValue = {
  openAddImportantDate: () => void;
  importantDatesRefreshKey: number;
};

const ImportantDateModalContext =
  createContext<ImportantDateModalContextValue | null>(null);

export function ImportantDateModalProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const { user } = useAuth();
  const [open, setOpen] = useState(false);
  const [importantDatesRefreshKey, setImportantDatesRefreshKey] = useState(0);

  const openAddImportantDate = useCallback(() => setOpen(true), []);

  const handleSaved = useCallback(() => {
    setOpen(false);
    setImportantDatesRefreshKey((k) => k + 1);
  }, []);

  const value = useMemo(
    () => ({ openAddImportantDate, importantDatesRefreshKey }),
    [openAddImportantDate, importantDatesRefreshKey]
  );

  const userId = user?.id ?? '';

  return (
    <ImportantDateModalContext.Provider value={value}>
      {children}
      {userId ? (
        <AddImportantDateModal
          isOpen={open}
          onClose={() => setOpen(false)}
          userId={userId}
          onSaved={handleSaved}
        />
      ) : null}
    </ImportantDateModalContext.Provider>
  );
}

export function useImportantDateModal(): ImportantDateModalContextValue {
  const v = useContext(ImportantDateModalContext);
  if (!v) {
    throw new Error(
      'useImportantDateModal must be used within ImportantDateModalProvider'
    );
  }
  return v;
}

export function useOptionalImportantDateModal(): ImportantDateModalContextValue | null {
  return useContext(ImportantDateModalContext);
}
