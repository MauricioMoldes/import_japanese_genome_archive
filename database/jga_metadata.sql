
-- ----------------------------
-- Sequence structure for dbgap_table_id_seq
-- ----------------------------
DROP SEQUENCE IF EXISTS "jga_table_id_seq";
CREATE SEQUENCE "jga_table_id_seq" 
INCREMENT 1
MINVALUE  1
MAXVALUE 9223372036854775807
START 1
CACHE 1;

-- ----------------------------
-- Table structure for study_table
-- ----------------------------
DROP TABLE IF EXISTS "jga_study_table";
CREATE TABLE "jga_study_table" (
  "id" int4 NOT NULL DEFAULT nextval('jga_table_id_seq'::regclass),
  "jga_stable_id" text COLLATE "pg_catalog"."default",
  "title" text COLLATE "pg_catalog"."default" NULL,
  "description" text COLLATE "pg_catalog"."default" NULL,
  "status" text COLLATE "pg_catalog"."default" NULL,
  "visibility" text COLLATE "pg_catalog"."default" NULL,
  "repository" text COLLATE "pg_catalog"."default" NULL,
  "publications" JSONB  NULL,
  "study_type" JSONB  NULL,
  "alias" text COLLATE "pg_catalog"."default" NULL,
  "dbxrefs" JSONB  NULL,  
  "abstract" text COLLATE "pg_catalog"."default" NULL,
  "center_name" text COLLATE "pg_catalog"."default" NULL,  
  "date_created" timestamp(6) NULL,
  "date_modified" timestamp(6) NULL,
  "date_published" timestamp(6) NULL,
  "created_at" timestamp(6) NOT NULL DEFAULT timezone('utc'::text, now()),
  "edited_at" timestamp(6) NOT NULL DEFAULT timezone('utc'::text, now()),
  "created_by_db_user" varchar(255) COLLATE "pg_catalog"."default" NOT NULL DEFAULT "current_user"(),
  "edited_by_db_user" varchar(255) COLLATE "pg_catalog"."default" NOT NULL DEFAULT "current_user"()  
)

-- ----------------------------
-- Primary Key structure for table study_table
-- ----------------------------
--ALTER TABLE "jga_study_table" ADD CONSTRAINT "jga_stable_id_pkey" PRIMARY KEY ("jga_stable_id");
