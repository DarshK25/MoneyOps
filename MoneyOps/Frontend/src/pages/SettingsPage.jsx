import { useState, useEffect } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { toast } from "sonner";
import { Save, User, Building, Bell, Shield, BadgeCheck, Globe, Briefcase, MapPin, Hash, Target, Users } from "lucide-react";
import { useUser } from "@clerk/clerk-react";
import { useOnboardingStatus } from "@/hooks/useOnboardingStatus";

const inputStyle = {
    backgroundColor: "#1A1A1A",
    border: "1px solid #2A2A2A",
    borderRadius: "8px",
    color: "#ffffff",
    padding: "10px 12px",
    fontSize: "14px",
    width: "100%",
    outline: "none",
    transition: "border-color 0.15s ease",
};

const ENUM_LABELS = {
    businessType: {
        sole_proprietorship: "Sole Proprietorship",
        partnership: "Partnership",
        llp: "Limited Liability Partnership (LLP)",
        private_limited: "Private Limited Company",
        public_limited: "Public Limited Company",
        opc: "One Person Company (OPC)",
    },
    industry: {
        it_software: "IT & Software",
        manufacturing: "Manufacturing",
        retail: "Retail & E-commerce",
        services: "Professional Services",
        healthcare: "Healthcare",
        education: "Education",
        construction: "Construction & Real Estate",
        energy_utilities: "Energy & Utilities",
        finance: "Finance & Banking",
        hospitality: "Hospitality & Tourism",
        logistics: "Logistics & Supply Chain",
        agriculture: "Agriculture & Food",
        media: "Media & Entertainment",
        telecom: "Telecommunications",
        aerospace: "Aerospace & Defence",
        government: "Government & Public Sector",
        other: "Other",
    },
    annualTurnover: {
        below_10l: "Below ₹10 Lakhs",
        "10l_to_1cr": "₹10 Lakhs – ₹1 Crore",
        "1cr_to_10cr": "₹1 Crore – ₹10 Crores",
        above_10cr: "Above ₹10 Crores",
    },
    targetMarket: {
        B2B: "B2B (Business to Business)",
        B2C: "B2C (Business to Consumer)",
        B2G: "B2G (Business to Government)",
    },
    gstFilingFrequency: {
        monthly: "Monthly",
        quarterly: "Quarterly",
    }
};

const getReadable = (category, value) => {
    if (!value) return "Not specified";
    return ENUM_LABELS[category]?.[value] || value.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase());
};

