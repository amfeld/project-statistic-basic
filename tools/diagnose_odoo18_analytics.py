#!/usr/bin/env python3
"""
Diagnostic script to check Odoo 18 analytic configuration.
Run this in Odoo shell to understand your analytic setup.

Usage:
    odoo-bin shell -d your_database --config=/path/to/odoo.conf

Then run:
    exec(open('/home/user/projekt-statistik-v3/tools/diagnose_odoo18_analytics.py').read())
"""

import logging
_logger = logging.getLogger(__name__)

print("=" * 80)
print("ODOO 18 ANALYTIC CONFIGURATION DIAGNOSTIC")
print("=" * 80)
print()

# 1. Check for Analytic Plans
print("1. Checking Analytic Plans...")
print("-" * 80)
try:
    AnalyticPlan = env['account.analytic.plan']
    plans = AnalyticPlan.search([])
    print(f"   Found {len(plans)} analytic plan(s):")
    for plan in plans:
        print(f"   - ID: {plan.id}, Name: {plan.name}, External ID: {plan.get_external_id().get(plan.id, 'N/A')}")
    print()
except Exception as e:
    print(f"   ERROR: Could not load analytic plans: {e}")
    print()

# 2. Check for Projects Analytic Plan External ID
print("2. Checking 'Projects' Analytic Plan External ID...")
print("-" * 80)
try:
    # Try the standard external ID
    project_plan = env.ref('analytic.analytic_plan_projects', raise_if_not_found=False)
    if project_plan:
        print(f"   ✓ Found: analytic.analytic_plan_projects")
        print(f"     ID: {project_plan.id}, Name: {project_plan.name}")
    else:
        print(f"   ✗ NOT FOUND: analytic.analytic_plan_projects")
        print(f"   Searching for plans with 'project' in name...")
        project_plans = AnalyticPlan.search([('name', 'ilike', 'project')])
        if project_plans:
            for plan in project_plans:
                ext_id = plan.get_external_id().get(plan.id, 'N/A')
                print(f"   - ID: {plan.id}, Name: {plan.name}, External ID: {ext_id}")
        else:
            print(f"   No plans with 'project' in name found.")
    print()
except Exception as e:
    print(f"   ERROR: {e}")
    print()

# 3. Check project.project fields
print("3. Checking project.project fields for analytic accounts...")
print("-" * 80)
try:
    Project = env['project.project']

    # Check if analytic_account_id exists
    if hasattr(Project, 'analytic_account_id'):
        print(f"   ✓ Field 'analytic_account_id' EXISTS (unexpected in v18!)")
    else:
        print(f"   ✗ Field 'analytic_account_id' DOES NOT EXIST (expected in v18)")

    # Check if account_id exists
    if hasattr(Project, 'account_id'):
        print(f"   ✓ Field 'account_id' EXISTS")
        field_info = Project._fields.get('account_id')
        if field_info:
            print(f"     Type: {field_info.type}, Relation: {getattr(field_info, 'comodel_name', 'N/A')}")
    else:
        print(f"   ✗ Field 'account_id' DOES NOT EXIST")

    print()
except Exception as e:
    print(f"   ERROR: {e}")
    print()

# 4. Check sample project
print("4. Checking sample project...")
print("-" * 80)
try:
    projects = env['project.project'].search([], limit=1)
    if projects:
        project = projects[0]
        print(f"   Project: {project.name} (ID: {project.id})")

        # Check analytic_account_id
        if hasattr(project, 'analytic_account_id'):
            print(f"   analytic_account_id: {project.analytic_account_id}")
        else:
            print(f"   analytic_account_id: FIELD NOT FOUND")

        # Check account_id
        if hasattr(project, 'account_id'):
            print(f"   account_id: {project.account_id}")
            if project.account_id:
                print(f"     - Account Name: {project.account_id.name}")
                print(f"     - Account ID: {project.account_id.id}")
                if hasattr(project.account_id, 'plan_id'):
                    print(f"     - Plan: {project.account_id.plan_id.name if project.account_id.plan_id else 'None'}")
        else:
            print(f"   account_id: FIELD NOT FOUND")
    else:
        print(f"   No projects found in database")
    print()
except Exception as e:
    print(f"   ERROR: {e}")
    print()

# 5. Check analytic_distribution structure
print("5. Checking analytic_distribution structure...")
print("-" * 80)
try:
    MoveLine = env['account.move.line']
    lines_with_dist = MoveLine.search([('analytic_distribution', '!=', False)], limit=5)
    if lines_with_dist:
        print(f"   Found {len(lines_with_dist)} sample line(s) with analytic_distribution:")
        for line in lines_with_dist:
            print(f"   - Move: {line.move_id.name}, Distribution: {line.analytic_distribution}")
    else:
        print(f"   No account.move.line records with analytic_distribution found")
    print()
except Exception as e:
    print(f"   ERROR: {e}")
    print()

# 6. Recommendations
print("=" * 80)
print("RECOMMENDATIONS:")
print("=" * 80)
if not project_plan:
    print("⚠ The external ID 'analytic.analytic_plan_projects' was not found!")
    print("  → You need to update the code to use the correct external ID or plan lookup")
    print()

if not hasattr(Project, 'analytic_account_id'):
    print("⚠ Field 'analytic_account_id' does not exist on project.project!")
    print("  → Remove all references to 'project.analytic_account_id' from your code")
    print("  → Use 'project.account_id' instead")
    print()

print("✓ Consider using @api.depends() with proper field dependencies instead of empty depends")
print("✓ Consider using store=False for most fields and compute them on-demand")
print()

print("=" * 80)
print("DIAGNOSTIC COMPLETE")
print("=" * 80)
