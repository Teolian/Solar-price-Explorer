-- Fix radiation unique constraint
-- Drop old constraint and add new one with area included

DO $$
BEGIN
    -- Drop old constraint if exists
    ALTER TABLE radiation DROP CONSTRAINT IF EXISTS unique_radiation_record;

    -- Add new constraint with area
    ALTER TABLE radiation ADD CONSTRAINT unique_radiation_record
        UNIQUE(timestamp, station, area);
END $$;
