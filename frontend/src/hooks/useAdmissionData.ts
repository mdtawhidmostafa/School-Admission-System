import {useCallback, useEffect, useRef, useState} from 'react';
import {request, validStudent} from '../api/client';
import type {AdmissionClass, Hold} from '../api/client';

/** Classes and student history fail independently. Never erase successful data on a partial failure. */
export function useAdmissionData(student: string) {
  const [classes, setClasses] = useState<AdmissionClass[]>([]);
  const [holds, setHolds] = useState<Hold[]>([]);
  const [classError, setClassError] = useState(false);
  const [historyError, setHistoryError] = useState(false);
  const sequence = useRef(0);

  const refresh = useCallback(async (): Promise<boolean> => {
    const current = ++sequence.current;
    const results = await Promise.allSettled([
      request<AdmissionClass[]>('GET', '/classes'),
      validStudent(student) ? request<Hold[]>('GET', '/me/holds', student) : Promise.resolve([] as Hold[]),
    ]);
    if (current !== sequence.current) return false;
    const [classResult, historyResult] = results;
    const classesFailed = classResult.status === 'rejected';
    const historyFailed = historyResult.status === 'rejected';
    setClassError(classesFailed);
    setHistoryError(historyFailed);
    if (classResult.status === 'fulfilled') setClasses(classResult.value);
    if (historyResult.status === 'fulfilled') setHolds(historyResult.value);
    return !(classesFailed || historyFailed);
  }, [student]);

  useEffect(() => {
    // Never show another student's old history after the identity changes.
    setHolds([]);
    void refresh();
    const interval = window.setInterval(() => { void refresh(); }, 3000);
    return () => { window.clearInterval(interval); sequence.current++; };
  }, [refresh]);

  return {classes, holds, classError, historyError, refresh};
}
