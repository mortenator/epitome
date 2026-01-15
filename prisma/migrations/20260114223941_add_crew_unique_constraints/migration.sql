-- Clean up duplicate crew members with "TBD" or empty emails/phones before creating unique constraints
-- Keep the first occurrence and update references to point to it

-- First, handle email duplicates (including "TBD" and empty strings)
WITH duplicates AS (
  SELECT 
    id,
    email,
    "organizationId",
    ROW_NUMBER() OVER (PARTITION BY "organizationId", email ORDER BY "createdAt") as rn
  FROM crew_members
  WHERE email IS NOT NULL AND email != '' AND email != 'TBD'
)
UPDATE crew_members cm
SET email = NULL
WHERE EXISTS (
  SELECT 1 FROM duplicates d 
  WHERE d.id = cm.id AND d.rn > 1
);

-- Handle phone duplicates
WITH duplicates AS (
  SELECT 
    id,
    phone,
    "organizationId",
    ROW_NUMBER() OVER (PARTITION BY "organizationId", phone ORDER BY "createdAt") as rn
  FROM crew_members
  WHERE phone IS NOT NULL AND phone != '' AND phone != 'TBD'
)
UPDATE crew_members cm
SET phone = NULL
WHERE EXISTS (
  SELECT 1 FROM duplicates d 
  WHERE d.id = cm.id AND d.rn > 1
);

-- Set "TBD" emails and phones to NULL (they're not valid identifiers)
UPDATE crew_members SET email = NULL WHERE email = 'TBD' OR email = '';
UPDATE crew_members SET phone = NULL WHERE phone = 'TBD' OR phone = '';

-- Create unique partial indexes for crew_members email and phone
-- These allow multiple NULLs but enforce uniqueness for non-NULL values per organization

CREATE UNIQUE INDEX "crew_members_email_org_unique" ON "crew_members"("email", "organizationId") 
WHERE "email" IS NOT NULL;

CREATE UNIQUE INDEX "crew_members_phone_org_unique" ON "crew_members"("phone", "organizationId") 
WHERE "phone" IS NOT NULL;
