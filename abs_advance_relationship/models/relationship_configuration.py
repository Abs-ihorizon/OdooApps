# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from xml.sax.saxutils import escape, quoteattr


RELATIONAL_TYPES = {"many2one", "one2many", "many2many"}


class DocumentRelationshipModel(models.Model):
    _name = "document.relationship.model"
    _description = "Advance Relationship Document Type"
    _order = "sequence, name"

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    model_id = fields.Many2one(
        "ir.model", required=True, ondelete="cascade", domain=[("transient", "=", False)]
    )
    model_name = fields.Char(related="model_id.model", store=True, readonly=True, index=True)
    document_type_label = fields.Char(required=True, translate=True)
    # Odoo 19 does not support ondelete='restrict' when ir.model.fields is the
    # comodel. Required structural fields cascade; optional display fields are
    # cleared if their underlying custom field is removed.
    name_field_id = fields.Many2one("ir.model.fields", required=True, ondelete="cascade")
    date_field_id = fields.Many2one("ir.model.fields", ondelete="set null")
    partner_field_id = fields.Many2one("ir.model.fields", ondelete="set null")
    status_field_id = fields.Many2one("ir.model.fields", ondelete="set null")
    amount_field_id = fields.Many2one("ir.model.fields", ondelete="set null")
    currency_field_id = fields.Many2one("ir.model.fields", ondelete="set null")
    company_field_id = fields.Many2one("ir.model.fields", ondelete="set null")
    icon = fields.Char(default="fa-file-o", help="Font Awesome class, for example fa-id-card-o")
    default_color = fields.Char(default="#607d8b")
    enable_relationship_map = fields.Boolean(default=True)
    show_in_actions_menu = fields.Boolean(default=True)
    show_smart_button = fields.Boolean(default=False)
    form_view_id = fields.Many2one(
        "ir.ui.view",
        string="Form View",
        ondelete="set null",
        domain="[('model', '=', model_name), ('type', '=', 'form')]",
    )
    smart_button_label = fields.Char(default="Relationship Map", translate=True)
    smart_button_icon = fields.Char(default="fa-share-alt")
    generated_view_id = fields.Many2one(
        "ir.ui.view", string="Generated Smart Button View", readonly=True,
        copy=False, ondelete="set null",
    )
    allow_public_sharing = fields.Boolean(default=False)
    maximum_depth = fields.Integer(default=10)
    action_id = fields.Many2one("ir.actions.server", readonly=True, copy=False, ondelete="set null")
    source_rule_ids = fields.One2many(
        "document.relationship.rule", "source_model_config_id", string="Outgoing Rules"
    )
    target_rule_ids = fields.One2many(
        "document.relationship.rule", "target_model_config_id", string="Incoming Rules"
    )
    status_mapping_ids = fields.One2many(
        "document.relationship.status.mapping", "model_config_id", string="Status Mappings"
    )

    _model_unique = models.Constraint(
        "UNIQUE(model_id)", "A document model can only be configured once."
    )
    _positive_depth = models.Constraint(
        "CHECK(maximum_depth > 0 AND maximum_depth <= 50)",
        "Maximum depth must be between 1 and 50.",
    )

    @api.onchange("model_id")
    def _onchange_model_id(self):
        for record in self:
            for field_name in (
                "name_field_id", "date_field_id", "partner_field_id",
                "status_field_id", "amount_field_id", "currency_field_id",
                "company_field_id",
            ):
                selected_field = record[field_name]
                if selected_field and selected_field.model_id != record.model_id:
                    record[field_name] = False
            if record.model_id and not record.name:
                record.name = record.model_id.name
            if record.model_id and not record.document_type_label:
                record.document_type_label = record.model_id.name

    def _validate_field(self, field, allowed_types, label, relation=None):
        if not field:
            return
        if field.model_id != self.model_id:
            raise ValidationError(_("%s must belong to model %s.") % (label, self.model_name))
        if field.ttype not in allowed_types:
            raise ValidationError(
                _("%(label)s has an invalid field type: %(type)s.")
                % {"label": label, "type": field.ttype}
            )
        if relation and field.relation != relation:
            raise ValidationError(_("%s must point to %s.") % (label, relation))

    @api.constrains(
        "model_id", "name_field_id", "date_field_id", "partner_field_id",
        "status_field_id", "amount_field_id", "currency_field_id", "company_field_id"
    )
    def _check_display_fields(self):
        for record in self:
            record._validate_field(record.name_field_id, {"char", "text"}, _("Name Field"))
            record._validate_field(record.date_field_id, {"date", "datetime"}, _("Date Field"))
            record._validate_field(record.partner_field_id, {"many2one"}, _("Partner Field"), "res.partner")
            record._validate_field(record.status_field_id, {"selection", "many2one", "char"}, _("Status Field"))
            record._validate_field(record.amount_field_id, {"float", "monetary", "integer"}, _("Amount Field"))
            record._validate_field(record.currency_field_id, {"many2one"}, _("Currency Field"), "res.currency")
            record._validate_field(record.company_field_id, {"many2one"}, _("Company Field"), "res.company")

    def _prepare_server_action_values(self):
        self.ensure_one()
        code = (
            "if records:\n"
            "    action = env['document.relationship.model'].action_open_relationship_map("
            "records._name, records[0].id)"
        )
        return {
            "name": _("Relationship Map"),
            "model_id": self.model_id.id,
            "binding_model_id": self.model_id.id,
            "binding_view_types": "list,form",
            "state": "code",
            "code": code,
            "group_ids": [(6, 0, [self.env.ref(
                "abs_document_relationship_map.group_relationship_map_user"
            ).id])],
        }

    def action_sync_action_menu(self):
        self.ensure_one()
        if not self.env.user.has_group("abs_document_relationship_map.group_relationship_map_manager"):
            raise UserError(_("Only a Relationship Map Manager can update action bindings."))
        if self.show_in_actions_menu and self.enable_relationship_map and self.active:
            values = self._prepare_server_action_values()
            if self.action_id:
                self.action_id.sudo().write(values)
            else:
                self.action_id = self.env["ir.actions.server"].sudo().create(values)
        elif self.action_id:
            self.action_id.sudo().unlink()
            self.action_id = False
        return {"type": "ir.actions.client", "tag": "reload"}

    def _prepare_smart_button_arch(self):
        self.ensure_one()
        action = self.env.ref(
            "abs_document_relationship_map.action_document_relationship_map"
        )
        model_name = escape(self.model_name or "")
        button_label = escape(self.smart_button_label or _("Relationship Map"))
        button_icon = quoteattr(self.smart_button_icon or "fa-share-alt")
        button = """
            <button name="%s"
                    type="action"
                    class="oe_stat_button"
                    icon=%s
                    groups="abs_document_relationship_map.group_relationship_map_user"
                    context="{'active_model': '%s', 'active_id': id}">
                <div class="o_stat_info">
                    <span class="o_stat_text">%s</span>
                </div>
            </button>
        """ % (action.id, button_icon, model_name, button_label)

        # Custom forms do not always contain Odoo's standard button_box. Read
        # the fully combined parent architecture and choose a valid insertion
        # point before creating the inherited view.
        combined_arch = self.form_view_id._get_combined_arch()
        if combined_arch.xpath("//div[@name='button_box']"):
            return """
                <data>
                    <xpath expr="//div[@name='button_box']" position="inside">
                        %s
                    </xpath>
                </data>
            """ % button
        if combined_arch.xpath("//sheet"):
            return """
                <data>
                    <xpath expr="//sheet" position="inside">
                        <div class="oe_button_box" name="button_box">
                            %s
                        </div>
                    </xpath>
                </data>
            """ % button
        return """
            <data>
                <xpath expr="//form" position="inside">
                    <div class="oe_button_box" name="button_box">
                        %s
                    </div>
                </xpath>
            </data>
        """ % button

    def action_sync_smart_button(self):
        self.ensure_one()
        if not self.env.user.has_group(
            "abs_document_relationship_map.group_relationship_map_manager"
        ):
            raise UserError(_("Only a Relationship Map Manager can update smart buttons."))

        should_generate = (
            self.show_smart_button
            and self.enable_relationship_map
            and self.active
        )
        if should_generate:
            if not self.form_view_id:
                raise UserError(_("Select the custom model's Form View first."))
            if self.form_view_id.model != self.model_name:
                raise UserError(_("The selected Form View does not belong to this model."))
            values = {
                "name": "advance.relationship.smart.button.%s" % self.model_name,
                "type": "form",
                "model": self.model_name,
                "inherit_id": self.form_view_id.id,
                "priority": 99,
                "arch": self._prepare_smart_button_arch(),
                "active": True,
            }
            try:
                if self.generated_view_id:
                    self.generated_view_id.sudo().write(values)
                else:
                    self.generated_view_id = self.env["ir.ui.view"].sudo().create(values)
            except Exception as error:
                raise UserError(_(
                    "Smart Button could not be generated for the selected form. "
                    "Technical detail: %s"
                ) % error) from error
        elif self.generated_view_id:
            self.generated_view_id.sudo().unlink()
            self.generated_view_id = False
        return {"type": "ir.actions.client", "tag": "reload"}

    def action_remove_smart_button(self):
        self.ensure_one()
        if not self.env.user.has_group(
            "abs_document_relationship_map.group_relationship_map_manager"
        ):
            raise UserError(_("Only a Relationship Map Manager can remove smart buttons."))
        if self.generated_view_id:
            self.generated_view_id.sudo().unlink()
        self.write({"generated_view_id": False, "show_smart_button": False})
        return {"type": "ir.actions.client", "tag": "reload"}

    @api.model
    def action_open_relationship_map(self, model_name, res_id):
        config = self.search([
            ("model_name", "=", model_name),
            ("active", "=", True),
            ("enable_relationship_map", "=", True),
        ], limit=1)
        if not config:
            raise UserError(_("Relationship Map is not enabled for this model."))
        record = self.env[model_name].browse(int(res_id)).exists()
        if not record:
            raise UserError(_("The selected document no longer exists."))
        record.check_access_rights("read")
        record.check_access_rule("read")
        return {
            "type": "ir.actions.client",
            "name": _("Relationship Map"),
            "tag": "document_relationship_map_action",
            "target": "current",
            "context": {"active_model": model_name, "active_id": record.id},
        }

    def unlink(self):
        actions = self.mapped("action_id")
        generated_views = self.mapped("generated_view_id")
        result = super().unlink()
        if actions:
            actions.sudo().unlink()
        if generated_views:
            generated_views.sudo().unlink()
        return result


