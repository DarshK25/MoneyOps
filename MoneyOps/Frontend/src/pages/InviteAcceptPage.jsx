import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { useUser } from "@/contexts/AuthContext";
import { useOnboardingStatus } from "@/hooks/useOnboardingStatus";
import { Loader2 } from "lucide-react";

export default function InviteAcceptPage() {
    const { token } = useParams();
    const navigate = useNavigate();
    const { isLoaded, isSignedIn } = useUser();
    const { userId: internalUserId, orgId: internalOrgId, isLoading: statusLoading } = useOnboardingStatus();
    const [status, setStatus] = useState("processing");
    const [errorMsg, setErrorMsg] = useState("");

    useEffect(() => {
        if (!isLoaded) return;

        if (!isSignedIn) {
            toast.info("Please sign in to accept the invitation");
            navigate("/auth/sign-up");
            return;
        }

        if (statusLoading || !internalUserId) return;

        const handleAccept = async () => {
            try {
                await api.post(`/api/invites/accept/${token}`);

                toast.success("Successfully joined the organization!");
                navigate("/team");
                
            } catch (err) {
                setStatus("error");
                setErrorMsg(err.message);
                toast.error(err.message);
            }
        };

        handleAccept();
    }, [isLoaded, isSignedIn, token, navigate, statusLoading, internalUserId]);

    if (!isLoaded || statusLoading) {
        return (
            <div className="flex flex-col items-center justify-center min-h-screen bg-black">
               <Loader2 className="h-8 w-8 animate-spin text-[#4CBB17]" />
               <p className="mt-4 text-[#A0A0A0]">Loading...</p>
            </div>
        );
    }

    if (status === "error") {
        return (
            <div className="flex flex-col items-center justify-center min-h-screen bg-black p-4">
                <div className="mo-card max-w-md w-full text-center">
                    <h2 className="text-xl font-bold text-red-500 mb-2">Invalid Invite</h2>
                    <p className="text-[#A0A0A0] mb-6">{errorMsg}</p>
                    <button onClick={() => navigate("/workspace/overview")} className="mo-btn-primary w-full justify-center">Go to Dashboard</button>
                </div>
            </div>
        );
    }

    return (
        <div className="flex flex-col items-center justify-center min-h-screen bg-black">
           <Loader2 className="h-8 w-8 animate-spin text-[#4CBB17]" />
           <p className="mt-4 text-[#A0A0A0]">Accepting invitation...</p>
        </div>
    );
}
