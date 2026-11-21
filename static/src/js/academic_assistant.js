import { Component, useRef, useState } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";
import { useService } from "@web/core/utils/hooks";
import { registry } from "@web/core/registry";

class AcademicAssistant extends Component {
    static template = "erpobe.AcademicAssistant";
    static props = ["*"];

    setup() {
        this.inputRef = useRef("input");
        this.action = useService("action");
        const pageModel = this.getPageContext().model;
        this.state = useState({
            isOpen: false,
            isLoading: false,
            input: "",
            messages: [{
                role: "assistant",
                title: "Assistant akademik",
                type: "suggestion",
                message: "Tanyakan data akademik yang tersedia sesuai hak akses akun Anda.",
                data: {},
                suggested_questions: this.getWelcomeSuggestions(pageModel),
            }],
            context: {},
        });
    }

    getWelcomeSuggestions(model) {
        if (model === "erpobe.master.mahasiswa") {
            return [
                "Bagaimana performanya?",
                "Berapa rata-rata IPK mahasiswa?",
                "Tampilkan mahasiswa angkatan 2022.",
            ];
        }
        if (model === "erpobe.akademik.rps") {
            return [
                "Apakah pemetaannya sudah sesuai?",
                "Tampilkan RPS yang belum divalidasi.",
                "RPS mana yang bobotnya belum lengkap?",
            ];
        }
        if (model === "erpobe.akademik.cpl") {
            return [
                "Bagaimana capaian CPL?",
                "CPL mana yang paling rendah?",
                "Berapa jumlah CPL?",
            ];
        }
        if (model === "erpobe.akademik.cpmk") {
            return [
                "Bagaimana capaian CPMK?",
                "CPMK mana yang paling rendah?",
                "Berapa jumlah CPMK?",
            ];
        }
        if (model === "erpobe.master.matakuliah") {
            return [
                "Tampilkan mata kuliah semester 3.",
                "Mata kuliah mana dengan capaian CPMK terendah?",
                "Bagaimana statistik nilai mata kuliah?",
            ];
        }
        return [
            "Berapa jumlah mahasiswa aktif?",
            "Bagaimana capaian CPL?",
            "Tampilkan RPS yang belum divalidasi.",
            "Berapa jumlah dosen?",
        ];
    }

    toggle() {
        this.state.isOpen = !this.state.isOpen;
        if (this.state.isOpen) {
            setTimeout(() => this.inputRef.el?.focus(), 0);
        }
    }

    getPageContext() {
        const controller = this.action.currentController;
        const model = controller?.action?.res_model;
        if (!model) {
            return {};
        }
        return {
            model,
            res_id: Number.isInteger(controller.state?.resId)
                ? controller.state.resId
                : false,
            view_type: controller.state?.view_type || "",
        };
    }

    getStatisticFacts(data) {
        return Object.entries(data || {}).filter(([, value]) =>
            ["string", "number", "boolean"].includes(typeof value)
        );
    }

    getDisplayTable(data) {
        if (Array.isArray(data?.rows) && Array.isArray(data?.columns)) {
            return { columns: data.columns, rows: data.rows };
        }
        if (Array.isArray(data?.counts)) {
            return {
                columns: ["Kategori", "Jumlah"],
                rows: data.counts,
            };
        }
        if (Array.isArray(data?.outcomes)) {
            return {
                columns: ["Kode", "Nama", "Target"],
                rows: data.outcomes,
            };
        }
        if (Array.isArray(data?.cpmk) || Array.isArray(data?.cpl)) {
            return {
                columns: ["Relasi"],
                rows: [...(data.cpmk || []), ...(data.cpl || [])].map((item) => [item]),
            };
        }
        return null;
    }

    async askSuggestion(question) {
        this.state.input = question;
        await this.send();
    }

    clearConversation() {
        this.state.context = {};
        this.state.messages = [{
            role: "assistant",
            title: "Percakapan dibersihkan",
            type: "suggestion",
            message: "Riwayat percakapan pada halaman ini telah dihapus.",
            data: {},
            suggested_questions: [
                "Berapa jumlah mahasiswa aktif?",
                "Bagaimana capaian CPL?",
                "Tampilkan RPS yang belum divalidasi.",
            ],
        }];
    }

    async send(event) {
        event?.preventDefault();
        const question = this.state.input.trim();
        if (!question || this.state.isLoading) {
            return;
        }
        this.state.messages.push({
            role: "user",
            type: "text",
            message: question,
            data: {},
        });
        this.state.input = "";
        this.state.isLoading = true;
        try {
            const response = await rpc("/web/erpobe/assistant/query", {
                question,
                context: this.state.context,
                page_context: this.getPageContext(),
            });
            this.state.context = response.context || {};
            this.state.messages.push({ role: "assistant", ...response });
        } catch (error) {
            console.error("Academic assistant request failed", error);
            this.state.messages.push({
                role: "assistant",
                title: "Koneksi bermasalah",
                type: "warning",
                message: "Assistant tidak dapat mengambil data saat ini. Silakan coba kembali.",
                data: {},
                suggested_questions: [],
            });
        } finally {
            this.state.isLoading = false;
        }
    }
}

registry.category("main_components").add("erpobe.academic_assistant", {
    Component: AcademicAssistant,
});
