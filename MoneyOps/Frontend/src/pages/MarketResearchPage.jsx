import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { MarketResearchDashboard } from "@/components/MarketResearchDashboard";
import { Loader2 } from "lucide-react";
import { useOnboardingStatus } from "@/hooks/useOnboardingStatus";

export default function MarketResearchPage() {
    const [isHydrated, setIsHydrated] = useState(false);
    const [loading, setLoading] = useState(true);
    const [data, setData] = useState(null);
    const { orgId, userId } = useOnboardingStatus();

    useEffect(() => {
        setIsHydrated(true);
        if (orgId) fetchMarketData();
    }, [orgId]);

    async function fetchMarketData() {
        setLoading(true);
        try {
            const json = await api.get("/api/v1/market/intelligence", { org_uuid: orgId, business_id: 1, user_id: userId || "" });
            setData(json.data || json);
        } catch {
            setData({ data: [], highlights: [] });
        } finally {
            setLoading(false);
        }
    }

    if (!isHydrated || loading) {
        return (
            <div className="flex h-64 items-center justify-center">
                <Loader2 className="h-8 w-8 animate-spin text-[#4CBB17]" />
            </div>
        );
    }

    return (
        <div className="flex flex-col gap-6">
            <MarketResearchDashboard
                businessId={1}
                data={data}
                onRefresh={fetchMarketData}
            />
        </div>
    );
}
