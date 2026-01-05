/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { rpc } from "@web/core/network/rpc";

patch(PaymentScreen.prototype, {
    async validateOrder() {
        const button = document.querySelector(".validation-button.next");
        if (button) button.innerHTML = `
            <i class="fa fa-spinner fa-spin"></i>
        `;
        if (button) button.disabled = true;

        try {
            const safeLines = this.currentOrder.lines.map(line => ({
                product_id: line.product_id?.id ?? line.product_id,
                qty: line.qty,
                price_unit: line.price_unit,
                price_subtotal: line.price_subtotal,
                price_subtotal_incl: line.price_subtotal_incl,
                discount: line.discount || 0,
                tax_ids: Array.isArray(line.tax_ids) ? line.tax_ids.map(t => t.id ?? t) : [],
            }));

            const response = await rpc("/pos/pra/push", {
                config_id: this.currentOrder.config_id?.id ?? null,
                order_id: this.currentOrder.id,
                date_order: this.currentOrder.date_order,
                invoice_number: this.currentOrder.pos_reference,
                partner_id: this.currentOrder.partner_id?.id ?? null,
                total_qty: this.currentOrder.lines.reduce((acc, l) => acc + (l.qty || 0), 0),
                amount_total: this.currentOrder.amount_total,
                amount_paid: this.currentOrder.amount_paid,
                amount_return: this.currentOrder.amount_return,
                lines: safeLines,
            });

            this.currentOrder.pra_last_response = response.text;
            this.currentOrder.pra_status_code = response.status_code;
            this.currentOrder.pra_push_failed = (response.status_code != 200);
            this.currentOrder.pra_invoice_number = response.InvoiceNumber;

        } finally {
            if (button) button.innerHTML = "Validate";
            if (button) button.disabled = false;
        }

        return super.validateOrder(...arguments);
    },
})

patch(PosOrder.prototype, {
    export_for_printing() {
        let result = super.export_for_printing(...arguments);
        result.headerData.praInvoiceNumber = this.pra_invoice_number;
        return result;
    },
});