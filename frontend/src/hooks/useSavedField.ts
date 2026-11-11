import {useEffect, useState} from 'react';

/** Persist assignment-only browser drafts; do not use for administrator credentials. */
export function useSavedField(key: string, fallback = '') {
  const [value, setValue] = useState(() => localStorage.getItem(key) ?? fallback);
  useEffect(() => { localStorage.setItem(key, value); }, [key, value]);
  return [value, setValue] as const;
}
