-- Run once after backup. Abort rather than choosing which duplicate user's filters to delete.
BEGIN;
DO $$ BEGIN
 IF EXISTS(SELECT 1 FROM users GROUP BY id_tg HAVING count(*) > 1) THEN
  RAISE EXCEPTION 'Duplicate Telegram IDs. Inspect SELECT id_tg,count(*) FROM users GROUP BY id_tg HAVING count(*)>1 before migration';
 END IF;
END $$;
CREATE UNIQUE INDEX IF NOT EXISTS users_id_tg_unique ON users(id_tg);
COMMIT;
