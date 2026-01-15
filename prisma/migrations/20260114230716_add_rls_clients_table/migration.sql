-- Enable Row Level Security on clients table
ALTER TABLE "clients" ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view clients in their organization
CREATE POLICY "Users can view clients in their organization"
  ON "clients" FOR SELECT
  USING (
    "organizationId" IN (
      SELECT "organizationId" 
      FROM "users" 
      WHERE id = auth.uid()::text
    )
  );

-- Policy: Users can insert clients in their organization
CREATE POLICY "Users can insert clients in their organization"
  ON "clients" FOR INSERT
  WITH CHECK (
    "organizationId" IN (
      SELECT "organizationId" 
      FROM "users" 
      WHERE id = auth.uid()::text
    )
  );

-- Policy: Users can update clients in their organization
CREATE POLICY "Users can update clients in their organization"
  ON "clients" FOR UPDATE
  USING (
    "organizationId" IN (
      SELECT "organizationId" 
      FROM "users" 
      WHERE id = auth.uid()::text
    )
  )
  WITH CHECK (
    "organizationId" IN (
      SELECT "organizationId" 
      FROM "users" 
      WHERE id = auth.uid()::text
    )
  );

-- Policy: Users can delete clients in their organization
CREATE POLICY "Users can delete clients in their organization"
  ON "clients" FOR DELETE
  USING (
    "organizationId" IN (
      SELECT "organizationId" 
      FROM "users" 
      WHERE id = auth.uid()::text
    )
  );
