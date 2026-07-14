import { useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";

const KNOWN_ERRORS = new Set(["access_denied", "server_error", "temporarily_unavailable"]);

export default function OAuth2RedirectPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { setToken } = useAuth();

  useEffect(() => {
    const token = searchParams.get("token");
    const error = searchParams.get("error");

    if (error) {
      const message = KNOWN_ERRORS.has(error) ? error : "authentication_failed";
      toast.error("Authentication failed: " + message);
      navigate("/auth/sign-in");
      return;
    }

    if (token) {
      window.history.replaceState({}, '', '/auth/oauth2/callback');

      const handleOAuthSuccess = async () => {
        try {
          const result = await setToken(token);
          if (result.success) {
            navigate("/dashboard", { replace: true });
          } else {
            throw new Error(result.error || "Failed to authenticate");
          }
        } catch (err) {
          console.error("OAuth redirect error:", err);
          toast.error("Authentication failed. Please try again.");
          navigate("/auth/sign-in");
        }
      };
      
      handleOAuthSuccess();
    } else {
      toast.error("No authentication token received");
      navigate("/auth/sign-in");
    }
  }, [searchParams, navigate, setToken]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#0A0A0A]">
      <div className="text-center">
        <Loader2 className="w-12 h-12 animate-spin text-[#4CBB17] mx-auto mb-4" />
        <p className="text-white/60">Completing sign in...</p>
      </div>
    </div>
  );
}
