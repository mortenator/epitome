-- CreateTable
CREATE TABLE "clients" (
    "id" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "contactName" TEXT,
    "email" TEXT,
    "phone" TEXT,
    "address" TEXT,
    "city" TEXT,
    "state" TEXT,
    "zip" TEXT,
    "notes" TEXT,
    "isActive" BOOLEAN NOT NULL DEFAULT true,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "organizationId" TEXT NOT NULL,

    CONSTRAINT "clients_pkey" PRIMARY KEY ("id")
);

-- AddForeignKey
ALTER TABLE "clients" ADD CONSTRAINT "clients_organizationId_fkey" FOREIGN KEY ("organizationId") REFERENCES "organizations"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- CreateIndex
CREATE UNIQUE INDEX "clients_organizationId_name_key" ON "clients"("organizationId", "name");

-- CreateIndex
CREATE INDEX "clients_organizationId_idx" ON "clients"("organizationId");

-- AddColumn to projects
ALTER TABLE "projects" ADD COLUMN "clientId" TEXT;

-- AddForeignKey
ALTER TABLE "projects" ADD CONSTRAINT "projects_clientId_fkey" FOREIGN KEY ("clientId") REFERENCES "clients"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- CreateIndex
CREATE INDEX "projects_clientId_idx" ON "projects"("clientId");

-- Migrate existing client data
-- Create clients from unique project.client values
INSERT INTO "clients" ("id", "name", "organizationId", "createdAt", "updatedAt")
SELECT DISTINCT ON (p."client", p."organizationId")
    gen_random_uuid()::text,
    p."client",
    p."organizationId",
    NOW(),
    NOW()
FROM "projects" p
WHERE p."client" IS NOT NULL AND p."client" != 'TBD' AND p."client" != '';

-- Update projects to link to clients
UPDATE "projects" p
SET "clientId" = c."id"
FROM "clients" c
WHERE p."client" = c."name" AND p."organizationId" = c."organizationId";
