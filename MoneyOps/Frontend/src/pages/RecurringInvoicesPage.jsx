import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
    Plus,
    Loader2,
    RefreshCw,
    Eye,
    Trash2,
    Calendar,
    MoreVertical,
    Search,
    Play
} from "lucide-react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { useUser } from "@/contexts/AuthContext";
import { useOnboardingStatus } from "@/hooks/useOnboardingStatus";

const FREQUENCY_LABELS = {
    DAILY: "Daily",
    WEEKLY: "Weekly",
    MONTHLY: "Monthly",
    YEARLY: "Yearly"
};

export default function RecurringInvoicesPage() {
    const { user } = useUser();
    const { userId: internalUserId, orgId: internalOrgId } = useOnboardingStatus();
    const navigate = useNavigate();
    const [recurringInvoices, setRecurringInvoices] = useState([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState("");
    const [actionLoading, setActionLoading] = useState(null);
    const [showCreateForm, setShowCreateForm] = useState(false);
    const [clients, setClients] = useState([]);
    const [formData, setFormData] = useState({
        clientId: "",
        frequency: "MONTHLY",
        interval: 1,
        startDate: new Date().toISOString().split('T')[0],
        endDate: "",
        items: [{ description: "", quantity: 1, rate: "", gstPercent: "18" }],
        currency: "INR",
        paymentTerms: 30,
        notes: ""
    });

    useEffect(() => {
        if (internalUserId && internalOrgId) {
            fetchRecurringInvoices();
            fetchClients();
        }
    }, [internalUserId, internalOrgId]);

    const fetchRecurringInvoices = async () => {
        try {
            setLoading(true);
            const data = await api.get("/api/recurring-invoices");
            setRecurringInvoices(Array.isArray(data) ? data : data?.data?.content || data?.content || []);
        } catch {
            toast.error("Failed to load recurring invoices");
            setRecurringInvoices([]);
        } finally {
            setLoading(false);
        }
    };

    const fetchClients = async () => {
        try {
            const data = await api.get("/api/clients");
            setClients(Array.isArray(data) ? data : data?.data?.content || data?.content || []);
        } catch {
            // Ignore client fetch errors
        }
    };

    const handleCreateRecurring = async (e) => {
        e.preventDefault();
        try {
            const selectedClient = clients.find(c => c.id === formData.clientId);

            const payload = {
                ...formData,
                clientName: selectedClient?.name || "",
                clientEmail: selectedClient?.email || "",
                clientCompany: selectedClient?.company || "",
                clientPhone: selectedClient?.phoneNumber || "",
                items: formData.items.map(item => ({
                    type: "PRODUCT",
                    description: item.description,
                    quantity: parseInt(item.quantity) || 1,
                    rate: parseFloat(item.rate) || 0,
                    gstPercent: parseFloat(item.gstPercent) || 0
                }))
            };

            await api.post("/api/recurring-invoices", payload);
            toast.success("Recurring invoice schedule created");
            setShowCreateForm(false);
            setFormData({
                clientId: "",
                frequency: "MONTHLY",
                interval: 1,
                startDate: new Date().toISOString().split('T')[0],
                endDate: "",
                items: [{ description: "", quantity: 1, rate: "", gstPercent: "18" }],
                currency: "INR",
                paymentTerms: 30,
                notes: ""
            });
            fetchRecurringInvoices();
        } catch (error) {
            toast.error(error.message || "Failed to create recurring invoice");
        }
    };

    const handleDeactivate = async (id) => {
        if (!window.confirm("Deactivate this recurring invoice schedule?")) return;
        try {
            await api.delete(`/api/recurring-invoices/${id}`);
            toast.success("Recurring invoice deactivated");
            fetchRecurringInvoices();
        } catch (error) {
            toast.error(error.message || "Failed to deactivate");
        }
    };

    const handleGenerateNow = async (id) => {
        try {
            setActionLoading(id);
            await api.post(`/api/recurring-invoices/${id}/generate`);
            toast.success("Invoice generated successfully");
            fetchRecurringInvoices();
        } catch (error) {
            toast.error(error.message || "Failed to generate invoice");
        } finally {
            setActionLoading(null);
        }
    };

    const addItem = () => {
        setFormData({
            ...formData,
            items: [...formData.items, { description: "", quantity: 1, rate: "", gstPercent: "18" }]
        });
    };

    const updateItem = (index, field, value) => {
        const newItems = [...formData.items];
        newItems[index] = { ...newItems[index], [field]: value };
        setFormData({ ...formData, items: newItems });
    };

    const removeItem = (index) => {
        setFormData({ ...formData, items: formData.items.filter((_, i) => i !== index) });
    };

    const filteredInvoices = recurringInvoices.filter((inv) => {
        const searchMatch =
            !searchQuery ||
            inv.clientName?.toLowerCase().includes(searchQuery.toLowerCase()) ||
            inv.notes?.toLowerCase().includes(searchQuery.toLowerCase());
        return searchMatch;
    });

    const formatDate = (dateStr) => {
        if (!dateStr) return "N/A";
        return new Date(dateStr).toLocaleDateString("en-IN", {
            day: "numeric",
            month: "short",
            year: "numeric"
        });
    };

    return (
        <div className="flex flex-col gap-6">
            <div className="flex items-center justify-between flex-wrap gap-4">
                <div>
                    <h1 className="mo-h1">Recurring Invoices</h1>
                    <p className="mo-text-secondary mt-1">Manage recurring invoice schedules</p>
                </div>
                <div className="flex items-center gap-2">
                    <button
                        className="mo-btn-secondary flex items-center gap-2"
                        onClick={fetchRecurringInvoices}
                        disabled={loading}
                        aria-label="Refresh recurring invoices"
                    >
                        <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
                    </button>
                    <button
                        className="mo-btn-primary flex items-center gap-2"
                        onClick={() => setShowCreateForm(true)}
                    >
                        <Plus className="h-4 w-4" /> New Schedule
                    </button>
                </div>
            </div>

            {showCreateForm && (
                <div className="mo-card">
                    <h2 className="mo-h2 mb-4">Create Recurring Invoice</h2>
                    <form onSubmit={handleCreateRecurring} className="space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="mo-label">Client</label>
                                <select
                                    className="mo-input"
                                    value={formData.clientId}
                                    onChange={(e) => setFormData({ ...formData, clientId: e.target.value })}
                                    required
                                >
                                    <option value="">Select Client</option>
                                    {clients.map(client => (
                                        <option key={client.id} value={client.id}>{client.name}</option>
                                    ))}
                                </select>
                            </div>
                            <div>
                                <label className="mo-label">Frequency</label>
                                <select
                                    className="mo-input"
                                    value={formData.frequency}
                                    onChange={(e) => setFormData({ ...formData, frequency: e.target.value })}
                                >
                                    <option value="DAILY">Daily</option>
                                    <option value="WEEKLY">Weekly</option>
                                    <option value="MONTHLY">Monthly</option>
                                    <option value="YEARLY">Yearly</option>
                                </select>
                            </div>
                            <div>
                                <label className="mo-label">Interval</label>
                                <Input
                                    type="number"
                                    value={formData.interval}
                                    onChange={(e) => setFormData({ ...formData, interval: parseInt(e.target.value) || 1 })}
                                    min="1"
                                    className="mo-input"
                                />
                            </div>
                            <div>
                                <label className="mo-label">Payment Terms (days)</label>
                                <Input
                                    type="number"
                                    value={formData.paymentTerms}
                                    onChange={(e) => setFormData({ ...formData, paymentTerms: parseInt(e.target.value) || 30 })}
                                    className="mo-input"
                                />
                            </div>
                            <div>
                                <label className="mo-label">Start Date</label>
                                <Input
                                    type="date"
                                    value={formData.startDate}
                                    onChange={(e) => setFormData({ ...formData, startDate: e.target.value })}
                                    required
                                    className="mo-input"
                                />
                            </div>
                            <div>
                                <label className="mo-label">End Date (optional)</label>
                                <Input
                                    type="date"
                                    value={formData.endDate}
                                    onChange={(e) => setFormData({ ...formData, endDate: e.target.value })}
                                    className="mo-input"
                                />
                            </div>
                        </div>

                        <div>
                            <label className="mo-label">Items</label>
                            {formData.items.map((item, index) => (
                                <div key={index} className="grid grid-cols-5 gap-2 mb-2">
                                    <Input
                                        placeholder="Description"
                                        value={item.description}
                                        onChange={(e) => updateItem(index, "description", e.target.value)}
                                        className="mo-input col-span-2"
                                        required
                                    />
                                    <Input
                                        type="number"
                                        placeholder="Qty"
                                        value={item.quantity}
                                        onChange={(e) => updateItem(index, "quantity", e.target.value)}
                                        className="mo-input"
                                        min="1"
                                    />
                                    <Input
                                        type="number"
                                        placeholder="Rate"
                                        value={item.rate}
                                        onChange={(e) => updateItem(index, "rate", e.target.value)}
                                        className="mo-input"
                                        min="0"
                                        step="0.01"
                                    />
                                    <div className="flex gap-1">
                                        <Input
                                            type="number"
                                            placeholder="GST %"
                                            value={item.gstPercent}
                                            onChange={(e) => updateItem(index, "gstPercent", e.target.value)}
                                            className="mo-input"
                                        />
                                        {formData.items.length > 1 && (
                                            <button type="button" onClick={() => removeItem(index)} className="mo-btn-danger p-2">
                                                <Trash2 className="h-4 w-4" />
                                            </button>
                                        )}
                                    </div>
                                </div>
                            ))}
                            <button type="button" onClick={addItem} className="mo-btn-secondary mt-2">
                                <Plus className="h-4 w-4 mr-1" /> Add Item
                            </button>
                        </div>

                        <div>
                            <label className="mo-label">Notes</label>
                            <textarea
                                className="mo-input min-h-[80px]"
                                value={formData.notes}
                                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                                placeholder="Optional notes"
                            />
                        </div>

                        <div className="flex gap-2">
                            <button type="submit" className="mo-btn-primary">Create Schedule</button>
                            <button
                                type="button"
                                className="mo-btn-secondary"
                                onClick={() => setShowCreateForm(false)}
                            >
                                Cancel
                            </button>
                        </div>
                    </form>
                </div>
            )}

            <div className="mo-card">
                <div className="mb-4">
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[#A0A0A0]" />
                        <Input
                            placeholder="Search recurring invoices..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="mo-input pl-10"
                        />
                    </div>
                </div>

                {loading ? (
                    <div className="flex justify-center py-8">
                        <Loader2 className="h-8 w-8 animate-spin text-[#4CBB17]" />
                    </div>
                ) : filteredInvoices.length === 0 ? (
                    <div className="text-center py-8 text-[#A0A0A0]">
                        <Calendar className="h-12 w-12 mx-auto mb-4 text-[#A0A0A0]" />
                        <p>No recurring invoice schedules found</p>
                        <p className="text-sm mt-1">Create a schedule to automatically generate invoices</p>
                    </div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full text-left">
                            <thead>
                                <tr className="border-b border-[#333]">
                                    <th className="pb-3 text-sm font-medium text-[#A0A0A0]">Client</th>
                                    <th className="pb-3 text-sm font-medium text-[#A0A0A0]">Frequency</th>
                                    <th className="pb-3 text-sm font-medium text-[#A0A0A0]">Next Generation</th>
                                    <th className="pb-3 text-sm font-medium text-[#A0A0A0]">Status</th>
                                    <th className="pb-3 text-sm font-medium text-[#A0A0A0]">Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {filteredInvoices.map((inv) => (
                                    <tr key={inv.id} className="border-b border-[#222] hover:bg-[#1a1a1a]">
                                        <td className="py-3">
                                            <div>
                                                <p className="text-white font-medium">{inv.clientName || "Unknown"}</p>
                                                <p className="text-xs text-[#A0A0A0]">{inv.clientCompany || ""}</p>
                                            </div>
                                        </td>
                                        <td className="py-3">
                                            <span className="text-sm text-[#A0A0A0]">
                                                {FREQUENCY_LABELS[inv.frequency] || inv.frequency}
                                                {inv.interval > 1 ? ` (every ${inv.interval})` : ""}
                                            </span>
                                        </td>
                                        <td className="py-3">
                                            <span className="text-sm text-[#A0A0A0]">
                                                {formatDate(inv.nextGenerationDate)}
                                            </span>
                                        </td>
                                        <td className="py-3">
                                            <span className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium ${
                                                inv.isActive
                                                    ? "bg-[#4CBB1720] text-[#4CBB17] border border-[#4CBB1740]"
                                                    : "bg-[#A0A0A020] text-[#A0A0A0] border border-[#A0A0A040]"
                                            }`}>
                                                {inv.isActive ? "Active" : "Inactive"}
                                            </span>
                                        </td>
                                        <td className="py-3">
                                            <div className="flex items-center gap-2">
                                                <button
                                                    className="mo-btn-secondary p-2"
                                                    onClick={() => handleGenerateNow(inv.id)}
                                                    disabled={actionLoading === inv.id}
                                                    title="Generate Invoice Now"
                                                >
                                                    {actionLoading === inv.id ? (
                                                        <Loader2 className="h-4 w-4 animate-spin" />
                                                    ) : (
                                                        <Play className="h-4 w-4" />
                                                    )}
                                                </button>
                                                <DropdownMenu>
                                                    <DropdownMenuTrigger asChild>
                                                        <button className="mo-btn-secondary p-2">
                                                            <MoreVertical className="h-4 w-4" />
                                                        </button>
                                                    </DropdownMenuTrigger>
                                                    <DropdownMenuContent className="bg-[#1a1a1a] border-[#333]">
                                                        <DropdownMenuItem
                                                            className="text-red-400 hover:text-red-300 cursor-pointer"
                                                            onClick={() => handleDeactivate(inv.id)}
                                                        >
                                                            <Trash2 className="h-4 w-4 mr-2" />
                                                            Deactivate
                                                        </DropdownMenuItem>
                                                    </DropdownMenuContent>
                                                </DropdownMenu>
                                            </div>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    );
}
