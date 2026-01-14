-- CreateEnum
CREATE TYPE "UserRole" AS ENUM ('ADMIN', 'PRODUCER', 'COORDINATOR', 'CREW');

-- CreateEnum
CREATE TYPE "ProjectStatus" AS ENUM ('BID', 'AWARDED', 'ACTIVE', 'WRAPPED', 'CLOSED', 'CANCELLED');

-- CreateEnum
CREATE TYPE "BudgetStatus" AS ENUM ('DRAFT', 'PENDING_REVIEW', 'CLIENT_REVIEW', 'APPROVED', 'REVISED');

-- CreateEnum
CREATE TYPE "BudgetSectionType" AS ENUM ('LABOR', 'EXPENSES', 'TALENT', 'PRODUCTION', 'INSURANCE');

-- CreateEnum
CREATE TYPE "FringeType" AS ENUM ('PAYROLL_TAX', 'WORKERS_COMP', 'INSURANCE', 'AGENCY_FEE', 'CUSTOM');

-- CreateEnum
CREATE TYPE "Department" AS ENUM ('PRODUCTION', 'CAMERA', 'GRIP_ELECTRIC', 'ART', 'WARDROBE', 'HAIR_MAKEUP', 'SOUND', 'LOCATIONS', 'TRANSPORTATION', 'CATERING', 'POST_PRODUCTION', 'OTHER');

-- CreateEnum
CREATE TYPE "UnionStatus" AS ENUM ('NON_UNION', 'IATSE', 'TEAMSTERS', 'SAG_AFTRA', 'DGA', 'WGA', 'OTHER_UNION');

-- CreateEnum
CREATE TYPE "DealType" AS ENUM ('DAY_RATE', 'WEEKLY_RATE', 'FLAT_FEE', 'HOURLY');

-- CreateEnum
CREATE TYPE "CrewStatus" AS ENUM ('HOLD', 'CONFIRMED', 'CANCELLED', 'WRAPPED');

-- CreateEnum
CREATE TYPE "POStatus" AS ENUM ('DRAFT', 'PENDING', 'APPROVED', 'ISSUED', 'RECEIVED', 'INVOICED', 'PAID', 'CANCELLED');

-- CreateEnum
CREATE TYPE "TimecardStatus" AS ENUM ('DRAFT', 'SUBMITTED', 'APPROVED', 'REJECTED', 'PROCESSED', 'PAID');

-- CreateEnum
CREATE TYPE "CallSheetStatus" AS ENUM ('DRAFT', 'REVIEW', 'APPROVED', 'DISTRIBUTED');

-- CreateEnum
CREATE TYPE "LocationType" AS ENUM ('SHOOT', 'BASECAMP', 'CREW_PARKING', 'TRUCK_PARKING', 'CATERING', 'HOLDING', 'HOSPITAL', 'HOTEL', 'OTHER');

-- CreateEnum
CREATE TYPE "ScheduleEventType" AS ENUM ('CREW_CALL', 'TALENT_CALL', 'MEAL', 'SHOOT', 'COMPANY_MOVE', 'WRAP', 'GENERAL');

-- CreateEnum
CREATE TYPE "RSVPStatus" AS ENUM ('PENDING', 'SENT', 'VIEWED', 'CONFIRMED', 'DECLINED');

