# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import Command
from odoo.tests import Form, HttpCase, new_test_user, tagged
from odoo.exceptions import UserError

from .common import TestSaleProjectCommon


@tagged('post_install', '-at_install')
class TestSaleProject(HttpCase, TestSaleProjectCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.project_plan, _other_plans = cls.env['account.analytic.plan']._get_all_plans()
        cls.analytic_plan = cls.env['account.analytic.plan'].create({
            'name': 'Plan Test',
        })
        cls.analytic_account_sale = cls.env['account.analytic.account'].create({
            'name': 'Project for selling timesheet - AA',
            'plan_id': cls.analytic_plan.id,
            'code': 'AA-2030'
        })
        cls.analytic_account = cls.env['account.analytic.account'].create({
            'name': 'Main AA of Project',
            'plan_id': cls.project_plan.id,
        })

        # Create projects
        cls.project_global = cls.env['project.project'].create({
            'name': 'Global Project',
            'account_id': cls.analytic_account.id,
            cls.analytic_plan._column_name(): cls.analytic_account_sale.id,
            'allow_billable': True,
        })
        cls.project_template = cls.env['project.project'].create({
            'name': 'Project TEMPLATE for services',
        })
        cls.project_template_state = cls.env['project.task.type'].create({
            'name': 'Only stage in project template',
            'sequence': 1,
            'project_ids': [(4, cls.project_template.id)]
        })

        # Create service products
        uom_hour = cls.env.ref('uom.product_uom_hour')

        cls.product_order_service1 = cls.env['product.product'].create({
            'name': "Service Ordered, create no task",
            'standard_price': 11,
            'list_price': 13,
            'type': 'service',
            'invoice_policy': 'order',
            'uom_id': uom_hour.id,
            'uom_po_id': uom_hour.id,
            'default_code': 'SERV-ORDERED1',
            'service_tracking': 'no',
            'project_id': False,
        })
        cls.product_order_service2 = cls.env['product.product'].create({
            'name': "Service Ordered, create task in global project",
            'standard_price': 30,
            'list_price': 90,
            'type': 'service',
            'invoice_policy': 'order',
            'uom_id': uom_hour.id,
            'uom_po_id': uom_hour.id,
            'default_code': 'SERV-ORDERED2',
            'service_tracking': 'task_global_project',
            'project_id': cls.project_global.id,
        })
        cls.product_order_service3 = cls.env['product.product'].create({
            'name': "Service Ordered, create task in new project",
            'standard_price': 10,
            'list_price': 20,
            'type': 'service',
            'invoice_policy': 'order',
            'uom_id': uom_hour.id,
            'uom_po_id': uom_hour.id,
            'default_code': 'SERV-ORDERED3',
            'service_tracking': 'task_in_project',
            'project_id': False,  # will create a project
        })
        cls.product_order_service4 = cls.env['product.product'].create({
            'name': "Service Ordered, create project only",
            'standard_price': 15,
            'list_price': 30,
            'type': 'service',
            'invoice_policy': 'order',
            'uom_id': uom_hour.id,
            'uom_po_id': uom_hour.id,
            'default_code': 'SERV-ORDERED4',
            'service_tracking': 'project_only',
            'project_id': False,
        })

        # Create partner
        cls.partner = cls.env['res.partner'].create({'name': "Mur en béton"})

        project = cls.env['project.project'].create({
            'name': 'Test History Project',
            'type_ids': [Command.create({'name': 'To Do'})],
            'allow_billable': True
        })

        cls.env['project.task'].create({
            'name': 'Test History Task',
            'stage_id': project.type_ids[0].id,
            'project_id': project.id,
        })

        # Create additional analytic plans at setup to avoid adding fields in project.project between tests
        cls.analytic_plan_1 = cls.env['account.analytic.plan'].create({'name': 'Sale Project Plan 1'})
        cls.analytic_plan_2 = cls.env['account.analytic.plan'].create({'name': 'Sale Project Plan 2'})

    def test_task_create_sol_ui(self):
        self.start_tour('/odoo', 'task_create_sol_tour', login='admin')

    def test_project_create_sol_ui(self):
        self.product_order_service5 = self.env['product.product'].create({
            'name': 'New Sale order line',
            'type': 'service',
            'invoice_policy': 'delivery',
        })
        self.start_tour('/odoo', 'project_create_sol_tour', login='admin')

    def test_sale_order_with_project_task(self):
        SaleOrder = self.env['sale.order'].with_context(tracking_disable=True)
        SaleOrderLine = self.env['sale.order.line'].with_context(tracking_disable=True)

        sale_order = SaleOrder.create({
            'partner_id': self.partner.id,
            'partner_invoice_id': self.partner.id,
            'partner_shipping_id': self.partner.id,
        })
        so_line_order_no_task = SaleOrderLine.create({
            'product_id': self.product_order_service1.id,
            'product_uom_qty': 10,
            'order_id': sale_order.id,
        })

        so_line_order_task_in_global = SaleOrderLine.create({
            'name': f"{self.product_order_service2.name}\n[TEST1]\nGlobal project",
            'product_id': self.product_order_service2.id,
            'product_uom_qty': 10,
            'order_id': sale_order.id,
        })

        self.product_order_service3.description_sale = "Task in New Project"
        so_line_order_new_task_new_project = SaleOrderLine.create({
            'name': f"{self.product_order_service3.display_name}\n[TEST2]\nNew project",
            'product_id': self.product_order_service3.id,
            'product_uom_qty': 10,
            'order_id': sale_order.id,
        })
        so_line_order_new_task_new_project2 = SaleOrderLine.create({
            'product_id': self.product_order_service3.id,
            'product_uom_qty': 10,
            'order_id': sale_order.id,
        })

        so_line_order_only_project = SaleOrderLine.create({
            'product_id': self.product_order_service4.id,
            'product_uom_qty': 10,
            'order_id': sale_order.id,
        })
        sale_order.action_confirm()

        # service_tracking 'no'
        self.assertFalse(so_line_order_no_task.project_id, "The project should not be linked to no task product")
        self.assertFalse(so_line_order_no_task.task_id, "The task should not be linked to no task product")
        # service_tracking 'task_global_project'
        self.assertFalse(so_line_order_task_in_global.project_id, "Only task should be created, project should not be linked")
        self.assertEqual(self.project_global.tasks.sale_line_id, so_line_order_task_in_global, "Global project's task should be linked to so line")
        self.assertEqual(
            so_line_order_task_in_global.task_id.name,
            f"{sale_order.name} - [TEST1]",
            "Task name in global project should include SO name & partial line description",
        )
        self.assertEqual(
            str(so_line_order_task_in_global.task_id.description),
            '<p>Global project</p>',
        )
        #  service_tracking 'task_in_project'
        self.assertTrue(so_line_order_new_task_new_project.project_id, "Sales order line should be linked to newly created project")
        self.assertTrue(so_line_order_new_task_new_project.task_id, "Sales order line should be linked to newly created task")
        self.assertEqual(
            so_line_order_new_task_new_project.task_id.name,
            "[TEST2]",
            "Task name in new project should only include partial line description",
        )
        self.assertEqual(
            str(so_line_order_new_task_new_project.task_id.description),
            '<p>New project</p>',
        )
        self.assertEqual(
            so_line_order_new_task_new_project2.task_id.name,
            self.product_order_service3.display_name,
            "Task name created from a SOL with default description should use the product name",
        )
        # service_tracking 'project_only'
        self.assertFalse(so_line_order_only_project.task_id, "Task should not be created")
        self.assertTrue(so_line_order_only_project.project_id, "Sales order line should be linked to newly created project")

        self.assertEqual(self.env['sale.order'].search([('tasks_ids', 'in', so_line_order_new_task_new_project.task_id.ids)]), sale_order)
        self.assertEqual(self.env['sale.order'].search([('tasks_ids', '=', so_line_order_new_task_new_project.task_id.id)]), sale_order)
        self.assertEqual(self.env['sale.order'].search([('tasks_ids.project_id', '=', so_line_order_new_task_new_project.project_id.id)]), sale_order)

        self.assertEqual(self.project_global._get_sale_order_items(), self.project_global.sale_line_id | self.project_global.tasks.sale_line_id, 'The _get_sale_order_items should returns all the SOLs linked to the project and its active tasks.')

        sale_order_2 = SaleOrder.create({
            'partner_id': self.partner.id,
            'partner_invoice_id': self.partner.id,
            'partner_shipping_id': self.partner.id,
        })
        sale_line_1_order_2 = SaleOrderLine.create({
            'product_id': self.product_order_service1.id,
            'product_uom_qty': 10,
            'product_uom': self.product_order_service1.uom_id.id,
            'price_unit': self.product_order_service1.list_price,
            'order_id': sale_order_2.id,
        })
        section_sale_line_order_2 = SaleOrderLine.create({
            'display_type': 'line_section',
            'name': 'Test Section',
            'order_id': sale_order_2.id,
        })
        note_sale_line_order_2 = SaleOrderLine.create({
            'display_type': 'line_note',
            'name': 'Test Note',
            'order_id': sale_order_2.id,
        })
        sale_order_2.action_confirm()
        task = self.env['project.task'].create({
            'name': 'Task',
            'sale_line_id': sale_line_1_order_2.id,
            'project_id': self.project_global.id,
        })
        self.assertEqual(task.sale_line_id, sale_line_1_order_2)
        self.assertIn(task.sale_line_id, self.project_global._get_sale_order_items())
        self.assertEqual(self.project_global._get_sale_orders(), sale_order | sale_order_2)

        sale_order_lines = sale_order.order_line + sale_line_1_order_2  # exclude the Section and Note Sales Order Items
        sale_items_data = self.project_global.get_sale_items_data(limit=5, with_action=False, section_id='billable_fixed')

        expected_sale_line_dict = {
            sol_read['id']: sol_read
            for sol_read in sale_order_lines._read_format(
                ['name', 'product_uom_qty', 'qty_delivered', 'qty_invoiced', 'product_uom', 'product_id'])
        }
        actual_sol_ids = []
        for line in sale_items_data['sol_items']:
            sol_id = line['id']
            actual_sol_ids.append(sol_id)
            self.assertIn(sol_id, expected_sale_line_dict)
            self.assertDictEqual(line, expected_sale_line_dict[sol_id])
        self.assertNotIn(section_sale_line_order_2.id, actual_sol_ids, 'The section Sales Order Item should not be takken into account in the Sales section of project.')
        self.assertNotIn(note_sale_line_order_2.id, actual_sol_ids, 'The note Sales Order Item should not be takken into account in the Sales section of project.')

    def test_sol_product_type_update(self):
        sale_order = self.env['sale.order'].with_context(tracking_disable=True).create({
            'partner_id': self.partner.id,
            'partner_invoice_id': self.partner.id,
            'partner_shipping_id': self.partner.id,
        })
        self.product_order_service3.type = 'consu'
        sale_order_line = self.env['sale.order.line'].create({
            'order_id': sale_order.id,
            'name': self.product_order_service3.name,
            'product_id': self.product_order_service3.id,
            'product_uom_qty': 5,
            'product_uom': self.product_order_service3.uom_id.id,
            'price_unit': self.product_order_service3.list_price
        })
        self.assertFalse(sale_order_line.is_service, "As the product is consumable, the SOL should not be a service")

        self.product_order_service3.type = 'service'
        self.assertTrue(sale_order_line.is_service, "As the product is a service, the SOL should be a service")

    def test_cancel_so_linked_to_project(self):
        """ Test that cancelling a SO linked to a project will not raise an error """
        # Ensure user don't have edit right access to the project
        group_sale_manager = self.env.ref('sales_team.group_sale_manager')
        group_project_user = self.env.ref('project.group_project_user')
        self.env.user.write({'groups_id': [(6, 0, [group_sale_manager.id, group_project_user.id])]})
        sale_order = self.env['sale.order'].with_context(tracking_disable=True).create({
            'partner_id': self.partner.id,
            'partner_invoice_id': self.partner.id,
            'partner_shipping_id': self.partner.id,
        })
        sale_order_line = self.env['sale.order.line'].create({
            'name': self.product_order_service2.name,
            'product_id': self.product_order_service2.id,
            'order_id': sale_order.id,
        })
        self.assertFalse(self.project_global.tasks.sale_line_id, "The project tasks should not be linked to the SOL")

        sale_order.action_confirm()
        self.assertEqual(self.project_global.tasks.sale_line_id.id, sale_order_line.id, "The project tasks should be linked to the SOL from the SO")
        #use of sudo() since the env.user does not have the access right to edit projects.
        self.project_global.sudo().sale_line_id = sale_order_line
        sale_order.with_context({'disable_cancel_warning': True}).action_cancel()

    def test_links_with_sale_order_line(self):
        """
            Check that the subtasks are linked to the correct sale order line.
        """
        product_A, product_B, product_C = self.env['product.product'].create([
            {
                'name': 'product_A',
                'lst_price': 100.0,
                'type': 'service',
                'service_tracking': 'task_in_project',
            },
            {
                'name': 'product_B',
                'lst_price': 100.0,
                'type': 'service',
                'service_tracking': 'task_in_project',
            },
            {
                'name': 'product_C',
                'lst_price': 100.0,
                'type': 'service',
                'service_tracking': 'task_in_project',
            },
        ])
        sale_order_first, sale_order_second = self.env['sale.order'].create([
            {
                'partner_id': self.partner.id,
                'order_line': [
                    Command.create({'product_id': product_A.id}),
                    Command.create({'product_id': product_B.id}),
                ]
            },
            {
                'partner_id': self.partner.id,
                'order_line': [
                    Command.create({'product_id': product_C.id}),
                ]
            }
        ])
        (sale_order_first + sale_order_second).action_confirm()

        sale_order_line_A = sale_order_first.order_line.filtered(lambda sol: sol.product_id == product_A)
        sale_order_line_B = sale_order_first.order_line - sale_order_line_A
        sale_order_line_C = sale_order_second.order_line

        project_first = sale_order_first.project_ids
        project_second = sale_order_second.project_ids

        task_A = sale_order_first.tasks_ids.filtered(lambda task: task.sale_line_id == sale_order_line_A)
        task_B = sale_order_first.tasks_ids - task_A
        task_C = sale_order_second.tasks_ids

        # [CASE 1] Parent in the same project --> use parent's sale order line
        task_A.write({
            'child_ids': [
                Command.create({'name': 'Sub A in first project', 'project_id': project_first.id}),
            ]
        })
        task_B.write({
            'child_ids': [
                Command.create({'name': 'Sub B in first project', 'project_id': project_first.id}),
            ]
        })
        task_C.write({
            'child_ids': [
                Command.create({'name': 'Sub C in second project', 'project_id': project_second.id}),
            ]
        })
        self.assertEqual(task_A.child_ids.sale_line_id, sale_order_line_A)
        self.assertEqual(task_B.child_ids.sale_line_id, sale_order_line_B)
        self.assertEqual(task_C.child_ids.sale_line_id, sale_order_line_C)

        # [CASE 2] Parent in an other project --> use parent's sale_order line
        task_B.write({
            'child_ids': [
                Command.create({'name': 'Sub B in second project', 'project_id': project_second.id}),
            ]
        })
        sub_B_second = task_B.child_ids.filtered(lambda sub: sub.name == 'Sub B in second project')
        self.assertEqual(sub_B_second.sale_line_id, sale_order_line_B)

        # [CASE 3] Without parent --> use sale order line of the project
        task_D = self.env['project.task'].create({
            'name': 'Task D',
            'project_id': project_first.id,
        })
        self.assertEqual(task_D.sale_line_id, project_first.sale_line_id)

    def test_compute_project_and_task_button(self):
        """
            Ensures that when a sale order has at least one sol with a service product whose service-policy is either delivered on milestone or ordered prepaid, then the
            show_create_project_button is set to True. If the sale order also has one project linked to it, then the show_project_and_task_button should be True, and the show_create_button
            should be updated to False
        """
        sale_order_1 = self.env['sale.order'].with_context(tracking_disable=True).create({
            'partner_id': self.partner.id,
            'partner_invoice_id': self.partner.id,
            'partner_shipping_id': self.partner.id,
        })
        sale_order_2 = sale_order_1.copy()
        sale_order_3 = sale_order_1.copy()
        (sale_order_1 | sale_order_2 | sale_order_3).action_confirm()
        # consumable product, manual service product
        self.env['sale.order.line'].create([{
            'product_id': self.product_consumable.id,
            'order_id': sale_order_1.id,
        }])
        self.assertFalse(sale_order_1.show_create_project_button, "There is no service product with one of the correct service_policy on the sale order, the button should be hidden")
        self.assertFalse(sale_order_1.show_project_button, "There is no project on the sale order, the button should be hidden")
        self.assertFalse(sale_order_1.show_task_button, "There is no project on the sale order, the button should be hidden")
        # add a milestone product
        line_delivered_milestone = self.env['sale.order.line'].create({
            'product_id': self.product_service_delivered_milestone.id,
            'order_id': sale_order_1.id,
        })
        # the user does not have project creation right
        user_wrong_group = new_test_user(self.env, groups='sales_team.group_sale_manager,project.group_project_user', login='wendy', name='wendy')
        sale_order_1.with_user(user_wrong_group)._compute_show_project_and_task_button()
        self.assertFalse(sale_order_1.show_create_project_button, "The user does not have the right to create a new project, the button should be hidden")
        self.assertFalse(sale_order_1.show_project_button, "There is no project on the sale order, the button should be hidden")
        self.assertFalse(sale_order_1.show_task_button, "There is no project on the sale order, the button should be hidden")
        # the user has project creation right
        sale_order_1._compute_show_project_and_task_button()
        self.assertTrue(sale_order_1.show_create_project_button, "There is a product service with the service_policy set on 'delivered on milestone' on the sale order, the button should be displayed")
        self.assertFalse(sale_order_1.show_project_button, "There is no project on the sale order, the button should be hidden")
        self.assertFalse(sale_order_1.show_task_button, "There is no project on the sale order, the button should be hidden")
        # add a project to the SO
        line_delivered_milestone.project_id = self.project_global
        sale_order_1._compute_show_project_and_task_button()
        self.assertFalse(sale_order_1.show_create_project_button, "There is a product service with the service_policy set on 'delivered on milestone' and a project on the sale order, the button should be hidden")
        self.assertTrue(sale_order_1.show_project_button, "There is a product service with the service_policy set on 'delivered on milestone' and a project on the sale order, the button should be displayed")
        self.assertTrue(sale_order_1.show_task_button, "There is a product service with the service_policy set on 'delivered on milestone' and a project on the sale order, the button should be displayed")

        # add an ordered_prepaid service product
        line_prepaid = self.env['sale.order.line'].create({
            'product_id': self.product_service_ordered_prepaid.id,
            'order_id': sale_order_2.id,
        })
        sale_order_2._compute_show_project_and_task_button()
        self.assertTrue(sale_order_2.show_create_project_button, "There is a product service with the service_policy set on 'ordered_prepaid' on the sale order, the button should be displayed")
        self.assertFalse(sale_order_2.show_project_button, "There is no project on the sale order, the button should be hidden")
        self.assertFalse(sale_order_2.show_task_button, "There is no project on the sale order, the button should be hidden")
        # create a new task, whose sale order item is a sol of the SO
        self.env['project.task'].create({
            'name': 'Test Task',
            'project_id': self.project_global.id,
            'sale_line_id': line_prepaid.id,
        })
        sale_order_2._compute_tasks_ids()
        sale_order_2._compute_show_project_and_task_button()
        self.assertTrue(sale_order_2.show_create_project_button, "There is a product service with the service_policy set on 'ordered_prepaid' on the sale order, the button should be displayed")
        self.assertFalse(sale_order_2.show_project_button, "There is no project on the sale order, the button should be hidden")
        self.assertTrue(sale_order_2.show_task_button, "There is no project on the sale order and there is a task whose sale item is one of the sale_line of the SO, the button should be displayed")

        # add a manual service product
        self.env['sale.order.line'].create({
            'product_id': self.product_service_delivered_manual.id,
            'order_id': sale_order_3.id,
        })
        sale_order_3._compute_show_project_and_task_button()
        self.assertTrue(sale_order_3.show_create_project_button, "There is a product service with the service_policy set on 'manual' on the sale order, the button should be displayed")
        self.assertFalse(sale_order_3.show_project_button, "There is no project on the sale order, the button should be hidden")
        self.assertFalse(sale_order_3.show_task_button, "There is no project on the sale order, the button should be hidden")

    def test_create_task_from_template_line(self):
        """
        When we add an SOL from a template that is a service that has a service_policy that will generate a task,
        even if default_task_id is present in the context, a new task should be created when confirming the SO.
        """
        default_task = self.env['project.task'].with_context(tracking_disable=True).create({
            'name': 'Task',
            'project_id': self.project_global.id
        })
        sale_order = self.env['sale.order'].with_context(tracking_disable=True, default_task_id=default_task.id).create({
            'partner_id': self.partner.id,
        })
        quotation_template = self.env['sale.order.template'].create({
            'name': 'Test quotation',
        })
        quotation_template.write({
            'sale_order_template_line_ids': [
                Command.set(
                    self.env['sale.order.template.line'].create([{
                        'name': self.product_order_service2.display_name,
                        'sale_order_template_id': quotation_template.id,
                        'product_id': self.product_order_service2.id,
                        'product_uom_id': self.product_order_service2.uom_id.id,
                    }, {
                        'name': self.product_order_service3.display_name,
                        'sale_order_template_id': quotation_template.id,
                        'product_id': self.product_order_service3.id,
                        'product_uom_id': self.product_order_service3.uom_id.id,
                    }]).ids
                )
            ]
        })
        sale_order.with_context(default_task_id=default_task.id).write({
            'sale_order_template_id': quotation_template.id,
        })
        sale_order.with_context(default_task_id=default_task.id)._onchange_sale_order_template_id()
        self.assertFalse(sale_order.order_line.mapped('task_id'),
                         "SOL should have no related tasks, because they are from services that generates a task")
        sale_order.action_confirm()
        self.assertEqual(sale_order.tasks_count, 2, "SO should have 2 related tasks")
        self.assertNotIn(default_task, sale_order.tasks_ids, "SO should link to the default task from the context")

    def test_project_creation_on_so_confirm_with_account(self):
        # Ensures that the company of the account of the SO is propagated to the project.
        sale_order = self.env['sale.order'].with_context(tracking_disable=True).create({
            'partner_id': self.partner.id,
            'partner_invoice_id': self.partner.id,
            'partner_shipping_id': self.partner.id,
        })
        analytic_account_company = self.env['account.analytic.account'].create({
            'name': 'Account with company',
            'plan_id': self.analytic_plan.id,
            'company_id': self.env.company.id,
        })
        analytic_plan_name = self.analytic_plan._column_name()
        project = self.env['project.project'].create({
            'name': 'SO Project',
            analytic_plan_name: analytic_account_company.id,
        })
        sale_order.project_id = project
        self.env['sale.order.line'].create({
            'name': self.product_order_service2.name,
            'product_id': self.product_order_service3.id,
            'order_id': sale_order.id,
        })
        self.assertTrue(sale_order.project_id[analytic_plan_name], "The SO should have an analytic account before it is confirmed.")
        sale_order.action_confirm()
        self.assertEqual(self.env.company, sale_order.project_id[analytic_plan_name].company_id, "The company of the account should be the company of the SO.")
        self.assertEqual(sale_order.project_id[analytic_plan_name], sale_order.project_ids[analytic_plan_name], "The project created for the SO and the project of the SO should have the same account.")
        self.assertEqual(self.env.company, sale_order.project_ids.company_id, "The project created for the SO should have the same company as its account.")

    def test_project_creation_on_so_with_manual_analytic(self):
        """ Tests that the manually added analytic account (of a plan other than projects) and the project account
            created when SO is confirmed are both still in the line after confirmation.
        """
        analytic_distribution_manual = {str(self.analytic_account_sale.id): 100}
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'partner_invoice_id': self.partner.id,
            'partner_shipping_id': self.partner.id,
            'order_line': [
                Command.create({
                    'product_id': self.product_order_service3.id,
                    'analytic_distribution': analytic_distribution_manual,
                }),
            ],
        })
        self.assertEqual(sale_order.order_line.analytic_distribution, analytic_distribution_manual)
        sale_order.action_confirm()
        expected_analytic_distribution = {f"{self.analytic_account_sale.id},{sale_order.order_line.project_id.account_id.id}": 100}
        self.assertEqual(sale_order.order_line.analytic_distribution, expected_analytic_distribution)

    def test_project_on_sol_with_analytic_distribution_model(self):
        """ If a line has a distribution coming from an analytic distribution model, and the sale order has a project,
            both the project account and the accounts from the ADM should still be in the line after confirmation.
            The Project account should appear on all lines if there are several Analytic Distribution Models applying.
        """
        # We create one distribution model with two accounts in one line, based on product
        # and a second model with a different plan, based on partner
        analytic_account_1 = self.env['account.analytic.account'].create({
            'name': 'Analytic Account - Plan 1',
            'plan_id': self.analytic_plan_1.id,
        })
        analytic_account_2 = self.env['account.analytic.account'].create({
            'name': 'Analytic Account - Plan 2',
            'plan_id': self.analytic_plan_2.id,
        })
        distribution_model_product = self.env['account.analytic.distribution.model'].create({
            'product_id': self.product_a.id,
            'analytic_distribution': {','.join([str(analytic_account_1.id), str(analytic_account_2.id)]): 100},
            'company_id': self.company.id,
        })
        distribution_model_partner = self.env['account.analytic.distribution.model'].create({
            'partner_id': self.partner.id,
            'analytic_distribution': {self.analytic_account_sale.id: 100},
            'company_id': self.company.id,
        })

        project = self.env['project.project'].create({
            'name': 'Project Test',
            'account_id': self.analytic_account.id,
            'allow_billable': True,
        })
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'partner_invoice_id': self.partner.id,
            'partner_shipping_id': self.partner.id,
            'project_id': project.id,
            'order_line': [
                Command.create({'product_id': self.product_a.id}),
            ],
        })

        expected_analytic_distribution = {
            f"{analytic_account_1.id},{analytic_account_2.id},{project.account_id.id}": 100,
            f"{self.analytic_account_sale.id},{project.account_id.id}": 100,
        }
        self.assertEqual(sale_order.order_line.analytic_distribution, expected_analytic_distribution)

        # If the project is removed from the SO, only the product's analytic distribution is still in the line
        sale_order.project_id = None
        self.assertEqual(
            sale_order.order_line.analytic_distribution,
            distribution_model_product.analytic_distribution | distribution_model_partner.analytic_distribution
        )

        # If project is added and the SO is confirmed, both analytic distributions are in the line
        sale_order.project_id = project
        sale_order.action_confirm()
        self.assertEqual(sale_order.order_line.analytic_distribution, expected_analytic_distribution)

    def test_include_archived_projects_in_stat_btn_related_view(self):
        """Checks if the project stat-button action includes both archived and active projects."""
        # Setup
        project_A = self.env['project.project'].create({'name': 'Project_A'})
        project_B = self.env['project.project'].create({'name': 'Project_B'})

        product_A = self.env['product.product'].create({
            'name': 'product A',
            'list_price': 1.0,
            'type': 'service',
            'service_tracking': 'task_global_project',
            'project_id':project_A.id,
        })
        product_B = self.env['product.product'].create({
            'name': 'product B',
            'list_price': 2.0,
            'type': 'service',
            'service_tracking': 'task_global_project',
            'project_id':project_B.id,
        })

        sale_order = self.env['sale.order'].with_context(tracking_disable=True).create({
            'partner_id': self.partner.id,
            'partner_invoice_id': self.partner.id,
            'partner_shipping_id': self.partner.id,
        })

        SaleOrderLine = self.env['sale.order.line'].with_context(tracking_disable=True)
        SaleOrderLine.create({
            'name': product_A.name,
            'product_id': product_A.id,
            'product_uom_qty': 10,
            'price_unit': product_A.list_price,
            'order_id': sale_order.id,
        })
        SaleOrderLine.create({
            'name': product_B.name,
            'product_id': product_B.id,
            'product_uom_qty': 10,
            'price_unit': product_B.list_price,
            'order_id': sale_order.id,
        })

        def get_project_ids_from_action_domain(action):
            for el in action['domain']:
                if len(el) == 3 and el[0] == 'id' and el[1] == 'in':
                    domain_proj_ids = el[2]
                    break
            else:
                raise Exception(f"Couldn't find projects ids in the following action domain: {action['domain']}")
            return domain_proj_ids

        # Check if button action includes both projects BEFORE archivization
        action = sale_order.action_view_project_ids()
        self.assertEqual(len(get_project_ids_from_action_domain(action)), 2, "Domain should contain 2 projects.")

        # Check if button action includes both projects AFTER archivization
        project_B.write({'active': False})
        action = sale_order.action_view_project_ids()
        self.assertEqual(len(get_project_ids_from_action_domain(action)), 2, "Domain should contain 2 projects. (one archived, one not)")

    def test_sale_order_line_view_form_editable(self):
        """ Check the behavior of the form view editable of `sale.order.line` introduced in that module

            Test Case:
            =========
            1. create SO to use it as default_order_id when the SOL will be created by the editable form
            2. open form view of `sale.order.line` to create and edit a SOL
            3. create on the fly a product and check default values of that product
                3.1. type should be "service"
                3.2. service_policy should be "ordered_prepaid" (Prepaid/Fixed Price)
            4. check if the qty_delivered is editable
                4.1. if sale_timesheet is installed then the field should be readonly otherwise editable
            5. change the product set on the SOL form view to service product with invoice policy to 'delivered_milestones'
            6. check if the qty_delivered field is readonly
            7. change the product set on the SOL form view to service product with invoice policy to 'ordered_prepaid'
            8. check if the qty_delivered is editable
                8.1. if sale_timesheet is installed then the field should be readonly otherwise editable
            9. change the product set on the SOL form view to service product with invoice policy to 'delivered_manual'
            10. check if the qty_delivered is editable
        """
        so = self.env['sale.order'].create({
            'partner_id': self.partner.id,
        })
        so.action_confirm()
        SaleOrderLine = self.env['sale.order.line'].with_context(default_order_id=so.id)
        self.assertEqual(self.product_service_ordered_prepaid.service_policy, 'ordered_prepaid')
        self.assertEqual(self.product_service_delivered_milestone.service_policy, 'delivered_milestones')
        self.assertEqual(self.product_service_delivered_manual.service_policy, 'delivered_manual')
        with Form(SaleOrderLine, 'sale_project.sale_order_line_view_form_editable') as sol_form:
            product_context = sol_form._get_context('product_id')
            product = sol_form.product_id.with_context(product_context).new({
                'name': 'Test product',
            })
            self.assertEqual(product.type, 'service')
            self.assertEqual(product.type, 'service')
            self.assertEqual(product.service_policy, 'ordered_prepaid')
            sol_form.product_id = product
            is_readonly = product.service_type != 'manual'
            self.assertEqual(sol_form._get_modifier('qty_delivered', 'readonly'), is_readonly)
            if is_readonly:
                self.assertEqual(sol_form.qty_delivered_method, 'timesheet')
                self.assertEqual(sol_form.qty_delivered, 0, 'quantity delivered is readonly')
            else:
                sol_form.qty_delivered = 1
                self.assertEqual(sol_form.qty_delivered_method, 'manual')
                self.assertEqual(sol_form.qty_delivered, 1, 'quantity delivered is editable')
                sol_form.qty_delivered = 0  # reset for the next test case

            sol_form.product_id = self.product_service_delivered_milestone
            self.assertTrue(sol_form._get_modifier('qty_delivered', 'readonly'))
            self.assertEqual(sol_form.qty_delivered_method, 'milestones')

            sol_form.product_id = self.product_service_ordered_prepaid
            is_readonly = self.product_service_ordered_prepaid.service_type != 'manual'
            self.assertEqual(sol_form._get_modifier('qty_delivered', 'readonly'), is_readonly)
            if is_readonly:  # then sale_timesheet module installed
                self.assertEqual(sol_form.qty_delivered_method, 'timesheet')
                self.assertEqual(sol_form.qty_delivered, 0, 'quantity delivered is readonly')
            else:
                sol_form.qty_delivered = 1
                self.assertEqual(sol_form.qty_delivered_method, 'manual')
                self.assertEqual(sol_form.qty_delivered, 1, 'quantity delivered is editable')
                sol_form.qty_delivered = 0  # reset for the next test case

            sol_form.product_id = self.product_service_delivered_manual
            self.assertFalse(sol_form._get_modifier('qty_delivered', 'readonly'))
            sol_form.qty_delivered = 1
            self.assertEqual(sol_form.qty_delivered_method, 'manual')
            self.assertEqual(sol_form.qty_delivered, 1, 'quantity delivered is editable')

    def test_generated_project_stages(self):
        """ This test checks that when a project is created on SO confirmation, the following stages are automatically
            generated for the new project (assuming there is no project template set on the product):
            - To Do
            - In Progress
            - Done
            - Cancelled
        """
        sale_order = self.env['sale.order'].with_context(mail_notrack=True, mail_create_nolog=True).create({
            'partner_id': self.partner.id,
        })
        product = self.env['product.product'].create({
            'name': "Service with template",
            'standard_price': 10,
            'list_price': 20,
            'type': 'service',
            'invoice_policy': 'order',
            'uom_id': self.uom_hour.id,
            'uom_po_id': self.uom_hour.id,
            'default_code': 'c1',
            'service_tracking': 'task_in_project',
            'project_id': False,  # will create a project,
            'project_template_id': False, # no project template
        })
        sale_order_line = self.env['sale.order.line'].create({
            'order_id': sale_order.id,
            'name': product.name,
            'product_id': product.id,
            'product_uom_qty': 10,
            'product_uom': product.uom_id.id,
            'price_unit': product.list_price,
        })
        names = ['To Do', 'In Progress', 'Done', 'Cancelled']
        project = sale_order_line._timesheet_create_project()
        self.assertEqual(names, project.type_ids.mapped('name'), "The project stages' name should be equal to: %s" % names)

    def test_quick_create_sol(self):
        """
        When creating a SOL on the fly through the quick create, use a product matching
        what was typed in the field if there is one, and make sure the SOL name is computed correctly.
        """
        product_service = self.env['product.product'].create({
            'name': 'Signage',
            'type': 'service',
            'invoice_policy': 'order',
            'uom_id': self.env.ref('uom.product_uom_hour').id,
            'uom_po_id': self.env.ref('uom.product_uom_hour').id,
        })
        sale_line_id, sale_line_name = self.env['sale.order.line'].with_context(
            default_partner_id=self.partner.id,
            form_view_ref='sale_project.sale_order_line_view_form_editable',
        ).name_create('gnag')

        sale_line = self.env['sale.order.line'].browse(sale_line_id)
        self.assertEqual(sale_line.product_id, product_service, 'The created SOL should use the right product.')
        self.assertTrue(product_service.name in sale_line_name, 'The created SOL should use the full name of the product and not just what was typed.')

    def test_sale_order_items_of_the_project_status(self):
        """
        Checks that the sale order items appearing in the project status display every
        sale.order.line referrencing a product ignores the notes and sections
        """
        project = self.env['project.project'].create({
            'name': 'Project X',
            'partner_id': self.partner.id,
            'allow_billable': True,
        })
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [
                Command.create({
                    'product_id': self.product_order_service1.id,
                    'product_uom_qty': 1,
                }),
                Command.create({
                    'name': "Section",
                    'display_type': "line_section",
                }),
                Command.create({
                    'name': "notes",
                    'display_type': "line_section",
                }),
                Command.create({
                    'product_id': self.product_a.id,
                    'product_uom_qty': 1,
                }),
            ],
            'project_id': project.id,
        })
        relevant_sale_order_lines = sale_order.order_line.filtered(lambda sol: sol.product_id)
        reported_sale_order_lines = self.env['sale.order.line'].search(project.action_view_sols()['domain'])
        self.assertEqual(project.sale_order_line_count, 2)
        self.assertEqual(relevant_sale_order_lines, reported_sale_order_lines)

    def test_project_tasks_active_on_so_confirm(self):
        """ Test if project and task are well unarchived when a SO with a service product using a project template
            is confirmed.
        """
        # Create archived Project template with one task
        self.archived_project_template = self.env['project.project'].create({
            'name': 'Archived project template',
            'allow_billable': True,
        })
        self.archived_project_template_task = self.env['project.task'].create({
            'name': 'Task 1',
            'project_id': self.archived_project_template.id,
        })
        self.archived_project_template.active = False

        # Create service product using the project template
        service_with_project_template = self.env['product.product'].create({
            'name': 'Service with archived project template',
            'type': 'service',
            'invoice_policy': 'order',
            'service_tracking': 'task_in_project',
            'project_template_id': self.archived_project_template.id,
        })

        # Create SO with the service product
        sale_order = self.env['sale.order'].create({'partner_id': self.partner.id})
        self.env['sale.order.line'].create({
            'product_id': service_with_project_template.id,
            'order_id': sale_order.id,
        })

        self.assertFalse(len(sale_order.project_ids), "The SO should not have linked project before it is confirmed.")
        sale_order.action_confirm()
        self.assertEqual(len(sale_order.project_ids), 1, "The SO should have created project after it is confirmed.")
        self.assertTrue(sale_order.project_ids.active, "The project should be active when SO is confirmed.")
        self.assertTrue(all(sale_order.project_ids.with_context(active_test=False).tasks.mapped('active')), "All tasks should be unarchived for the project created when SO is confirmed.")

    def test_sale_order_with_project_task_from_multi_companies(self):
        uom_hour = self.env.ref("uom.product_uom_hour")
        will_smith = self.env["res.partner"].create({"name": "Will Smith"})
        multi_company_project = self.env["project.project"].create({
            "name": "Multi Company Project",
            "company_id": None,
            "allow_billable": True,
        })

        company_a, company_b = self.env['res.company'].create([
            {"name": "Company A"},
            {"name": "Company B"},
        ])

        # cannot be done in batch because of `_check_sale_product_company` constraint
        product_a, product_b = (
            self.env["product.product"].with_company(company).create({
                "name": "Task Creating Product",
                "standard_price": 30,
                "list_price": 90,
                "type": "service",
                "service_tracking": "task_global_project",
                "invoice_policy": "order",
                "uom_id": uom_hour.id,
                "uom_po_id": uom_hour.id,
                "project_id": multi_company_project.id,
            })
            for company in [company_a, company_b]
        )
        sale_order_a, sale_order_b = self.env["sale.order"].create([
            {
                "partner_id": will_smith.id,
                "order_line": [
                    Command.create({
                        "product_id": product.id,
                        "product_uom_qty": 10,
                    }),
                    Command.create({
                        "product_id": product.id,
                        "product_uom_qty": 10,
                    }),
                ],
                'company_id': company.id,
            }
            for company, product in zip([company_a, company_b], [product_a, product_b])
        ])
        (sale_order_a + sale_order_b).action_confirm()

        for company in [company_a, company_b]:
            self.assertEqual(multi_company_project.with_company(company).sale_order_count, 2, "Expected all sale orders to be counted by project")
            self.assertEqual(
                multi_company_project.with_company(company).sale_order_line_count,
                len(sale_order_a.order_line) + len(sale_order_b.order_line),  # expect 4
                "Expected all sale order lines lines to be counted by project")
            sale_order_action = multi_company_project.with_company(company).action_view_sos()
            self.assertEqual(sale_order_action["type"], "ir.actions.act_window")
            self.assertEqual(sale_order_action["res_model"], "sale.order")

    def test_action_view_task_stages(self):
        SaleOrder = self.env['sale.order'].with_context(tracking_disable=True)
        SaleOrderLine = self.env['sale.order.line'].with_context(tracking_disable=True)

        sale_order_2 = SaleOrder.create({
            'partner_id': self.partner.id,
            'partner_invoice_id': self.partner.id,
            'partner_shipping_id': self.partner.id,
        })
        sale_line_1_order_2 = SaleOrderLine.create({
            'product_id': self.product_order_service1.id,
            'product_uom_qty': 10,
            'product_uom': self.product_order_service1.uom_id.id,
            'price_unit': self.product_order_service1.list_price,
            'order_id': sale_order_2.id,
        })

        self.env['project.task'].create({
            'name': 'Task',
            'sale_line_id': sale_line_1_order_2.id,
            'project_id': self.project_global.id,
        })
        action = sale_order_2.action_view_task()
        self.assertEqual(action["context"]["default_project_id"], self.project_global.id)

    def test_creating_AA_when_adding_service_to_confirmed_so(self):
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'partner_invoice_id': self.partner.id,
            'partner_shipping_id': self.partner.id,
        })

        self.env['sale.order.line'].create({
            'product_id': self.product_a.id,
            'product_uom_qty': 1,
            'order_id': sale_order.id,
        })

        sale_order.action_confirm()
        self.assertFalse(sale_order.project_account_id)

        self.env['sale.order.line'].create({
            'product_id': self.product_order_service4.id,
            'product_uom_qty': 1,
            'order_id': sale_order.id,
        })

        self.assertTrue(sale_order.project_account_id)

    def test_cancel_multiple_quotations(self):
        quotations = self.env['sale.order'].create([
            {
                'partner_id': self.partner.id,
                'order_line': [
                    Command.create({'product_id': self.product.id}),
                ],
            },
            {
                'partner_id': self.partner.id,
                'order_line': [
                    Command.create({'product_id': self.product.id}),
                ],
            }
        ])
        quotations._action_cancel()
        self.assertEqual(set(quotations.mapped('state')), {'cancel'}, "Both quotations are in 'cancel' state.")

    def test_onchange_sale_fields(self):
        SaleOrder, SaleOrderLine = self.env['sale.order'], self.env['sale.order.line']
        sale_orders = sale_order_0, sale_order_1 = SaleOrder.create([{'partner_id': self.partner.id}] * 2)
        sale_order_line_0, sale_order_line_1 = SaleOrderLine.create([{
            'order_id': sale_order.id,
            'product_id': self.service_product.id,
        } for sale_order in sale_orders])

        self.project_global.partner_id = self.partner
        with Form(self.project_global) as project_form:
            project_form.sale_line_id = sale_order_line_0
            self.assertEqual(
                project_form.reinvoiced_sale_order_id, sale_order_0,
                "Project's sale order should match its sale order line's order.",
            )
            project_form.sale_line_id = SaleOrderLine
            project_form.reinvoiced_sale_order_id = sale_order_1
            self.assertEqual(
                project_form.sale_line_id, sale_order_line_1,
                "Project's sale order line should match its sale order's first line.",
            )

            project_form.reinvoiced_sale_order_id = sale_order_0
            self.assertEqual(
                project_form.sale_line_id, sale_order_line_1,
                "Project's sale order line shouldn't have change as it was already set.",
            )

            project_form.reinvoiced_sale_order_id = sale_order_1
            project_form.sale_line_id = sale_order_line_0
            self.assertEqual(
                project_form.reinvoiced_sale_order_id, sale_order_1,
                "Project's sale order shouldn't have change as it was already set.",
            )

    def test_task_compute_sale_order_id(self):
        """
        Check whether a task's sale_order_id is set iff its partner_id matches
        the SO's partner_id, partner_invoice_id, or partner_shipping_id fields.
        """
        project_user = new_test_user(
            self.env,
            name='Project user',
            login='Project user',
            groups='project.group_project_user',
        )
        partners = [
            self.partner,    # partner_id
            self.partner_a,  # partner_invoice_id
            self.partner_b,  # partner_shipping_id
            self.env['res.partner'].create({'name': "unrelated partner"}),
        ]
        sale_order = self.env['sale.order'].with_context(tracking_disable=True).create({
            'partner_id': partners[0].id,
            'partner_invoice_id': partners[1].id,
            'partner_shipping_id': partners[2].id,
            'order_line': [Command.create({'product_id': self.product_order_service1.id})],
        })
        sale_order.action_confirm()

        task0, task1, task2, task3 = self.env['project.task'].with_user(project_user).create([{
            'name': f"Task {i}",
            'sale_line_id': sale_order.order_line.id,
            'project_id': self.project_global.id,
            'partner_id': partner.id,
        } for i, partner in enumerate(partners)])

        self.assertEqual(task0.sale_order_id, sale_order, "Task matches SO's partner_id")
        self.assertEqual(task1.sale_order_id, sale_order, "Task matches SO's partner_invoice_id")
        self.assertEqual(task2.sale_order_id, sale_order, "Task matches SO's partner_shipping_id")
        self.assertFalse(task3.sale_order_id, "Task partner doesn't match any of the SO partners")

        task3.with_user(project_user).write({
            'partner_id': self.partner.id,
            'sale_line_id': sale_order.order_line.id,
        })
        self.assertEqual(task3.sale_order_id, sale_order, "Task matches SO's partner_id")

    def test_action_view_project_ids(self):
        order = self.env['sale.order'].create({
            'name': 'Project Order',
            'partner_id': self.partner.id
        })

        sol = self.env['sale.order.line'].create({
            'product_id': self.product_order_service4.id,
            'order_id': order.id,
        })

        order.action_confirm()
        action = order.action_view_project_ids()
        self.assertEqual(action['type'], 'ir.actions.act_window', 'Should return a window action')
        self.assertEqual(action['context']['default_sale_line_id'], sol.id, 'The SOL linked to the SO should be chosen as default value')

        self.product_order_service4.type = 'consu'
        action = order.action_view_project_ids()
        self.assertEqual(action['type'], 'ir.actions.act_window', 'Should return a window action')
        self.assertFalse(action['context']['default_sale_line_id'], 'No SOL should be set by default since the product changed')

    def test_copy_so_doesnt_copy_project(self):
        origin = self.env['sale.order'].create({
            'name': 'Project Order',
            'partner_id': self.partner.id
        })
        self.env['sale.order.line'].create({
            'product_id': self.product_order_service4.id,
            'order_id': origin.id,
        })
        origin.action_confirm()
        self.assertTrue(origin.project_id)
        self.assertEqual(
            origin.order_line.analytic_distribution,
            origin.order_line.project_id._get_analytic_distribution(),
        )
        copy = origin.copy()
        self.assertFalse(copy.project_id)
        self.assertFalse(copy.order_line.analytic_distribution)
        copy.action_confirm()
        self.assertTrue(copy.project_id)
        self.assertEqual(
            copy.order_line.analytic_distribution,
            copy.order_line.project_id._get_analytic_distribution(),
        )

    def test_confirm_sale_order_on_task_save(self):
        sale_order = self.env['sale.order'].create({
            'name': 'Sale Order',
            'partner_id': self.partner.id,
        })
        sale_order_line = self.env['sale.order.line'].create({
            'order_id': sale_order.id,
            'product_id': self.product_order_service1.id,
        })
        self.assertEqual(sale_order.state, 'draft')

        task = self.env['project.task'].create({
            'name': 'Task',
            'project_id': self.project_global.id,
        })
        task.write({'sale_line_id': sale_order_line.id})
        self.assertEqual(sale_order.state, 'sale')

    def test_confirm_sale_order_on_project_creation(self):
        sale_order = self.env['sale.order'].create({
            'name': 'Sale Order',
            'partner_id': self.partner.id,
        })
        sale_order_line = self.env['sale.order.line'].create({
            'order_id': sale_order.id,
            'product_id': self.product_order_service1.id,
        })
        self.assertEqual(sale_order.state, 'draft')

        self.env['project.project'].create({
            'name': 'Project',
            'sale_line_id': sale_order_line.id,
        })
        self.assertEqual(sale_order.state, 'sale')

    def test_analytics_on_so_confirmation_no_project(self):
        # Config 1: no project_id on the SO
        self.product_order_service3.project_template_id = self.project_template
        so = self.env['sale.order'].create({'partner_id': self.partner.id})
        sol_no_project, sol_task_in_global_project, sol_task_in_template_project, sol_new_project = self.env['sale.order.line'].create([
            {'order_id': so.id, 'product_id': self.product_order_service1.id, 'sequence': 1}, # no service_tracking
            {'order_id': so.id, 'product_id': self.product_order_service2.id, 'sequence': 2}, # service_tracking: 'task_global_project'
            {'order_id': so.id, 'product_id': self.product_order_service3.id, 'sequence': 3}, # service_tracking': 'task_in_project'
            {'order_id': so.id, 'product_id': self.product_order_service4.id, 'sequence': 4}, # service_tracking: 'project_only'
        ])
        n_analytic_accounts = self.env['account.analytic.account'].search_count([])
        so.action_confirm()
        self.assertEqual(
            n_analytic_accounts + 1,
            self.env['account.analytic.account'].search_count([]),
            "Only one analytic account should have been created due to the generation of both `sol_task_in_template_project` and `sol_new_project` projects."
        )
        self.assertEqual(len(so.order_line.project_id | so.order_line.task_id.project_id), 3, "Three projects should be linked to the SO.")
        self.assertFalse(sol_no_project.project_id, "`sol_no_project` should not generate any project.")
        self.assertEqual(
            so.project_id,
            sol_task_in_template_project.project_id,
            "The project of the SO should be set to the project with the lowest (sequence, id)."
        )
        self.assertNotEqual(
            sol_task_in_global_project.project_id.account_id,
            sol_task_in_template_project.project_id.account_id,
            "As the project of `sol_task_in_global_project` was not generated but already defined, its AA was kept the same."
        )
        self.assertEqual(
            sol_task_in_template_project.project_id.account_id,
            sol_new_project.project_id.account_id,
            "As the projects of `sol_task_in_template_project` and `sol_new_project` were generated, they share the same AA which was created after SO confirmation."
        )

    def test_analytics_on_so_confirmation_project_with_accounts(self):
        # Config 2: a project_id on the SO with AAs
        # Also add an AA to the project template
        plan_name = self.analytic_plan._column_name()
        self.project_template[plan_name] = self.analytic_account_sale
        self.product_order_service3.project_template_id = self.project_template
        so = self.env['sale.order'].create({'partner_id': self.partner.id, 'project_id': self.project_global.id})
        sol_task_in_template_project, sol_new_project = self.env['sale.order.line'].create([
            {'order_id': so.id, 'product_id': self.product_order_service3.id},
            {'order_id': so.id, 'product_id': self.product_order_service4.id},
        ])
        so.action_confirm()
        self.assertEqual(len(so.order_line.project_id), 2, "Two projects should be linked to the SO.")
        self.assertEqual(
            self.project_global.account_id,
            sol_task_in_template_project.project_id.account_id,
            "The main AA of the project of `sol_task_in_template_project` should be the same as the main AA of the project set on the SO."
        )
        self.assertEqual(
            self.project_template[plan_name],
            sol_task_in_template_project.project_id[plan_name],
            "The other AA of the project of `sol_task_in_template_project` should be the same as the other AA of its project template."
        )
        self.assertEqual(
            self.project_global.account_id,
            sol_new_project.project_id.account_id,
            "The main AA of the project of `sol_new_project` should should be the same the main AA of the project set on the SO."
        )
        self.assertEqual(
            self.project_global[plan_name],
            sol_new_project.project_id[plan_name],
            "The other AA of the project of `sol_new_project` should be the same as the other AA of the project set on the SO."
        )

    def test_analytics_on_so_confirmation_project_without_account(self):
        # Config 3: a project_id on the SO without AA
        self.product_order_service3.project_template_id = self.project_template
        self.project_global.account_id = False
        so = self.env['sale.order'].create({'partner_id': self.partner.id, 'project_id': self.project_global.id})
        sol_task_in_template_project, sol_new_project = self.env['sale.order.line'].create([
            {'order_id': so.id, 'product_id': self.product_order_service3.id},
            {'order_id': so.id, 'product_id': self.product_order_service4.id},
        ])
        so.action_confirm()
        self.assertEqual(len(so.order_line.project_id), 2, "Two projects should be linked to the SO.")
        self.assertFalse(self.project_global.account_id, "The AA of the project of the SO should still be empty.")
        self.assertEqual(
            sol_task_in_template_project.project_id.account_id,
            sol_new_project.project_id.account_id,
            "As the projects of `sol_task_in_template_project` and `sol_new_project` were generated, they share the same AA which was created after SO confirmation."
        )

    def test_global_project_service_takes_so_project_on_so_confirmation(self):
        self.product_order_service2.project_id = False
        so = self.env['sale.order'].create({'partner_id': self.partner.id})
        sol_task_in_global_project, sol_new_project = self.env['sale.order.line'].create([
            {'order_id': so.id, 'product_id': self.product_order_service2.id},
            {'order_id': so.id, 'product_id': self.product_order_service3.id},
        ])
        so.action_confirm()
        self.assertEqual(
            so.project_id,
            sol_new_project.project_id,
            "The project of the SO should be set to the project that was generated by `sol_new_project` at SO confirmation."
        )
        self.assertEqual(
            so.project_id,
            sol_task_in_global_project.task_id.project_id,
            "The project of the task of `sol_task_in_global_project` should be set to the project of the SO."
        )

    def test_global_project_service_takes_so_project_on_already_confirmed_so(self):
        self.product_order_service2.project_id = False
        so = self.env['sale.order'].create({'partner_id': self.partner.id})
        so.action_confirm()
        sol_task_in_global_project, sol_new_project = self.env['sale.order.line'].create([
            {'order_id': so.id, 'product_id': self.product_order_service2.id},
            {'order_id': so.id, 'product_id': self.product_order_service3.id},
        ])
        self.assertEqual(
            so.project_id,
            sol_new_project.project_id,
            "The project of the SO should be set to the project that was generated by `sol_new_project` after adding the SOLs in batch to the SO."
        )
        self.assertEqual(
            so.project_id,
            sol_task_in_global_project.task_id.project_id,
            "The project of the task of `sol_task_in_global_project` should be set to the project of the SO."
        )

    def test_global_project_service_no_so_project_error(self):
        self.product_order_service2.project_id = False
        so = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'order_line': [Command.create({'product_id': self.product_order_service2.id})],
        })
        with self.assertRaises(UserError, msg="The SOL has a product which creates a task on SO confirmation, but no project is configured on the product or SO."):
            so.action_confirm()

    def test_so_confirmation_in_batch(self):
        so1, so2 = self.env['sale.order'].create([{
            'partner_id': self.partner.id,
            'order_line': [Command.create({'product_id': self.product_order_service3.id})],
        } for _dummy in range(2)])
        (so1 | so2).action_confirm()
        self.assertEqual(
            so1.project_id,
            so1.order_line.project_id,
            "The project of `so1` should be set to the project that was generated at SO confirmation."
        )
        self.assertEqual(
            so2.project_id,
            so2.order_line.project_id,
            "The project of `so1` should be set to the project that was generated at SO confirmation."
        )

    def test_so_with_service_product_negative_qty(self):
        so = self.env['sale.order'].create({'partner_id': self.partner.id})
        sol = self.env['sale.order.line'].create({
            'order_id': so.id,
            'product_id': self.product_order_service2.id,
            'product_uom_qty': -5,
        })
        so.action_confirm()
        self.assertFalse(self.product_order_service2.project_id.task_ids)
        self.assertFalse(sol.task_id)
