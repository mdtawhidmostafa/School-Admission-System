import {PlusCircle} from 'lucide-react';

type Props = {
  adminKey: string; setAdminKey: (value: string) => void;
  name: string; setName: (value: string) => void;
  seats: string; setSeats: (value: string) => void;
  busy: boolean; onCreate: () => void;
};

export function AdminClassForm(props: Props) {
  const {adminKey, setAdminKey, name, setName, seats, setSeats, busy, onCreate} = props;
  return (
    <div className="form-card">
      <label htmlFor="admin-key">Administrator API Key (protected mode only)</label>
      <input id="admin-key" type="password" autoComplete="off"
        placeholder="Leave empty for assignment mode" value={adminKey}
        onChange={event => setAdminKey(event.target.value)}/>
      <label htmlFor="classname">Class &amp; Shift Name</label>
      <input id="classname" placeholder="e.g. Class 6 - Morning Shift" maxLength={150}
        value={name} onChange={event => setName(event.target.value)}/>
      <label htmlFor="seats">Total Seats</label>
      <input id="seats" type="number" min="1" max="1000000" step="1" value={seats}
        onChange={event => setSeats(event.target.value)}/>
      <button className="primary" disabled={busy} onClick={onCreate}>
        <PlusCircle size={18}/> Create Class
      </button>
      <p className="hint">No login in assignment mode; admin key is held in memory only.</p>
    </div>
  );
}
