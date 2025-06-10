/*
  Warnings:

  - The values [IN_PROGRESS,RESOLVED] on the enum `Status` will be removed. If these variants are still used in the database, this will fail.

*/
-- AlterEnum
BEGIN;
CREATE TYPE "Status_new" AS ENUM ('OPEN', 'CLOSED', 'PLANNED', 'CLOSED_REMOTE', 'CLOSED_ONSITE', 'PLANNED_ONSITE', 'VERIFYING', 'WAITING_CLIENT', 'TO_REPORT');
ALTER TABLE "Ticket" ALTER COLUMN "status" DROP DEFAULT;
ALTER TABLE "Ticket" ALTER COLUMN "status" TYPE "Status_new" USING ("status"::text::"Status_new");
ALTER TYPE "Status" RENAME TO "Status_old";
ALTER TYPE "Status_new" RENAME TO "Status";
DROP TYPE "Status_old";
ALTER TABLE "Ticket" ALTER COLUMN "status" SET DEFAULT 'OPEN';
COMMIT;
