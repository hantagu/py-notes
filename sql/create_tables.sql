CREATE TABLE IF NOT EXISTS "users"
(
    "id" INT NOT NULL,
    "username" VARCHAR(32),

    "first_name" VARCHAR(64) NOT NULL,
    "last_name" VARCHAR(64),

    CONSTRAINT "pk_user_id"
        PRIMARY KEY ("id"),

    CONSTRAINT "unique_user_username"
        UNIQUE ("username")
);


CREATE TABLE IF NOT EXISTS "books"
(
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "owner_id" INT NOT NULL,

    "title" VARCHAR(64) NOT NULL,

    CONSTRAINT "pk_book_id"
        PRIMARY KEY ("id"),

    CONSTRAINT "unique_book_owner_id"
        FOREIGN KEY ("owner_id") REFERENCES "users"("id") ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS "notes"
(
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "book_id" UUID NOT NULL,

    "title" VARCHAR(64) NOT NULL,
    "text" TEXT NOT NULL,

    CONSTRAINT "pk_note_id"
        PRIMARY KEY ("id"),

    CONSTRAINT "fk_note_book_id"
        FOREIGN KEY ("book_id") REFERENCES "books"("id") ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS "task_lists"
(
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "owner_id" INT NOT NULL,

    "title" VARCHAR(64) NOT NULL,

    CONSTRAINT "pk_task_list_id"
        PRIMARY KEY ("id"),

    CONSTRAINT "fk_task_list_owner_id"
        FOREIGN KEY ("owner_id") REFERENCES "users"("id") ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS "tasks"
(
    "id" UUID NOT NULL DEFAULT gen_random_uuid(),
    "task_list_id" UUID NOT NULL,

    "text" VARCHAR(64) NOT NULL,
    "is_done" BOOLEAN NOT NULL,

    CONSTRAINT "pk_task_id"
        PRIMARY KEY ("id"),

    CONSTRAINT "fk_task_task_list_id"
        FOREIGN KEY ("task_list_id") REFERENCES "task_lists"("id") ON DELETE CASCADE
)
