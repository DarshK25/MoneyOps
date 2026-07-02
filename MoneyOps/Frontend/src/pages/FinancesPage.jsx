import { useState, useEffect, useMemo } from "react";
import { Calculator, TrendingUp, AlertCircle, CheckCircle, Loader2, RefreshCw, ArrowUpRight, ArrowDownRight, IndianRupee } from "lucide-react";
import { toast } from "sonner";
import { useAuth, useUser } from "@/contexts/AuthContext";
import { useOnboardingStatus } from "@/hooks/useOnboardingStatus";

function formatInr(value) {
    return `₹${Number(value || 0).toLocaleString("en-IN")}`;
}

function toMonthKey(value) {
    if (!value) return null;
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return null;
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}`;
}

export default function FinancesPage() {
    const { getToken } = useAuth();
    const { user } = useUser();
    const { userId: internalUserId, orgId: internalOrgId } = useOnboardingStatus();
    const [loading, setLoading] = useState(true);
    const [transactions, setTransactions] = useState([]);
    const [invoices, setInvoices] = useState([]);
    const [metrics, setMetrics] = useState(null);
    const [orgName, setOrgName] = useState("");

    useEffect(() => {
        if (internalUserId && internalOrgId) {
            fetchFinanceData();
        }
    }, [internalUserId, internalOrgId]);

    async function fetchFinanceData() {
        setLoading(true);
        try {
            const token = await getToken();
            const headers = {
                Authorization: `Bearer ${token}`,
                "X-User-Id": internalUserId,
                "X-Org-Id": internalOrgId,
            };

            const [txRes, invRes, metricsRes, orgRes] = await Promise.all([
                fetch("/api/transactions", { headers }),
                fetch("/api/invoices", { headers }),
                fetch("/api/finance-intelligence/metrics?businessId=1", { headers }),
                fetch("/api/org/my", { headers }),
            ]);

            if (txRes.ok) {
                const data = await txRes.json();
                setTransactions(Array.isArray(data) ? data : data?.content || data.transactions || []);
            }
            if (invRes.ok) {
                const data = await invRes.json();
                setInvoices(Array.isArray(data) ? data : data?.content || data?.data || []);
            }
            if (metricsRes.ok) setMetrics(await metricsRes.json());
            if (orgRes.ok) {
                const orgData = await orgRes.json();
                setOrgName(orgData?.data?.legalName || "");
            }
        } catch (error) {
            console.error("Failed to fetch finance data:", error);
            toast.error("Failed to load financial data");
        } finally {
            setLoading(false);
        }
    }

    const { totalRevenue, totalExpenses, netWorth, netProfit, collectionRate, overdueCount, overdueAmount } = useMemo(() => {
        const income = transactions
            .filter((t) => String(t.type || "").toUpperCase() === "INCOME")
            .reduce((sum, t) => sum + Math.abs(Number(t.amount || 0)), 0);
        const expense = transactions
            .filter((t) => String(t.type || "").toUpperCase() === "EXPENSE")
            .reduce((sum, t) => sum + Math.abs(Number(t.amount || 0)), 0);
        const invoiceRevenue = invoices.reduce((sum, inv) => sum + Number(inv.totalAmount || 0), 0);
        const revenue = Math.max(income, invoiceRevenue);
        const profit = metrics?.netProfit || revenue - expense;
        return {
            totalRevenue: revenue,
            totalExpenses: expense,
            netWorth: revenue - expense,
            netProfit: profit,
            collectionRate: metrics?.collectionRate || 0,
            overdueCount: metrics?.overdueCount || 0,
            overdueAmount: metrics?.overdueAmount || 0,
        };
    }, [transactions, invoices, metrics]);

    const monthlyGrowth = useMemo(() => {
        const monthMap = {};
        transactions.forEach((t) => {
            const key = toMonthKey(t.transactionDate || t.date || t.createdAt);
            if (!key) return;
            const amount = Number(t.amount || 0);
            if (!monthMap[key]) monthMap[key] = 0;
            if (String(t.type || "").toUpperCase() === "INCOME") monthMap[key] += amount;
            else monthMap[key] -= Math.abs(amount);
        });
        const sorted = Object.keys(monthMap).sort();
        if (sorted.length < 2) return null;
        const last = monthMap[sorted[sorted.length - 1]];
        const prev = monthMap[sorted[sorted.length - 2]];
        if (!prev || prev === 0) return null;
        return ((last - prev) / Math.abs(prev)) * 100;
    }, [transactions]);

    const recentInvoices = useMemo(() => {
        return [...invoices]
            .sort((a, b) => new Date(b.issueDate || b.createdAt).getTime() - new Date(a.issueDate || a.createdAt).getTime())
            .slice(0, 4);
    }, [invoices]);

    const quickActions = useMemo(() => [
        { label: "View Transactions", icon: Calculator, path: "/transactions" },
        { label: "View Cash Flow", icon: TrendingUp, path: "/cashflow" },
        { label: "Review Overdue", icon: AlertCircle, path: "/invoices", count: overdueCount },
        { label: "Generate Report", icon: CheckCircle, path: "/analytics" },
    ], [overdueCount]);

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <Loader2 className="h-8 w-8 animate-spin text-[#4CBB17]" />
            </div>
        );
    }

    return (
        <div className="flex flex-col gap-6">
            <div className="flex items-center justify-between flex-wrap gap-4">
                <div>
                    <h1 className="mo-h1">Finances</h1>
                    <p className="mo-text-secondary mt-1">
                        {orgName ? `${orgName} · ` : ""}Manage your accounts, transactions, and financial data
                    </p>
                </div>
                <button onClick={fetchFinanceData} className="mo-btn-secondary flex items-center gap-2">
                    <RefreshCw className="h-4 w-4" /> Refresh
                </button>
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <div className="mo-stat-card">
                    <div className="flex items-center justify-between mb-3">
                        <span className="text-sm text-[#A0A0A0] font-medium">Total Revenue</span>
                        <ArrowUpRight className="h-4 w-4 text-[#4CBB17]" />
                    </div>
                    <div className="text-2xl font-bold text-white">{formatInr(totalRevenue)}</div>
                    <p className="text-xs text-[#4CBB17] mt-1">From invoices & income</p>
                </div>
                <div className="mo-stat-card">
                    <div className="flex items-center justify-between mb-3">
                        <span className="text-sm text-[#A0A0A0] font-medium">Total Expenses</span>
                        <ArrowDownRight className="h-4 w-4 text-[#CD1C18]" />
                    </div>
                    <div className="text-2xl font-bold text-white">{formatInr(totalExpenses)}</div>
                    <p className="text-xs text-[#CD1C18] mt-1">Recorded transactions</p>
                </div>
                <div className="mo-stat-card">
                    <div className="flex items-center justify-between mb-3">
                        <span className="text-sm text-[#A0A0A0] font-medium">Net Worth</span>
                        <IndianRupee className="h-4 w-4 text-[#A0A0A0]" />
                    </div>
                    <div className="text-2xl font-bold" style={{ color: netWorth >= 0 ? "#4CBB17" : "#CD1C18" }}>
                        {formatInr(netWorth)}
                    </div>
                    <p className="text-xs text-[#A0A0A0] mt-1">Revenue minus expenses</p>
                </div>
                <div className="mo-stat-card">
                    <div className="flex items-center justify-between mb-3">
                        <span className="text-sm text-[#A0A0A0] font-medium">Monthly Growth</span>
                        <TrendingUp className="h-4 w-4 text-[#A0A0A0]" />
                    </div>
                    <div className="text-2xl font-bold" style={{ color: monthlyGrowth !== null && monthlyGrowth >= 0 ? "#4CBB17" : "#A0A0A0" }}>
                        {monthlyGrowth !== null ? `${monthlyGrowth >= 0 ? "+" : ""}${monthlyGrowth.toFixed(1)}%` : "—"}
                    </div>
                    <p className="text-xs text-[#A0A0A0] mt-1">Month over month</p>
                </div>
            </div>

            <div className="grid gap-6 md:grid-cols-2">
                <div className="mo-card">
                    <h2 className="mo-h2 mb-1">Recent Activity</h2>
                    <p className="mo-text-secondary mb-4">Latest invoices and transactions</p>
                    {recentInvoices.length === 0 && transactions.length === 0 ? (
                        <p className="text-sm text-[#A0A0A0] text-center py-8">No financial activity recorded yet.</p>
                    ) : (
                        <div className="space-y-3">
                            {recentInvoices.map((inv) => {
                                const isPaid = String(inv.status || "").toLowerCase() === "paid";
                                return (
                                    <div key={inv.id || inv._id} className="flex items-center gap-3 p-3 bg-[#111111] rounded-lg border border-[#2A2A2A]">
                                        <div className="flex-shrink-0">
                                            {isPaid ? (
                                                <CheckCircle className="h-5 w-5 text-[#4CBB17]" />
                                            ) : (
                                                <AlertCircle className="h-5 w-5 text-[#FFB300]" />
                                            )}
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <p className="text-sm font-medium text-white truncate">
                                                Invoice #{inv.invoiceNumber} — {inv.clientName || "No client"}
                                            </p>
                                            <p className="text-xs text-[#A0A0A0] mt-0.5">
                                                {inv.issueDate ? new Date(inv.issueDate).toLocaleDateString() : ""} · {formatInr(inv.totalAmount)}
                                            </p>
                                        </div>
                                        <span className={`text-xs px-2 py-0.5 rounded-md font-medium flex-shrink-0 border ${isPaid
                                            ? "bg-[#4CBB1720] text-[#4CBB17] border-[#4CBB1740]"
                                            : "bg-[#FFB30020] text-[#FFB300] border-[#FFB30040]"
                                        }`}>
                                            {inv.status}
                                        </span>
                                    </div>
                                );
                            })}
                        </div>
                    )}
                </div>

                <div className="mo-card">
                    <h2 className="mo-h2 mb-1">Quick Actions</h2>
                    <p className="mo-text-secondary mb-4">Common finance management tasks</p>
                    <div className="space-y-2">
                        {quickActions.map(({ label, icon: Icon, path, count }) => (
                            <a
                                key={label}
                                href={path}
                                className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium text-[#A0A0A0] border border-[#2A2A2A] bg-[#111111] hover:border-[#4CBB17] hover:text-white transition-all"
                            >
                                <Icon className="h-4 w-4 text-[#4CBB17]" />
                                {label}
                                {count > 0 && (
                                    <span className="ml-auto text-xs px-2 py-0.5 rounded-full bg-[#CD1C1820] text-[#CD1C18] border border-[#CD1C1840]">
                                        {count} overdue
                                    </span>
                                )}
                            </a>
                        ))}
                    </div>
                </div>
            </div>

            <div className="mo-card">
                <h2 className="mo-h2 mb-1">Financial Summary</h2>
                <p className="mo-text-secondary mb-6">Overview of your financial position from live data</p>
                <div className="grid gap-6 md:grid-cols-4">
                    <div className="text-center p-4 bg-[#111111] rounded-xl border border-[#2A2A2A]">
                        <div className="text-2xl font-bold text-[#4CBB17]">{formatInr(totalRevenue)}</div>
                        <div className="text-sm text-[#A0A0A0] mt-1">Total Revenue</div>
                    </div>
                    <div className="text-center p-4 bg-[#111111] rounded-xl border border-[#2A2A2A]">
                        <div className="text-2xl font-bold text-[#CD1C18]">{formatInr(totalExpenses)}</div>
                        <div className="text-sm text-[#A0A0A0] mt-1">Total Expenses</div>
                    </div>
                    <div className="text-center p-4 bg-[#111111] rounded-xl border border-[#2A2A2A]">
                        <div className="text-2xl font-bold text-white">{formatInr(netProfit)}</div>
                        <div className="text-sm text-[#A0A0A0] mt-1">Net Profit</div>
                    </div>
                    <div className="text-center p-4 bg-[#111111] rounded-xl border border-[#2A2A2A]">
                        <div className="text-2xl font-bold text-[#60A5FA]">{collectionRate.toFixed(1)}%</div>
                        <div className="text-sm text-[#A0A0A0] mt-1">Collection Rate</div>
                    </div>
                </div>
            </div>
        </div>
    );
}
