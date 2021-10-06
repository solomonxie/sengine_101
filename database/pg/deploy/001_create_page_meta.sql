BEGIN;

CREATE SEQUENCE page_meta_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE page_meta (
    mid integer DEFAULT nextval('page_meta_id_seq'::regclass) NOT NULL,
    url character varying(3000),
    state integer DEFAULT 0,
    title character varying(3000),
    page_type integer default 1,
    headers jsonb,
    keywords jsonb,
    sub_links jsonb,
    extra jsonb,
    created_time timestamp default timezone('UTC'::text, now()),
    updated_time timestamp default timezone('UTC'::text, now()),

    PRIMARY KEY (mid)
);

COMMIT;
