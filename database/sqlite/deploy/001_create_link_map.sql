-- -------------------------------------------------------------
-- TablePlus 4.1.0(376)
--
-- https://tableplus.com/
--
-- Database: mysqlite.db
-- Generation Time: 2021-10-05 00:55:10.7140
-- -------------------------------------------------------------


DROP TABLE IF EXISTS "link_map";
CREATE TABLE "link_map" (
    "id" integer,
    "state" integer NOT NULL DEFAULT '0',
    "url" varchar NOT NULL,
    "raw_path" varchar,
    "meta_path" varchar,
    "text_path" varchar,
    PRIMARY KEY (id)
);

