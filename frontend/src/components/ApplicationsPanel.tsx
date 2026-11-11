import {CheckCircle2,XCircle,RefreshCcw} from 'lucide-react';
import type {Hold} from '../api/client';

export type ApplicationsPanelProps={
  studentIsValid:boolean;holds:Hold[];now:number;busy:boolean;
  onConfirm:(h:Hold)=>void;onCancel:(h:Hold)=>void;onRefresh:()=>void;
};
/** Presentation only: backend owns expiry and confirmation truth. */
export function ApplicationsPanel({studentIsValid,holds,now,busy,onConfirm,onCancel,onRefresh}:ApplicationsPanelProps){
  const remaining=(h:Hold)=>Math.max(0,Math.ceil((Date.parse(h.expiresAt)-now)/1000));
  const active=(h:Hold)=>h.status==='HELD'&&remaining(h)>0;
  const status=(h:Hold)=>h.status==='HELD'&&!active(h)?'EXPIRED':h.status;
  const clock=(s:number)=>`${String(Math.floor(s/60)).padStart(2,'0')}:${String(s%60).padStart(2,'0')}`;
  return <>
    <div className="section-head"><div><h2>My Applications</h2><p>Every reservation and admission for this student.</p></div><button className="secondary" onClick={onRefresh}><RefreshCcw size={16}/> Refresh</button></div>
    {!studentIsValid?<div className="empty">Enter a valid 17-digit Student ID above to see applications.</div>
    :holds.length===0?<div className="empty">No applications found. Browse Classes to reserve a seat.</div>
    :<div className="application-list">{holds.map(h=><article key={h.holdId} className="application">
      <div><h3>{h.className??h.classId}</h3><small>Application ID: {h.holdId}</small></div>
      <div className="application-status"><span className={'pill '+(status(h)==='CONFIRMED'?'green':status(h)==='HELD'?'amber':'grey')}>{status(h)}</span>
      {active(h)&&<div className="countdown">Expires in {clock(remaining(h))}</div>}</div>
      <div className="application-actions">{active(h)&&<><button className="primary" disabled={busy} onClick={()=>onConfirm(h)}><CheckCircle2 size={16}/> Pay Fee & Confirm</button><button className="secondary danger" disabled={busy} onClick={()=>onCancel(h)}><XCircle size={16}/> Cancel</button></>}</div>
    </article>)}</div>}
  </>;
}
