import type { MetadataRoute } from "next";

const SITE_URL = process.env.NEXT_PUBLIC_SITE_URL ?? "https://housefax.ai";

export default function sitemap(): MetadataRoute.Sitemap {
  const now = new Date();
  const routes = [
    "",
    "/search",
    "/pricing",
    "/faq",
    "/sample-report/123-main-street",
    "/login",
    "/signup",
    "/terms",
    "/privacy",
    "/support",
  ];

  return routes.map((path) => ({
    url: `${SITE_URL}${path || "/"}`,
    lastModified: now,
    changeFrequency: path === "" ? "weekly" : "monthly",
    priority: path === "" ? 1 : path === "/pricing" || path === "/search" ? 0.9 : 0.6,
  }));
}
