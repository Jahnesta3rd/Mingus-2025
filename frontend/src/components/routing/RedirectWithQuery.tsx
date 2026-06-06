import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';

type RedirectWithQueryProps = {
  /** Pathname only (e.g. `/register`). Current location search is appended. */
  toPath: string;
};

/** Preserves `location.search` when redirecting (bare `<Navigate>` drops query strings). */
export function RedirectWithQuery({ toPath }: RedirectWithQueryProps) {
  const { search } = useLocation();
  const target = `${toPath}${search}`;
  return <Navigate to={target} replace />;
}