-- CreateTable
CREATE TABLE "organizations" (
    "id" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "slug" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "defaultInsuranceRate" DECIMAL(5,4) NOT NULL DEFAULT 0.03,
    "defaultPayrollTaxRate" DECIMAL(5,4) NOT NULL DEFAULT 0.23,
    "defaultWorkersCompRate" DECIMAL(5,4) NOT NULL DEFAULT 0.02,
    "defaultAgencyFeeRate" DECIMAL(5,4) NOT NULL DEFAULT 0.17,

    CONSTRAINT "organizations_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "users" (
    "id" TEXT NOT NULL,
    "email" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "hashedPassword" TEXT,
    "role" "UserRole" NOT NULL DEFAULT 'CREW',
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "organizationId" TEXT NOT NULL,

    CONSTRAINT "users_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "projects" (
    "id" TEXT NOT NULL,
    "status" "ProjectStatus" NOT NULL DEFAULT 'ACTIVE',
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "jobNumber" TEXT NOT NULL,
    "jobName" TEXT NOT NULL,
    "client" TEXT NOT NULL,
    "agency" TEXT,
    "brand" TEXT,
    "bidDate" TIMESTAMP(3),
    "awardDate" TIMESTAMP(3),
    "prepStartDate" TIMESTAMP(3),
    "shootStartDate" TIMESTAMP(3),
    "shootEndDate" TIMESTAMP(3),
    "wrapDate" TIMESTAMP(3),
    "insuranceRate" DECIMAL(5,4),
    "payrollTaxRate" DECIMAL(5,4),
    "workersCompRate" DECIMAL(5,4),
    "agencyFeeRate" DECIMAL(5,4),
    "organizationId" TEXT NOT NULL,

    CONSTRAINT "projects_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "budgets" (
    "id" TEXT NOT NULL,
    "version" INTEGER NOT NULL DEFAULT 1,
    "name" TEXT NOT NULL,
    "status" "BudgetStatus" NOT NULL DEFAULT 'DRAFT',
    "isActive" BOOLEAN NOT NULL DEFAULT false,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "lockedAt" TIMESTAMP(3),
    "projectId" TEXT NOT NULL,
    "createdById" TEXT NOT NULL,

    CONSTRAINT "budgets_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "budget_sections" (
    "id" TEXT NOT NULL,
    "code" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "sortOrder" INTEGER NOT NULL,
    "sectionType" "BudgetSectionType" NOT NULL DEFAULT 'LABOR',
    "budgetId" TEXT NOT NULL,

    CONSTRAINT "budget_sections_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "budget_lines" (
    "id" TEXT NOT NULL,
    "lineNumber" INTEGER NOT NULL,
    "description" TEXT NOT NULL,
    "sortOrder" INTEGER NOT NULL,
    "quantity" DECIMAL(10,2) NOT NULL DEFAULT 1,
    "rate" DECIMAL(12,2) NOT NULL DEFAULT 0,
    "days" DECIMAL(10,2) NOT NULL DEFAULT 1,
    "ot15Hours" DECIMAL(10,2) NOT NULL DEFAULT 0,
    "ot20Hours" DECIMAL(10,2) NOT NULL DEFAULT 0,
    "estimatedTotal" DECIMAL(14,2) NOT NULL DEFAULT 0,
    "notes" TEXT,
    "isContracted" BOOLEAN NOT NULL DEFAULT false,
    "sectionId" TEXT NOT NULL,

    CONSTRAINT "budget_lines_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "budget_fringes" (
    "id" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "fringeType" "FringeType" NOT NULL,
    "rate" DECIMAL(5,4) NOT NULL,
    "isActive" BOOLEAN NOT NULL DEFAULT true,
    "sectionId" TEXT NOT NULL,

    CONSTRAINT "budget_fringes_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "crew_members" (
    "id" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "firstName" TEXT NOT NULL,
    "lastName" TEXT NOT NULL,
    "email" TEXT,
    "phone" TEXT,
    "address" TEXT,
    "city" TEXT,
    "state" TEXT,
    "zip" TEXT,
    "department" "Department",
    "primaryRole" TEXT,
    "defaultRate" DECIMAL(12,2),
    "unionStatus" "UnionStatus" NOT NULL DEFAULT 'NON_UNION',
    "unionLocal" TEXT,
    "loanOutCompany" TEXT,
    "w9OnFile" BOOLEAN NOT NULL DEFAULT false,
    "skills" TEXT[],
    "notes" TEXT,
    "isActive" BOOLEAN NOT NULL DEFAULT true,
    "organizationId" TEXT NOT NULL,

    CONSTRAINT "crew_members_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "project_crew" (
    "id" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "role" TEXT NOT NULL,
    "department" "Department" NOT NULL,
    "dealRate" DECIMAL(12,2) NOT NULL,
    "dealType" "DealType" NOT NULL DEFAULT 'DAY_RATE',
    "guaranteedDays" DECIMAL(10,2),
    "kitFee" DECIMAL(12,2),
    "perDiem" DECIMAL(10,2),
    "status" "CrewStatus" NOT NULL DEFAULT 'HOLD',
    "dealMemoSigned" BOOLEAN NOT NULL DEFAULT false,
    "startDate" TIMESTAMP(3),
    "endDate" TIMESTAMP(3),
    "dietaryRestrictions" TEXT,
    "shirtSize" TEXT,
    "vehicleInfo" TEXT,
    "notes" TEXT,
    "projectId" TEXT NOT NULL,
    "crewMemberId" TEXT,
    "budgetLineId" TEXT,

    CONSTRAINT "project_crew_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "vendors" (
    "id" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "contactName" TEXT,
    "email" TEXT,
    "phone" TEXT,
    "address" TEXT,
    "taxId" TEXT,
    "w9OnFile" BOOLEAN NOT NULL DEFAULT false,
    "notes" TEXT,
    "isActive" BOOLEAN NOT NULL DEFAULT true,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "organizationId" TEXT NOT NULL,

    CONSTRAINT "vendors_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "purchase_orders" (
    "id" TEXT NOT NULL,
    "poNumber" TEXT NOT NULL,
    "status" "POStatus" NOT NULL DEFAULT 'DRAFT',
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "description" TEXT NOT NULL,
    "amount" DECIMAL(14,2) NOT NULL,
    "taxAmount" DECIMAL(14,2) NOT NULL DEFAULT 0,
    "totalAmount" DECIMAL(14,2) NOT NULL,
    "issueDate" TIMESTAMP(3),
    "dueDate" TIMESTAMP(3),
    "paidDate" TIMESTAMP(3),
    "invoiceNumber" TEXT,
    "paymentMethod" TEXT,
    "paymentRef" TEXT,
    "notes" TEXT,
    "projectId" TEXT NOT NULL,
    "vendorId" TEXT,
    "budgetLineId" TEXT,
    "createdById" TEXT NOT NULL,
    "approvedById" TEXT,
    "approvedAt" TIMESTAMP(3),

    CONSTRAINT "purchase_orders_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "timecards" (
    "id" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "workDate" TIMESTAMP(3) NOT NULL,
    "callTime" TIMESTAMP(3),
    "wrapTime" TIMESTAMP(3),
    "regularHours" DECIMAL(5,2) NOT NULL DEFAULT 0,
    "ot15Hours" DECIMAL(5,2) NOT NULL DEFAULT 0,
    "ot20Hours" DECIMAL(5,2) NOT NULL DEFAULT 0,
    "mealPenalty" DECIMAL(10,2) NOT NULL DEFAULT 0,
    "regularAmount" DECIMAL(12,2) NOT NULL DEFAULT 0,
    "ot15Amount" DECIMAL(12,2) NOT NULL DEFAULT 0,
    "ot20Amount" DECIMAL(12,2) NOT NULL DEFAULT 0,
    "totalAmount" DECIMAL(12,2) NOT NULL DEFAULT 0,
    "status" "TimecardStatus" NOT NULL DEFAULT 'DRAFT',
    "notes" TEXT,
    "projectCrewId" TEXT NOT NULL,
    "submittedById" TEXT,
    "submittedAt" TIMESTAMP(3),

    CONSTRAINT "timecards_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "call_sheets" (
    "id" TEXT NOT NULL,
    "dayNumber" INTEGER NOT NULL,
    "shootDate" TIMESTAMP(3) NOT NULL,
    "status" "CallSheetStatus" NOT NULL DEFAULT 'DRAFT',
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "generalCrewCall" TIMESTAMP(3),
    "firstShot" TIMESTAMP(3),
    "estimatedWrap" TIMESTAMP(3),
    "weatherHigh" TEXT,
    "weatherLow" TEXT,
    "weatherSummary" TEXT,
    "sunrise" TEXT,
    "sunset" TEXT,
    "nearestHospital" TEXT,
    "hospitalAddress" TEXT,
    "emergencyContact" TEXT,
    "emergencyPhone" TEXT,
    "notes" TEXT,
    "projectId" TEXT NOT NULL,

    CONSTRAINT "call_sheets_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "locations" (
    "id" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "address" TEXT,
    "city" TEXT,
    "state" TEXT,
    "zip" TEXT,
    "latitude" DECIMAL(10,8),
    "longitude" DECIMAL(11,8),
    "mapLink" TEXT,
    "contactName" TEXT,
    "contactPhone" TEXT,
    "contactEmail" TEXT,
    "parkingNotes" TEXT,
    "parkingAddress" TEXT,
    "loadingNotes" TEXT,
    "accessNotes" TEXT,
    "arrivalInstructions" TEXT,
    "notes" TEXT,
    "projectId" TEXT NOT NULL,

    CONSTRAINT "locations_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "call_sheet_locations" (
    "id" TEXT NOT NULL,
    "locationType" "LocationType" NOT NULL DEFAULT 'SHOOT',
    "callTime" TIMESTAMP(3),
    "notes" TEXT,
    "callSheetId" TEXT NOT NULL,
    "locationId" TEXT NOT NULL,

    CONSTRAINT "call_sheet_locations_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "schedule_events" (
    "id" TEXT NOT NULL,
    "sortOrder" INTEGER NOT NULL,
    "time" TIMESTAMP(3) NOT NULL,
    "endTime" TIMESTAMP(3),
    "description" TEXT NOT NULL,
    "scene" TEXT,
    "location" TEXT,
    "notes" TEXT,
    "eventType" "ScheduleEventType" NOT NULL DEFAULT 'GENERAL',
    "callSheetId" TEXT NOT NULL,

    CONSTRAINT "schedule_events_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "call_sheet_rsvps" (
    "id" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "status" "RSVPStatus" NOT NULL DEFAULT 'PENDING',
    "sentAt" TIMESTAMP(3),
    "viewedAt" TIMESTAMP(3),
    "confirmedAt" TIMESTAMP(3),
    "personalizedCallTime" TIMESTAMP(3),
    "personalizedNotes" TEXT,
    "callSheetId" TEXT NOT NULL,
    "projectCrewId" TEXT NOT NULL,

    CONSTRAINT "call_sheet_rsvps_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "organizations_slug_key" ON "organizations"("slug");

-- CreateIndex
CREATE UNIQUE INDEX "users_email_key" ON "users"("email");

-- CreateIndex
CREATE INDEX "users_organizationId_idx" ON "users"("organizationId");

-- CreateIndex
CREATE INDEX "projects_organizationId_idx" ON "projects"("organizationId");

-- CreateIndex
CREATE INDEX "projects_status_idx" ON "projects"("status");

-- CreateIndex
CREATE UNIQUE INDEX "projects_organizationId_jobNumber_key" ON "projects"("organizationId", "jobNumber");

-- CreateIndex
CREATE INDEX "budgets_projectId_idx" ON "budgets"("projectId");

-- CreateIndex
CREATE INDEX "budgets_status_idx" ON "budgets"("status");

-- CreateIndex
CREATE UNIQUE INDEX "budgets_projectId_version_key" ON "budgets"("projectId", "version");

-- CreateIndex
CREATE INDEX "budget_sections_budgetId_idx" ON "budget_sections"("budgetId");

-- CreateIndex
CREATE UNIQUE INDEX "budget_sections_budgetId_code_key" ON "budget_sections"("budgetId", "code");

-- CreateIndex
CREATE INDEX "budget_lines_sectionId_idx" ON "budget_lines"("sectionId");

-- CreateIndex
CREATE UNIQUE INDEX "budget_lines_sectionId_lineNumber_key" ON "budget_lines"("sectionId", "lineNumber");

-- CreateIndex
CREATE INDEX "budget_fringes_sectionId_idx" ON "budget_fringes"("sectionId");

-- CreateIndex
CREATE INDEX "crew_members_organizationId_idx" ON "crew_members"("organizationId");

-- CreateIndex
CREATE INDEX "crew_members_department_idx" ON "crew_members"("department");

-- CreateIndex
CREATE INDEX "crew_members_lastName_firstName_idx" ON "crew_members"("lastName", "firstName");

-- CreateIndex
CREATE INDEX "project_crew_projectId_idx" ON "project_crew"("projectId");

-- CreateIndex
CREATE INDEX "project_crew_crewMemberId_idx" ON "project_crew"("crewMemberId");

-- CreateIndex
CREATE INDEX "project_crew_budgetLineId_idx" ON "project_crew"("budgetLineId");

-- CreateIndex
CREATE INDEX "project_crew_department_idx" ON "project_crew"("department");

-- CreateIndex
CREATE INDEX "vendors_organizationId_idx" ON "vendors"("organizationId");

-- CreateIndex
CREATE INDEX "purchase_orders_projectId_idx" ON "purchase_orders"("projectId");

-- CreateIndex
CREATE INDEX "purchase_orders_budgetLineId_idx" ON "purchase_orders"("budgetLineId");

-- CreateIndex
CREATE INDEX "purchase_orders_status_idx" ON "purchase_orders"("status");

-- CreateIndex
CREATE UNIQUE INDEX "purchase_orders_projectId_poNumber_key" ON "purchase_orders"("projectId", "poNumber");

-- CreateIndex
CREATE INDEX "timecards_projectCrewId_idx" ON "timecards"("projectCrewId");

-- CreateIndex
CREATE INDEX "timecards_workDate_idx" ON "timecards"("workDate");

-- CreateIndex
CREATE INDEX "timecards_status_idx" ON "timecards"("status");

-- CreateIndex
CREATE INDEX "call_sheets_projectId_idx" ON "call_sheets"("projectId");

-- CreateIndex
CREATE INDEX "call_sheets_shootDate_idx" ON "call_sheets"("shootDate");

-- CreateIndex
CREATE UNIQUE INDEX "call_sheets_projectId_dayNumber_key" ON "call_sheets"("projectId", "dayNumber");

-- CreateIndex
CREATE INDEX "locations_projectId_idx" ON "locations"("projectId");

-- CreateIndex
CREATE UNIQUE INDEX "call_sheet_locations_callSheetId_locationId_key" ON "call_sheet_locations"("callSheetId", "locationId");

-- CreateIndex
CREATE INDEX "schedule_events_callSheetId_idx" ON "schedule_events"("callSheetId");

-- CreateIndex
CREATE INDEX "schedule_events_time_idx" ON "schedule_events"("time");

-- CreateIndex
CREATE INDEX "call_sheet_rsvps_callSheetId_idx" ON "call_sheet_rsvps"("callSheetId");

-- CreateIndex
CREATE INDEX "call_sheet_rsvps_projectCrewId_idx" ON "call_sheet_rsvps"("projectCrewId");

-- CreateIndex
CREATE INDEX "call_sheet_rsvps_status_idx" ON "call_sheet_rsvps"("status");

-- CreateIndex
CREATE UNIQUE INDEX "call_sheet_rsvps_callSheetId_projectCrewId_key" ON "call_sheet_rsvps"("callSheetId", "projectCrewId");

-- AddForeignKey
ALTER TABLE "users" ADD CONSTRAINT "users_organizationId_fkey" FOREIGN KEY ("organizationId") REFERENCES "organizations"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "projects" ADD CONSTRAINT "projects_organizationId_fkey" FOREIGN KEY ("organizationId") REFERENCES "organizations"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "budgets" ADD CONSTRAINT "budgets_projectId_fkey" FOREIGN KEY ("projectId") REFERENCES "projects"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "budgets" ADD CONSTRAINT "budgets_createdById_fkey" FOREIGN KEY ("createdById") REFERENCES "users"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "budget_sections" ADD CONSTRAINT "budget_sections_budgetId_fkey" FOREIGN KEY ("budgetId") REFERENCES "budgets"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "budget_lines" ADD CONSTRAINT "budget_lines_sectionId_fkey" FOREIGN KEY ("sectionId") REFERENCES "budget_sections"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "budget_fringes" ADD CONSTRAINT "budget_fringes_sectionId_fkey" FOREIGN KEY ("sectionId") REFERENCES "budget_sections"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "crew_members" ADD CONSTRAINT "crew_members_organizationId_fkey" FOREIGN KEY ("organizationId") REFERENCES "organizations"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "project_crew" ADD CONSTRAINT "project_crew_projectId_fkey" FOREIGN KEY ("projectId") REFERENCES "projects"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "project_crew" ADD CONSTRAINT "project_crew_crewMemberId_fkey" FOREIGN KEY ("crewMemberId") REFERENCES "crew_members"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "project_crew" ADD CONSTRAINT "project_crew_budgetLineId_fkey" FOREIGN KEY ("budgetLineId") REFERENCES "budget_lines"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "vendors" ADD CONSTRAINT "vendors_organizationId_fkey" FOREIGN KEY ("organizationId") REFERENCES "organizations"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "purchase_orders" ADD CONSTRAINT "purchase_orders_projectId_fkey" FOREIGN KEY ("projectId") REFERENCES "projects"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "purchase_orders" ADD CONSTRAINT "purchase_orders_vendorId_fkey" FOREIGN KEY ("vendorId") REFERENCES "vendors"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "purchase_orders" ADD CONSTRAINT "purchase_orders_budgetLineId_fkey" FOREIGN KEY ("budgetLineId") REFERENCES "budget_lines"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "purchase_orders" ADD CONSTRAINT "purchase_orders_createdById_fkey" FOREIGN KEY ("createdById") REFERENCES "users"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "purchase_orders" ADD CONSTRAINT "purchase_orders_approvedById_fkey" FOREIGN KEY ("approvedById") REFERENCES "users"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "timecards" ADD CONSTRAINT "timecards_projectCrewId_fkey" FOREIGN KEY ("projectCrewId") REFERENCES "project_crew"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "timecards" ADD CONSTRAINT "timecards_submittedById_fkey" FOREIGN KEY ("submittedById") REFERENCES "users"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "call_sheets" ADD CONSTRAINT "call_sheets_projectId_fkey" FOREIGN KEY ("projectId") REFERENCES "projects"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "locations" ADD CONSTRAINT "locations_projectId_fkey" FOREIGN KEY ("projectId") REFERENCES "projects"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "call_sheet_locations" ADD CONSTRAINT "call_sheet_locations_callSheetId_fkey" FOREIGN KEY ("callSheetId") REFERENCES "call_sheets"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "call_sheet_locations" ADD CONSTRAINT "call_sheet_locations_locationId_fkey" FOREIGN KEY ("locationId") REFERENCES "locations"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "schedule_events" ADD CONSTRAINT "schedule_events_callSheetId_fkey" FOREIGN KEY ("callSheetId") REFERENCES "call_sheets"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "call_sheet_rsvps" ADD CONSTRAINT "call_sheet_rsvps_callSheetId_fkey" FOREIGN KEY ("callSheetId") REFERENCES "call_sheets"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "call_sheet_rsvps" ADD CONSTRAINT "call_sheet_rsvps_projectCrewId_fkey" FOREIGN KEY ("projectCrewId") REFERENCES "project_crew"("id") ON DELETE CASCADE ON UPDATE CASCADE;
