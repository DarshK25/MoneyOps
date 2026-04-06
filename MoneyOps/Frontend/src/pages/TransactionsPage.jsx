
import { useEffect, useMemo, useState } from "react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  AlertTriangle,
  Download,
  Lightbulb,
  Loader2,
  Plus,
  Receipt,
  RefreshCw,
  Search,
  Trash2,
  TrendingDown,
  TrendingUp,
  Upload,
} from "lucide-react";
import { toast } from "sonner";
import { useAuth } from "@clerk/clerk-react";
import { useOnboardingStatus } from "@/hooks/useOnboardingStatus";

const EXPENSE_CATEGORIES = [
  "Hardware / Parts",
  "Electrician Labour",
  "Site Survey",
  "Vehicle Fuel",
  "Office Rent",
  "Salaries",
  "Software Tools",
  "Travel",
  "Office Supplies",
  "Marketing",
  "Miscellaneous",
];

const CATEGORY_COLORS = {
  "Hardware / Parts": "#60A5FA",
  "Electrician Labour": "#A78BFA",
  "Site Survey": "#34D399",
  "Vehicle Fuel": "#F59E0B",
  "Office Rent": "#F472B6",
  Salaries: "#4CBB17",
  "Software Tools": "#67E8F9",
  Travel: "#FB923C",
  "Office Supplies": "#C084FC",
  Marketing: "#E879F9",
  Miscellaneous: "#9CA3AF",
};

const BLANK_EXPENSE = {
  date: new Date().toISOString().split("T")[0],
  description: "",
  category: "Miscellaneous",
  vendor: "",
  amount: "",
  gstAmount: "",
  type: "EXPENSE",
  source: "Manual",
};

const inputStyle = {
  backgroundColor: "#1A1A1A",
  border: "1px solid #2A2A2A",
  borderRadius: "8px",
  color: "#fff",
  padding: "8px 12px",
  fontSize: "14px",
  width: "100%",
  outline: "none",
};

const INR = (n) => typeof n === "number"
  ? `Rs. ${Math.abs(n).toLocaleString("en-IN", { maximumFractionDigits: 0 })}`
  : "Rs. 0";

function normalizeExpense(item) {
  return {
    ...item,
    date: item.date || item.transactionDate || "",
    transactionDate: item.transactionDate || item.date || "",
    vendor: item.vendor || "",
    gstAmount: typeof item.gstAmount === "number" ? item.gstAmount : Number(item.gstAmount || 0),
    source: item.source === "IMPORTED" ? "Imported" : item.source === "MANUAL" ? "Manual" : (item.source || "Manual"),
    type: item.type || "EXPENSE",
  };
}

function CategoryPill({ category }) {
  const color = CATEGORY_COLORS[category] || "#9CA3AF";
  return (
    <span style={{
      backgroundColor: `${color}22`,
      color,
      border: `1px solid ${color}44`,
      borderRadius: 6,
      padding: "2px 8px",
      fontSize: 11,
      fontWeight: 600,
      whiteSpace: "nowrap",
    }}>
      {category || "Uncategorized"}
    </span>
  );
}

