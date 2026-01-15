-- Enable Row Level Security (RLS) on all tables
-- This migration enables RLS but does NOT create policies
-- You'll need to create policies based on your access requirements

-- Core Tables
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;

-- Budgeting Tables
ALTER TABLE budgets ENABLE ROW LEVEL SECURITY;
ALTER TABLE budget_sections ENABLE ROW LEVEL SECURITY;
ALTER TABLE budget_lines ENABLE ROW LEVEL SECURITY;
ALTER TABLE budget_fringes ENABLE ROW LEVEL SECURITY;

-- Crew Management Tables
ALTER TABLE crew_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE project_crew ENABLE ROW LEVEL SECURITY;

-- Financial Tables
ALTER TABLE vendors ENABLE ROW LEVEL SECURITY;
ALTER TABLE purchase_orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE timecards ENABLE ROW LEVEL SECURITY;

-- Call Sheets & Logistics Tables
ALTER TABLE call_sheets ENABLE ROW LEVEL SECURITY;
ALTER TABLE locations ENABLE ROW LEVEL SECURITY;
ALTER TABLE call_sheet_locations ENABLE ROW LEVEL SECURITY;
ALTER TABLE schedule_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE call_sheet_rsvps ENABLE ROW LEVEL SECURITY;

-- Basic Policy: Allow all operations for authenticated users within their organization
-- NOTE: This is a permissive policy for development. Adjust for production!

-- Organizations: Users can only see their own organization
CREATE POLICY "Users can view their own organization"
  ON organizations FOR SELECT
  USING (id IN (SELECT "organizationId" FROM users WHERE id = auth.uid()::text));

-- Users: Users can see other users in their organization
CREATE POLICY "Users can view users in their organization"
  ON users FOR SELECT
  USING ("organizationId" IN (SELECT "organizationId" FROM users WHERE id = auth.uid()::text));

-- Projects: Users can see projects in their organization
CREATE POLICY "Users can view projects in their organization"
  ON projects FOR SELECT
  USING ("organizationId" IN (SELECT "organizationId" FROM users WHERE id = auth.uid()::text));

-- For now, allow full access to authenticated users (adjust based on your needs)
-- You'll want to create more granular policies based on user roles

-- Temporary permissive policy for development (REMOVE IN PRODUCTION)
-- This allows authenticated users full access - replace with role-based policies
DO $$
DECLARE
  table_name text;
BEGIN
  FOR table_name IN 
    SELECT tablename FROM pg_tables 
    WHERE schemaname = 'public' 
    AND tablename NOT IN ('organizations', 'users', 'projects')
  LOOP
    EXECUTE format('
      CREATE POLICY IF NOT EXISTS "Authenticated users full access" 
      ON %I FOR ALL 
      USING (auth.role() = ''authenticated'')
      WITH CHECK (auth.role() = ''authenticated'');
    ', table_name);
  END LOOP;
END $$;
