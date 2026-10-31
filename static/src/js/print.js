import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";

export class TritonPrint extends Interaction {
    static selector = ".o_triton_print";

    dynamicContent = {
        _root: {
            "t-on-click": this.print,
        },
    };

    print() {
        window.print();
    }
}

registry.category("public.interactions").add("erpobe.triton_print", TritonPrint);
