import { createPortal } from "react-dom";
import { motion, AnimatePresence } from "framer-motion";
import { CheckCircle2, FileText, IndianRupee, Percent, X } from "lucide-react";

const INR = (value) =>`Rs. ${Number(value || 0).toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;

export default function LiveInvoicePreview({ draft, onUpdate, onClose, onConfirm }) {
    if (!draft) return null;

    const quantity = draft.item_type === "PRODUCT" ? Number(draft.quantity || 0) : 1;
    const subtotal = Number(draft.amount || 0) * (quantity || 1);
    const gstPercent = Number(draft.gst_percent || 0);
    const gstTotal = subtotal * (gstPercent / 100);
    const total = subtotal + gstTotal;

    const updateField = (field, value) => {
        onUpdate?.({ ...draft, [field]: value });
    };

    return createPortal(
        <AnimatePresence>
            <div className="fixed inset-0 z-[9998] bg-black/75 backdrop-blur-md p-4 flex items-center justify-center">
                <motion.div
                    initial={{ opacity: 0, y: 20, scale: 0.96 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: 20, scale: 0.96 }}
                    className="w-full max-w-lg rounded-2xl border border-white/10 bg-[#111] shadow-2xl overflow-hidden"
                >
                    <div className="flex items-center justify-between px-5 py-4 border-b border-white/10">
                        <div className="flex items-center gap-2">
                            <FileText className="h-4 w-4 text-[#4CBB17]" />
                            <div>
                                <p className="text-sm font-semibold text-white">Live Invoice Preview</p>
                                <p className="text-[11px] text-white/45">Voice draft updates appear here</p>
                            </div>
                        </div>
                        <button onClick={onClose} className="text-white/35 hover:text-white transition-colors">
                            <X className="h-4 w-4" />
                        </button>
                    </div>

                    <div className="p-5 space-y-4">
                        <div className="grid gap-3 md:grid-cols-2">
                            <PreviewField label="Client" value={draft.client_name || "Pending"} />
                            <PreviewField label="Due Date" value={draft.due_date || "Pending"} />
                            <PreviewField label="Type" value={draft.item_type || "Pending"} />
                            <PreviewField label="Session" value={draft.session_id || "Current"} muted />
                        </div>

                        <div className="space-y-2">
                            <label className="text-[11px] uppercase tracking-widest text-white/40">Description</label>
                            <textarea
                                value={draft.item_description || ""}
                                onChange={(e) => updateField("item_description", e.target.value)}
                                className="w-full min-h-24 rounded-xl border border-white/10 bg-white/[0.03] px-4 py-3 text-sm text-white outline-none focus:border-[#4CBB17]/50"
                                placeholder="Invoice line item description"
                            />
                        </div>

                        <div className="grid gap-3 md:grid-cols-3">
                            <EditableField
                                label="Amount"
                                icon={<IndianRupee className="h-3.5 w-3.5" />}
                                value={draft.amount || ""}
                                onChange={(value) => updateField("amount", value)}
                            />
                            <EditableField
                                label="Quantity"
                                value={draft.item_type === "PRODUCT" ? draft.quantity || "" : "1"}
                                disabled={draft.item_type !== "PRODUCT"}
                                onChange={(value) => updateField("quantity", value)}
                            />
                            <EditableField
                                label="GST %"
                                icon={<Percent className="h-3.5 w-3.5" />}
                                value={draft.gst_percent || ""}
                                onChange={(value) => updateField("gst_percent", value)}
                            />
                        </div>

                        <div className="rounded-xl border border-white/10 bg-white/[0.03] p-4 grid gap-3 md:grid-cols-3">
                            <AmountBlock label="Subtotal" value={INR(subtotal)} />
                            <AmountBlock label="GST" value={INR(gstTotal)} />
                            <AmountBlock label="Total" value={INR(total)} highlight />
                        </div>

                        {draft.awaiting_confirmation && (
                            <div className="rounded-xl border border-[#4CBB17]/30 bg-[#4CBB17]/10 p-3 flex items-start gap-2">
                                <CheckCircle2 className="h-4 w-4 text-[#4CBB17] mt-0.5" />
                                <p className="text-xs text-[#CDEFB8]">
                                    The voice agent is waiting for confirmation. You can confirm here or by voice.
                                </p>
                            </div>
                        )}
                    </div>

                    <div className="px-5 py-4 border-t border-white/10 flex items-center justify-end gap-3">
                        <button onClick={onClose} className="mo-btn-secondary text-sm">
                            Close
                        </button>
                        <button
                            onClick={onConfirm}
                            disabled={!draft.awaiting_confirmation}
                            className="mo-btn-primary text-sm disabled:opacity-40"
                        >
                            Confirm Invoice
                        </button>
                    </div>
                </motion.div>
            </div>
        </AnimatePresence>,
        document.body
    );
}

function PreviewField({ label, value, muted = false }) {
    return (
        <div className="rounded-xl border border-white/10 bg-white/[0.03] px-4 py-3">
            <p className="text-[11px] uppercase tracking-widest text-white/35">{label}</p>
            <p className={`mt-1 text-sm ${muted ? "text-white/55" : "text-white"}`}>{value}</p>
        </div>
    );
}

function EditableField({ label, value, onChange, icon, disabled = false }) {
    return (
        <div className="space-y-2">
            <label className="text-[11px] uppercase tracking-widest text-white/40 flex items-center gap-1.5">
                {icon}
                {label}
            </label>
            <input
                value={value}
                disabled={disabled}
                onChange={(e) => onChange?.(e.target.value)}
                className="w-full rounded-xl border border-white/10 bg-white/[0.03] px-3 py-2 text-sm text-white outline-none focus:border-[#4CBB17]/50 disabled:opacity-45"
            />
        </div>
    );
}

function AmountBlock({ label, value, highlight = false }) {
    return (
        <div>
            <p className="text-[11px] uppercase tracking-widest text-white/35">{label}</p>
            <p className={`mt-1 text-lg font-semibold ${highlight ? "text-[#4CBB17]" : "text-white"}`}>{value}</p>
        </div>
    );
}