export default function TransactionsPage() {
  const { getToken } = useAuth();
  const { userId, orgId } = useOnboardingStatus();
  const [expenses, setExpenses] = useState([]);
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [filterCategory, setFilterCategory] = useState("all");
  const [filterSource, setFilterSource] = useState("all");
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [isImportOpen, setIsImportOpen] = useState(false);
  const [newExpense, setNewExpense] = useState(BLANK_EXPENSE);
  const [uploadFile, setUploadFile] = useState(null);
  const [isSaving, setIsSaving] = useState(false);
  const [isUploading, setIsUploading] = useState(false);

  const periodLabel = new Date().toLocaleString("default", { month: "long", year: "numeric" });

  const authHeaders = async () => {
    const token = await getToken();
    return {
      Authorization: `Bearer ${token}`,
      "X-User-Id": userId,
      "X-Org-Id": orgId,
      "Content-Type": "application/json",
    };
  };

  const fetchExpenses = async () => {
    if (!userId || !orgId) return;
    setLoading(true);
    try {
      const headers = await authHeaders();
      const [txnRes, invRes] = await Promise.allSettled([
        fetch("/api/transactions", { headers }),
        fetch("/api/invoices", { headers }),
      ]);

      if (txnRes.status === "fulfilled" && txnRes.value.ok) {
        const data = await txnRes.value.json();
        const raw = Array.isArray(data) ? data : data.transactions || data.data || [];
        setExpenses(raw.map(normalizeExpense));
      } else {
        setExpenses([]);
      }

      if (invRes.status === "fulfilled" && invRes.value.ok) {
        const data = await invRes.value.json();
        setInvoices(Array.isArray(data) ? data : data.invoices || data.data || []);
      } else {
        setInvoices([]);
      }
    } catch (error) {
      console.error(error);
      toast.error("Failed to load transactions.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchExpenses(); }, [userId, orgId]);
  const stats = useMemo(() => {
    const now = new Date();
    const currentMonth = now.getMonth();
    const currentYear = now.getFullYear();
    const prevMonth = currentMonth === 0 ? 11 : currentMonth - 1;
    const prevYear = currentMonth === 0 ? currentYear - 1 : currentYear;
    const isInMonth = (value, month, year) => {
      const date = new Date(value);
      return date.getMonth() === month && date.getFullYear() === year;
    };

    const allExpenses = expenses.filter((item) => item.type === "EXPENSE" || item.type === "debit");
    const current = allExpenses.filter((item) => isInMonth(item.date, currentMonth, currentYear));
    const previous = allExpenses.filter((item) => isInMonth(item.date, prevMonth, prevYear));
    const totalThis = current.reduce((sum, item) => sum + Math.abs(item.amount || 0), 0);
    const totalPrev = previous.reduce((sum, item) => sum + Math.abs(item.amount || 0), 0);
    const revenue = invoices
      .filter((invoice) => isInMonth(invoice.issueDate || invoice.createdAt, currentMonth, currentYear))
      .reduce((sum, invoice) => sum + (invoice.totalAmount || invoice.amount || 0), 0);

    return {
      totalThis,
      revenue,
      pctChange: totalPrev > 0 ? (((totalThis - totalPrev) / totalPrev) * 100).toFixed(1) : null,
      netMargin: revenue > 0 ? (((revenue - totalThis) / revenue) * 100).toFixed(1) : null,
      uncategorized: allExpenses.filter((item) => !item.category || item.category === "Uncategorized").length,
      gstRecoverable: allExpenses.reduce((sum, item) => sum + Math.abs(item.gstAmount || 0), 0),
    };
  }, [expenses, invoices]);

  const categoryBreakdown = useMemo(() => {
    const totals = {};
    expenses
      .filter((item) => item.type === "EXPENSE" || item.type === "debit")
      .forEach((item) => {
        const category = item.category || "Miscellaneous";
        totals[category] = (totals[category] || 0) + Math.abs(item.amount || 0);
      });
    return Object.entries(totals).sort((a, b) => b[1] - a[1]).slice(0, 6);
  }, [expenses]);

  const filtered = useMemo(() => expenses.filter((item) => {
    const q = searchQuery.toLowerCase();
    const matchesSearch = !searchQuery
      || item.description?.toLowerCase().includes(q)
      || item.vendor?.toLowerCase().includes(q)
      || item.category?.toLowerCase().includes(q)
      || item.merchantName?.toLowerCase().includes(q);
    const matchesCategory = filterCategory === "all" || item.category === filterCategory;
    const matchesSource = filterSource === "all"
      || (filterSource === "Manual" && item.source !== "Imported")
      || (filterSource === "Imported" && item.source === "Imported");
    return matchesSearch && matchesCategory && matchesSource;
  }), [expenses, searchQuery, filterCategory, filterSource]);

  const aiInsight = useMemo(() => {
    if (!categoryBreakdown.length) return null;
    const [topCategory, topAmount] = categoryBreakdown[0];
    const notes = [`${topCategory} is your top spend this month at ${INR(topAmount)}.`];
    if (stats.gstRecoverable > 0) notes.push(`Potential GST ITC available: ${INR(stats.gstRecoverable)}.`);
    if (stats.netMargin !== null && Number.parseFloat(stats.netMargin) < 40) notes.push(`Net margin is ${stats.netMargin}%, below target.`);
    return notes.join(" ");
  }, [categoryBreakdown, stats]);

  const handleAddExpense = async () => {
    if (!newExpense.description || !newExpense.amount) {
      toast.error("Description and amount are required.");
      return;
    }
    setIsSaving(true);
    try {
      const headers = await authHeaders();
      const response = await fetch("/api/transactions", {
        method: "POST",
        headers,
        body: JSON.stringify({
          ...newExpense,
          transactionDate: newExpense.date,
          amount: Number.parseFloat(newExpense.amount),
          gstAmount: newExpense.gstAmount ? Number.parseFloat(newExpense.gstAmount) : 0,
          type: "EXPENSE",
          source: "MANUAL",
        }),
      });
      if (!response.ok) throw new Error("save failed");
      toast.success("Expense recorded.");
      setIsAddOpen(false);
      setNewExpense(BLANK_EXPENSE);
      fetchExpenses();
    } catch (error) {
      console.error(error);
      toast.error("Failed to save expense.");
    } finally {
      setIsSaving(false);
    }
  };

  const handleImport = async () => {
    if (!uploadFile) return toast.error("Select a CSV file first.");
    setIsUploading(true);
    try {
      const token = await getToken();
      const formData = new FormData();
      formData.append("file", uploadFile);
      const response = await fetch("/api/transactions/import", {
        method: "POST",
        headers: { Authorization: `Bearer ${token}`, "X-User-Id": userId, "X-Org-Id": orgId },
        body: formData,
      });
      if (!response.ok) throw new Error("import failed");
      const data = await response.json();
      toast.success(data.message || "Statement imported.");
      setIsImportOpen(false);
      setUploadFile(null);
      fetchExpenses();
    } catch (error) {
      console.error(error);
      toast.error("Failed to import statement.");
    } finally {
      setIsUploading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Delete this expense?")) return;
    try {
      const headers = await authHeaders();
      const response = await fetch(`/api/transactions/${id}`, { method: "DELETE", headers });
      if (!response.ok) throw new Error("delete failed");
      toast.success("Deleted.");
      fetchExpenses();
    } catch (error) {
      console.error(error);
      toast.error("Failed to delete.");
    }
  };

  const exportCSV = () => {
    const rows = [["Date", "Description", "Category", "Vendor", "Amount", "GST", "Source"], ...filtered.map((item) => [
      item.date,
      item.description || item.merchantName || "",
      item.category || "",
      item.vendor || "",
      item.amount,
      item.gstAmount || "",
      item.source || "Manual",
    ])];
    const escapeCell = (value) => `"${String(value ?? "").replaceAll('"', '""')}"`;
    const csv = rows.map((row) => row.map(escapeCell).join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `expenses-${new Date().toISOString().slice(0, 10)}.csv`;
    link.click();
    URL.revokeObjectURL(link.href);
  };

  const maxCatAmount = categoryBreakdown[0]?.[1] || 1;
  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="mo-h1">Transactions</h1>
          <p className="mo-text-secondary mt-1">{orgId ? "Expense tracking for your workspace" : "Your Workspace"} - {periodLabel}</p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <span className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium border" style={{ backgroundColor: "#4CBB1710", borderColor: "#4CBB1730", color: "#4CBB17" }}>
            <span className="text-base" role="img" aria-label="Voice">Mic</span>
            Voice: "Add expense"
          </span>

          <Dialog open={isImportOpen} onOpenChange={setIsImportOpen}>
            <DialogTrigger asChild><button className="mo-btn-secondary flex items-center gap-2"><Upload className="h-4 w-4" /> Import Statement</button></DialogTrigger>
            <DialogContent className="bg-[#111111] border-[#2A2A2A] text-white">
              <DialogHeader><DialogTitle className="text-white">Import Bank Statement</DialogTitle></DialogHeader>
              <div className="flex flex-col gap-4 py-4">
                <p className="text-sm text-[#A0A0A0]">Upload a CSV or Excel export from your bank.</p>
                <div className="rounded-xl border-2 border-dashed border-[#2A2A2A] p-6 text-center cursor-pointer hover:border-[#4CBB17] transition-colors" onClick={() => document.getElementById("import-csv-input")?.click()}>
                  <Upload className="h-8 w-8 text-[#A0A0A0] mx-auto mb-2" />
                  <p className="text-sm text-[#A0A0A0]">{uploadFile ? uploadFile.name : "Click to upload CSV / Excel"}</p>
                  <input id="import-csv-input" type="file" accept=".csv,.xlsx,.xls" className="hidden" onChange={(event) => setUploadFile(event.target.files?.[0] || null)} />
                </div>
                <button onClick={handleImport} disabled={isUploading || !uploadFile} className="mo-btn-primary w-full flex items-center justify-center gap-2 disabled:opacity-40">
                  {isUploading ? <><Loader2 className="h-4 w-4 animate-spin" /> Importing...</> : "Import & Auto-categorize"}
                </button>
              </div>
            </DialogContent>
          </Dialog>

          <Dialog open={isAddOpen} onOpenChange={setIsAddOpen}>
            <DialogTrigger asChild><button className="mo-btn-primary flex items-center gap-2"><Plus className="h-4 w-4" /> Add Expense</button></DialogTrigger>
            <DialogContent className="max-h-[90vh] overflow-y-auto bg-[#111111] border-[#2A2A2A] text-white">
              <DialogHeader><DialogTitle className="text-white">Record Expense</DialogTitle></DialogHeader>
              <div className="flex flex-col gap-4 py-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="flex flex-col gap-1.5"><label className="text-xs text-[#A0A0A0] font-medium">Date *</label><input type="date" value={newExpense.date} onChange={(event) => setNewExpense((prev) => ({ ...prev, date: event.target.value }))} style={{ ...inputStyle, colorScheme: "dark" }} /></div>
                  <div className="flex flex-col gap-1.5"><label className="text-xs text-[#A0A0A0] font-medium">Amount (Rs.) *</label><input type="number" placeholder="0" value={newExpense.amount} onChange={(event) => setNewExpense((prev) => ({ ...prev, amount: event.target.value }))} style={inputStyle} /></div>
                </div>
                <div className="flex flex-col gap-1.5"><label className="text-xs text-[#A0A0A0] font-medium">Description *</label><input placeholder="e.g. DC charger hardware x 3" value={newExpense.description} onChange={(event) => setNewExpense((prev) => ({ ...prev, description: event.target.value }))} style={inputStyle} /></div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="flex flex-col gap-1.5">
                    <label className="text-xs text-[#A0A0A0] font-medium">Category</label>
                    <Select value={newExpense.category} onValueChange={(value) => setNewExpense((prev) => ({ ...prev, category: value }))}>
                      <SelectTrigger className="bg-[#1A1A1A] border-[#2A2A2A] text-white"><SelectValue /></SelectTrigger>
                      <SelectContent className="bg-[#1A1A1A] border-[#2A2A2A]">{EXPENSE_CATEGORIES.map((category) => <SelectItem key={category} value={category} className="text-white">{category}</SelectItem>)}</SelectContent>
                    </Select>
                  </div>
                  <div className="flex flex-col gap-1.5"><label className="text-xs text-[#A0A0A0] font-medium">Vendor</label><input placeholder="e.g. Delta Electronics" value={newExpense.vendor} onChange={(event) => setNewExpense((prev) => ({ ...prev, vendor: event.target.value }))} style={inputStyle} /></div>
                </div>
                <div className="flex flex-col gap-1.5"><label className="text-xs text-[#A0A0A0] font-medium">GST Amount (Rs.) - optional</label><input type="number" placeholder="0" value={newExpense.gstAmount} onChange={(event) => setNewExpense((prev) => ({ ...prev, gstAmount: event.target.value }))} style={inputStyle} /></div>
                <button onClick={handleAddExpense} disabled={isSaving} className="mo-btn-primary w-full flex items-center justify-center gap-2 disabled:opacity-40">{isSaving ? <><Loader2 className="h-4 w-4 animate-spin" /> Saving...</> : "Save Expense"}</button>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        <StatCard title="Total Expenses" value={INR(stats.totalThis)} note={stats.pctChange !== null ? `${Math.abs(Number.parseFloat(stats.pctChange))}% vs last month` : null} trend={stats.pctChange} />
        <SimpleCard title="Gross Revenue" value={INR(stats.revenue)} subtitle="From invoices raised" accent="text-[#4CBB17]" />
        <SimpleCard title="Net Margin" value={stats.netMargin !== null ? `${stats.netMargin}%` : "-"} subtitle="Target: 50%+" />
        <SimpleCard title="Uncategorized" value={stats.uncategorized} subtitle={stats.uncategorized > 0 ? "Needs review" : "All categorized"} accent={stats.uncategorized > 0 ? "text-[#F59E0B]" : "text-[#4CBB17]"} />
      </div>

      <div className="rounded-xl p-4 flex items-center justify-between gap-4 flex-wrap" style={{ backgroundColor: "#1A1A1A", border: "1px solid #2A2A2A" }}>
        <div className="flex items-center gap-3"><div className="p-2 rounded-lg" style={{ backgroundColor: "#4CBB1715" }}><Upload className="h-5 w-5 text-[#4CBB17]" /></div><div><p className="text-sm font-medium text-white">Import bank statement to auto-capture expenses</p><p className="text-xs text-[#A0A0A0] mt-0.5">Download CSV from net banking, upload it here, and review AI categorization.</p></div></div>
        <button onClick={() => setIsImportOpen(true)} className="mo-btn-secondary flex items-center gap-2 text-sm"><Upload className="h-4 w-4" /> Import CSV</button>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="mo-card">
          <div className="flex items-center justify-between mb-4"><h3 className="font-semibold text-white text-sm">By category</h3><span className="text-xs text-[#A0A0A0]">{periodLabel}</span></div>
          {loading ? <div className="flex items-center justify-center h-32"><Loader2 className="h-6 w-6 animate-spin text-[#4CBB17]" /></div> : categoryBreakdown.length === 0 ? <p className="text-sm text-[#A0A0A0] text-center py-8">No expenses yet</p> : <div className="flex flex-col gap-3">{categoryBreakdown.map(([category, amount]) => { const color = CATEGORY_COLORS[category] || "#9CA3AF"; const pct = Math.round((amount / maxCatAmount) * 100); return <div key={category} className="flex items-center gap-3"><span className="text-xs text-[#A0A0A0] w-36 truncate flex-shrink-0">{category}</span><div className="flex-1 h-2 rounded-full overflow-hidden" style={{ backgroundColor: "#2A2A2A" }}><div className="h-full rounded-full" style={{ width: `${pct}%`, backgroundColor: color }} /></div><span className="text-xs font-semibold text-white w-20 text-right flex-shrink-0">{INR(amount)}</span></div>; })}</div>}
        </div>

        <div className="rounded-xl p-4 flex flex-col gap-3" style={{ backgroundColor: "#1A1A1A", border: "1px solid #2A2A2A" }}>
          <div className="flex items-center gap-2"><Lightbulb className="h-4 w-4 text-[#F59E0B]" /><h3 className="font-semibold text-white text-sm">AI Insight</h3></div>
          <p className="text-sm text-[#A0A0A0] leading-relaxed">{aiInsight || "Add expenses to receive insights about spending patterns and tax opportunities."}</p>
          {stats.gstRecoverable > 0 && <div className="rounded-lg p-3 flex items-start gap-2 mt-1" style={{ backgroundColor: "#F59E0B10", border: "1px solid #F59E0B30" }}><AlertTriangle className="h-4 w-4 text-[#F59E0B] flex-shrink-0 mt-0.5" /><p className="text-xs text-[#F59E0B]">GST note: {INR(stats.gstRecoverable)} may be claimable as input credit. Ensure vendor invoices are available.</p></div>}
        </div>
      </div>
      <div className="mo-card !p-0 overflow-hidden">
        <div className="flex items-center justify-between px-5 py-4 border-b flex-wrap gap-3" style={{ borderColor: "#2A2A2A" }}>
          <h3 className="font-semibold text-white text-sm">All expenses - {periodLabel}</h3>
          <div className="flex items-center gap-2 flex-wrap">
            <div className="relative"><Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-[#A0A0A0]" /><input placeholder="Search..." value={searchQuery} onChange={(event) => setSearchQuery(event.target.value)} className="pl-8 pr-3 py-1.5 rounded-lg text-xs text-white placeholder-[#A0A0A0] focus:outline-none" style={{ backgroundColor: "#1A1A1A", border: "1px solid #2A2A2A", width: 160 }} /></div>
            <Select value={filterCategory} onValueChange={setFilterCategory}><SelectTrigger className="bg-[#1A1A1A] border-[#2A2A2A] text-white text-xs h-8 w-36"><SelectValue placeholder="Category" /></SelectTrigger><SelectContent className="bg-[#1A1A1A] border-[#2A2A2A]"><SelectItem value="all" className="text-white text-xs">All Categories</SelectItem>{EXPENSE_CATEGORIES.map((category) => <SelectItem key={category} value={category} className="text-white text-xs">{category}</SelectItem>)}</SelectContent></Select>
            <Select value={filterSource} onValueChange={setFilterSource}><SelectTrigger className="bg-[#1A1A1A] border-[#2A2A2A] text-white text-xs h-8 w-28"><SelectValue placeholder="Source" /></SelectTrigger><SelectContent className="bg-[#1A1A1A] border-[#2A2A2A]"><SelectItem value="all" className="text-white text-xs">All Sources</SelectItem><SelectItem value="Manual" className="text-white text-xs">Manual</SelectItem><SelectItem value="Imported" className="text-white text-xs">Imported</SelectItem></SelectContent></Select>
            <button onClick={fetchExpenses} className="mo-btn-secondary flex items-center gap-1.5 text-xs py-1.5 px-3"><RefreshCw className="h-3 w-3" /></button>
            <button onClick={exportCSV} className="mo-btn-secondary flex items-center gap-1.5 text-xs py-1.5 px-3"><Download className="h-3.5 w-3.5" /> Export</button>
          </div>
        </div>

        {loading ? <div className="flex items-center justify-center h-48"><Loader2 className="h-8 w-8 animate-spin text-[#4CBB17]" /></div> : filtered.length === 0 ? <div className="flex flex-col items-center justify-center py-16"><Receipt className="h-16 w-16 text-[#2A2A2A] mb-4" /><h3 className="text-lg font-semibold text-white mb-2">No expenses yet</h3><p className="text-[#A0A0A0] text-sm text-center max-w-xs">Record your first expense manually or import a bank statement CSV.</p><div className="mt-6 flex gap-2"><button onClick={() => setIsAddOpen(true)} className="mo-btn-primary flex items-center gap-2 text-sm"><Plus className="h-4 w-4" /> Add Expense</button><button onClick={() => setIsImportOpen(true)} className="mo-btn-secondary flex items-center gap-2 text-sm"><Upload className="h-4 w-4" /> Import CSV</button></div></div> : <div className="overflow-x-auto"><table className="w-full text-sm"><thead><tr style={{ borderBottom: "1px solid #2A2A2A" }}>{["DATE", "DESCRIPTION", "CATEGORY", "VENDOR", "AMOUNT", "GST", "SOURCE"].map((heading) => <th key={heading} className="px-4 py-3 text-left text-[10px] font-semibold tracking-widest text-[#A0A0A0]">{heading}</th>)}<th className="px-4 py-3" /></tr></thead><tbody className="divide-y divide-[#1A1A1A]">{filtered.map((expense) => { const isUncategorized = !expense.category || expense.category === "Uncategorized"; return <tr key={expense.id} className="group hover:bg-[#1A1A1A] transition-colors" style={isUncategorized ? { backgroundColor: "#F59E0B08" } : {}}><td className="px-4 py-3 text-[#A0A0A0] whitespace-nowrap text-xs">{expense.date ? new Date(expense.date).toLocaleDateString("en-IN", { day: "numeric", month: "short" }) : "-"}</td><td className="px-4 py-3 text-white max-w-[200px] truncate">{expense.description || expense.merchantName || "-"}</td><td className="px-4 py-3">{isUncategorized ? <span className="flex items-center gap-1 text-xs text-[#F59E0B]"><AlertTriangle className="h-3 w-3" /> Uncategorized</span> : <CategoryPill category={expense.category} />}</td><td className="px-4 py-3 text-[#A0A0A0] text-xs">{expense.vendor || "-"}</td><td className="px-4 py-3 font-semibold text-white whitespace-nowrap">{INR(expense.amount)}</td><td className="px-4 py-3 text-[#A0A0A0] text-xs whitespace-nowrap">{expense.gstAmount ? INR(expense.gstAmount) : "-"}</td><td className="px-4 py-3"><span className="text-xs px-2 py-0.5 rounded-md font-medium" style={{ backgroundColor: expense.source === "Imported" ? "#60A5FA15" : "#4CBB1715", color: expense.source === "Imported" ? "#60A5FA" : "#4CBB17" }}>{expense.source || "Manual"}</span></td><td className="px-4 py-3"><button className="opacity-0 group-hover:opacity-100 transition-opacity p-1.5 rounded hover:bg-[#CD1C1820] text-[#A0A0A0] hover:text-[#CD1C18]" onClick={() => handleDelete(expense.id)}><Trash2 className="h-3.5 w-3.5" /></button></td></tr>; })}</tbody></table></div>}
      </div>
    </div>
  );
}

function SimpleCard({ title, value, subtitle, accent = "text-white" }) {
  return <div className="mo-card"><p className="text-xs text-[#A0A0A0] font-medium uppercase tracking-wide mb-2">{title}</p><p className={`text-2xl font-bold ${accent}`}>{value}</p>{subtitle && <p className="text-xs text-[#A0A0A0] mt-1">{subtitle}</p>}</div>;
}

function StatCard({ title, value, note, trend }) {
  return <div className="mo-card"><p className="text-xs text-[#A0A0A0] font-medium uppercase tracking-wide mb-2">{title}</p><p className="text-2xl font-bold text-white">{value}</p>{note && <p className={`text-xs mt-1 flex items-center gap-1 ${Number.parseFloat(trend) > 0 ? "text-[#CD1C18]" : "text-[#4CBB17]"}`}>{Number.parseFloat(trend) > 0 ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}{note}</p>}</div>;
}
