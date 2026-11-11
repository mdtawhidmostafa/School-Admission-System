import {useEffect, useState} from 'react';
import {createRoot} from 'react-dom/client';
import {
  AlertTriangle, BookOpen, CalendarClock, CheckCircle2,
  GraduationCap, RefreshCcw, School, Users,
} from 'lucide-react';
import {request, validStudent} from './api/client';
import type {AdmissionClass, Hold} from './api/client';
import {AdminClassForm} from './components/AdminClassForm';
import {ApplicationsPanel} from './components/ApplicationsPanel';
import {ClassCard} from './components/ClassCard';
import {useAdmissionData} from './hooks/useAdmissionData';
import {useSavedField} from './hooks/useSavedField';
import './style.css';

type Tab = 'browse' | 'applications' | 'admin';
type Notice = {type: 'error' | 'success'; text: string};

function App() {
  const [student, setStudent] = useSavedField('admission.student');
  const [name, setName] = useSavedField('admission.draft.className');
  const [seats, setSeats] = useSavedField('admission.draft.seats', '120');
  // Keep admin credentials in memory only.
  const [adminKey, setAdminKey] = useState('');
  const [tab, setTab] = useState<Tab>('browse');
  const [notice, setNotice] = useState<Notice | null>(null);
  const [busy, setBusy] = useState(false);
  const [now, setNow] = useState(Date.now());
  const {classes, holds, classError, historyError, refresh} = useAdmissionData(student);
  const serverDown = classError || historyError;

  useEffect(() => {
    const interval = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(interval);
  }, []);

  const refreshManually = async () => {
    if (!await refresh()) {
      setNotice({type: 'error', text: 'Some data could not refresh. Previous results are retained.'});
    }
  };

  const action = async (operation: () => Promise<unknown>, success: string) => {
    if (busy) return;
    setBusy(true);
    setNotice(null);
    try {
      await operation();
      setNotice({type: 'success', text: success});
    } catch (error) {
      setNotice({type: 'error', text: error instanceof Error ? error.message : 'Request failed.'});
    } finally {
      await refresh();
      setBusy(false);
    }
  };

  const create = () => {
    const count = Number(seats);
    if (!name.trim() || name.trim().length > 150 || !Number.isInteger(count) || count < 1 || count > 1_000_000) {
      setNotice({type: 'error', text: 'A class name (max 150 characters) and 1–1,000,000 seats are required.'});
      return;
    }
    void action(async () => {
      await request('POST', '/classes', undefined, {name: name.trim(), totalSeats: count}, adminKey);
      setName('');
      setSeats('120');
    }, 'Class created successfully.');
  };

  const reserve = (item: AdmissionClass) => {
    if (!validStudent(student)) {
      setNotice({type: 'error', text: 'Enter a valid 17-digit Birth Registration Number.'});
      window.scrollTo({top: 0, behavior: 'smooth'});
      return;
    }
    void action(() => request('POST', `/classes/${item.id}/holds`, student),
      `Seat held for ${item.name}. Confirm before expiry.`);
  };
  const confirm = (hold: Hold) => void action(
    () => request('POST', `/holds/${hold.holdId}/confirm`, student), 'Admission confirmed successfully.');
  const cancel = (hold: Hold) => void action(
    () => request('DELETE', `/holds/${hold.holdId}`, student), 'Seat hold cancelled.');

  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="brand">
          <div className="logo"><GraduationCap size={25}/></div>
          <div><strong>Ahnaf International School  </strong><small>School Admission Portal</small></div>
        </div>
        <div className="menu-title">NAVIGATION</div>
        <button className={tab === 'browse' ? 'nav active' : 'nav'} onClick={() => setTab('browse')}>
          <BookOpen size={19}/> Browse Classes
        </button>
        <button className={tab === 'applications' ? 'nav active' : 'nav'} onClick={() => setTab('applications')}>
          <CalendarClock size={19}/> My Applications
        </button>
        <div className="menu-title secondary-title">SCHOOL MANAGEMENT</div>
        <button className={tab === 'admin' ? 'nav active' : 'nav'} onClick={() => setTab('admin')}>
          <School size={19}/> Create Class
        </button>
        <div className="side-note"><CheckCircle2 size={18}/>
          <span>Real-time reservation status<small>Powered by PostgreSQL</small></span>
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <div className="top-title">School Admission System <span className="dot">•</span> 2026</div>
          <span className="online"><span/> {serverDown ? 'Some data unavailable' : 'Live availability'}</span>
        </header>
        <div className="content">
          <div className="hero">
            <div className="hero-content">
              <span className="eyebrow">ACADEMIC YEAR 2026</span>
              <h1>{tab === 'browse' ? 'Find your place to grow' : tab === 'applications' ? 'Your applications' : 'School management'}</h1>
              <p>{tab === 'browse' ? 'Explore classes and reserve an available seat.' :
                tab === 'applications' ? 'Review and manage your admission requests.' : 'Create classes and configure seats.'}</p>
            </div>
            <div className="hero-art"><GraduationCap size={115} strokeWidth={1.2}/></div>
          </div>

          <section className="identity">
            <div><label htmlFor="student">Student Birth Registration Number</label>
              <p>Enter a 17-digit student number. No login is required for this assignment.</p>
            </div>
            <div className="identity-input"><Users size={18}/>
              <input id="student" aria-label="Student Birth Registration Number" inputMode="numeric"
                maxLength={17} placeholder="17-digit student ID" value={student}
                onChange={event => setStudent(event.target.value.replace(/\D/g, '').slice(0, 17))}/>
            </div>
          </section>

          {notice && <div role="alert" className={`notice ${notice.type}`}>
            {notice.type === 'error' ? <AlertTriangle size={19}/> : <CheckCircle2 size={19}/>}
            <span>{notice.text}</span>
            <button aria-label="Dismiss message" onClick={() => setNotice(null)}>×</button>
          </div>}
          {serverDown && <div role="alert" className="notice error">
            <AlertTriangle size={18}/>Some requests failed. Saved records are still shown.
          </div>}

          {tab === 'browse' && <>
            <div className="section-head"><div><h2>Available Classes</h2>
              <p>Availability refreshes every 3 seconds.</p></div>
              <button className="secondary" onClick={() => void refreshManually()}><RefreshCcw size={16}/> Refresh</button>
            </div>
            <div className="stats">
              <div><span>Total Classes</span><strong>{classes.length}</strong></div>
              <div><span>Available Seats</span><strong>{classes.reduce((sum, item) => sum + item.availableSeats, 0)}</strong></div>
              <div><span>Confirmed Admissions</span><strong>{classes.reduce((sum, item) => sum + item.confirmedSeats, 0)}</strong></div>
            </div>
            <div className="cards">
              {classes.map(item => <ClassCard key={item.id} item={item} busy={busy} onReserve={reserve}/>)}
              {classes.length === 0 && !classError && <div className="empty">No classes created yet.</div>}
            </div>
          </>}

          {tab === 'applications' && <ApplicationsPanel studentIsValid={validStudent(student)}
            holds={holds} now={now} busy={busy} onConfirm={confirm} onCancel={cancel}
            onRefresh={() => void refreshManually()}/>}

          {tab === 'admin' && <>
            <div className="section-head"><div><h2>Create New Class</h2>
              <p>Each class-shift has its own seat allocation.</p></div></div>
            <AdminClassForm adminKey={adminKey} setAdminKey={setAdminKey}
              name={name} setName={setName} seats={seats} setSeats={setSeats}
              busy={busy} onCreate={create}/>
          </>}
        </div>
      </main>
    </div>
  );
}

createRoot(document.getElementById('root')!).render(<App/>);
