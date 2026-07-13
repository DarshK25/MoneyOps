import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { Loader2, Star, Quote } from "lucide-react";

const ROTATING_TEXTS = [
  "Automate your invoicing workflow",
  "Track expenses in real-time",
  "AI-powered financial insights",
  "Seamless team collaboration",
  "Smart payment reminders",
  "Compliance made simple",
  "Cash flow forecasting",
  "Instant financial reports"
];

const REVIEWS = [
  {
    name: "Sarah Chen",
    role: "CFO, TechStart Inc",
    text: "MoneyOps reduced our invoice processing time by 85%. Game changer for our finance team.",
    rating: 5
  },
  {
    name: "Michael Rodriguez",
    role: "Founder, GrowthLabs",
    text: "The AI insights helped us identify cash flow issues before they became problems. Incredible platform.",
    rating: 5
  },
  {
    name: "Emily Watson",
    role: "Finance Manager, CloudScale",
    text: "We're getting paid 3x faster since switching to MoneyOps. The automation is seamless.",
    rating: 5
  }
];

const STATS = [
  { value: "$2.5B+", label: "Processed annually" },
  { value: "10K+", label: "Active businesses" },
  { value: "99.9%", label: "Uptime SLA" },
  { value: "4.9/5", label: "Customer rating" }
];

