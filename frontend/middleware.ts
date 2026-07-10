import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * Auth gate for the authenticated zone.
 * When GOOGLE_CLIENT_ID is set, unauthenticated users are redirected to /login.
 * In local demo mode (no Google OAuth), all routes remain open for development.
 */
export function middleware(req: NextRequest) {
  const googleConfigured = Boolean(
    process.env.GOOGLE_CLIENT_ID && process.env.GOOGLE_CLIENT_SECRET
  );
  if (!googleConfigured) {
    return NextResponse.next();
  }

  const token =
    req.cookies.get("next-auth.session-token")?.value ||
    req.cookies.get("__Secure-next-auth.session-token")?.value;

  if (!token) {
    const login = new URL("/login", req.url);
    login.searchParams.set("callbackUrl", req.nextUrl.pathname);
    return NextResponse.redirect(login);
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    "/dashboard/:path*",
    "/welcome",
    "/settings/:path*",
    "/admin/:path*",
    "/search",
    "/report/:path*",
  ],
};
