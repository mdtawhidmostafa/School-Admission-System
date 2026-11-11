import {GraduationCap} from 'lucide-react';
import type {AdmissionClass} from '../api/client';

type Props = {item: AdmissionClass; busy: boolean; onReserve: (item: AdmissionClass) => void};

export function ClassCard({item, busy, onReserve}: Props) {
  const used = item.confirmedSeats + item.heldSeats;
  const progress = item.totalSeats > 0 ? Math.min(100, 100 * used / item.totalSeats) : 0;
  return (
    <article className="class-card">
      <div className="class-icon"><GraduationCap size={24}/></div>
      <div className="class-card-head">
        <h3>{item.name}</h3>
        <span className={item.availableSeats ? 'pill green' : 'pill red'}>
          {item.availableSeats ? 'Seats Open' : 'Fully Booked'}
        </span>
      </div>
      <div className="seat-grid">
        <div><strong>{item.totalSeats}</strong><small>Total</small></div>
        <div><strong>{item.confirmedSeats}</strong><small>Confirmed</small></div>
        <div><strong>{item.heldSeats}</strong><small>Held</small></div>
        <div><strong>{item.availableSeats}</strong><small>Available</small></div>
      </div>
      <div className="progress"><div style={{width: `${progress}%`}}/></div>
      <button className="primary full" disabled={busy || item.availableSeats <= 0}
        onClick={() => onReserve(item)}>
        {item.availableSeats > 0 ? 'Apply Now' : 'No Seats Available'}
      </button>
    </article>
  );
}