export default function SettingsPage() {
    const { user } = useUser();
    const { orgId, userId } = useOnboardingStatus();
    
    const [profile, setProfile] = useState({
        firstName: "",
        lastName: "",
        email: "",
        phone: "",
        professionalTitle: "",
    });

    const [business, setBusiness] = useState({
        id: "",
        companyName: "",
        tradingName: "",
        businessType: "",
        industry: "",
        registrationDate: "",
        annualTurnover: "",
        primaryEmail: "",
        primaryPhone: "",
        website: "",
        employeeCount: "",
        address: "",
        panNumber: "",
        stateOfRegistration: "",
        gstRegistered: false,
        gstin: "",
        gstFilingFrequency: "",
        tanNumber: "",
        cin: "",
        llpin: "",
        msmeNumber: "",
        iecCode: "",
        professionalTaxReg: "",
        primaryActivity: "",
        targetMarket: "",
        keyProducts: [],
        currentChallenges: [],
        accountingMethod: "",
    });

    const [notifications, setNotifications] = useState({
        invoiceDue: true,
        paymentReceived: true,
        clientUpdates: false,
        weeklyReport: true,
        systemAlerts: true,
    });

    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (user) {
            setProfile({
                firstName: user.firstName || "",
                lastName: user.lastName || "",
                email: user.primaryEmailAddress?.emailAddress || "",
                phone: user.primaryPhoneNumber?.phoneNumber || "",
                professionalTitle: "",
            });
        }

        const fetchBusinessData = async () => {
            if (!userId) return;
            try {
                const response = await fetch(`/api/org/my`, {
                    headers: {
                        "X-User-Id": userId
                    }
                });
                if (response.ok) {
                    const result = await response.json();
                    const data = result.data;
                    if (!data) return;
                    setBusiness({
                        id: data.id,
                        companyName: data.legalName || "",
                        tradingName: data.tradingName || "",
                        businessType: data.businessType || "",
                        industry: data.industry || "",
                        registrationDate: data.registrationDate || "",
                        annualTurnover: data.annualTurnover || "",
                        primaryEmail: data.primaryEmail || "",
                        primaryPhone: data.primaryPhone || "",
                        website: data.website || "",
                        employeeCount: data.employeeCount || "",
                        address: data.registeredAddress || "",
                        panNumber: data.panNumber || "",
                        stateOfRegistration: data.stateOfRegistration || "",
                        gstRegistered: data.gstRegistered || false,
                        gstin: data.gstin || "",
                        gstFilingFrequency: data.gstFilingFrequency || "",
                        tanNumber: data.tanNumber || "",
                        cin: data.cin || "",
                        llpin: data.llpin || "",
                        msmeNumber: data.msmeNumber || "",
                        iecCode: data.iecCode || "",
                        professionalTaxReg: data.professionalTaxReg || "",
                        primaryActivity: data.primaryActivity || "",
                        targetMarket: data.targetMarket || "",
                        keyProducts: data.keyProducts || [],
                        currentChallenges: data.currentChallenges || [],
                        accountingMethod: data.accountingMethod || "",
                    });
                }
            } catch (error) {
                console.error("Failed to fetch business data:", error);
            } finally {
                setLoading(false);
            }
        };

        fetchBusinessData();
    }, [user, orgId, userId]);

    const handleSaveProfile = async () => {
        toast.info("Profile saving via Clerk is currently browse-only");
    };

    const handleSaveBusiness = async () => {
        setLoading(true);
        try {
            const targetId = orgId || business.id; 
            if (!targetId) throw new Error("Organization ID not found");

            const response = await fetch(`/api/org/${targetId}`, {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json",
                    "X-User-Id": userId
                },
                body: JSON.stringify({
                    legalName: business.companyName,
                    tradingName: business.tradingName,
                    businessType: business.businessType,
                    industry: business.industry,
                    registrationDate: business.registrationDate,
                    annualTurnover: business.annualTurnover,
                    primaryEmail: business.primaryEmail,
                    primaryPhone: business.primaryPhone,
                    website: business.website,
                    employeeCount: business.employeeCount,
                    registeredAddress: business.address,
                    panNumber: business.panNumber,
                    stateOfRegistration: business.stateOfRegistration,
                    gstRegistered: business.gstRegistered,
                    gstin: business.gstin,
                    gstFilingFrequency: business.gstFilingFrequency,
                    tanNumber: business.tanNumber,
                    cin: business.cin,
                    llpin: business.llpin,
                    msmeNumber: business.msmeNumber,
                    iecCode: business.iecCode,
                    professionalTaxReg: business.professionalTaxReg,
                    primaryActivity: business.primaryActivity,
                    targetMarket: business.targetMarket,
                    accountingMethod: business.accountingMethod,
                })
            });
            if (!response.ok) throw new Error("Failed to update business");
            toast.success("Business settings saved");
        } catch (error) {
            toast.error(error.message);
        } finally {
            setLoading(false);
        }
    };

    const StatusBadge = ({ value, category }) => (
        <span className="text-[10px] uppercase tracking-wider font-bold px-2 py-0.5 rounded-md bg-[#4CBB1720] text-[#4CBB17] border border-[#4CBB1740]">
            {getReadable(category, value)}
        </span>
    );

    return (
        <div className="flex flex-col gap-6 max-w-6xl mx-auto w-full pb-10">
            {/* ── Header ──────────────────────────────────────────────────────── */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="mo-h1">Settings</h1>
                    <p className="mo-text-secondary mt-1">Manage your account and business configuration</p>
                </div>
                <div className="hidden md:block">
                     <Building className="h-10 w-10 text-[#2A2A2A]" />
                </div>
            </div>

            <Tabs defaultValue="profile" className="flex flex-col gap-6">
                <TabsList className="bg-[#111111] border border-[#2A2A2A] h-auto p-1 rounded-xl w-fit flex gap-1">
                    {[
                        { value: "profile", label: "Profile", icon: User },
                        { value: "business", label: "Business", icon: Building },
                        { value: "notifications", label: "Notifications", icon: Bell },
                        { value: "security", label: "Security", icon: Shield },
                    ].map(({ value, label, icon: Icon }) => (
                        <TabsTrigger
                            key={value}
                            value={value}
                            className="px-5 py-2.5 rounded-lg text-sm font-medium text-[#A0A0A0] data-[state=active]:bg-[#4CBB17] data-[state=active]:text-black transition-all flex items-center gap-2"
                        >
                            <Icon className="h-4 w-4" />
                            {label}
                        </TabsTrigger>
                    ))}
                </TabsList>

                {/* ── Profile Tab ─────────────────────────────────────────────── */}
                <TabsContent value="profile" className="animate-in fade-in duration-300">
                    <div className="mo-card">
                        <div className="flex items-center gap-3 mb-6">
                            <div className="h-10 w-10 rounded-full bg-[#1A1A1A] flex items-center justify-center border border-[#2A2A2A]">
                                <User className="h-5 w-5 text-[#4CBB17]" />
                            </div>
                            <div>
                                <h2 className="mo-h2">Personal Information</h2>
                                <p className="mo-text-secondary text-sm">Update your public profile and contact info</p>
                            </div>
                        </div>

                        <div className="grid gap-6 md:grid-cols-2">
                             {[
                                { label: "First Name", id: "p-first", field: "firstName", placeholder: "John" },
                                { label: "Last Name", id: "p-last", field: "lastName", placeholder: "Doe" },
                                { label: "Email Address", id: "p-email", field: "email", type: "email", placeholder: "john@example.com" },
                                { label: "Phone Number", id: "p-phone", field: "phone", type: "tel", placeholder: "+91 98765 43210" },
                                { label: "Professional Title", id: "p-title", field: "professionalTitle", placeholder: "Managing Director", colSpan: true },
                            ].map(({ label, id, field, type, placeholder, colSpan }) => (
                                <div key={id} className={`grid gap-2 ${colSpan ? "md:col-span-2" : ""}`}>
                                    <label htmlFor={id} className="text-xs font-bold text-[#606060] uppercase tracking-wider">{label}</label>
                                    <input
                                        id={id}
                                        type={type || "text"}
                                        value={profile[field]}
                                        onChange={(e) => setProfile((p) => ({ ...p, [field]: e.target.value }))}
                                        placeholder={placeholder}
                                        style={inputStyle}
                                    />
                                </div>
                            ))}
                        </div>
                        <div className="mt-8 pt-6 border-t border-[#2A2A2A] flex justify-end">
                            <button onClick={handleSaveProfile} className="mo-btn-primary flex items-center gap-2">
                                <Save className="h-4 w-4" /> Save Changes
                            </button>
                        </div>
                    </div>
                </TabsContent>

                {/* ── Business Tab (DETAILED V2) ────────────────────────────────── */}
                <TabsContent value="business" className="animate-in fade-in duration-300">
                    <div className="flex flex-col gap-6">
                        
                        {/* 1. Core Identity Section */}
                        <div className="mo-card">
                            <div className="flex items-center justify-between mb-6">
                                <div className="flex items-center gap-3">
                                    <Globe className="h-5 w-5 text-[#4CBB17]" />
                                    <h3 className="font-bold text-lg">Core Identity</h3>
                                </div>
                                <StatusBadge category="businessType" value={business.businessType} />
                            </div>
                            
                            <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
                                <div className="grid gap-2 md:col-span-2">
                                    <label className="text-[10px] font-bold text-[#606060] uppercase tracking-wider">Legal Business Name</label>
                                    <input value={business.companyName} onChange={e => setBusiness({...business, companyName: e.target.value})} style={inputStyle} />
                                </div>
                                <div className="grid gap-2">
                                    <label className="text-[10px] font-bold text-[#606060] uppercase tracking-wider">Trading Name</label>
                                    <input value={business.tradingName} onChange={e => setBusiness({...business, tradingName: e.target.value})} placeholder="e.g. Acme Stores" style={inputStyle} />
                                </div>
                                <div className="grid gap-2">
                                    <label className="text-[10px] font-bold text-[#606060] uppercase tracking-wider">Industry</label>
                                    <div className="relative">
                                        <input value={getReadable('industry', business.industry)} readOnly style={{...inputStyle, cursor: 'default'}} />
                                        <div className="absolute right-3 top-3"><Briefcase className="h-3.5 w-3.5 text-[#404040]" /></div>
                                    </div>
                                </div>
                                <div className="grid gap-2">
                                    <label className="text-[10px] font-bold text-[#606060] uppercase tracking-wider">Registration Date</label>
                                    <input type="date" value={business.registrationDate} onChange={e => setBusiness({...business, registrationDate: e.target.value})} style={inputStyle} />
                                </div>
                                <div className="grid gap-2">
                                    <label className="text-[10px] font-bold text-[#606060] uppercase tracking-wider">Website URL</label>
                                    <input value={business.website} onChange={e => setBusiness({...business, website: e.target.value})} placeholder="https://" style={inputStyle} />
                                </div>
                            </div>
                        </div>

                         {/* 2. Regulatory & Tax IDs */}
                         <div className="mo-card">
                            <div className="flex items-center gap-3 mb-6">
                                <BadgeCheck className="h-5 w-5 text-[#4CBB17]" />
                                <h3 className="font-bold text-lg">Regulatory & Compliance</h3>
                            </div>
                            
                            <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-4">
                                <div className="grid gap-2">
                                    <label className="text-[10px] font-bold text-[#606060] uppercase tracking-wider">PAN Number</label>
                                    <input value={business.panNumber} onChange={e => setBusiness({...business, panNumber: e.target.value.toUpperCase()})} style={inputStyle} maxLength={10} />
                                </div>
                                <div className="grid gap-2">
                                    <label className="text-[10px] font-bold text-[#606060] uppercase tracking-wider">GSTIN</label>
                                    <input value={business.gstin} onChange={e => setBusiness({...business, gstin: e.target.value.toUpperCase()})} style={inputStyle} maxLength={15} />
                                </div>
                                <div className="grid gap-2">
                                    <label className="text-[10px] font-bold text-[#606060] uppercase tracking-wider">TAN Number</label>
                                    <input value={business.tanNumber} onChange={e => setBusiness({...business, tanNumber: e.target.value.toUpperCase()})} style={inputStyle} />
                                </div>
                                <div className="grid gap-2">
                                    <label className="text-[10px] font-bold text-[#606060] uppercase tracking-wider">State of Reg.</label>
                                    <input value={business.stateOfRegistration} onChange={e => setBusiness({...business, stateOfRegistration: e.target.value})} style={inputStyle} />
                                </div>
                                <div className="grid gap-2">
                                    <label className="text-[10px] font-bold text-[#606060] uppercase tracking-wider">CIN / LLPIN</label>
                                    <input value={business.cin || business.llpin} onChange={e => setBusiness({...business, cin: e.target.value.toUpperCase()})} style={inputStyle} />
                                </div>
                                <div className="grid gap-2">
                                    <label className="text-[10px] font-bold text-[#606060] uppercase tracking-wider">MSME Number</label>
                                    <input value={business.msmeNumber} onChange={e => setBusiness({...business, msmeNumber: e.target.value})} style={inputStyle} />
                                </div>
                                <div className="grid gap-2">
                                    <label className="text-[10px] font-bold text-[#606060] uppercase tracking-wider">IEC Code</label>
                                    <input value={business.iecCode} onChange={e => setBusiness({...business, iecCode: e.target.value})} style={inputStyle} />
                                </div>
                                <div className="grid gap-2">
                                    <label className="text-[10px] font-bold text-[#606060] uppercase tracking-wider">GST Frequency</label>
                                    <input value={getReadable('gstFilingFrequency', business.gstFilingFrequency)} readOnly style={{...inputStyle, cursor: 'default'}} />
                                </div>
                            </div>
                        </div>

                         {/* 3. Operational Context */}
                         <div className="mo-card">
                            <div className="flex items-center gap-3 mb-6">
                                <Target className="h-5 w-5 text-[#4CBB17]" />
                                <h3 className="font-bold text-lg">Operations & Context</h3>
                            </div>
                            
                            <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
                                <div className="grid gap-2">
                                    <label className="text-[10px] font-bold text-[#606060] uppercase tracking-wider">Annual Turnover</label>
                                    <div className="flex items-center gap-2 p-3 bg-[#111111] border border-[#2A2A2A] rounded-lg">
                                        <Hash className="h-3.5 w-3.5 text-[#4CBB17]" />
                                        <span className="text-sm">{getReadable('annualTurnover', business.annualTurnover)}</span>
                                    </div>
                                </div>
                                <div className="grid gap-2">
                                    <label className="text-[10px] font-bold text-[#606060] uppercase tracking-wider">Target Market</label>
                                    <div className="flex items-center gap-2 p-3 bg-[#111111] border border-[#2A2A2A] rounded-lg">
                                        <Users className="h-3.5 w-3.5 text-[#4CBB17]" />
                                        <span className="text-sm">{getReadable('targetMarket', business.targetMarket)}</span>
                                    </div>
                                </div>
                                <div className="grid gap-2">
                                    <label className="text-[10px] font-bold text-[#606060] uppercase tracking-wider">Team Size</label>
                                    <input type="number" value={business.employeeCount} onChange={e => setBusiness({...business, employeeCount: e.target.value})} style={inputStyle} />
                                </div>
                                <div className="grid gap-2">
                                    <label className="text-[10px] font-bold text-[#606060] uppercase tracking-wider">Accounting Method</label>
                                    <div className="flex items-center gap-2 p-3 bg-[#111111] border border-[#2A2A2A] rounded-lg">
                                        <BadgeCheck className="h-3.5 w-3.5 text-[#4CBB17]" />
                                        <span className="text-sm">{business.accountingMethod === 'accrual' ? 'Accrual Basis' : 'Cash Basis'}</span>
                                    </div>
                                </div>
                                <div className="grid gap-2">
                                    <label className="text-[10px] font-bold text-[#606060] uppercase tracking-wider">FY Start Month</label>
                                    <input value={business.fyStartMonth || "April"} readOnly style={{...inputStyle, cursor: 'default'}} />
                                </div>
                                <div className="grid gap-2 md:col-span-3">
                                    <label className="text-[10px] font-bold text-[#606060] uppercase tracking-wider">Primary Activity</label>
                                    <textarea 
                                        value={business.primaryActivity} 
                                        onChange={e => setBusiness({...business, primaryActivity: e.target.value})} 
                                        className="w-full bg-[#1A1A1A] border border-[#2A2A2A] rounded-lg p-3 text-sm text-white focus:outline-none min-h-[80px]" 
                                    />
                                </div>
                            </div>
                        </div>

                         {/* 4. Contact & Location */}
                         <div className="mo-card">
                            <div className="flex items-center gap-3 mb-6">
                                <MapPin className="h-5 w-5 text-[#4CBB17]" />
                                <h3 className="font-bold text-lg">Contact & Address</h3>
                            </div>
                            
                            <div className="grid gap-5 md:grid-cols-2">
                                <div className="grid gap-2">
                                    <label className="text-[10px] font-bold text-[#606060] uppercase tracking-wider">Official Email</label>
                                    <input value={business.primaryEmail} onChange={e => setBusiness({...business, primaryEmail: e.target.value})} style={inputStyle} />
                                </div>
                                <div className="grid gap-2">
                                    <label className="text-[10px] font-bold text-[#606060] uppercase tracking-wider">Official Phone</label>
                                    <input value={business.primaryPhone} onChange={e => setBusiness({...business, primaryPhone: e.target.value})} style={inputStyle} />
                                </div>
                                <div className="grid gap-2 md:col-span-2">
                                    <label className="text-[10px] font-bold text-[#606060] uppercase tracking-wider">Registered Address</label>
                                    <textarea 
                                        value={business.address} 
                                        onChange={e => setBusiness({...business, address: e.target.value})} 
                                        className="w-full bg-[#1A1A1A] border border-[#2A2A2A] rounded-lg p-3 text-sm text-white focus:outline-none min-h-[60px]" 
                                    />
                                </div>
                            </div>
                        </div>

                        <div className="flex justify-end sticky bottom-4 z-10">
                            <button 
                                onClick={handleSaveBusiness} 
                                disabled={loading}
                                className="mo-btn-primary flex items-center gap-2 shadow-2xl disabled:opacity-50"
                            >
                                <Save className="h-4 w-4" /> Save Business Details
                            </button>
                        </div>
                    </div>
                </TabsContent>

                {/* ── Notifications Tab ────────────────────────────────────────── */}
                <TabsContent value="notifications" className="animate-in fade-in duration-300">
                    <div className="mo-card">
                        <div className="flex items-center gap-3 mb-6">
                            <Bell className="h-5 w-5 text-[#4CBB17]" />
                            <h2 className="mo-h2">Communication Preferences</h2>
                        </div>
                        <div className="space-y-4">
                            {Object.entries(notifications).map(([key, enabled]) => {
                                const labels = {
                                    invoiceDue: { title: "Invoice Due Reminders", desc: "Get notified when invoices are about to be due" },
                                    paymentReceived: { title: "Payment Received", desc: "Get notified when a payment is received" },
                                    clientUpdates: { title: "Client Updates", desc: "Notifications when client info changes" },
                                    weeklyReport: { title: "Weekly Report", desc: "Receive a weekly financial summary every Monday" },
                                    systemAlerts: { title: "System Alerts", desc: "Important system and security notifications" },
                                };
                                const info = labels[key];

                                return (
                                    <div key={key} className="flex items-center justify-between p-4 bg-[#111111] rounded-xl border border-[#2A2A2A]">
                                        <div>
                                            <p className="text-sm font-medium text-white">{info.title}</p>
                                            <p className="text-xs text-[#A0A0A0] mt-0.5">{info.desc}</p>
                                        </div>
                                        <button
                                            id={`notif-${key}`}
                                            role="switch"
                                            aria-checked={enabled}
                                            onClick={() => setNotifications((prev) => ({ ...prev, [key]: !prev[key] }))}
                                            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${enabled ? "bg-[#4CBB17]" : "bg-[#2A2A2A]"
                                                }`}
                                        >
                                            <span
                                                className={`inline-block h-4 w-4 transform rounded-full bg-black transition-transform ${enabled ? "translate-x-6" : "translate-x-1"
                                                    }`}
                                            />
                                        </button>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                </TabsContent>

                {/* ── Security Tab ─────────────────────────────────────────────── */}
                <TabsContent value="security" className="animate-in fade-in duration-300">
                    <div className="mo-card">
                        <div className="flex items-center gap-3 mb-6">
                            <Shield className="h-5 w-5 text-[#4CBB17]" />
                            <h2 className="mo-h2">Account Security</h2>
                        </div>
                        <div className="p-6 bg-[#4CBB1708] border border-[#4CBB1715] rounded-2xl flex items-start gap-4">
                            <div className="p-2 bg-[#4CBB1720] rounded-lg">
                                <BadgeCheck className="h-5 w-5 text-[#4CBB17]" />
                            </div>
                            <div>
                                <p className="text-sm text-white font-bold">Authenticated by Clerk</p>
                                <p className="text-sm text-[#A0A0A0] mt-1 leading-relaxed">
                                    Your session and identity are managed by Clerk's enterprise-grade security. 
                                    Multi-factor authentication, session management, and password policies are active.
                                </p>
                            </div>
                        </div>
                    </div>
                </TabsContent>
            </Tabs>
        </div>
    );
}
