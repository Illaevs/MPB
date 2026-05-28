ALTER TABLE task_auctions
  ADD COLUMN IF NOT EXISTS is_block BOOLEAN DEFAULT FALSE;

ALTER TABLE task_auctions
  ADD COLUMN IF NOT EXISTS block_id VARCHAR(36);

ALTER TABLE task_auction_bids
  ADD COLUMN IF NOT EXISTS covers_children BOOLEAN DEFAULT FALSE;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint
    WHERE conname = 'fk_ta_block'
  ) THEN
    ALTER TABLE task_auctions
      ADD CONSTRAINT fk_ta_block
      FOREIGN KEY (block_id) REFERENCES task_auctions(id) ON DELETE CASCADE;
  END IF;
END $$;
