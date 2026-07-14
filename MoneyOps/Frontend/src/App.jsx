import { Routes, Route } from "react-router-dom";
import { Toaster } from "sonner";
import LandingPage from "@/pages/LandingPage";
import SignInPage from "@/pages/SignInPage";
import SignUpPage from "@/pages/SignUpPage";
import OnboardingPage from "@/pages/OnboardingPage";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import ClientsPage from "@/pages/ClientsPage";
import CashflowPage from "@/pages/CashflowPage";
import FinancesPage from "@/pages/FinancesPage";
import InvoicesPage from "@/pages/InvoicesPage";
import NewInvoicePage from "@/pages/NewInvoicePage";
import InvoiceDetailPage from "@/pages/InvoiceDetailPage";
import SettingsPage from "@/pages/SettingsPage";
import AnalyticsPage from "@/pages/AnalyticsPage";
import TransactionsPage from "@/pages/TransactionsPage";
import TeamsPage from "@/pages/TeamsPage";
import DocumentsPage from "@/pages/DocumentsPage";
import SalesCRMPage from "@/pages/SalesCRMPage";
import MarketResearchPage from "@/pages/MarketResearchPage";
import FinanceIntelligencePage from "@/pages/FinanceIntelligencePage";
import CompliancePage from "@/pages/CompliancePage";
import OrchestratorPage from "@/pages/OrchestratorPage";
import OrchestratorChatPage from "@/pages/OrchestratorChatPage";
import RecurringInvoicesPage from "@/pages/RecurringInvoicesPage";
import BulkUploadPage from "@/pages/BulkUploadPage";
import DashboardLayout from "@/components/DashboardLayout";
import InviteAcceptPage from "@/pages/InviteAcceptPage";
import OAuth2RedirectPage from "@/pages/OAuth2RedirectPage";

export default function App() {
    return (
        <>
            <Toaster position="top-right" richColors />

            <Routes>
                <Route path="/" element={<LandingPage />} />

                {/* Auth routes */}
                <Route path="/auth/sign-in" element={<SignInPage />} />
                <Route path="/auth/sign-up" element={<SignUpPage />} />
                <Route path="/auth/oauth2/callback" element={<OAuth2RedirectPage />} />

                {/* Onboarding — protected (must be signed in) but no sidebar */}
                <Route
                    path="/onboarding"
                    element={
                        <ProtectedRoute>
                            <OnboardingPage />
                        </ProtectedRoute>
                    }
                />

                {/* Invite acceptance route */}
                <Route
                    path="/auth/invite/:token"
                    element={
                        <ProtectedRoute>
                            <InviteAcceptPage />
                        </ProtectedRoute>
                    }
                />

                {/* Chat workspace — standalone (no sidebar) */}
                <Route
                    path="/agent/chat"
                    element={
                        <ProtectedRoute>
                            <OrchestratorChatPage />
                        </ProtectedRoute>
                    }
                />

                {/* Dashboard Routes (Sidebar + Voice Agent) */}
                <Route
                    element={
                        <ProtectedRoute>
                            <DashboardLayout />
                        </ProtectedRoute>
                    }
                >
                    <Route path="/dashboard" element={<AnalyticsPage />} />
                    <Route path="/cashflow" element={<CashflowPage />} />
                    <Route path="/transactions" element={<TransactionsPage />} />
                    <Route path="/documents" element={<DocumentsPage />} />
                    <Route path="/settings" element={<SettingsPage />} />

                    <Route path="/invoices" element={<InvoicesPage />} />
                    <Route path="/invoices/new" element={<NewInvoicePage />} />
                    <Route path="/invoices/:id" element={<InvoiceDetailPage />} />
                    <Route path="/invoices/recurring" element={<RecurringInvoicesPage />} />
                    <Route path="/invoices/bulk" element={<BulkUploadPage />} />

                    <Route path="/clients" element={<ClientsPage />} />
                    <Route path="/crm" element={<SalesCRMPage />} />
                    <Route path="/market" element={<MarketResearchPage />} />

                    <Route path="/finance" element={<FinancesPage />} />
                    <Route path="/intelligence" element={<FinanceIntelligencePage />} />
                    <Route path="/compliance" element={<CompliancePage />} />

                    <Route path="/agent" element={<OrchestratorPage />} />
                    <Route path="/team" element={<TeamsPage />} />
                </Route>
            </Routes>
        </>
    );
}