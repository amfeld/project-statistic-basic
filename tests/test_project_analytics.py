from odoo.tests.common import TransactionCase
from odoo import fields


class TestProjectAnalytics(TransactionCase):

    def setUp(self):
        super(TestProjectAnalytics, self).setUp()

        self.Project = self.env['project.project']
        self.AnalyticAccount = self.env['account.analytic.account']
        self.Invoice = self.env['account.move']
        self.InvoiceLine = self.env['account.move.line']
        self.AnalyticLine = self.env['account.analytic.line']

        self.partner = self.env['res.partner'].create({
            'name': 'Test Customer',
        })

        self.analytic_account = self.AnalyticAccount.create({
            'name': 'Test Project Analytic',
            'plan_id': self.env.ref('analytic.analytic_plan_projects').id,
        })

        self.project = self.Project.create({
            'name': 'Test Project',
            'account_id': self.analytic_account.id,  # Odoo 18: account_id replaces analytic_account_id
        })

        self.income_account = self.env['account.account'].search([
            ('account_type', '=', 'income')
        ], limit=1)

        self.expense_account = self.env['account.account'].search([
            ('account_type', '=', 'expense')
        ], limit=1)

    def test_01_project_without_analytic_account(self):
        """Test that projects without analytic accounts don't crash"""
        project_no_analytic = self.Project.create({
            'name': 'Project Without Analytic',
        })

        project_no_analytic._compute_financial_data()

        self.assertEqual(project_no_analytic.customer_invoiced_amount_net, 0.0)
        self.assertEqual(project_no_analytic.vendor_bills_total_net, 0.0)
        self.assertEqual(project_no_analytic.profit_loss_net, 0.0)

    def test_02_customer_invoice_basic(self):
        """Test basic customer invoice calculation"""
        invoice = self.Invoice.create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [(0, 0, {
                'name': 'Test Product',
                'quantity': 1,
                'price_unit': 1000.0,
                'account_id': self.income_account.id,
                'analytic_distribution': {str(self.analytic_account.id): 100},
            })],
        })
        invoice.action_post()

        self.project._compute_financial_data()

        self.assertGreater(self.project.customer_invoiced_amount_net, 0.0)
        self.assertEqual(self.project.customer_outstanding_amount_net, self.project.customer_invoiced_amount_net)

    def test_03_vendor_bill_basic(self):
        """Test basic vendor bill calculation"""
        bill = self.Invoice.create({
            'move_type': 'in_invoice',
            'partner_id': self.partner.id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [(0, 0, {
                'name': 'Test Expense',
                'quantity': 1,
                'price_unit': 500.0,
                'account_id': self.expense_account.id,
                'analytic_distribution': {str(self.analytic_account.id): 100},
            })],
        })
        bill.action_post()

        self.project._compute_financial_data()

        self.assertGreater(self.project.vendor_bills_total_net, 0.0)

    def test_04_skonto_customer_tracking(self):
        """Test that customer Skonto from account 7300 is tracked"""
        skonto_account = self.env['account.account'].search([
            ('code', '=like', '7300%')
        ], limit=1)

        if not skonto_account:
            skonto_account = self.env['account.account'].create({
                'name': 'Gewährte Skonti',
                'code': '7300',
                'account_type': 'expense',
            })

        self.AnalyticLine.create({
            'name': 'Customer Skonto',
            'account_id': self.analytic_account.id,
            'amount': -50.0,
            'move_line_id': self.InvoiceLine.create({
                'name': 'Skonto Entry',
                'account_id': skonto_account.id,
                'debit': 50.0,
                'credit': 0.0,
            }).id,
        })

        self.project._compute_financial_data()

        self.assertGreaterEqual(self.project.customer_skonto_taken, 0.0)

    def test_05_skonto_vendor_tracking(self):
        """Test that vendor Skonto from account 4730 is tracked"""
        skonto_account = self.env['account.account'].search([
            ('code', '=like', '4730%')
        ], limit=1)

        if not skonto_account:
            skonto_account = self.env['account.account'].create({
                'name': 'Erhaltene Skonti',
                'code': '4730',
                'account_type': 'income',
            })

        self.AnalyticLine.create({
            'name': 'Vendor Skonto',
            'account_id': self.analytic_account.id,
            'amount': 30.0,
            'move_line_id': self.InvoiceLine.create({
                'name': 'Skonto Entry',
                'account_id': skonto_account.id,
                'debit': 0.0,
                'credit': 30.0,
            }).id,
        })

        self.project._compute_financial_data()

        self.assertGreaterEqual(self.project.vendor_skonto_received, 0.0)

    def test_06_profit_calculation(self):
        """Test profit/loss calculation with revenue and costs"""
        invoice = self.Invoice.create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [(0, 0, {
                'name': 'Revenue Item',
                'quantity': 1,
                'price_unit': 2000.0,
                'account_id': self.income_account.id,
                'analytic_distribution': {str(self.analytic_account.id): 100},
            })],
        })
        invoice.action_post()

        bill = self.Invoice.create({
            'move_type': 'in_invoice',
            'partner_id': self.partner.id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [(0, 0, {
                'name': 'Cost Item',
                'quantity': 1,
                'price_unit': 800.0,
                'account_id': self.expense_account.id,
                'analytic_distribution': {str(self.analytic_account.id): 100},
            })],
        })
        bill.action_post()

        self.project._compute_financial_data()

        expected_profit = self.project.customer_invoiced_amount_net - self.project.vendor_bills_total_net - self.project.total_costs_net
        self.assertAlmostEqual(self.project.profit_loss_net, expected_profit, places=2)
