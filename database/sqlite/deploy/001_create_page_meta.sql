-- -------------------------------------------------------------
-- TablePlus 4.1.0(376)
--
-- https://tableplus.com/
--
-- Database: mysqlite.db
-- Generation Time: 2021-10-05 00:55:10.7140
-- -------------------------------------------------------------

BEGIN;

CREATE TABLE IF NOT EXISTS "page_meta" (
    mid integer,
    url varchar(3000),
    state integer DEFAULT 0,
    page_type integer default 1,
    -- title varchar(3000),
    -- headers text,
    -- keywords text,
    -- sub_links text,
    -- extra text,
    created_time datetime,
    updated_time datetime,

    PRIMARY KEY (mid)
);

COMMIT;
