CREATE TABLE IF NOT EXISTS classes (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name varchar(150) NOT NULL UNIQUE,
  total_seats integer NOT NULL CHECK (total_seats BETWEEN 1 AND 1000000),
  created_at timestamptz NOT NULL DEFAULT clock_timestamp()
);
CREATE TABLE IF NOT EXISTS holds (
  id uuid PRIMARY KEY,
  class_id uuid NOT NULL REFERENCES classes(id),
  student_id varchar(17) NOT NULL CHECK (student_id ~ '^[0-9]{17}$'),
  status varchar(12) NOT NULL CHECK (status IN ('HELD','CONFIRMED','EXPIRED','CANCELLED')),
  expires_at timestamptz NOT NULL,
  confirmed_at timestamptz NULL,
  created_at timestamptz NOT NULL DEFAULT clock_timestamp()
);
CREATE UNIQUE INDEX IF NOT EXISTS uq_active_admission ON holds(class_id,student_id)
  WHERE status IN ('HELD','CONFIRMED');
CREATE INDEX IF NOT EXISTS idx_hold_expiry ON holds(class_id,expires_at) WHERE status='HELD';
