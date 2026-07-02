import { useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";

export default function OAuth2RedirectPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { setToken } = useAuth();

  useEffect(() => {
    const token = searchParams.get("token");
    const error = searchParams.get("error");

    if (error) {
      toast.error("Authentication failed: " + error);
      navigate("/sign-in");
      return;
    }

    if (token) {
      // Store the token and fetch user data
      const handleOAuthSuccess = async () => {
        try {
          const result = await setToken(token);
          if (result.success) {
            toast.success("Signed in successfully!");
            navigate("/analytics");
          } else {
            throw new Error(result.error || "Failed to authenticate");
          }
        } catch (err) {
          console.error("OAuth redirect error:", err);
          toast.error("Authentication failed. Please try again.");
          navigate("/sign-in");
        }
      };
      
      handleOAuthSuccess();
    } else {
      toast.error("No authentication token received");
      navigate("/sign-in");
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
