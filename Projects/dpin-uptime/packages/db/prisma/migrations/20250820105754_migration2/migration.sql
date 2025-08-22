/*
  Warnings:

  - The primary key for the `User` table will be changed. If it partially fails, the table could be left without primary key constraint.
  - The primary key for the `Validator` table will be changed. If it partially fails, the table could be left without primary key constraint.
  - The primary key for the `Website` table will be changed. If it partially fails, the table could be left without primary key constraint.
  - The primary key for the `WebsiteTick` table will be changed. If it partially fails, the table could be left without primary key constraint.

*/
-- DropForeignKey
ALTER TABLE "public"."WebsiteTick" DROP CONSTRAINT "WebsiteTick_validatorId_fkey";

-- DropForeignKey
ALTER TABLE "public"."WebsiteTick" DROP CONSTRAINT "WebsiteTick_websiteId_fkey";

-- AlterTable
ALTER TABLE "public"."User" DROP CONSTRAINT "User_pkey",
ALTER COLUMN "id" DROP DEFAULT,
ALTER COLUMN "id" SET DATA TYPE TEXT,
ADD CONSTRAINT "User_pkey" PRIMARY KEY ("id");
DROP SEQUENCE "User_id_seq";

-- AlterTable
ALTER TABLE "public"."Validator" DROP CONSTRAINT "Validator_pkey",
ADD COLUMN     "pendingPayouts" INTEGER NOT NULL DEFAULT 0,
ALTER COLUMN "id" DROP DEFAULT,
ALTER COLUMN "id" SET DATA TYPE TEXT,
ADD CONSTRAINT "Validator_pkey" PRIMARY KEY ("id");
DROP SEQUENCE "Validator_id_seq";

-- AlterTable
ALTER TABLE "public"."Website" DROP CONSTRAINT "Website_pkey",
ADD COLUMN     "disabled" BOOLEAN NOT NULL DEFAULT false,
ALTER COLUMN "id" DROP DEFAULT,
ALTER COLUMN "id" SET DATA TYPE TEXT,
ADD CONSTRAINT "Website_pkey" PRIMARY KEY ("id");
DROP SEQUENCE "Website_id_seq";

-- AlterTable
ALTER TABLE "public"."WebsiteTick" DROP CONSTRAINT "WebsiteTick_pkey",
ALTER COLUMN "id" DROP DEFAULT,
ALTER COLUMN "id" SET DATA TYPE TEXT,
ALTER COLUMN "websiteId" SET DATA TYPE TEXT,
ALTER COLUMN "validatorId" SET DATA TYPE TEXT,
ADD CONSTRAINT "WebsiteTick_pkey" PRIMARY KEY ("id");
DROP SEQUENCE "WebsiteTick_id_seq";

-- AddForeignKey
ALTER TABLE "public"."WebsiteTick" ADD CONSTRAINT "WebsiteTick_websiteId_fkey" FOREIGN KEY ("websiteId") REFERENCES "public"."Website"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "public"."WebsiteTick" ADD CONSTRAINT "WebsiteTick_validatorId_fkey" FOREIGN KEY ("validatorId") REFERENCES "public"."Validator"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