export function SignIn({ redirectUrl = "/" }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [currentTextIndex, setCurrentTextIndex] = useState(0);
  const [currentReviewIndex, setCurrentReviewIndex] = useState(0);
  const navigate = useNavigate();
  const { signIn } = useAuth();

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTextIndex((prev) => (prev + 1) % ROTATING_TEXTS.length);
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentReviewIndex((prev) => (prev + 1) % REVIEWS.length);
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    const result = await signIn(email, password);

    if (result.success) {
      toast.success("Signed in successfully!");
      navigate(redirectUrl);
    } else {
      toast.error(result.error || "Failed to sign in");
    }

    setLoading(false);
  };

  const handleGoogleSignIn = () => {
    const backendUrl = import.meta.env.VITE_API_URL || '';
    window.location.href = `${backendUrl}/oauth2/authorization/google`;
  };

  const currentReview = REVIEWS[currentReviewIndex];

  return (
    <div className="flex min-h-screen bg-[#0A0A0A] overflow-hidden">
      {/* Left Side - Animated Background */}
      <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden bg-[#0A0A0A]">
        {/* Vent Grid with Green Lasers Traveling Along Borders */}
        <svg className="absolute inset-0 w-full h-full" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="2.5" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>

          {(() => {
            const TW = 260, TH = 80, COLS = 8, ROWS = 14;
            const els = [];
            for (let r = 0; r < ROWS; r++) {
              for (let c = 0; c < COLS; c++) {
                const x = c * TW, y1 = r * TH + 30, y2 = r * TH + 70, m1 = r * TH + 10, m2 = r * TH + 50;
                els.push(
                  <path key={`b1-${r}-${c}`} d={`M ${x},${y1} L ${x+60},${y1} L ${x+80},${m1} L ${x+180},${m1} L ${x+200},${y1} L ${x+TW},${y1}`} fill="none" stroke="rgba(180,180,185,0.06)" strokeWidth="0.5" />,
                  <path key={`b2-${r}-${c}`} d={`M ${x},${y2} L ${x+60},${y2} L ${x+80},${m2} L ${x+180},${m2} L ${x+200},${y2} L ${x+TW},${y2}`} fill="none" stroke="rgba(180,180,185,0.06)" strokeWidth="0.5" />,
                  <line key={`s1-${r}-${c}`} x1={x+80} y1={m1} x2={x+80} y2={m2} stroke="rgba(180,180,185,0.06)" strokeWidth="0.5" />,
                  <line key={`s2-${r}-${c}`} x1={x+180} y1={m1} x2={x+180} y2={m2} stroke="rgba(180,180,185,0.06)" strokeWidth="0.5" />,
                );
              }
            }

            function zigzagRow(r, yOff) {
              let d = '';
              for (let c = 0; c < COLS; c++) {
                const x = c * TW, y = r * TH + yOff, m = r * TH + yOff - 20;
                if (c === 0) d += `M ${x},${y} `;
                d += `L ${x+60},${y} L ${x+80},${m} L ${x+180},${m} L ${x+200},${y} L ${x+TW},${y} `;
              }
              return d;
            }

            const vTop = 10, vBot = ROWS * TH + 50;
            const vertCols = [80, 340, 600];

            function diagRamps(r) {
              let d = '';
              for (let c = 0; c < COLS - 1; c++) {
                const x = c * TW, y = r * TH + 30, m = r * TH + 10;
                if (c === 0) d += `M ${x+60},${y} `;
                d += `L ${x+80},${m} L ${x+180},${m} L ${x+200},${y} L ${x+260},${y} L ${x+280},${m} `;
              }
              return d;
            }

            const zigRows = [
              { r: 2, yOff: 70, speed: 9, delay: -8 },
              { r: 5, yOff: 30, speed: 7, delay: -2 },
              { r: 8, yOff: 70, speed: 10, delay: -5 },
              { r: 11, yOff: 30, speed: 8, delay: -7.5 },
            ];
            zigRows.forEach(({ r, yOff, speed, delay }) => {
              els.push(
                <path key={`l-z-${r}-${yOff}`} d={zigzagRow(r, yOff)} fill="none" stroke="#4CBB17" strokeWidth="2" strokeLinecap="round" strokeDasharray="50 2800" className="laser-track" style={{animationDuration: `${speed}s`, animationDelay: `${delay}s`}} filter="url(#glow)" />
              );
            });

            vertCols.forEach((x, i) => {
              els.push(
                <line key={`l-v-${x}`} x1={x} y1={vTop} x2={x} y2={vBot} stroke="#4CBB17" strokeWidth="2" strokeLinecap="round" strokeDasharray="25 1400" className="laser-vert" style={{animationDuration: '5s', animationDelay: `-${1.5 + i * 1.5}s`}} filter="url(#glow)" />
              );
            });

            [3, 9].forEach((r, i) => {
              els.push(
                <path key={`l-d-${r}`} d={diagRamps(r)} fill="none" stroke="#4CBB17" strokeWidth="2" strokeLinecap="round" strokeDasharray="30 1000" className="laser-diag" style={{animationDuration: '7s', animationDelay: `-${1.2 + i * 3}s`}} filter="url(#glow)" />
              );
            });

            return els;
          })()}
        </svg>

        {/* Content Container */}
        <div className="relative z-10 flex flex-col justify-between p-12 w-full">
          {/* Brand */}
          <div>
            <h1 className="text-4xl font-bold text-white mb-2 flex items-center gap-3">
              <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-[#4CBB17] to-[#3DA012] flex items-center justify-center shadow-lg shadow-[#4CBB17]/20">
                <span className="text-white text-2xl font-bold">M</span>
              </div>
              MoneyOps
            </h1>
            <p className="text-white/60 text-lg">Financial operations, automated</p>
          </div>

          {/* Main Content Area */}
          <div className="space-y-8">
            {/* Rotating Feature Text */}
            <div className="space-y-4">
              <h2 className="text-4xl font-bold text-white transition-all duration-500 min-h-[120px] flex items-center">
                {ROTATING_TEXTS[currentTextIndex]}
              </h2>
              <p className="text-white/70 text-lg">
                Join thousands of businesses automating their financial operations with AI-powered intelligence.
              </p>
            </div>

            {/* Customer Review */}
            <div className="backdrop-blur-xl bg-white/5 rounded-2xl border border-white/10 p-6 transition-all duration-500">
              <div className="flex items-center gap-1 mb-3">
                {[...Array(currentReview.rating)].map((_, i) => (
                  <Star key={i} className="w-4 h-4 fill-[#4CBB17] text-[#4CBB17]" />
                ))}
              </div>
              <Quote className="w-8 h-8 text-[#4CBB17] mb-3 opacity-50" />
              <p className="text-white/90 text-base mb-4 leading-relaxed">
                "{currentReview.text}"
              </p>
              <div>
                <p className="text-white font-semibold">{currentReview.name}</p>
                <p className="text-white/60 text-sm">{currentReview.role}</p>
              </div>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-2 gap-4">
              {STATS.map((stat, i) => (
                <div
                  key={i}
                  className="backdrop-blur-xl bg-white/5 rounded-xl border border-white/10 p-4"
                >
                  <div className="text-2xl font-bold text-white mb-1">{stat.value}</div>
                  <div className="text-white/60 text-sm">{stat.label}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Bottom Features */}
          <div className="flex flex-wrap gap-6 text-sm">
            <div className="flex items-center gap-2 text-white/80">
              <div className="w-2 h-2 rounded-full bg-[#4CBB17] animate-pulse" />
              <span>Bank-grade security</span>
            </div>
            <div className="flex items-center gap-2 text-white/80">
              <div className="w-2 h-2 rounded-full bg-[#4CBB17] animate-pulse" />
              <span>24/7 support</span>
            </div>
            <div className="flex items-center gap-2 text-white/80">
              <div className="w-2 h-2 rounded-full bg-[#4CBB17] animate-pulse" />
              <span>Free 14-day trial</span>
            </div>
          </div>
        </div>
      </div>

      {/* Right Side - Sign In Form */}
      <div className="flex-1 flex items-center justify-center p-8 relative">
        {/* Mobile Brand */}
        <div className="lg:hidden absolute top-8 left-8">
          <h1 className="text-2xl font-bold text-white flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#4CBB17] to-[#3DA012] flex items-center justify-center">
              <span className="text-white text-sm font-bold">M</span>
            </div>
            MoneyOps
          </h1>
        </div>

        <div className="w-full max-w-md space-y-8">
          <div className="text-center">
            <h2 className="text-3xl font-bold text-white">Welcome back</h2>
            <p className="mt-2 text-white/60">Sign in to your account</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <Label htmlFor="email" className="text-white/80">Email</Label>
              <Input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="mt-2 bg-white/5 border-white/10 text-white placeholder:text-white/40 focus:border-[#4CBB17] focus:ring-[#4CBB17] backdrop-blur-sm"
                placeholder="you@company.com"
              />
            </div>

            <div>
              <Label htmlFor="password" className="text-white/80">Password</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="mt-2 bg-white/5 border-white/10 text-white placeholder:text-white/40 focus:border-[#4CBB17] focus:ring-[#4CBB17] backdrop-blur-sm"
                placeholder="••••••••"
              />
            </div>

            <Button
              type="submit"
              className="w-full bg-gradient-to-r from-[#4CBB17] to-[#3DA012] hover:from-[#3DA012] hover:to-[#2E8009] text-white font-medium shadow-lg shadow-[#4CBB17]/20"
              disabled={loading}
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Signing in...
                </>
              ) : (
                "Sign In"
              )}
            </Button>
          </form>

          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t border-white/10" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-[#0A0A0A] px-2 text-white/40">Or continue with</span>
            </div>
          </div>

          <Button
            type="button"
            variant="outline"
            className="w-full bg-white/5 border-white/10 hover:bg-white/10 text-white backdrop-blur-sm"
            onClick={handleGoogleSignIn}
          >
            <svg className="mr-2 h-5 w-5" viewBox="0 0 24 24">
              <path
                fill="#4285F4"
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
              />
              <path
                fill="#34A853"
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
              />
              <path
                fill="#FBBC05"
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
              />
              <path
                fill="#EA4335"
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84C6.71 7.07 8.7 5.38 12 5.38z"
              />
            </svg>
            Sign in with Google
          </Button>

          <div className="text-center text-sm">
            <span className="text-white/60">Don't have an account? </span>
            <a href="/sign-up" className="text-[#4CBB17] hover:underline font-medium">
              Sign up
            </a>
          </div>
        </div>
      </div>

      <style>{`
        @keyframes dash-track {
          to { stroke-dashoffset: -2800; }
        }
        @keyframes dash-vert {
          to { stroke-dashoffset: -1400; }
        }
        @keyframes dash-diag {
          to { stroke-dashoffset: -1000; }
        }
        .laser-track {
          animation: dash-track 5s linear infinite;
        }
        .laser-vert {
          animation: dash-vert 3s linear infinite;
        }
        .laser-diag {
          animation: dash-diag 4s linear infinite;
        }
      `}</style>
    </div>
  );
}