class DocumentRelationshipRule(models.Model):
    _name = "document.relationship.rule"
    _description = "Advance Relationship Rule"
    _order = "sequence, name"

    name = fields.Char(required=True, translate=True)
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
    source_model_config_id = fields.Many2one(
        "document.relationship.model", required=True, ondelete="cascade"
    )
    target_model_config_id = fields.Many2one(
        "document.relationship.model", required=True, ondelete="cascade"
    )
    field_owner = fields.Selection(
        [("source", "Source Model"), ("target", "Target Model")],
        required=True,
        default="source",
        help="Select the model on which the relational field physically exists.",
    )
    relationship_model_id = fields.Many2one(
        "ir.model", compute="_compute_relationship_model", store=True
    )
    relationship_field_id = fields.Many2one(
        "ir.model.fields", required=True, ondelete="cascade",
        domain="[('model_id', '=', relationship_model_id), ('ttype', 'in', ['many2one', 'one2many', 'many2many'])]",
    )
    relationship_code = fields.Char(required=True, default="related")
    edge_label = fields.Char(required=True, translate=True)
    edge_color = fields.Char(default="#9ba4a8")
    direction = fields.Selection(
        [
            ("source_to_target", "Source to Target"),
            ("target_to_source", "Target to Source"),
            ("bidirectional", "Bidirectional"),
        ],
        required=True,
        default="source_to_target",
    )
    include_in_public_map = fields.Boolean(default=False)

    _rule_unique = models.Constraint(
        "UNIQUE(source_model_config_id, target_model_config_id, field_owner, relationship_field_id, direction)",
        "This relationship rule already exists.",
    )

    @api.depends("field_owner", "source_model_config_id.model_id", "target_model_config_id.model_id")
    def _compute_relationship_model(self):
        for rule in self:
            rule.relationship_model_id = (
                rule.source_model_config_id.model_id
                if rule.field_owner == "source"
                else rule.target_model_config_id.model_id
            )

    @api.onchange("field_owner", "source_model_config_id", "target_model_config_id")
    def _onchange_relationship_owner(self):
        for rule in self:
            if (
                rule.relationship_field_id
                and rule.relationship_field_id.model_id != rule.relationship_model_id
            ):
                rule.relationship_field_id = False

    @api.constrains(
        "source_model_config_id", "target_model_config_id", "field_owner", "relationship_field_id"
    )
    def _check_relationship_field(self):
        for rule in self:
            if rule.source_model_config_id == rule.target_model_config_id:
                raise ValidationError(_("Source and target configurations must be different."))
            field = rule.relationship_field_id
            owner = (
                rule.source_model_config_id if rule.field_owner == "source"
                else rule.target_model_config_id
            )
            opposite = (
                rule.target_model_config_id if rule.field_owner == "source"
                else rule.source_model_config_id
            )
            if field.model_id != owner.model_id:
                raise ValidationError(_("The relationship field does not belong to the selected owner model."))
            if field.ttype not in RELATIONAL_TYPES:
                raise ValidationError(_("Only Many2one, One2many and Many2many fields are supported."))
            if field.relation != opposite.model_name:
                raise ValidationError(
                    _("Field %(field)s points to %(actual)s, not %(expected)s.")
                    % {
                        "field": field.name,
                        "actual": field.relation or _("no model"),
                        "expected": opposite.model_name,
                    }
                )


class DocumentRelationshipStatusMapping(models.Model):
    _name = "document.relationship.status.mapping"
    _description = "Advance Relationship Status Mapping"
    _order = "sequence, id"

    sequence = fields.Integer(default=10)
    model_config_id = fields.Many2one(
        "document.relationship.model", required=True, ondelete="cascade"
    )
    technical_value = fields.Char(required=True)
    display_label = fields.Char(required=True, translate=True)
    status_category = fields.Selection(
        [
            ("draft", "Draft"),
            ("in_progress", "In Progress"),
            ("partial", "Partial"),
            ("completed", "Completed"),
            ("failed", "Failed"),
            ("cancelled", "Cancelled"),
            ("overdue", "Overdue"),
        ],
        required=True,
        default="in_progress",
    )
    color = fields.Char()
    icon = fields.Char()

    _mapping_unique = models.Constraint(
        "UNIQUE(model_config_id, technical_value)",
        "A technical status can only be mapped once per model.",
    )
