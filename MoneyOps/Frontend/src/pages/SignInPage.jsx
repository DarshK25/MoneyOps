import { SignIn } from "@/components/auth/SignIn";
import { useLocation } from "react-router-dom";

export default function SignInPage() {
    const location = useLocation();
    const from = (location.state?.from?.pathname) || "/workspace/overview";

    return <SignIn redirectUrl={from} />;
}
