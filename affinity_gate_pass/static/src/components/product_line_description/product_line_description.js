/** @odoo-module **/

import {_t} from "@web/core/l10n/translation";
import {AutoComplete} from "@web/core/autocomplete/autocomplete";
import {getActiveHotkey} from "@web/core/hotkeys/hotkey_service";
import {Many2XAutocomplete} from "@web/views/fields/relational_utils";
import {Many2OneField, many2OneField} from "@web/views/fields/many2one/many2one_field";
import {onMounted, onPatched, onWillUnmount, useRef, useState} from "@odoo/owl";
import {registry} from "@web/core/registry";

export class ProductLineAutocomplete extends AutoComplete {
    onInputKeydown(event) {
        super.onInputKeydown(event);
        const hotkey = getActiveHotkey(event);
        const labelVisibilityButton = document.getElementById('labelVisibilityButtonId');
        if (hotkey === "enter") {
            if (labelVisibilityButton && !this.props.value) {
                labelVisibilityButton.click();
                event.stopPropagation();
                event.preventDefault();
            }
        }
    }
}

export class ProductLineFieldAutocomplete extends Many2XAutocomplete {
    static components = {
        ...Many2XAutocomplete.components, AutoComplete: ProductLineAutocomplete,
    };
    static template = "affinity_gate_pass.ProductLineFieldAutocomplete";
}

export class ProductLineDescriptionField extends Many2OneField {
    static components = {
        ...Many2OneField.components, Many2XAutocomplete: ProductLineFieldAutocomplete,
    };
    static template = "affinity_gate_pass.ProductLineDescriptionField";

    setup() {
        super.setup();
        this.isPrintMode = useState({value: false});
        this.labelVisibility = useState({value: false});
        this.switchToLabel = false;
        this.labelNode = useRef("labelNodeRef");

        onPatched(() => {
            if (this.labelNode.el && this.switchToLabel) {
                this.switchToLabel = false;
                this.labelNode.el.focus();
            }
        });

        this.onBeforePrint = () => {
            this.isPrintMode.value = true;
        };

        this.onAfterPrint = () => {
            this.isPrintMode.value = false;
        };

        onMounted(() => {
            window.addEventListener("beforeprint", this.onBeforePrint);
            window.addEventListener("afterprint", this.onAfterPrint);
        });

        onWillUnmount(() => {
            window.removeEventListener("beforeprint", this.onBeforePrint);
            window.removeEventListener("afterprint", this.onAfterPrint);
        });
    }

    get productName() {
        const value = this.props.record.data[this.props.name];
        if (Array.isArray(value)) {
            return value[1];
        }
        return value || "";
    }

    get label() {
        let label = this.props.record.data.description || "";
        if (this.productName && label.includes(this.productName)) {
            label = label.replace(this.productName, "");
            if (label.includes("\n")) {
                label = label.replace("\n", "");
            }
        }
        return label;
    }

    get Many2XAutocompleteProps() {
        const props = super.Many2XAutocompleteProps;
        props.placeholder = _t("Search a product");
        return props;
    }

    switchLabelVisibility() {
        this.labelVisibility.value = !this.labelVisibility.value;
        this.switchToLabel = true;
    }

    onDescriptionChange(ev) {
        const value = ev.target.value;
        const computedName = (this.productName && value && `${this.productName}\n${value}` || !value && this.productName || value);
        this.props.record.update({description: computedName});
    }
}

export const productLineDescriptionField = {
    ...many2OneField, component: ProductLineDescriptionField, supportedTypes: ["many2one"],
};

registry.category("fields").add("product_line_description", productLineDescriptionField);